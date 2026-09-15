# KOWAS-EPI 데이터 인벤토리

작성일: 2026-09-15 · 검증 환경: Python 3.14 + pandas 3.0.5 (`.venv`)

## 가정 및 전제

- CSV의 빈 문자열(`""`)을 결측으로 간주했다. `pd.read_csv(..., dtype=str, keep_default_na=False)`로 읽어 pandas의 기본 NaN 추정(빈 칸 외의 값을 NaN으로 오인하는 것 등)을 배제했다.
- 아래 모든 수치는 README.md에 적힌 숫자와의 **일치 여부를 실제로 코드로 재계산**해서 확인한 것이며, 전부 일치했다(불일치 0건). 따라서 이 문서는 README 스키마 설명의 정오표가 아니라 "실측 확인 완료" 기록이다.
- 문제 정의(§1~§2, §8~§9)는 README 원문을 그대로 요약했고 새로 해석하지 않았다.

---

## 1. 문제 정의 요약

| 항목 | 내용 |
|---|---|
| 과제 | 시·도(17개) × 주차 단위로, 원점 주차 t까지 공개된 정보만으로 **t+2주 하수 바이러스 농도**(회귀)와 **급증 경보**(분류)를 예측 |
| 출력 ① | `pred_conc` — t+2주 주간 평균 하수 바이러스 농도(copies/mL), 0 이상 유한 실수 |
| 출력 ② | `pred_alert` — t+2주 급증 경보 0/1. `target_conc_t2 ≥ 1.3 × conc_base_avg(t)`이면 1 (대회 조작적 정의, 공식 보건 경보 기준 아님) |
| 입력 | 하수 농도 시계열, KOWAS 3주 평균값, 기상(강수·기온), 처리인구, 처리장 위치, 전국 집계, DataON 유역 자료(선택) |
| 예측 범위 제약 | 채점 대상은 하수 지표뿐이며 임상 환자 수 직접 예측은 아님 |
| 평가 방법 | 롤링 백테스트. 10개 평가 창(분기 단위, `folds.csv`)마다 그 창 시작 2주 전까지의 자료로 `fit()`을 새로 하고, 주차별로 `predict()`를 호출 |
| 지표 | `점수 = 0.6 × (1 − sMAPE/sMAPE_기준선) + 0.4 × Macro-F1`, sMAPE_기준선은 `conc_3wk_avg`를 그대로 예측값으로 쓴 sMAPE |
| 기준 모델 성능 | 최종 정량점수 0.2212 (회귀 항은 0, 분류만 기여) |
| 핵심 제약 | (a) 원점 주차 이후 정보 누수 금지, (b) 모델 코드·패키지에 KOWAS 수치를 상수로 담으면 안 됨, (c) 네트워크 없이 실행 가능해야 함, (d) 학습된 가중치 미포함(평가 창마다 재학습), (e) `plant_meta.csv`의 `in_current_registry`·`last_sample_week`는 미래 정보를 담고 있어 입력·필터로 사용 금지 |

---

## 2. 파일별 상세

### 2-1. `kowas_epi_panel.csv` — 핵심 패널 (입력 + 라벨)

- **행 수**: 3,043 (17개 시·도 × 179주, 완전 격자 — 결측 없는 시·도×주 조합 없음)
- **열 수**: 19
- **컬럼**: `date_week, week_start_date, region, region_code, pathogen, n_sites, conc_mean, conc_log10, conc_3wk_avg, conc_base_avg, wow_change_rate, precip_mm, temp_avg, pop_served, pop_sampled, missing_reason, target_week_t2, target_conc_t2, target_alert_t2`
- **결측 현황 (실측, README와 일치)**:

| 컬럼 | 결측 행 수 | README 명시값 |
|---|---|---|
| `conc_mean`, `conc_log10`, `pop_sampled` | 196 | 196 (일치) |
| `conc_3wk_avg` | 99 | 99 (일치) |
| `conc_base_avg` | 82 | 82 (일치) |
| `wow_change_rate` | 256 | 256 (일치) |
| `target_conc_t2` (라벨 ①) | 227 → 유효 2,816 | 유효 2,816 (일치) |
| `target_alert_t2` (라벨 ②) | 272 → 유효 2,771, 양성 847 (30.6%) | 유효 2,771·양성 847 (일치) |
| `missing_reason` | 2,847 (공란=결측 사유 없음), `no_measurement` 131, `no_source_row` 65 | 합산 196 (일치) |

