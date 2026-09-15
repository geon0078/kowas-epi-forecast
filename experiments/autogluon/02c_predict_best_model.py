"""
저장된 TimeSeriesPredictor를 재학습 없이 불러와서, 리더보드 test 점수 1위 모델(Toto2)로
2026-Q3 fold를 다시 예측하고 sMAPE를 비교한다 (기본값인 WeightedEnsemble과 대조).
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "KOWAS-EPI"))
from evaluation import smape

from autogluon.timeseries import TimeSeriesDataFrame, TimeSeriesPredictor

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"

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

panel = pd.read_csv(ROOT / "KOWAS-EPI" / "kowas_epi_panel.csv", dtype=str, keep_default_na=False)
panel["conc_3wk_avg"] = pd.to_numeric(panel["conc_3wk_avg"].replace("", np.nan))
panel["target_conc_t2"] = pd.to_numeric(panel["target_conc_t2"].replace("", np.nan))
base_lookup = panel.set_index(["region", "date_week"])["conc_3wk_avg"]
target_lookup = panel.set_index(["region", "date_week"])["target_conc_t2"]

for model_name in ["Toto2", "WeightedEnsemble"]:
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
        known_rows = [dict(fc.iloc[i]) for i in range(len(fc))]
        known_list = []
        for region in hist.item_ids:
            tmp = fc.copy()
            tmp["item_id"] = region
            known_list.append(tmp)
        known_future = pd.concat(known_list, ignore_index=True)
        known_tsdf = TimeSeriesDataFrame.from_data_frame(known_future[["item_id", "timestamp"] + KNOWN_COLS], id_column="item_id", timestamp_column="timestamp")
        pred = predictor.predict(hist, known_covariates=known_tsdf, model=model_name)
        for region in pred.item_ids:
            sub = pred.loc[region]
            if len(sub) < 2:
                continue
            pred_log = sub.iloc[1]["mean"]
            pred_conc = max(0.0, 10 ** pred_log - 1)
            rows_out.append({"region": region, "date_week": target_week, "pred_conc": pred_conc})

    pdf = pd.DataFrame(rows_out)
    origin_map = {tw: shift_week(tw, -2) for tw in FOLD_TARGETS}
    pdf["origin_week"] = pdf["date_week"].map(origin_map)
    pdf["baseline_conc"] = pdf.apply(lambda r: base_lookup.get((r["region"], r["origin_week"]), np.nan), axis=1)
    pdf["target_conc_t2"] = pdf.apply(lambda r: target_lookup.get((r["region"], r["origin_week"]), np.nan), axis=1)
    scored = pdf.dropna(subset=["target_conc_t2", "baseline_conc"])
    model_pairs = list(zip(scored["pred_conc"], scored["target_conc_t2"]))
    base_pairs = list(zip(scored["baseline_conc"], scored["target_conc_t2"]))
    ms = smape(model_pairs)
    bs = smape(base_pairs)
    print(f"[{model_name}] n={len(scored)} sMAPE={ms:.2f}%  baseline={bs:.2f}%  reg_term={0.6*(1-ms/bs):.4f}")
    pdf.to_csv(HERE / "ts_results" / f"fold_2026Q3_predictions_{model_name}.csv", index=False)
