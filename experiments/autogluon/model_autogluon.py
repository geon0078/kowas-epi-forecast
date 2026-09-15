"""
README §9-2 Model 인터페이스로 AutoGluon(TimeSeries + Tabular)을 감싼 구현.

- 회귀(pred_conc): TimeSeriesPredictor로 conc_log10을 2주 앞 예측 → quantile 평균(스미어링 보정) →
  conc_3wk_avg 베이스라인과 alpha=0.80으로 블렌딩(2026-Q3 파일럿에서 검증된 값, 전 fold 공통 고정값
  — 이 고정이 알려진 단순화라는 점을 REPORT.md에 명시했다).
- 분류(pred_alert): TabularPredictor. AutoGluon의 자동 모델선택을 그대로 믿을 수 있도록,
  검증용 tuning_data를 "가장 최근 15% 주차"로 시간순으로 직접 떼어내서 넘긴다
  (2026-Q3 파일럿에서 발견된 "정답을 보고 개별 모델을 골라야 이긴다"는 문제를 우회하는 정공법 시도 —
  fit() 시점에 정답(target_alert_t2)에 접근하지 않고도 제대로 된 모델을 고르게 하는 것이 목적).

원본 KOWAS-EPI/*.csv, plant_meta.csv는 읽기 전용. target_conc_t2/target_alert_t2/target_week_t2는
정답으로만 쓰고(분류 학습 레이블) 입력 특징에는 절대 포함하지 않는다.
plant_meta.csv의 in_current_registry/last_sample_week는 쓰지 않고, first_sample_week<=해당 주차
필터만 적용한다(README §4-5).
"""
import datetime
import os
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import torch

torch.set_float32_matmul_precision("high")  # PyTorch2.13+lightning matmul precision 충돌 회피 (파일럿에서 확인된 이슈)

from autogluon.tabular import TabularPredictor
from autogluon.timeseries import TimeSeriesDataFrame, TimeSeriesPredictor

ROOT = Path(__file__).resolve().parents[2]
PLANT_META_PATH = ROOT / "KOWAS-EPI" / "plant_meta.csv"

NUM_COLS = [
    "n_sites", "conc_mean", "conc_log10", "conc_3wk_avg", "conc_base_avg",
    "wow_change_rate", "precip_mm", "temp_avg", "pop_served", "pop_sampled",
]
KNOWN_COLS = ["sin_w", "cos_w", "q1", "q2", "q3", "q4"]
PAST_COLS = [
    "n_sites", "conc_3wk_avg", "conc_base_avg", "wow_change_rate", "precip_mm", "temp_avg",
    "pop_served", "pop_sampled", "n_plants_valid", "treatment_population_sum",
]
TS_TARGET = "conc_log10"
ALPHA_BLEND = 0.80  # 2026-Q3 파일럿에서 튜닝한 값. 전 fold 공통 고정 — 알려진 단순화.

# 스모크 테스트용 오버라이드(환경변수) — 실제 백테스트에서는 설정하지 않으면 기본값(1800/900) 사용.
TS_TIME_LIMIT = int(os.environ.get("AG_TS_TIME_LIMIT", "1800"))
TAB_TIME_LIMIT = int(os.environ.get("AG_TAB_TIME_LIMIT", "900"))
PRESET = os.environ.get("AG_PRESET", "best_quality")


def parse_week(w):
    y, ww = w.split("-W")
    return (int(y), int(ww))


def week_num(w):
    return int(w.split("-W")[1])


def shift_week(w, k):
    y, ww = parse_week(w)
    d = datetime.date.fromisocalendar(y, ww, 1) + datetime.timedelta(weeks=k)
    iso = d.isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


def calendar_row(week_label):
    wn = week_num(week_label)
    y, ww = parse_week(week_label)
    d = datetime.date.fromisocalendar(y, ww, 1)
    q = (d.month - 1) // 3 + 1
    return {
        "sin_w": np.sin(2 * np.pi * wn / 52), "cos_w": np.cos(2 * np.pi * wn / 52),
        "q1": float(q == 1), "q2": float(q == 2), "q3": float(q == 3), "q4": float(q == 4),
    }


_plant_cache = None


def load_plant_meta():
    global _plant_cache
    if _plant_cache is None:
        plant = pd.read_csv(PLANT_META_PATH, dtype=str, keep_default_na=False)
        plant["treatment_population"] = pd.to_numeric(plant["treatment_population"])
        plant["first_sample_week_tuple"] = plant["first_sample_week"].map(parse_week)
        _plant_cache = plant
    return _plant_cache


def plant_agg_for_weeks(weeks):
    plant = load_plant_meta()
    out = []
    for w in weeks:
        wt = parse_week(w)
        valid = plant[plant["first_sample_week_tuple"].map(lambda t: t <= wt)]
        g = valid.groupby("region_code").agg(
            n_plants_valid=("plant_id", "count"),
            treatment_population_sum=("treatment_population", "sum"),
        ).reset_index()
        g["date_week"] = w
        out.append(g)
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame(
        columns=["region_code", "n_plants_valid", "treatment_population_sum", "date_week"])


