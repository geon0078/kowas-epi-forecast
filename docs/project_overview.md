# KOWAS-EPI 프로젝트 개요 — 주제 · 데이터 · 변수 간 관계

작성일: 2026-09-15

## 가정 및 전제

- 이 문서는 지금까지 검증된 산출물(`docs/data_inventory.md`, `docs/variable_specification.md`, `docs/literature/review.md`, `reports/midterm/eda_findings.md`, `figures/01~10.png`)의 내용을 "주제/데이터/변수 간 관계" 세 축으로 재구성한 종합 문서다. 새로운 계산은 하지 않았고, 기존에 실제로 검증한 수치만 인용했다.
- 변수 간 관계 섹션의 상관계수·검정 결과는 모두 2단계 EDA(fold별 fitting 기간 재현)에서 직접 계산한 값이며, README에 보고된 전체데이터 값과 별도로 표시했다.

---

## 1. 주제

**과제**: 질병관리청 KOWAS 하수 기반 감염병 감시 데이터를 이용해, **시·도별 2주 뒤(t+2) 하수 바이러스 농도**(회귀, `pred_conc`)와 **급증 경보**(분류, `pred_alert`, 농도 ≥ 기준선×1.3)를 예측하는 모델을 만드는 것이다(README §1~§2).

**동기**: 하수 기반 역학(WBE)은 임상 신고보다 앞서 유행을 포착할 수 있다는 기대에서 출발하지만, 문헌 리뷰(`docs/literature/review.md`)와 자체 EDA를 종합하면 이 기대가 이 데이터에 단순하게 적용되지 않는다는 것이 이번 프로젝트의 핵심 발견이다:
- 문헌상 WBE의 전형적 선행 시차는 며칠~2주 수준으로 보고 폭이 좁다.
- 이 데이터의 하수-임상 교차상관은 시차 0주 부근에서 최대이고, 그 최대 지점조차 평가 창(시간)에 따라 이동한다(`figures/03_xcorr_heatmap.png`).
- 따라서 "하수가 항상 임상을 선행한다"는 단순 가정에 의존할 수 없는, 예상보다 도전적인 예측 과제다.

**목표**: 기준 나이브 모델(최종 정량점수 0.2212, README §8-3)을 넘어서는 모델을 개발하며, 대학원 시계열/AI 예측 수업 중간보고서와 KISTI 경진대회 제출을 병행한다.

---

## 2. 데이터

### 2-1. 구성 파일

| 파일 | 행 | 역할 |
|---|---|---|
| `kowas_epi_panel.csv` | 3,043 (17개 시·도 × 179주) | 핵심 패널 — 입력 16열 + 라벨 2열 |
| `national_weekly.csv` | 179 | 전국 하수 집계 + 전국 코로나19 신고수(보조 입력) |
| `plant_meta.csv` | 118 | 처리장 위치·처리인구(시점 주의 필요) |
| `folds.csv` | 10 | 평가 창(2024-Q2~2026-Q3) 정의 |
| `eval_keys.csv` | 2,159 | 채점 대상 키 |
| `dataon_reference.csv` | 4 | 이종 도메인 융합 후보(원자료 미포함) |

전체 스키마·값 범위·결측 건수는 `docs/variable_specification.md`(변수명세서)에 정리되어 있다.

### 2-2. 핵심 특성

- **극단적 스케일 차이**: `conc_mean`은 2.58~50,824,297.61 범위(README §5-2). 지역별 중앙값도 최대 27배 차이(`figures/05_regional_conc_boxplot.png`), 연도별 중앙값은 2023년 55,555 → 2026년 1,359로 급락.
- **결측 구조**: `conc_mean` 196행 결측 — 연말 미보고 3주(51행), 부분보고·미측정(145행). 지역별로 결측 분포가 다르다(서울 초반 장기 결측 등, `figures/06_missingness_heatmap.png`).
- **데이터 품질 이슈**: `pop_sampled`가 `pop_served`를 초과하는 201행(서울·대전, 과거 처리장 중복집계, `figures/09_pop_sampled_vs_served.png`), `wow_change_rate` 극단치(전체의 0.1%, `figures/07_wow_change_rate_outliers.png`).
- **시점 주의**: `plant_meta.csv`는 2026-09 스냅샷이라 `in_current_registry`·`last_sample_week`는 미래 정보 — 모델 입력 금지(README §4-5).
- **정답이 이미 배포본에 포함**: `target_conc_t2`/`target_alert_t2`는 전체 CSV에 이미 값이 채워져 있고(2026-W35·W36만 공란), `evaluation.py`가 원점 주차 이후 값을 가려서 모델에 넘기는 방식으로 블라인드를 구현한다(README FAQ, §8-1).

---

## 3. 변수 간 관계

fitting 기간(fold별 `train_until`)에서 직접 재현한 결과다(`reports/midterm/eda_findings.md` 참고).

### 3-1. 강수/기온 ↔ 농도 — 거의 무관 (예상과 다른 핵심 발견)

