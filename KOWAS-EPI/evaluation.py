"""KOWAS-EPI 평가 도구 (Python 3.9+ 표준 라이브러리만 사용).

  python evaluation.py backtest --model baseline_model.py --out predictions.csv   # 10개 평가 창 롤링 백테스트
  python evaluation.py backtest --model my_model.py --folds 2025-Q3,2026-Q2       # 일부 창만
  python evaluation.py score predictions.csv                                      # 예측 CSV 채점(운영측 채점과 같은 방식)
  python evaluation.py selftest                                                   # 산식·누수 차단 자체 시험

모델 파일은 Model 클래스를 정의한다.
  class Model:
      def fit(self, rows, national): ...                     # 학습 — 평가 창 시작 2주 전까지 공개된 자료
      def predict(self, rows, origin_week, national): ...    # 원점 주차까지 공개된 자료 → {region: (pred_conc, pred_alert)}
rows 는 kowas_epi_panel.csv, national 은 national_weekly.csv 의 행(dict, 값은 문자열)이다.
두 목록 모두 원점 주차 이후 행이 없고, 원점 주차 이후가 목표주인 라벨(target_conc_t2·target_alert_t2)은 빈 문자열로 가려져 있다.
패널·전국 집계 CSV 를 모델 코드에서 직접 읽으면 안 된다(미래 값 누수). 정적 자료(DataON 파생 자료)는 읽어도 된다. plant_meta.csv 도 읽을 수 있으나 채취 기간·등록 여부 열은
2026-09 스냅샷이므로 원점 이후 정보를 쓰면 안 된다(README §4-5).
"""
import argparse, csv, importlib.util, json, math, sys, time
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
COLUMNS = ["region", "date_week", "pred_conc", "pred_alert"]
LABELS = ("target_conc_t2", "target_alert_t2")


class SubmissionError(ValueError):
    pass


def read_csv(name):
    with open(HERE / name, encoding="utf-8-sig") as h:
        return list(csv.DictReader(h))


def parse(k):
    y, w = k.split("-W"); return int(y), int(w)


def shift(k, n):
    d = date.fromisocalendar(*parse(k), 1) + timedelta(weeks=n); i = d.isocalendar(); return f"{i[0]}-W{i[1]:02d}"


def load_folds(selected="all"):
    folds = read_csv("folds.csv")
    if selected == "all":
        return folds
    wanted = selected.split(",")
    unknown = set(wanted) - {f["fold_id"] for f in folds}
    if unknown:
        raise SystemExit(f"없는 평가 창: {sorted(unknown)} — folds.csv 의 fold_id 중에서 고르세요.")
    return [f for f in folds if f["fold_id"] in wanted]


def fold_weeks(fold):
    out, k = [], fold["target_start"]
    while parse(k) <= parse(fold["target_end"]):
        out.append(k); k = shift(k, 1)
    return out


def known_at(panel, week):
    """week 까지 공개된 정보: 이후 행은 빼고, 목표주가 week 이후인 라벨은 가린다."""
    view = []
    for r in panel:
        if parse(r["date_week"]) > parse(week):
            continue
        hidden = parse(r["target_week_t2"]) > parse(week)
        view.append(dict(r, **{c: "" for c in LABELS}) if hidden else dict(r))   # 사본 — 모델이 바꿔도 채점 자료는 그대로
    return view


def national_at(national, week):
    return [dict(r) for r in national if parse(r["date_week"]) <= parse(week)]


# ---------------- 지표 ----------------
def smape(pairs):
    return 100 / len(pairs) * sum(0.0 if abs(y) + abs(p) == 0 else 2 * abs(p - y) / (abs(y) + abs(p)) for p, y in pairs)


def macro_f1(pairs):
    scores = []
    for c in (0, 1):
        tp = sum(p == c and y == c for p, y in pairs)
        fp = sum(p == c and y != c for p, y in pairs)
        fn = sum(p != c and y == c for p, y in pairs)
        scores.append(1.0 if tp + fp + fn == 0 else 2 * tp / (2 * tp + fp + fn))
    return sum(scores) / 2


