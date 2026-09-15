# KOWAS-EPI 변수명세서

작성일: 2026-09-15 · `docs/data_inventory.md`(0단계 검증 결과)를 기반으로 모든 파일의 변수를 표로 정리.

## 가정 및 전제

- 값 범위·결측 건수는 전부 `KOWAS-EPI/*.csv`를 pandas로 직접 읽어(`dtype=str, keep_default_na=False`로 빈 문자열만 결측으로 취급) 재계산한 실측치이며, README.md §4의 서술과 전부 대조해 일치를 확인했다(0단계, `docs/data_inventory.md` 참고).
- "구분" 열은 README §9-2 `Model` 인터페이스 기준으로 분류했다: **키**(행 식별자), **입력**(모델이 `fit`/`predict`에서 받는 특징), **라벨**(맞혀야 할 정답, 모델 입력으로 쓰면 안 됨), **메타**(정적 부가정보).
- `plant_meta.csv`의 `in_current_registry`·`last_sample_week`는 2026-09-14 스냅샷 시점의 미래 정보라 "입력 금지" 컬럼으로 별도 표시했다(README §4-5, §9-1).

---

## 1. `kowas_epi_panel.csv` — 핵심 패널 (3,043행 = 17개 시·도 × 179주, 19열)

| 변수명 | 구분 | 타입 | 설명 | 값 범위 | 결측(행) |
|---|---|---|---|---|---|
| `date_week` | 키① | String | KOWAS 공식 주차(일~토 시작, **ISO 8601 주차 아님** — §4-4) | 2023-W14 ~ 2026-W36 | 0 |
| `week_start_date` | 키 보조 | Date | 주차 시작일(일요일) | 2023-04-02 ~ 2026-08-30 | 0 |
| `region` | 키② | String | 시·도명 | 서울·부산 등 17개 | 0 |
| `region_code` | 연계키 | String | 시·도 코드 — `plant_meta.csv` 연계용 | 01 ~ 17 | 0 |
| `pathogen` | 입력(상수) | String | 감시 병원체 | SARS-CoV-2 (전 행 동일) | 0 |
| `n_sites` | 입력 | Int | 그 주 유효 측정 처리장 수 | 0 ~ 12 | 0 |
| `conc_mean` | **입력(핵심)** | Float | 주간 평균 하수 바이러스 농도(copies/mL) | 2.58 ~ 50,824,297.61 | 196 |
| `conc_log10` | 입력 | Float | log10(1 + `conc_mean`) | 0.5539 ~ 7.7061 | 196 |
| `conc_3wk_avg` | 입력 | Float | KOWAS 제공 3주 평균값 — **`conc_mean`의 이동평균이 아닌 독립 변수**(§4-3), 평가 기준선으로도 쓰임 | 37.37 ~ 22,917,104.76 | 99 |
| `conc_base_avg` | 입력/기준선 | Float | 경보 기준선 = 같은 시·도 t−3~t 중 `conc_mean` 관측치 평균(2개 미만이면 공란), t까지 정보만 사용 → 입력으로 써도 무방 | 37.6450 ~ 19,753,140.7525 | 82 |
| `wow_change_rate` | 입력 | Float | 전주 대비 증감률(KOWAS 제공값, 이상치 있음 — §5-3) | −4,731.4543 ~ 9,638.9798 | 256 |
| `precip_mm` | 입력 | Float | 주간 누적 강수량(일~토, Open-Meteo 재분석) | 0 ~ 359.7 (mm) | 0 |
| `temp_avg` | 입력 | Float | 주 평균 기온(일~토, 재분석) | −12.4 ~ 32.9 (℃) | 0 |
| `pop_served` | 입력/메타 | Int | 시·도 하수처리 인구 합계 — **2026-09 현재 등록 처리장 기준 고정값**(과거 실제 처리인구 아님) | 343,577 ~ 9,667,667 | 0 |
| `pop_sampled` | 입력(주의) | Int | 그 주 채취 처리장 처리인구 합(KOWAS 원천값) — **중복집계로 `pop_served` 초과 201행**(서울 110·대전 91, 최대 2.02배), 신뢰도 가중치로 쓸 때 주의(§5-5) | 8,920 ~ 11,268,168 | 196 |
| `missing_reason` | 메타 | String | `conc_mean` 결측 사유 | 공란·`no_measurement`(131)·`no_source_row`(65) | 2,847(공란=결측 아님) |
| `target_week_t2` | 라벨 메타 | String | 목표주(t+2), 예측 CSV의 `date_week` 값 | 2023-W16 ~ 2026-W38 | 0 |
| `target_conc_t2` | **라벨①(회귀)** | Float | t+2주 `conc_mean` — 맞혀야 할 값. **모델 입력 금지** | 2.58 ~ 50,824,297.61 | 227(유효 2,816) |
| `target_alert_t2` | **라벨②(분류)** | Int | t+2주 급증 경보(`target_conc_t2 ≥ 1.3×conc_base_avg(t)`이면 1). **모델 입력 금지** | 0, 1 (양성 847건=30.6%) | 272(유효 2,771) |

---

## 2. `national_weekly.csv` — 전국 집계 (179행, 7열)