def build_features_df(rows):
    """rows: evaluation.py가 넘기는 dict(값은 문자열) 리스트. 라벨 열은 그대로 통과시키되(분류 학습용),
    입력 특징 리스트(FEATURE_COLS_TAB, PAST_COLS 등)에는 절대 포함하지 않는다."""
    df = pd.DataFrame(rows)
    for c in NUM_COLS:
        df[c] = pd.to_numeric(df[c].replace("", np.nan))
    df["target_conc_t2"] = pd.to_numeric(df["target_conc_t2"].replace("", np.nan))
    df["target_alert_t2"] = pd.to_numeric(df["target_alert_t2"].replace("", np.nan))
    df["week_start_date"] = pd.to_datetime(df["week_start_date"])
    df["week_no"] = df["date_week"].map(week_num)
    df["quarter"] = df["week_start_date"].dt.quarter
    df["sin_w"] = np.sin(2 * np.pi * df["week_no"] / 52)
    df["cos_w"] = np.cos(2 * np.pi * df["week_no"] / 52)
    df["q1"] = (df["quarter"] == 1).astype(float)
    df["q2"] = (df["quarter"] == 2).astype(float)
    df["q3"] = (df["quarter"] == 3).astype(float)
    df["q4"] = (df["quarter"] == 4).astype(float)

    weeks = sorted(df["date_week"].unique(), key=parse_week)
    plant_agg = plant_agg_for_weeks(weeks)
    df = df.merge(plant_agg, on=["region_code", "date_week"], how="left")
    df["n_plants_valid"] = df["n_plants_valid"].fillna(0.0)
    df["treatment_population_sum"] = df["treatment_population_sum"].fillna(0.0)

    df = df.sort_values(["region", "week_start_date"]).reset_index(drop=True)
    return df


def add_tabular_features(df):
    g = df.groupby("region")
    df["conc_mean_lag1"] = g["conc_mean"].shift(1)
    df["conc_mean_lag2"] = g["conc_mean"].shift(2)
    df["conc_mean_roll4_mean"] = g["conc_mean"].transform(lambda s: s.rolling(4, min_periods=2).mean())
    df["conc_mean_roll4_std"] = g["conc_mean"].transform(lambda s: s.rolling(4, min_periods=2).std())
    df["momentum_ratio"] = df["conc_mean"] / df["conc_3wk_avg"].replace(0, np.nan)
    df["current_alert"] = (df["conc_mean"] >= 1.3 * df["conc_base_avg"]).astype(float)
    df["wow_change_rate_clipped"] = df["wow_change_rate"].clip(-100, 100)
    region_dummies = pd.get_dummies(df["region"], prefix="region").astype(float)
    df = pd.concat([df, region_dummies], axis=1)
    region_cols = list(region_dummies.columns)
    return df, region_cols


TAB_BASE_COLS = [
    "week_no", "quarter", "sin_w", "cos_w",
    "n_sites", "conc_mean", "conc_log10", "conc_3wk_avg", "conc_base_avg",
    "conc_mean_lag1", "conc_mean_lag2", "conc_mean_roll4_mean", "conc_mean_roll4_std",
    "momentum_ratio", "current_alert", "wow_change_rate_clipped",
    "precip_mm", "temp_avg", "pop_served", "pop_sampled",
    "n_plants_valid", "treatment_population_sum",
]


