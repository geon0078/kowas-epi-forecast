# TODO — AutoGluon: 변수·전처리·알고리즘 탐색 → 10개 fold 전체 공식 백테스트

작성: 2026-09-15 저녁 · 최종 수정: 2026-09-15 (계획 확장 — 탐색 단계 추가)

## ⚠️ 실행 시점 — 반드시 읽을 것

**지금 실행하지 말 것.** 사용자가 자기 전에 신호를 줄 때만 시작한다. 신호가 오면 아래 **단계 1 → 2 → 3을 한 번에 이어서** 돌린다(중간에 멈추지 않음, 사용자는 자는 중이라 각 단계마다 확인받을 수 없음 — 문제가 생기면 로그에 정직하게 남기고 계속 진행하거나, 진행 불가능하면 그 단계에서 멈추고 이유를 남긴다).

이미 한 번 성급하게 먼저 실행했다가 사용자 지시로 중단(kill)한 적이 있다(2026-09-15 20:10경) — **이번에도 신호 전에는 절대 실행하지 않는다.**

---

## 지금까지 확인된 것 (2026-Q3 fold 파일럿, 좁은 손수 선택 변수 세트)

| | 베이스라인 | 개선 후 |
|---|---|---|
| 회귀 sMAPE | 60.46% | 55.99% (스미어링 보정 + baseline 80:20 블렌딩) |
| 분류 Macro-F1 | 0.5810 | 0.6599 (NeuralNetTorch_r143_BAG_L1) |

이건 **변수를 넓게 탐색하거나 선택 과정을 거친 게 아니라**, `docs/modeling_proposal.md`에서 손으로 고른 좁은 변수 세트(TS 공변량 ~10개, 분류 특징 ~30개)로 한 것이다. 분류의 "NeuralNetTorch가 최고"라는 선택도 **그 fold의 실제 정답을 보고 고른 것**이라 실제 제출 코드에는 못 쓴다(누수) — `model_autogluon.py`는 이미 이 문제를 시간순 `tuning_data`로 고치도록 다시 작성해뒀다.

이번 확장의 목적: **더 넓은 변수 그리드 + 전처리 기법 + 알고리즘을 정답을 보지 않고 체계적으로 탐색**해서, 그 결과로 회귀·분류 각각의 "최종 구성"을 확정한 뒤 10개 fold 전체 백테스트로 넘어간다.

---

## 전체 파이프라인 (신호 받으면 순서대로, 한 번에)

### 단계 1 — 변수 그리드 확장 + 전처리 + 알고리즘 탐색 (회귀·분류 각각 따로)

**탐색은 2026-Q3 fold 하나로 진행**(전 fold를 다 탐색하면 시간이 너무 오래 걸림). **탐색 중에도 그 fold의 실제 정답(`target_conc_t2`/`target_alert_t2`)을 보고 뭔가를 고르면 안 된다** — 오직 학습 데이터 안에서 시간순으로 떼어낸 검증 구간(`tuning_data`)의 성능만으로 비교·선택한다. 지난번 분류 모델 선택에서 저지른 누수를 이번엔 반복하지 않는다.

#### 1-A. 변수 그리드 확장 (기존 `docs/modeling_proposal.md` 제안보다 넓게)

| 범주 | 추가 후보 |
|---|---|
| 시차 | `lag3`, `lag4` (기존 lag1·lag2에 추가) |
| 롤링 | `roll2`, `roll8`, `roll12` (기존 roll4에 추가), 롤링 min/max |
| 변화율 | 1·2·4주 전 대비 증감률을 `conc_mean`으로 직접 계산(KOWAS `wow_change_rate` 원값 대신/추가로) |
| 가속도 | 모멘텀 비율의 1차 차분(2차 변화) |
| 전국 대비 상대값 | `national_weekly.csv`의 `conc_mean_national` 대비 그 지역 비율 — **`national` 인자로 이미 fit()/predict()에 넘어오는 자료라 추가 파일 안 읽어도 됨** |
| 캘린더 세분화 | 월 더미(계절 더미보다 세밀), 연도 더미(장기 하락 추세 반영) |
| 결측 신뢰도 | 최근 4·8주 내 결측 횟수/비율 |
| plant_meta 비율 | 처리인구 대비 처리장 수(밀도), 지난 조사에서 쓴 것에 이 비율 추가 |

#### 1-B. 전처리 기법 비교

- **회귀 타깃**: (a) `conc_log10` + 스미어링 보정(기존, 검증됨) vs (b) 원스케일 `conc_mean` 직접 학습 + AutoGluon 내부 `target_scaler` — **1차 시도에서 (b)가 n=136으로 행 수가 안 맞는 버그가 있었으니, 이번엔 그 버그를 먼저 고치고 나서 (a)와 실제로 비교한다.** 버그를 못 고치면 (a)로 확정하고 그 사실을 REPORT.md에 남긴다.
- **`wow_change_rate` 처리**: 클리핑 폭(±100 vs ±50 vs 없음) 비교
- **베이스라인 블렌딩 α**: 0.80 고정 대신 tuning_data 구간에서 그리드서치(0.0~1.0, 0.05 간격)로 재탐색

