"""
AutoGluon TabularPredictor 실험 — target_alert_t2(급증 경보) 분류.
train/test 분할은 evaluation.py의 known_at() 원칙을 그대로 따른다:
  - 학습: date_week <= train_until 이면서 target_week_t2 <= train_until 인 행만
          (train_until 시점에 실제로 라벨을 알 수 있었던 행만 학습에 씀)
  - 평가: 2026-Q3 fold의 origin 주차(2026-W25~W34, target 2026-W27~W36)에 해당하는 행
시간 순서를 지키는 분할이며 무작위 k-fold를 쓰지 않는다.
target_conc_t2/target_alert_t2/target_week_t2는 라벨로만 쓰고 입력 특징에 넣지 않는다.
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "KOWAS-EPI"))
from evaluation import macro_f1  # noqa: E402 (원본 채점 함수 재사용)

from autogluon.tabular import TabularPredictor

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
OUTDIR = HERE / "tabular_results"
OUTDIR.mkdir(exist_ok=True)

TRAIN_UNTIL = "2026-W25"
FOLD_TARGETS = [f"2026-W{w:02d}" for w in range(27, 37)]


def parse_week(w):
    y, ww = w.split("-W")
    return (int(y), int(ww))


features = pd.read_parquet(DATA / "features.parquet")
labels = pd.read_parquet(DATA / "labels.parquet")
assert not {"target_conc_t2", "target_alert_t2", "target_week_t2"} & set(features.columns)

df = features.merge(labels, on=["region", "date_week"], how="left").sort_values(["region", "week_start_date"]).reset_index(drop=True)

# --- 시차/롤링 특징 (지역별로 인과적으로만 계산 — 미래 값 사용 없음) ---
g = df.groupby("region")
df["conc_mean_lag1"] = g["conc_mean"].shift(1)
df["conc_mean_lag2"] = g["conc_mean"].shift(2)
df["conc_mean_roll4_mean"] = g["conc_mean"].transform(lambda s: s.rolling(4, min_periods=2).mean())
df["conc_mean_roll4_std"] = g["conc_mean"].transform(lambda s: s.rolling(4, min_periods=2).std())
df["momentum_ratio"] = df["conc_mean"] / df["conc_3wk_avg"].replace(0, np.nan)
df["current_alert"] = ((df["conc_mean"] >= 1.3 * df["conc_base_avg"]).astype(float))
df["wow_change_rate_clipped"] = df["wow_change_rate"].clip(-100, 100)

# region을 문자열 카테고리로 그대로 두면 이 환경(AutoGluon 1.6.2 + pandas 2.3.3)의
# CategoryFeatureGenerator에서 "Length of values (2) does not match length of index" 라이브러리
# 버그가 발생한다(원인 미상, region 자체와 무관하게 카테고리형 컬럼이 있으면 재현됨).
# 원-핫 인코딩으로 우회한다 — 트리 기반 모델에는 어차피 동등한 정보량이다.
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
assert not ({"target_conc_t2", "target_alert_t2", "target_week_t2"} & set(FEATURE_COLS)), "라벨이 특징에 섞임 — 누수!"

train_until_tuple = parse_week(TRAIN_UNTIL)
is_row_visible = df["date_week"].map(parse_week) <= train_until_tuple
is_label_visible = df["target_week_t2"].map(parse_week) <= train_until_tuple  # known_at() 원칙과 동일
train_mask = is_row_visible & is_label_visible & df["target_alert_t2"].notna()

test_mask = df["date_week"].isin(FOLD_TARGETS[:0])  # placeholder, 아래에서 origin 기준으로 재설정
origin_weeks = [f"2026-W{w:02d}" for w in range(25, 35)]  # 2026-Q3 fold의 origin들 (target-2)
test_mask = df["date_week"].isin(origin_weeks) & df["target_alert_t2"].notna()

train_df = df.loc[train_mask, FEATURE_COLS + ["target_alert_t2"]].dropna(subset=["target_alert_t2"]).copy()
test_df = df.loc[test_mask, FEATURE_COLS + ["target_alert_t2", "date_week", "region"]].dropna(subset=["target_alert_t2"]).copy()
train_df["target_alert_t2"] = train_df["target_alert_t2"].astype(int)
test_df["target_alert_t2"] = test_df["target_alert_t2"].astype(int)

print(f"학습 행수: {len(train_df)} (date_week<={TRAIN_UNTIL} & target_week_t2<={TRAIN_UNTIL})")
print(f"평가 행수: {len(test_df)} (2026-Q3 fold origin 주차 {origin_weeks[0]}~{origin_weeks[-1]})")
print(f"학습 양성 비율: {train_df['target_alert_t2'].mean():.3f} | 평가 양성 비율: {test_df['target_alert_t2'].mean():.3f}")

predictor = TabularPredictor(
    label="target_alert_t2",
    eval_metric="f1_macro",
    path=str(HERE / "AutogluonModels" / "tabular"),
    verbosity=2,
)
predictor.fit(
    train_df.drop(columns=[]),
    presets="best_quality",
    time_limit=900,
)

try:
    lb = predictor.leaderboard(test_df.drop(columns=["date_week"]), extra_metrics=["accuracy", "balanced_accuracy", "f1"])
    lb.to_csv(OUTDIR / "tabular_leaderboard.csv", index=False)
    print(lb.to_string())
except Exception as exc:
    print(f"predictor.leaderboard() 실패(라이브러리 내부 버그로 추정) — 모델별 수동 채점으로 대체: {exc}")
    rows = []
    for name in predictor.model_names():
        try:
            p = predictor.predict(test_df[FEATURE_COLS], model=name)
            pairs_m = list(zip(p.astype(int).tolist(), test_df["target_alert_t2"].tolist()))
            rows.append({"model": name, "macro_f1_manual": macro_f1(pairs_m)})
        except Exception as exc2:
            rows.append({"model": name, "macro_f1_manual": None, "error": str(exc2)})
    lb = pd.DataFrame(rows).sort_values("macro_f1_manual", ascending=False)
    lb.to_csv(OUTDIR / "tabular_leaderboard_manual.csv", index=False)
    print(lb.to_string())

pred = predictor.predict(test_df[FEATURE_COLS])
pairs = list(zip(pred.astype(int).tolist(), test_df["target_alert_t2"].tolist()))
mf1 = macro_f1(pairs)
print(f"\n[2026-Q3 fold 재현] AutoGluon 최적모델({predictor.model_best}) Macro-F1 = {mf1:.4f}  (README 기준 모델: 0.5810)")

out_pred = test_df[["region", "date_week", "target_alert_t2"]].copy()
out_pred["pred_alert"] = pred.values
out_pred.to_csv(OUTDIR / "fold_2026Q3_predictions.csv", index=False)

with open(OUTDIR / "summary.txt", "w") as f:
    f.write(f"n_train={len(train_df)}\n")
    f.write(f"n_test={len(test_df)}\n")
    f.write(f"macro_f1={mf1:.4f}\n")
    f.write(f"baseline_macro_f1_readme=0.5810\n")

print("\n저장 위치:", OUTDIR)