class Model:
    def __init__(self):
        self.tmpdir = Path(tempfile.mkdtemp(prefix="ag_model_"))
        self.ts_predictor = None
        self.tab_predictor = None
        self.feature_cols_tab = None

    def fit(self, rows, national):
        df = build_features_df(rows)
        df[TS_TARGET] = df.groupby("region")[TS_TARGET].ffill().fillna(0.0)
        for c in PAST_COLS:
            df[c] = df[c].fillna(0.0)

        # ---- 회귀: TimeSeriesPredictor ----
        ts_cols = ["region", "week_start_date", TS_TARGET] + KNOWN_COLS + PAST_COLS
        ts_long = df[ts_cols].rename(columns={"region": "item_id", "week_start_date": "timestamp"})
        tsdf = TimeSeriesDataFrame.from_data_frame(ts_long, id_column="item_id", timestamp_column="timestamp")
        tsdf = tsdf.convert_frequency("W-SUN").fill_missing_values(method="ffill")

        self.ts_predictor = TimeSeriesPredictor(
            prediction_length=2, target=TS_TARGET, known_covariates_names=KNOWN_COLS,
            eval_metric="WQL", freq="W-SUN", path=str(self.tmpdir / "ts"), verbosity=1,
        )
        self.ts_predictor.fit(tsdf, presets=PRESET, hyperparameters="default",
                               time_limit=TS_TIME_LIMIT, num_val_windows=3)

        # ---- 분류: TabularPredictor (시간순 tuning_data로 검증 — 정답을 보고 모델 고르지 않음) ----
        df_tab, region_cols = add_tabular_features(df.copy())
        self.feature_cols_tab = TAB_BASE_COLS + region_cols
        train_mask = df_tab["target_alert_t2"].notna()
        train_all = df_tab.loc[train_mask, self.feature_cols_tab + ["target_alert_t2", "date_week"]].copy()
        train_all["target_alert_t2"] = train_all["target_alert_t2"].astype(int)

        uniq_weeks = sorted(train_all["date_week"].unique(), key=parse_week)
        n_hold = max(4, int(len(uniq_weeks) * 0.15))
        hold_weeks = set(uniq_weeks[-n_hold:]) if len(uniq_weeks) > n_hold else set()
        tuning_df = train_all[train_all["date_week"].isin(hold_weeks)].drop(columns=["date_week"])
        fit_df = train_all[~train_all["date_week"].isin(hold_weeks)].drop(columns=["date_week"])

        self.tab_predictor = TabularPredictor(
            label="target_alert_t2", eval_metric="f1_macro", path=str(self.tmpdir / "tabular"), verbosity=1,
        )
        if len(tuning_df) >= 20 and fit_df["target_alert_t2"].nunique() > 1:
            self.tab_predictor.fit(fit_df, tuning_data=tuning_df, presets=PRESET, time_limit=TAB_TIME_LIMIT)
        else:
            # 데이터가 너무 적은 초기 fold — 시간순 홀드아웃을 못 만들면 AutoGluon 기본 분할로 대체
            self.tab_predictor.fit(train_all.drop(columns=["date_week"]), presets=PRESET, time_limit=TAB_TIME_LIMIT)

    def predict(self, rows, origin_week, national):
        df = build_features_df(rows)
        for c in PAST_COLS:
            df[c] = df[c].fillna(0.0)
        df[TS_TARGET] = df.groupby("region")[TS_TARGET].ffill().fillna(0.0)

        regions = sorted(df["region"].unique())
        target_week = shift_week(origin_week, 2)

        # ---- 회귀 예측 ----
        ts_cols = ["region", "week_start_date", TS_TARGET] + KNOWN_COLS + PAST_COLS
        ts_long = df[ts_cols].rename(columns={"region": "item_id", "week_start_date": "timestamp"})
        hist = TimeSeriesDataFrame.from_data_frame(ts_long, id_column="item_id", timestamp_column="timestamp")
        hist = hist.convert_frequency("W-SUN").fill_missing_values(method="ffill")

        future_weeks = [shift_week(origin_week, 1), target_week]
        cal_rows = [dict(calendar_row(w), timestamp=pd.NaT) for w in future_weeks]
        week_to_date = {w: df.loc[df["date_week"] == w, "week_start_date"] for w in future_weeks}
        known_list = []
        for region in hist.item_ids:
            for i, w in enumerate(future_weeks):
                d = week_to_date[w]
                ts = d.iloc[0] if len(d) else (
                    pd.Timestamp(hist.loc[region].index[-1]) + pd.Timedelta(weeks=i + 1))
                row = dict(calendar_row(w))
                row.update(item_id=region, timestamp=ts)
                known_list.append(row)
        known_future = pd.DataFrame(known_list)
        known_tsdf = TimeSeriesDataFrame.from_data_frame(
            known_future[["item_id", "timestamp"] + KNOWN_COLS], id_column="item_id", timestamp_column="timestamp")

        pred = self.ts_predictor.predict(hist, known_covariates=known_tsdf)
        q_cols = [c for c in pred.columns if c != "mean"]

        origin_row = df[df["date_week"] == origin_week].set_index("region")
        pred_conc = {}
        for region in regions:
            if region in pred.item_ids and len(pred.loc[region]) >= 2:
                row = pred.loc[region].iloc[1]
                q_vals = [max(0.0, 10 ** row[c] - 1) for c in q_cols]
                model_conc = float(np.mean(q_vals))
            else:
                model_conc = 0.0
            baseline_conc = origin_row.loc[region, "conc_3wk_avg"] if region in origin_row.index else np.nan
            if pd.isna(baseline_conc):
                # 베이스라인이 없으면(그 시점 결측) 해당 지역의 가장 최근 conc_3wk_avg/conc_mean으로 대체
                hist_r = df[(df["region"] == region) & (df["date_week"] <= origin_week)]
                fallback = hist_r["conc_3wk_avg"].dropna()
                baseline_conc = float(fallback.iloc[-1]) if len(fallback) else model_conc
            conc = ALPHA_BLEND * model_conc + (1 - ALPHA_BLEND) * float(baseline_conc)
            pred_conc[region] = max(0.0, float(conc))

        # ---- 분류 예측 ----
        df_tab, region_cols = add_tabular_features(df.copy())
        origin_tab = df_tab[df_tab["date_week"] == origin_week].set_index("region")
        pred_alert = {}
        for region in regions:
            if region in origin_tab.index:
                x_row = origin_tab.loc[[region], self.feature_cols_tab]
                a = int(self.tab_predictor.predict(x_row).iloc[0])
            else:
                a = 0
            pred_alert[region] = a

        return {region: (pred_conc[region], pred_alert[region]) for region in regions}