| 변수명 | 구분 | 타입 | 설명 | 값 범위 | 결측(행) |
|---|---|---|---|---|---|
| `date_week` | 키 | String | 주차 | 2023-W14 ~ 2026-W36 | 0 |
| `week_start_date` | 키 보조 | Date | 주차 시작일 | 2023-04-02 ~ 2026-08-30 | 0 |
| `conc_mean_national` | 입력 | Float | 전국 하수 농도 집계(KOWAS 원천) | — | 3(연말 미보고) |
| `conc_3wk_avg` | 입력 | Float | 전국 3주 평균값 | — | 3 |
| `wow_change_rate` | 입력 | Float | 전국 전주 대비 증감률 | — | 6 |
| `n_samples` | 입력/메타 | Int | 전국 집계에 쓰인 시료 수 | — | 3 |
| `covid_cases_national` | 입력(제한적) | Int | 질병관리청 감염병포털 코로나19 표본감시 신고수(전국) — **시·도별 라벨 아님, 참고용 보조 변수** | — | 39(2024-W01 이전 공란, 유효 140) |

---

## 3. `plant_meta.csv` — 처리장 메타데이터 (118행, 10열)

| 변수명 | 구분 | 타입 | 설명 | 값 범위 | 결측(행) |
|---|---|---|---|---|---|
| `plant_id` | 키 | String | 처리장 코드(`P`+번호 3자리) | P006 ~ | 0 |
| `plant_name` | 메타 | String | 처리장명 | — | 0 |
| `region` / `region_code` | 연계키 | String | 소속 시·도 / 코드 | — | 0 |
| `latitude` / `longitude` | 메타 | Float | 위경도 | — | 각 1(P065 좌표 없음) |
| `treatment_population` | 입력 | Int | 처리인구 | — | 0 |
| `in_current_registry` | **입력 금지** | Int | 현재(2026-09) 등록 여부 — **미래 정보, 원점 t 모델에서 사용 금지**(§4-5) | 0, 1 (0인 처리장 4개: P019·P028·P065·P071) | 0 |
| `first_sample_week` | 입력(필터용) | String | 첫 채취 주 — **`first_sample_week ≤ t`인 처리장만 원점 t 모델에서 사용** | — | 0 |
| `last_sample_week` | **입력 금지** | String | 마지막 채취 주 — **미래 정보(패널 마지막 주 이후 값 포함 가능), 사용 금지**(§4-5) | — | 0 |

---

## 4. `dataon_reference.csv` — DataON 융합 후보 목록 (4행, 9열)

| 변수명 | 설명 |
|---|---|
| `ref_id`, `dataset_name_ko/en`, `provider`, `doi_or_id`, `license`, `format`, `contents`, `join_role` | 이종 도메인 융합 후보 데이터셋 서지정보. **원자료 미포함**, 목록만 제공(선택 확장용, §7). DATAON-02는 CC-BY-NC(비상업). |

---

## 5. `folds.csv` — 평가 창 정의 (10행, 8열)

| 변수명 | 타입 | 설명 |
|---|---|---|
| `fold_id` | String | 평가 창 ID (예: 2024-Q2) |
| `target_start` / `target_end` | String | 평가 대상 주차 범위 |
| `n_weeks` | Int | 평가 창 주 수(10 또는 13) |
| `train_until` | String | **그 평가 창의 fitting 상한 주차** — 이 이후 데이터는 그 창의 `fit()`/`predict()`에 절대 넘기면 안 됨 |
| `n_regression_labels` / `n_alert_labels` / `n_alert_positive` | Int | 그 창의 채점 대상 라벨 수·양성 수(참고용, 모델 입력 아님) |

---

## 6. `eval_keys.csv` — 평가 대상 키 (2,159행, 3열)

| 변수명 | 설명 |
|---|---|
| `fold_id`, `region`, `date_week` | 제출 CSV가 반드시 포함해야 할 `(region, date_week)` 키 목록(`date_week`=목표주 t+2) |

---

## 7. `submission_example.csv` — 제출 형식 예시 (4행, 4열)

| 변수명 | 타입 | 설명 |
|---|---|---|
| `region` | String | 시·도명 |
| `date_week` | String | 목표주(t+2) |
| `pred_conc` | Float | 예측 농도, 0 이상 유한 실수 |
| `pred_alert` | Int | 예측 경보, 0 또는 1(확률값 불가) |

---

## 요약 — 입력으로 써도 되는 것 vs 절대 안 되는 것

| 구분 | 컬럼 |
|---|---|
| **라벨(입력 금지)** | `target_conc_t2`, `target_alert_t2` |
| **미래 정보(입력·필터 금지)** | `plant_meta.csv`의 `in_current_registry`, `last_sample_week` |
| **주의해서 입력** | `pop_sampled`(중복집계 201행), `wow_change_rate`(이상치), `conc_base_avg`(2개 미만 관측 시 공란) |
| **핵심 입력** | `conc_mean`, `conc_3wk_avg`, `precip_mm`, `temp_avg`, `n_sites`, `pop_served`, `plant_meta`의 위경도·처리인구(단 `first_sample_week ≤ t` 필터 적용) |
