"""
KOWAS-EPI 데이터를 AutoGluon 실험용으로 가공한다.
원본 KOWAS-EPI/*.csv는 읽기 전용으로만 연다 — 절대 덮어쓰지 않는다.
target_conc_t2 / target_alert_t2 / target_week_t2 는 정답(라벨)이므로
여기서 만드는 "특징(feature)" 테이블에는 절대 포함하지 않는다.
"""
import pandas as pd
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KOWAS = ROOT / "KOWAS-EPI"
OUT = Path(__file__).resolve().parent / "data"
OUT.mkdir(exist_ok=True)


def parse_week(w):
    y, ww = w.split("-W")
    return (int(y), int(ww))


def week_num(w):
    return int(w.split("-W")[1])


panel = pd.read_csv(KOWAS / "kowas_epi_panel.csv", dtype=str, keep_default_na=False)
plant = pd.read_csv(KOWAS / "plant_meta.csv", dtype=str, keep_default_na=False)

num_cols = [
    "n_sites", "conc_mean", "conc_log10", "conc_3wk_avg", "conc_base_avg",
    "wow_change_rate", "precip_mm", "temp_avg", "pop_served", "pop_sampled",
]
for c in num_cols:
    panel[c] = pd.to_numeric(panel[c].replace("", np.nan))

panel["week_start_date"] = pd.to_datetime(panel["week_start_date"])
panel["week_no"] = panel["date_week"].map(week_num)
panel["week_tuple"] = panel["date_week"].map(parse_week)
panel["quarter"] = panel["week_start_date"].dt.quarter
panel["sin_w"] = np.sin(2 * np.pi * panel["week_no"] / 52)
panel["cos_w"] = np.cos(2 * np.pi * panel["week_no"] / 52)

# target_week_t2 는 그대로 보존해서 뒤 단계(라벨 결합)에서만 쓴다 — 특징으로는 쓰지 않는다.
labels = panel[["region", "date_week", "target_week_t2", "target_conc_t2", "target_alert_t2"]].copy()
labels["target_conc_t2"] = pd.to_numeric(labels["target_conc_t2"].replace("", np.nan))
labels["target_alert_t2"] = pd.to_numeric(labels["target_alert_t2"].replace("", np.nan))

# --- plant_meta: 원점 시점까지 유효한(first_sample_week <= 원점) 처리장만 집계 ---
# in_current_registry, last_sample_week 는 미래 정보이므로 절대 쓰지 않는다(README 4-5).
plant_num = plant.copy()
plant_num["treatment_population"] = pd.to_numeric(plant_num["treatment_population"])
plant_first_tuple = plant_num["first_sample_week"].map(parse_week)

all_weeks = sorted(panel["date_week"].unique(), key=parse_week)
region_codes = sorted(panel["region_code"].unique())

plant_agg_rows = []
for w in all_weeks:
    wt = parse_week(w)
    valid = plant_num[plant_first_tuple.map(lambda t: t <= wt)]
    g = valid.groupby("region_code").agg(
        n_plants_valid=("plant_id", "count"),
        treatment_population_sum=("treatment_population", "sum"),
    )
    g["date_week"] = w
    plant_agg_rows.append(g.reset_index())
plant_agg = pd.concat(plant_agg_rows, ignore_index=True)

panel = panel.merge(plant_agg, on=["region_code", "date_week"], how="left")
panel["n_plants_valid"] = panel["n_plants_valid"].fillna(0)
panel["treatment_population_sum"] = panel["treatment_population_sum"].fillna(0)

# --- 특징 테이블(라벨 없음) + 라벨 테이블 분리 저장 ---
feature_cols = [
    "date_week", "week_start_date", "week_no", "quarter", "sin_w", "cos_w",
    "region", "region_code", "n_sites", "conc_mean", "conc_log10",
    "conc_3wk_avg", "conc_base_avg", "wow_change_rate", "precip_mm", "temp_avg",
    "pop_served", "pop_sampled", "missing_reason",
    "n_plants_valid", "treatment_population_sum",
]
features = panel[feature_cols].sort_values(["region", "week_start_date"]).reset_index(drop=True)

assert not {"target_conc_t2", "target_alert_t2", "target_week_t2"} & set(features.columns), \
    "라벨 컬럼이 특징 테이블에 섞였다 — 누수!"

features.to_parquet(OUT / "features.parquet", index=False)
labels.to_parquet(OUT / "labels.parquet", index=False)

print("features shape:", features.shape)
print("labels shape:", labels.shape)
print("date range:", features["date_week"].min(), "~", features["date_week"].max())
print("regions:", features["region"].nunique())
print("saved to:", OUT)