def score_fold(preds, panel, fold):
    weeks = set(fold_weeks(fold))
    rows = [r for r in panel if r["target_week_t2"] in weeks]
    reg = [(preds[(r["region"], r["target_week_t2"])][0], float(r["target_conc_t2"]), float(r["conc_3wk_avg"]))
           for r in rows if r["target_conc_t2"] != "" and r["conc_3wk_avg"] != ""]
    cls = [(preds[(r["region"], r["target_week_t2"])][1], int(r["target_alert_t2"])) for r in rows if r["target_alert_t2"] != ""]
    s, b, f1 = smape([(p, y) for p, y, _ in reg]), smape([(x, y) for _, y, x in reg]), macro_f1(cls)
    return {"fold_id": fold["fold_id"], "n_reg": len(reg), "n_cls": len(cls), "smape": s, "smape_baseline": b,
            "macro_f1": f1, "score": 0.6 * (1 - s / b) + 0.4 * f1}


def summarize(results):
    final = sum(r["score"] for r in results) / len(results)
    for r in results:
        timing = f"  {r['total_seconds']:.1f}초" if "total_seconds" in r else ""
        failed = f"  실패 → 최저점 처리 ({r['error']})" if r.get("status") == "failed" else ""
        print(f"{r['fold_id']}  회귀 n={r['n_reg']:>3}  sMAPE {r['smape']:6.2f}% (기준선 {r['smape_baseline']:6.2f}%)  "
              f"분류 n={r['n_cls']:>3}  Macro-F1 {r['macro_f1']:.4f}  점수 {r['score']:.4f}{timing}{failed}")
    print(f"최종 정량점수 (평가 창 {len(results)}개 평균) = {final:.4f}")
    return final


# ---------------- 제출 CSV ----------------
def read_submission(path, folds, panel):
    keys = {(r["region"], r["target_week_t2"]) for f in folds for r in panel if r["target_week_t2"] in set(fold_weeks(f))}
    with open(path, encoding="utf-8-sig", newline="") as h:
        reader = csv.reader(h); header = next(reader, None); body = list(reader)
    if header != COLUMNS:
        raise SubmissionError(f"열 이름·순서는 {','.join(COLUMNS)} 이어야 합니다. 받은 헤더: {header}")
    preds, errors = {}, []
    for line, rec in enumerate(body, start=2):
        if len(rec) != 4:
            errors.append(f"{line}행: 열이 4개가 아닙니다"); continue
        k = (rec[0], rec[1])
        if k not in keys:
            continue
        if k in preds:
            errors.append(f"{line}행: {k} 중복"); continue
        try:
            conc = float(rec[2])
        except ValueError:
            conc = float("nan")
        if not math.isfinite(conc) or conc < 0:
            errors.append(f"{line}행: pred_conc 는 유한한 0 이상 실수여야 합니다 ({rec[2]!r})")
        if rec[3] not in ("0", "1"):
            errors.append(f"{line}행: pred_alert 는 정수 0 또는 1 이어야 합니다 ({rec[3]!r})")
        preds[k] = (conc, int(rec[3]) if rec[3] in ("0", "1") else 0)
    missing = sorted(keys - set(preds))
    if missing:
        errors.append(f"평가 키 {len(missing)}개 누락 (예: {missing[:3]})")
    if errors:
        raise SubmissionError("\n".join(errors[:20]))
    return preds


def write_submission(path, preds):
    with open(path, "w", encoding="utf-8", newline="") as h:
        w = csv.writer(h); w.writerow(COLUMNS)
        for (region, week), (conc, alert) in sorted(preds.items(), key=lambda kv: (parse(kv[0][1]), kv[0][0])):
            w.writerow([region, week, repr(float(conc)), int(alert)])