#### 1-C. 알고리즘 탐색

- 회귀: TimeSeriesPredictor `hyperparameters="default"`(현재 방식, 전체 zoo) 유지 — 이미 충분히 넓음. 대신 **`num_val_windows`를 늘려(3→5)** 모델 순위의 안정성을 재확인.
- 분류: TabularPredictor `presets="best_quality"`(현재 방식) 유지, 대신 **`tuning_data`(시간순 홀드아웃)를 실제로 넘겨서** 자동 선택된 모델이 이번엔 지난번처럼 검증세트 과최적화로 실전보다 낮게 나오는지 재확인.

#### 1-D. 변수 선택(중요도 기반 가지치기)

- 1-A의 넓은 변수 세트로 1차 학습 → `predictor.feature_importance()`(tuning_data 기준 permutation importance)로 중요도 계산
- 중요도 하위 변수 제거 → 재학습 → tuning_data 성능이 좋아지는지/나빠지는지 비교
- **최종 변수 세트는 tuning_data 성능이 가장 좋은 쪽으로 확정** (넓은 세트가 이기면 넓은 세트 그대로, 가지치기한 게 이기면 그걸로)

**산출물**: `experiments/autogluon/06_feature_search_regression.py`, `07_feature_search_classification.py`, `experiments/autogluon/search_results/`(회귀·분류 각각 변수세트/전처리/알고리즘 조합별 tuning_data 성능 표), `experiments/autogluon/search_results/winning_config.json`(회귀·분류 각각 최종 확정된 변수 세트·전처리·하이퍼파라미터 기록)

### 단계 2 — `model_autogluon.py`를 단계 1의 승자 구성으로 갱신

- 단계 1에서 확정된 변수 세트·전처리·알고리즘 설정을 `model_autogluon.py`에 반영
- **짧은 시간제한으로 스모크테스트**(2024-Q2 fold, `AG_PRESET=medium_quality` 등)로 인터페이스가 안 깨졌는지 재확인 — 이건 매번 코드를 바꿀 때마다 하는 필수 절차

### 단계 3 — 10개 fold 전체 공식 백테스트

```
cd KOWAS-EPI && source ../.venv-autogluon/bin/activate
nohup python evaluation.py backtest --model ../experiments/autogluon/model_autogluon.py \
  --out ../experiments/autogluon/predictions_full.csv \
  --json ../experiments/autogluon/score_full.json --keep-going \
  > ../experiments/autogluon/full_backtest.log 2>&1 &
```
실행 후 **반드시** `tail --pid=<PID> -f /dev/null`을 `run_in_background:true`로 걸어서 완료 알림이 오게 할 것 (지난번엔 이 단계를 빠뜨려서 알림이 안 왔었다 — 반복하지 말 것).

- 단계 1(탐색) + 단계 3(10개 fold 재학습) 합쳐서 총 소요시간이 꽤 길어질 수 있다(수 시간 단위) — 정확한 예상은 단계 1 탐색 범위에 달려있으니, 탐색을 시작하기 전에 각 실험(변수조합×전처리×알고리즘) 개수를 먼저 추정해서 시간이 너무 길어지면(예: 6시간 초과) 그리드를 자동으로 줄여도 된다 — 다 못 끝내는 것보다 합리적으로 줄여서 끝내는 게 낫다.

---

## 완료 후 보고 형식

1. 단계 1: 회귀·분류 각각 어떤 변수 조합·전처리·알고리즘이 tuning_data 기준 최선이었는지, 기존(좁은 세트) 대비 개선됐는지
2. 단계 3: 10개 fold 각각의 회귀항·Macro-F1·fold점수, 최종 정량점수(10개 평균) vs 베이스라인 0.2212
3. 전체적으로 실제 개선된 게 맞는지(아니면 2026-Q3 fold에서만 통했던 것으로 드러나는지) 솔직하게 — 좋게 포장하지 않기

## 지켜야 할 원칙 (계속 적용)

- 원본 데이터(`KOWAS-EPI/`)·기존 제출물(`docs/`, `reports/`, `notebooks/`, `figures/`)은 절대 손대지 않는다.
- `target_conc_t2`/`target_alert_t2`/`target_week_t2`는 라벨로만 쓰고 입력 특징에 넣지 않는다.
- `plant_meta.csv`의 `in_current_registry`/`last_sample_week` 사용 금지.
- **어떤 탐색·선택 과정도 그 fold의 실제 정답을 보고 하면 안 된다** — 오직 시간순 `tuning_data`로만 비교·선택한다(이번 확장의 핵심 원칙).
- 숫자를 지어내지 않는다 — 실제로 돌려서 나온 값만 기록한다.
- git 커밋/푸시는 하지 않는다(결과 검토 후 사용자에게 보고).
