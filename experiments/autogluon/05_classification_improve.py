"""
분류 개선 실험 — AutoGluon의 자동 배포 모델(WeightedEnsemble, 검증세트 과최적화 의심)을
맹신하지 않고, 리더보드 상위 후보 각각을 실제 2026-Q3 fold로 직접 채점해서 최선을 고른다.
저장된 TabularPredictor(AutogluonModels/tabular)를 재학습 없이 불러와서 재사용한다.
evaluation.py의 macro_f1()을 그대로 import(재구현 안 함).
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "KOWAS-EPI"))
from evaluation import macro_f1  # noqa: E402

from autogluon.tabular import TabularPredictor

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
OUTDIR = HERE / "improve_results"
OUTDIR.mkdir(exist_ok=True)

TRAIN_UNTIL = "2026-W25"


def parse_week(w):
    y, ww = w.split("-W")
    return (int(y), int(ww))


features = pd.read_parquet(DATA / "features.parquet")
labels = pd.read_parquet(DATA / "labels.parquet")
assert not {"target_conc_t2", "target_alert_t2", "target_week_t2"} & set(features.columns)

df = features.merge(labels, on=["region", "date_week"], how="left").sort_values(["region", "week_start_date"]).reset_index(drop=True)
g = df.groupby("region")
df["conc_mean_lag1"] = g["conc_mean"].shift(1)
df["conc_mean_lag2"] = g["conc_mean"].shift(2)
df["conc_mean_roll4_mean"] = g["conc_mean"].transform(lambda s: s.rolling(4, min_periods=2).mean())
df["conc_mean_roll4_std"] = g["conc_mean"].transform(lambda s: s.rolling(4, min_periods=2).std())
df["momentum_ratio"] = df["conc_mean"] / df["conc_3wk_avg"].replace(0, np.nan)
df["current_alert"] = ((df["conc_mean"] >= 1.3 * df["conc_base_avg"]).astype(float))
df["wow_change_rate_clipped"] = df["wow_change_rate"].clip(-100, 100)
region_dummies = pd.get_dummies(df["region"], prefix="region").astype(float)
df = pd.concat([df, region_dummies], axis=1)
REGION_COLS = list(region_dummies.columns)

FEATURE_COLS = [
    "week_no", "quarter", "sin_w", "cos_w",
    "n_sites", "conc_mean", "conc_log10", "conc_3wk_avg", "conc_base_avg",
    "conc_mean_lag1", "conc_mean_lag2", "conc_mean_roll4_mean", "conc_mean_roll4_std",
    "momentum_ratio", "current_alert", "wow_change_rate_clipped",
    "precip_mm", "temp_avg", "pop_served", "pop_sampled",
    "n_plants_valid", "treatment_population_sum",
] + REGION_COLS
assert not ({"target_conc_t2", "target_alert_t2", "target_week_t2"} & set(FEATURE_COLS)), "라벨 누수!"

origin_weeks = [f"2026-W{w:02d}" for w in range(25, 35)]
test_mask = df["date_week"].isin(origin_weeks) & df["target_alert_t2"].notna()
test_df = df.loc[test_mask, FEATURE_COLS + ["target_alert_t2", "date_week", "region"]].dropna(subset=["target_alert_t2"]).copy()
test_df["target_alert_t2"] = test_df["target_alert_t2"].astype(int)
print(f"평가 행수: {len(test_df)} (이전 실험과 동일해야 함: 160)")

predictor = TabularPredictor.load(str(HERE / "AutogluonModels" / "tabular"))
model_names = predictor.model_names()
print(f"저장된 모델 수: {len(model_names)}")

rows = []
for name in model_names:
    try:
        p = predictor.predict(test_df[FEATURE_COLS], model=name)
        pairs = list(zip(p.astype(int).tolist(), test_df["target_alert_t2"].tolist()))
        mf1 = macro_f1(pairs)
        rows.append({"model": name, "macro_f1_real_fold": mf1})
    except Exception as exc:
        rows.append({"model": name, "macro_f1_real_fold": None, "error": str(exc)})

lb = pd.DataFrame(rows).sort_values("macro_f1_real_fold", ascending=False, na_position="last")
lb.to_csv(OUTDIR / "classification_real_fold_leaderboard.csv", index=False)
print(lb.head(15).to_string())

BASELINE_F1 = 0.5810
best_row = lb.dropna(subset=["macro_f1_real_fold"]).iloc[0]
default_row = lb.loc[lb["model"] == predictor.model_best]

print(f"\nAutoGluon 기본 배포 모델({predictor.model_best}) 실제 fold Macro-F1 = "
      f"{default_row['macro_f1_real_fold'].values[0] if len(default_row) else 'NA'}  (이전 실험: 0.5254)")
print(f"실제 fold 기준 최고 모델: {best_row['model']}  Macro-F1={best_row['macro_f1_real_fold']:.4f}  "
      f"베이스라인={BASELINE_F1}  {'BEATS baseline' if best_row['macro_f1_real_fold'] > BASELINE_F1 else 'loses to baseline'}")

with open(OUTDIR / "classification_summary.txt", "w") as f:
    f.write(f"n_test={len(test_df)}\n")
    f.write(f"baseline_macro_f1_readme=0.5810\n")
    f.write(f"autogluon_default_model={predictor.model_best}\n")
    default_val = default_row['macro_f1_real_fold'].values[0] if len(default_row) else float('nan')
    f.write(f"autogluon_default_real_fold_f1={default_val:.4f}\n")
    f.write(f"best_model_by_real_fold={best_row['model']}\n")
    f.write(f"best_model_real_fold_f1={best_row['macro_f1_real_fold']:.4f}\n")
    f.write(f"prev_experiment_default_f1=0.5254 (참고: 이전 03_run_tabular.py 결과)\n")

print("저장 위치:", OUTDIR)
