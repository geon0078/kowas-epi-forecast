"""
회귀 개선 실험 — 로그공간 학습 ↔ 원스케일 sMAPE 채점 불일치 보정.
저장된 TimeSeriesPredictor(AutogluonModels/ts)를 재학습 없이 불러와서
같은 2026-Q3 fold에 대해 세 가지 후처리 방식을 비교한다:
  (1) baseline: 02_run_timeseries.py와 동일 — 점 예측(mean, 로그공간)을 그대로 지수변환
  (2) quantile_avg: quantile forecast 전체를 지수변환한 뒤 평균 (smearing estimator와 동등한 효과 —
      로그공간 median 최적 예측을 원스케일 기댓값 최적 예측에 가깝게 보정)
  (3) blend: (2)와 conc_3wk_avg 베이스라인을 여러 가중치로 블렌딩 — 최소한 베이스라인 성능 하한 확보
모두 evaluation.py의 smape()를 그대로 import해서 채점(재구현 안 함).
원본 KOWAS-EPI/*.csv는 읽기 전용, target_conc_t2/target_alert_t2는 채점에만 사용.
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "KOWAS-EPI"))
from evaluation import smape  # noqa: E402

from autogluon.timeseries import TimeSeriesDataFrame, TimeSeriesPredictor

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
OUTDIR = HERE / "improve_results"
OUTDIR.mkdir(exist_ok=True)

TRAIN_UNTIL = "2026-W25"
FOLD_TARGETS = [f"2026-W{w:02d}" for w in range(27, 37)]


def parse_week(w):
    y, ww = w.split("-W")
    return (int(y), int(ww))


def week_num(w):
    return int(w.split("-W")[1])


def shift_week(w, k):
    import datetime
    y, ww = parse_week(w)
    d = datetime.date.fromisocalendar(y, ww, 1) + datetime.timedelta(weeks=k)
    iso = d.isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


def calendar_covariates(week_labels):
    import datetime
    wn = np.array([week_num(w) for w in week_labels])
    quarters = []
    for w in week_labels:
        y, ww = parse_week(w)
        d = datetime.date.fromisocalendar(y, ww, 1)
        quarters.append((d.month - 1) // 3 + 1)
    quarters = np.array(quarters)
    return pd.DataFrame({
        "sin_w": np.sin(2 * np.pi * wn / 52), "cos_w": np.cos(2 * np.pi * wn / 52),
        "q1": (quarters == 1).astype(float), "q2": (quarters == 2).astype(float),
        "q3": (quarters == 3).astype(float), "q4": (quarters == 4).astype(float),
    })


features = pd.read_parquet(DATA / "features.parquet")
KNOWN_COLS = ["sin_w", "cos_w", "q1", "q2", "q3", "q4"]
q_dummy = calendar_covariates(features["date_week"].tolist())
features = pd.concat([features.reset_index(drop=True), q_dummy[["q1", "q2", "q3", "q4"]]], axis=1)
PAST_COLS = ["n_sites", "conc_3wk_avg", "conc_base_avg", "wow_change_rate", "precip_mm", "temp_avg",
             "pop_served", "pop_sampled", "n_plants_valid", "treatment_population_sum"]
for c in PAST_COLS:
    features[c] = features[c].fillna(0.0)
TARGET = "conc_log10"
features[TARGET] = features.groupby("region")[TARGET].ffill().fillna(0.0)
ts_cols = ["region", "week_start_date", TARGET] + KNOWN_COLS + PAST_COLS
ts_long = features[ts_cols].rename(columns={"region": "item_id", "week_start_date": "timestamp"})
full_tsdf = TimeSeriesDataFrame.from_data_frame(ts_long, id_column="item_id", timestamp_column="timestamp")
full_tsdf = full_tsdf.convert_frequency("W-SUN").fill_missing_values(method="ffill")

predictor = TimeSeriesPredictor.load(str(HERE / "AutogluonModels" / "ts"))
print("불러온 predictor, quantile_levels =", predictor.quantile_levels)

panel = pd.read_csv(ROOT / "KOWAS-EPI" / "kowas_epi_panel.csv", dtype=str, keep_default_na=False)
panel["conc_3wk_avg"] = pd.to_numeric(panel["conc_3wk_avg"].replace("", np.nan))
panel["target_conc_t2"] = pd.to_numeric(panel["target_conc_t2"].replace("", np.nan))
base_lookup = panel.set_index(["region", "date_week"])["conc_3wk_avg"]
target_lookup = panel.set_index(["region", "date_week"])["target_conc_t2"]

MODEL_NAME = "WeightedEnsemble"  # 02_run_timeseries.py의 기본 배포 모델과 동일 조건으로 비교
rows_out = []
for target_week in FOLD_TARGETS:
    origin = shift_week(target_week, -2)
    origin_date_s = features.loc[features["date_week"] == origin, "week_start_date"]
    if origin_date_s.empty:
        continue
    origin_date = origin_date_s.iloc[0]
    hist, _ = full_tsdf.split_by_time(origin_date + pd.Timedelta(days=1))
    future_weeks = [shift_week(origin, 1), shift_week(origin, 2)]
    fc = calendar_covariates(future_weeks)
    fc["timestamp"] = [features.loc[features["date_week"] == w, "week_start_date"].iloc[0] for w in future_weeks]
    known_list = []
    for region in hist.item_ids:
        tmp = fc.copy()
        tmp["item_id"] = region
        known_list.append(tmp)
    known_future = pd.concat(known_list, ignore_index=True)
    known_tsdf = TimeSeriesDataFrame.from_data_frame(
        known_future[["item_id", "timestamp"] + KNOWN_COLS], id_column="item_id", timestamp_column="timestamp"
    )
    pred = predictor.predict(hist, known_covariates=known_tsdf, model=MODEL_NAME)
    q_cols = [c for c in pred.columns if c != "mean"]
    for region in pred.item_ids:
        sub = pred.loc[region]
        if len(sub) < 2:
            continue
        row = sub.iloc[1]
        pred_log_mean = row["mean"]
        pred_conc_pointexp = max(0.0, 10 ** pred_log_mean - 1)
        q_exp_vals = [max(0.0, 10 ** row[c] - 1) for c in q_cols]
        pred_conc_qavg = float(np.mean(q_exp_vals))
        rows_out.append({
            "region": region, "date_week": target_week, "origin_week": origin,
            "pred_conc_pointexp": pred_conc_pointexp,
            "pred_conc_qavg": pred_conc_qavg,
        })

pdf = pd.DataFrame(rows_out)
pdf["baseline_conc"] = pdf.apply(lambda r: base_lookup.get((r["region"], r["origin_week"]), np.nan), axis=1)
pdf["target_conc_t2"] = pdf.apply(lambda r: target_lookup.get((r["region"], r["origin_week"]), np.nan), axis=1)
scored = pdf.dropna(subset=["target_conc_t2", "baseline_conc"]).copy()
print(f"채점행 n={len(scored)} (이전 실험과 동일해야 함: 164)")

base_pairs = list(zip(scored["baseline_conc"], scored["target_conc_t2"]))
base_smape = smape(base_pairs)

results = {}
for method_col, label in [("pred_conc_pointexp", "point_exp(이전 방식과 동일)"), ("pred_conc_qavg", "quantile_avg(스미어링 보정)")]:
    pairs = list(zip(scored[method_col], scored["target_conc_t2"]))
    s = smape(pairs)
    results[label] = s
    print(f"[{label}] sMAPE={s:.2f}%  베이스라인={base_smape:.2f}%  reg_term={0.6*(1-s/base_smape):.4f}  {'BEATS baseline' if s < base_smape else 'loses to baseline'}")

# --- 블렌딩: quantile_avg 예측과 베이스라인을 alpha로 가중평균, 여러 alpha 그리드 비교 ---
blend_rows = []
for alpha in [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
    blended = alpha * scored["pred_conc_qavg"] + (1 - alpha) * scored["baseline_conc"]
    pairs = list(zip(blended, scored["target_conc_t2"]))
    s = smape(pairs)
    blend_rows.append({"alpha": alpha, "smape": s, "reg_term": 0.6 * (1 - s / base_smape)})
    print(f"[blend alpha={alpha:.1f}] sMAPE={s:.2f}%  reg_term={0.6*(1-s/base_smape):.4f}")

blend_df = pd.DataFrame(blend_rows)
blend_df.to_csv(OUTDIR / "regression_blend_grid.csv", index=False)
best_blend = blend_df.loc[blend_df["smape"].idxmin()]

scored.to_csv(OUTDIR / "regression_predictions_compare.csv", index=False)
with open(OUTDIR / "regression_summary.txt", "w") as f:
    f.write(f"n_scored={len(scored)}\n")
    f.write(f"baseline_smape={base_smape:.4f}\n")
    for label, s in results.items():
        f.write(f"{label}_smape={s:.4f}\n")
    f.write(f"best_blend_alpha={best_blend['alpha']:.2f}\n")
    f.write(f"best_blend_smape={best_blend['smape']:.4f}\n")
    f.write(f"best_blend_reg_term={best_blend['reg_term']:.4f}\n")
    f.write(f"prev_experiment_model_smape=62.58 (참고: 이전 02_run_timeseries.py 결과)\n")

print(f"\n최적 블렌딩: alpha={best_blend['alpha']:.2f}  sMAPE={best_blend['smape']:.2f}%  "
      f"({'BEATS' if best_blend['smape'] < base_smape else 'loses to'} baseline {base_smape:.2f}%)")
print("저장 위치:", OUTDIR)