| 검정 | 관계 | 수치(fold별 재현) | README 전체데이터 |
|---|---|---|---|
| A. 강수 희석 부분상관 | `log10(conc_mean/conc_3wk_avg)` ↔ `log(1+precip_mm)` | 표본 작은 초기 fold +0.026(부호 반대) → 표본 큰 후기 fold −0.012(수렴) | r = −0.007 |
| B. 기상 추가 설명력 | `conc_log10` 예측에 강수·기온 추가 | ΔR² 0.0002~0.0012 (전 fold 거의 0) | ΔR² = +0.0002 |

→ 시·도 집계 단위에서는 강수가 농도에 미치는 영향이 사실상 없다. 원산점도(`figures/08_precip_dilution_scatter.png`)에서 회귀선 기울기가 0.0023으로 거의 수평임을 시각적으로도 확인했다. 문헌 보강조사(England 연구, `docs/literature/review.md` §3)는 **개별 처리장 단위에서는 강수가 유출량의 지배적 요인**이라고 보고해 대조적 — 여러 유역이 섞인 시·도 집계에서 신호가 상쇄된다는 README §5-4의 가설과 부합한다.

### 3-2. 하수 농도 ↔ 임상 지표 — 강한 상관, 그러나 방향이 불안정

- 전국 하수 농도(`conc_mean_national`)와 전국 코로나19 신고수(`covid_cases_national`)의 로그 교차상관은 README 전체데이터 기준 시차 0주·+1주에서 r=0.919로 최대(§6).
- fold별로 재현하면 이 최대 지점의 위치가 **시간에 따라 이동**한다: 2024년 fold는 lag 0/+1 우세(README와 일치), 2025-W12 이후 fold는 lag −1(임상이 하수보다 먼저)이 우세하거나 lag 0과 동률(`figures/03_xcorr_heatmap.png`).
- → 상관의 "크기"(강함)와 "선행 시차"(불확실)를 분리해서 해석해야 한다. 문헌(며칠~2주 선행)이 기대하는 방향과도 다르다.

### 3-3. `conc_mean` ↔ `conc_3wk_avg` — 독립적이지만 강하게 연관된 입력

`conc_3wk_avg`는 `conc_mean`의 단순 이동평균이 아니라 KOWAS가 처리장·시료 단위 원자료로 별도 산출한 값이다(README §4-3). 그럼에도 두 값은 밀접히 움직이며(`figures/01_national_trend.png`에서 두 선이 대체로 겹침), 이 값을 그대로 예측치로 쓰는 것이 기준 모델이자 이기기 까다로운 강한 베이스라인이 되는 이유다(AutoGluon 실험에서 실제로 확인, `experiments/autogluon/`).

### 3-4. 처리장 특성(`plant_meta`) ↔ 농도 수준 — 약한 탐색적 관계

시·도 내 유효 처리장 수와 평균 농도는 약한 음의 상관(r=−0.381, `figures/04_plant_meta_explore.png`) — 처리장이 적은 대구·세종·울산이 평균 농도가 높고 변동성도 크다. 처리인구 합과는 거의 무관(r=−0.088). 17개 지역뿐이라 인과관계로 해석할 수 없는 탐색적 관찰이다.

### 3-5. 계절/시간 ↔ 급증 경보 — 가장 강력한 예측 신호 중 하나

`target_alert_t2` 양성 비율은 지역별로는 완만하지만(전남 0.20~제주 0.36, 1.8배) **분기별로는 최대 6.3배 차이**(2025-Q4 0.075~2025-Q3 0.475)가 나는 뚜렷한 3분기 계절성을 보인다(`figures/10_alert_positive_rate.png`). 확장 EDA에서 새로 발견한 것으로, 분류 모델에 계절 변수가 반드시 필요함을 시사한다.

### 3-6. `pop_sampled` ↔ `pop_served` — 데이터 구조상 결함 관계(실제 변수 관계 아님)

201행(서울 110·대전 91)에서 `pop_sampled`가 `pop_served`를 최대 2.02배 초과 — 과거 처리장(중랑B 등)의 중복 합산 때문이며, 두 변수 간의 실질적 관계가 아니라 데이터 가공 이슈다(`figures/09`). 신뢰도 가중치로 활용 시 이 두 지역만 별도 보정이 필요하다.

---

## 4. 요약 그림/표 색인

| 관계 | 근거 그림 |
|---|---|
| 지역별 스케일 차이 | `figures/05_regional_conc_boxplot.png` |
| 결측 패턴 | `figures/06_missingness_heatmap.png` |
| 강수-농도 무관 | `figures/08_precip_dilution_scatter.png`, `figures/02_testA_testB_by_fold.png` |
| 하수-임상 교차상관 불안정성 | `figures/03_xcorr_heatmap.png` |
| 처리장 특성 | `figures/04_plant_meta_explore.png` |
| 계절성(경보) | `figures/10_alert_positive_rate.png` |
| 데이터 품질(중복집계) | `figures/09_pop_sampled_vs_served.png` |