# ---------------- 백테스트 ----------------
def load_model(path):
    spec = importlib.util.spec_from_file_location("participant_model", path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module.Model


def worst_fold(panel, fold, error):
    """실행에 실패한 평가 창: 가능한 최저 점수(sMAPE 200%, Macro-F1 0)로 처리한다."""
    weeks = set(fold_weeks(fold))
    rows = [r for r in panel if r["target_week_t2"] in weeks]
    reg = [(float(r["target_conc_t2"]), float(r["conc_3wk_avg"])) for r in rows if r["target_conc_t2"] != "" and r["conc_3wk_avg"] != ""]
    b = smape([(x, y) for y, x in reg])
    return {"fold_id": fold["fold_id"], "n_reg": len(reg), "n_cls": sum(r["target_alert_t2"] != "" for r in rows),
            "smape": 200.0, "smape_baseline": b, "macro_f1": 0.0, "score": 0.6 * (1 - 200.0 / b),
            "status": "failed", "error": f"{type(error).__name__}: {error}"}


def run_fold(Model, fold, panel, national, regions):
    model = Model()                                        # 창마다 새로 만들어 새로 학습
    model.fit(known_at(panel, fold["train_until"]), national_at(national, fold["train_until"]))
    fold_preds = {}
    for target in fold_weeks(fold):
        origin = shift(target, -2)
        out = model.predict(known_at(panel, origin), origin, national_at(national, origin))
        if set(out) != set(regions):
            raise ValueError(f"원점 {origin}: 17개 시·도 예측이 모두 있어야 합니다 (받은 {len(out)}개)")
        for region, (conc, alert) in out.items():
            conc = float(conc)
            if not math.isfinite(conc) or conc < 0 or float(alert) not in (0.0, 1.0):
                raise ValueError(f"원점 {origin} {region}: 예측값 형식 오류 ({conc}, {alert})")
            fold_preds[(region, target)] = (conc, int(alert))
    return fold_preds


def backtest(model_path, folds, panel, keep_going=False):
    """keep_going=True 이면 실패한 창을 최저점으로 처리하고 다음 창을 계속 실행한다(운영측 채점용)."""
    Model = load_model(model_path)
    national = read_csv("national_weekly.csv")
    regions = sorted({r["region"] for r in panel})
    preds, results = {}, []
    for fold in folds:
        started = time.time()
        try:
            fold_preds = run_fold(Model, fold, panel, national, regions)
        except Exception as exc:
            if not keep_going:
                raise
            res = worst_fold(panel, fold, exc)
        else:
            preds.update(fold_preds)
            res = dict(score_fold(fold_preds, panel, fold), status="ok")
        res["total_seconds"] = round(time.time() - started, 2)
        results.append(res)
    return preds, results


# ---------------- 자체 시험 ----------------
def selftest():
    import tempfile
    assert abs(smape([(110, 100)]) - 100 * 20 / 210) < 1e-12 and smape([(0, 0)]) == 0.0
    assert macro_f1([(1, 1), (0, 0)]) == 1.0 and macro_f1([(0, 0), (0, 0)]) == 1.0
    assert abs(macro_f1([(1, 1), (1, 0), (0, 0)]) - 2 / 3) < 1e-12
    panel = read_csv("kowas_epi_panel.csv"); folds = load_folds()
    # 누수 차단: 원점 이후 행이 없고, 원점 이후 목표주의 라벨은 가려진다
    for f in folds:
        for target in fold_weeks(f)[:2]:
            origin = shift(target, -2); view = known_at(panel, origin)
            assert max(parse(r["date_week"]) for r in view) <= parse(origin)
            assert all(r[c] == "" for r in view if parse(r["target_week_t2"]) > parse(origin) for c in LABELS)
            assert any(r["target_conc_t2"] != "" for r in view)
    # 공식 나이브는 회귀 항이 0 이므로 창별 점수 = 0.4 × Macro-F1
    preds, results = backtest(HERE / "baseline_model.py", folds, panel)
    assert all(abs(r["score"] - 0.4 * r["macro_f1"]) < 1e-9 for r in results)
    with tempfile.TemporaryDirectory() as d:
        good = Path(d) / "ok.csv"; write_submission(good, preds)
        again = read_submission(good, folds, panel)
        assert all(abs(again[k][0] - v[0]) < 1e-9 and again[k][1] == v[1] for k, v in preds.items())
        lines = good.read_text(encoding="utf-8").splitlines()
        for name, bad in (("dup", lines + [lines[1]]), ("missing", lines[:-1]),
                          ("negative", [lines[0], lines[1].rsplit(",", 2)[0] + ",-1,0"] + lines[2:]),
                          ("prob", [lines[0], lines[1].rsplit(",", 1)[0] + ",0.7"] + lines[2:]),
                          ("header", ["region,date_week,pred_alert,pred_conc"] + lines[1:])):
            p = Path(d) / f"{name}.csv"; p.write_text("\n".join(bad) + "\n", encoding="utf-8")
            try:
                read_submission(p, folds, panel)
            except SubmissionError:
                continue
            raise AssertionError(f"{name} 위반을 잡지 못함")
    with tempfile.TemporaryDirectory() as d:
        mutating = Path(d) / "mutating_model.py"          # 넘겨받은 행을 고쳐도 채점 자료는 바뀌지 않아야 한다
        mutating.write_text("class Model:\n    def fit(self, rows, national):\n        pass\n"
                            "    def predict(self, rows, origin_week, national):\n"
                            "        for r in rows:\n            r['target_conc_t2'] = '1'; r['conc_3wk_avg'] = '1'\n"
                            "        return {r['region']: (1.0, 1) for r in rows if r['date_week'] == origin_week}\n", encoding="utf-8")
        before = [dict(r) for r in panel]
        backtest(mutating, folds[:1], panel)
        assert panel == before, "모델이 채점용 자료를 바꿀 수 있음"
        crash = Path(d) / "crash_model.py"
        crash.write_text("class Model:\n    def fit(self, rows, national):\n        raise RuntimeError('boom')\n"
                         "    def predict(self, rows, origin_week, national):\n        return {}\n", encoding="utf-8")
        _, failed = backtest(crash, folds[:2], panel, keep_going=True)
        assert all(r["status"] == "failed" and r["score"] < min(x["score"] for x in results) for r in failed)
        try:
            backtest(crash, folds[:1], panel)
        except RuntimeError:
            pass
        else:
            raise AssertionError("keep_going 없이 실패가 숨겨짐")
    final = sum(r["score"] for r in results) / len(results)
    print(f"selftest 통과 · 공식 나이브 최종 정량점수 {final:.4f} (평가 창 {len(results)}개)")


def main(argv=None):
    ap = argparse.ArgumentParser(description="KOWAS-EPI 평가 도구")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("backtest"); b.add_argument("--model", required=True); b.add_argument("--folds", default="all")
    b.add_argument("--out", default="predictions.csv"); b.add_argument("--json")
    b.add_argument("--keep-going", action="store_true", help="실패한 평가 창을 최저점으로 처리하고 계속 실행(운영측 채점용)")
    s = sub.add_parser("score"); s.add_argument("predictions"); s.add_argument("--folds", default="all")
    sub.add_parser("selftest")
    a = ap.parse_args(argv)
    if a.cmd == "selftest":
        return selftest()
    panel, folds = read_csv("kowas_epi_panel.csv"), load_folds(a.folds)
    if a.cmd == "backtest":
        preds, results = backtest(a.model, folds, panel, keep_going=a.keep_going)
        write_submission(a.out, preds)
        final = summarize(results)
        print(f"예측 {len(preds)}행 → {a.out}")
        if a.json:
            Path(a.json).write_text(json.dumps({"final": final, "folds": results}, ensure_ascii=False, indent=1), encoding="utf-8")
        return
    try:
        preds = read_submission(a.predictions, folds, panel)
    except SubmissionError as exc:
        print("제출 파일 반려:\n" + str(exc), file=sys.stderr); sys.exit(2)
    summarize([score_fold(preds, panel, f) for f in folds])


if __name__ == "__main__":
    main()