- `n_sites == 0`인 행이 정확히 196개로 `conc_mean` 결측과 일치 (README §5-1과 동일).
- `pop_sampled > pop_served`인 행 201개(서울 110·대전 91), 최대 비율 2.02배 — README §5-5와 일치.
- `date_week` 범위 2023-W14~2026-W36 (179주), 17개 시·도명 모두 확인.
- `conc_mean` 값 범위 2.58 ~ 50,824,297.61 — README와 일치.

### 2-2. `national_weekly.csv` — 전국 집계

- **행 수**: 179 · **열 수**: 7
- **컬럼**: `date_week, week_start_date, conc_mean_national, conc_3wk_avg, wow_change_rate, n_samples, covid_cases_national`
- **결측**: `conc_mean_national`·`conc_3wk_avg`·`n_samples` 각 3행 결측(179−176=3, README "176주, 연말 3주 없음"과 일치), `wow_change_rate` 6행, `covid_cases_national` 39행 결측 → 유효 140행(README "2024-W01~2026-W36, 140주"와 일치).

### 2-3. `plant_meta.csv` — 처리장 메타데이터

- **행 수**: 118 · **열 수**: 10
- **컬럼**: `plant_id, plant_name, region, region_code, latitude, longitude, treatment_population, in_current_registry, first_sample_week, last_sample_week`
- **결측**: `latitude`·`longitude` 각 1행(P065, 중계펌프장(테크노)) — README와 일치.
- `in_current_registry == 0`인 처리장: P019·P028·P065·P071 (4개) — README §4-5와 일치.
- **시점 주의(README 그대로)**: 이 파일은 2026-09-14 스냅샷이며 `in_current_registry`·`last_sample_week`·`first_sample_week`는 미래 정보를 포함할 수 있어 원점 t 모델에서는 `first_sample_week ≤ t`인 처리장만 쓰고 나머지 두 열은 입력·필터로 쓰면 안 됨.

### 2-4. `dataon_reference.csv` — DataON 융합 후보 목록

- **행 수**: 4 · **열 수**: 9 (`ref_id, dataset_name_ko, dataset_name_en, provider, doi_or_id, license, format, contents, join_role`)
- 원자료 미포함, 목록만 제공. DATAON-02는 CC-BY-NC(비상업) 조건.

### 2-5. `folds.csv` — 평가 창 정의

- **행 수**: 10 (2024-Q2 ~ 2026-Q3) · **열 수**: 8 (`fold_id, target_start, target_end, n_weeks, train_until, n_regression_labels, n_alert_labels, n_alert_positive`)
- 결측 없음. `train_until`이 각 평가 창의 fitting 상한을 정의 (§3단계에서 사용).

### 2-6. `eval_keys.csv` — 평가 대상 키

- **행 수**: 2,159 · **열 수**: 3 (`fold_id, region, date_week`)
- 결측 없음. `predictions.csv` 제출 시 정확히 이 키 조합만큼 필요.

### 2-7. `submission_example.csv` — 제출 형식 예시

- **행 수**: 4 · **열**: `region, date_week, pred_conc, pred_alert`

### 2-8. `evaluation.py` / `baseline_model.py`

- `evaluation.py`: 표준 라이브러리만 사용하는 롤링 백테스트·채점·형식 검증 스크립트. `known_at()` / `national_at()` 함수가 원점 주차 이후 행 제거 및 라벨 마스킹으로 데이터 누수를 차단.
- `baseline_model.py`: 공식 나이브 기준 모델. 회귀는 `conc_3wk_avg` 그대로, 분류는 "현재 경보 지속" 규칙. 최종 정량점수 0.2212(README §8-3과 코드 로직 일치).

---

## 3. 스키마 일치 여부 결론

README.md §4에 기술된 모든 컬럼 정의, 결측 건수, 값 범위, 특수 사례(서울/대전 `pop_sampled` 초과, P065 좌표 결측, `in_current_registry`=0인 4개 처리장 등)를 실제 CSV에서 재계산한 결과 **불일치 0건**으로 확인했다. 이후 단계(EDA·모델링)에서는 README 수치를 그대로 신뢰하고 진행해도 된다.
