"""공식 나이브 기준 모델 — 제출 코드 인터페이스 예시.

회귀: 원점 주차의 KOWAS 제공 3주 평균값(conc_3wk_avg)을 그대로 2주 후 농도로 예측
분류: 원점 주차 농도가 기준선의 1.3배 이상이면 2주 후에도 경보(현재 경보 지속 규칙)
원점 주차 값이 비어 있으면 그 시·도의 가장 최근 값을 쓴다.
"""


class Model:
    def fit(self, rows, national):
        # 학습할 것이 없는 규칙 모델. 실제 모델은 rows·national(창 시작 2주 전까지 공개된 자료)로 학습한다.
        pass

    def predict(self, rows, origin_week, national):
        latest, current = {}, {}
        for r in rows:                                   # rows 는 주차 순으로 정렬되어 있다
            if r["conc_3wk_avg"] != "" or r["conc_mean"] != "":
                latest[r["region"]] = r
            if r["date_week"] == origin_week:
                current[r["region"]] = r
        out = {}
        for region in sorted({r["region"] for r in rows}):
            cur = current.get(region)
            ref = cur if cur and (cur["conc_3wk_avg"] or cur["conc_mean"]) else latest.get(region)
            conc = float(ref["conc_3wk_avg"] or ref["conc_mean"]) if ref else 0.0
            alert = int(cur is not None and cur["conc_mean"] != "" and cur["conc_base_avg"] != ""
                        and float(cur["conc_mean"]) >= 1.3 * float(cur["conc_base_avg"]))
            out[region] = (conc, alert)
        return out
