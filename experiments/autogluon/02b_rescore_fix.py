"""
02_run_timeseries.py의 채점 버그 수정판.
버그: 모델 입력용으로 conc_3wk_avg 결측치를 0으로 채운 컬럼을 베이스라인 조회에도 재사용해서
      실제로는 결측이라 채점에서 빠져야 할 행이 baseline_conc=0으로 들어가 sMAPE를 왜곡시켰다
      (evaluation.py의 score_fold()는 conc_3wk_avg가 빈 문자열인 행을 아예 제외한다).
여기서는 원본 패널을 다시 읽어(결측을 0으로 채우지 않고) 베이스라인만 정확히 재계산한다.
모델 재학습은 필요 없다 — 이미 저장된 예측값(fold_2026Q3_predictions.csv)만 재채점한다.
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "KOWAS-EPI"))
from evaluation import smape

HERE = Path(__file__).resolve().parent
panel = pd.read_csv(ROOT / "KOWAS-EPI" / "kowas_epi_panel.csv", dtype=str, keep_default_na=False)
panel["conc_3wk_avg"] = pd.to_numeric(panel["conc_3wk_avg"].replace("", np.nan))
panel["target_conc_t2"] = pd.to_numeric(panel["target_conc_t2"].replace("", np.nan))

pred_df = pd.read_csv(HERE / "ts_results" / "fold_2026Q3_predictions.csv")

FOLD_TARGETS = [f"2026-W{w:02d}" for w in range(27, 37)]


def parse_week(w):
    y, ww = w.split("-W")
    return (int(y), int(ww))


def shift_week(w, k):
    import datetime
    y, ww = parse_week(w)
    d = datetime.date.fromisocalendar(y, ww, 1) + datetime.timedelta(weeks=k)
    iso = d.isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


origin_map = {tw: shift_week(tw, -2) for tw in FOLD_TARGETS}
pred_df["origin_week"] = pred_df["date_week"].map(origin_map)

base_lookup = panel.set_index(["region", "date_week"])["conc_3wk_avg"]  # 결측은 NaN 그대로 유지
target_lookup = panel.set_index(["region", "date_week"])["target_conc_t2"]

pred_df["baseline_conc"] = pred_df.apply(lambda r: base_lookup.get((r["region"], r["origin_week"]), np.nan), axis=1)
pred_df["target_conc_t2"] = pred_df.apply(lambda r: target_lookup.get((r["region"], r["origin_week"]), np.nan), axis=1)

# evaluation.py의 score_fold()와 동일 필터: target_conc_t2, conc_3wk_avg 둘 다 있는 행만
scored = pred_df.dropna(subset=["target_conc_t2", "baseline_conc"])

model_pairs = list(zip(scored["pred_conc"], scored["target_conc_t2"]))
base_pairs = list(zip(scored["baseline_conc"], scored["target_conc_t2"]))
model_smape = smape(model_pairs)
base_smape = smape(base_pairs)
reg_term = 0.6 * (1 - model_smape / base_smape)

print(f"[수정 재채점] 채점행 n={len(scored)} (README folds.csv 2026-Q3 n_regression_labels=165(164))")
print(f"AutoGluon TS 모델 sMAPE = {model_smape:.2f}%")
print(f"베이스라인(conc_3wk_avg, 결측 제외) sMAPE = {base_smape:.2f}%  (README 공식표: 60.46%)")
print(f"회귀 항 점수 0.6*(1-smape/base) = {reg_term:.4f}  (README 기준모델 2026-Q3 창점수: 0.2324, 이 중 회귀항은 0)")

with open(HERE / "ts_results" / "summary_fixed.txt", "w") as f:
    f.write(f"n_scored={len(scored)}\n")
    f.write(f"model_smape={model_smape:.4f}\n")
    f.write(f"baseline_smape={base_smape:.4f}\n")
    f.write(f"baseline_smape_readme_official=60.46\n")
    f.write(f"regression_term={reg_term:.4f}\n")
