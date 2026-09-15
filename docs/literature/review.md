# 문헌 리뷰 — 하수 기반 역학(WBE)을 이용한 감염병 조기예측

작성일: 2026-09-15

## 가정 및 전제

- **검색 도구**: WebSearch(2026-09 시점 웹 인덱스) + WebFetch(개별 논문 페이지 확인). `parallel-cli`는 이 환경에 설치되어 있지 않아 사용하지 못했다.
- **검색 키워드**: "wastewater-based epidemiology forecasting", "SARS-CoV-2 wastewater surveillance lead time", "wastewater viral load early warning", "wastewater epidemiology time series model", "wastewater surveillance machine learning forecast", "Korea wastewater surveillance SARS-CoV-2", "wastewater precipitation dilution normalization" 등 영어 키워드를 주력으로 사용했다. 한국어 키워드("하수 기반 감염병 감시 예측")는 WebSearch가 미국 기반이라 결과가 거의 없어, 대신 "Korea wastewater surveillance"로 검색해 KOWAS 관련 영문 논문을 확보했다.
- **포함 기준**: (1) 동료심사 학술지 또는 arXiv/medRxiv 등 검증 가능한 프리프린트, (2) 하수 바이러스(주로 SARS-CoV-2) 농도와 임상 지표 간의 시차·예측·상관관계를 다룬 연구, (3) 2021년 이후 발표(팬데믹 이후 방법론이 성숙한 시기 우선).
- **제외 기준**: 원문에 접근할 수 없어 서지정보만 확인되고 방법론·수치를 전혀 검증하지 못한 자료, 리뷰 논문 자체가 재인용한 2차 통계치는 "2차 출처, 원문 미확인"으로 표시하고 표에 포함하되 신뢰도를 낮게 표시했다.
- **정확성 원칙**: 논문마다 WebFetch로 원문(또는 PMC 전문)에 접근해 저자·연도·수치를 직접 확인했다. 원문이 유료 장벽(paywall)에 막혀 검색 스니펫으로만 확인된 항목은 표에 "(원문 미확인)"으로 명시했다. 존재를 확인하지 못한 논문은 싣지 않았다.

---

## 1. 논문 비교표

| # | 서지정보 | 방법론 | 선행 시차(lead time) 결과 | 데이터 규모 | 주요 한계점 |
|---|---|---|---|---|---|
| 1 | Li, X. et al. (2022). *Science of the Total Environment*. "Wastewater surveillance to infer COVID-19 transmission: A systematic review." | 체계적 문헌고찰(PRISMA), 763편 중 92편 선별 | 다수 연구가 임상 사례 확진 이전 하수 양성을 보고(초기 팬데믹 연구 중 일부는 지역사회 첫 확진 이전 최대 수개월 선행 사례도 포함); 정량적 분포는 원문 결과표 미확인 | 34개국 92개 연구, 표본 26,197건, 대상 인구 321명~1,140만 명 | 연구 간 정규화·채취방법 이질성 커서 메타분석적 lead time 통합이 어려움 |
| 2 | Chen, C., Wang, Y., Kaur, G. et al. (2024). arXiv:2403.15291. "Wastewater-based Epidemiology for COVID-19 Surveillance and Beyond: A Survey." | 방법론 분류 서베이 — 모델 기반(배출모델·SEIR) vs 데이터 기반(ARIMA/SARIMA/VAR, 회귀·GAM, RF/SVR, ANN/ANFIS) | "하수 바이러스량은 대체로 임상 데이터보다 1~2주 선행" (서베이의 정성적 결론) | 2,567편 중 137편 선별, 75개국 이상 공개 데이터셋 목록화 | 배출량 개인차, 손실·희석에 따른 과소추정, 임상자료와의 시간 해상도 불일치 |
| 3 | Choi, Y.-J., Kim, L.H., Jang, J. et al. (2025). *Journal of Korean Medical Science*. "National Wastewater Surveillance of SARS-CoV-2 Across Provinces and Regions in the Republic of Korea From January to August 2023." | KOWAS 원 운영기관(질병관리청) 자체 분석 — 우측정렬 3주 이동평균 기반 교차상관 | 전국 상관 r=0.85 (P<0.001), 부산 r=0.90(지역 최고); **교차상관 최고점이 시차 0(동시)에서 발생** — 선행이 아니라 동시성 신호로 보고 | 17개 시·도, 62개 하수처리장, 34주(2023-01~08), 표본 2,176건, 전국 인구 약 52% 커버 | 처리장 포함률 50% 미만 지역은 유의한 상관 없음; 강우 희석(합류식 관거); 지역 간 인구이동 |
| 4 | Kim, Y.-T. et al. (2024). *Scientific Reports* 14:24544. "Development of a wastewater based infectious disease surveillance research system in South Korea." | 실시간 PCR 기반 47종 병원체 동시 감시, 스피어만 상관분석 | SARS-CoV-2는 **상관 없음**(ρ=−0.18, p=0.4); 반면 노로바이러스 GII(ρ=0.92)·인간코로나바이러스(ρ=0.90)는 강한 상관. 최대 2주 선행 가능성은 미국 NWSS 사례를 인용해 언급했을 뿐, 자체 데이터로 확인하지 않음 | 용인시 하수처리장 6개소, 2022-12~2023-11(1년), 월 2회, 표본 144건 | 6개 처리장 권역의 지역사회 임상자료와 직접 비교 불가; 병원체별 이질적 결과로 일반화 어려움 |
| 5 | Hill, D.T. et al. (2023). *Infectious Disease Modelling* 8(4):1138–1150. | 일반화선형혼합모델(GLMM), 포아송 카운트 모형으로 입원 예측 | 병원 입원과의 상관이 **10일 지연에서 최고**(r=0.415); 예측값-관측값 상관 r=0.77 | 56개 카운티·109개 처리장, 인구 약 1,380만 명, 2020-04~2022-06(약 26개월) | 대부분 지점에서 유량(flow) 자료 없어 정규화 곤란; 실험실 간 분석법 이질성; 감염지-입원지 주소 불일치 가능 |
| 6 | Ai, Y., He, F., Lancaster, E., Lee, J. (2022). *PLOS ONE*. "Application of machine learning for multi-community COVID-19 outbreak predictions with wastewater surveillance." | 비시계열(선형회귀·GBDT·DNN) vs 시계열(Prophet·LSTM) 비교 | LSTM 최고 성능(훈련 R²=0.94, 테스트 R²=0.81); **5일 시차**를 입력에 반영하면 RMSE 10% 개선 | 오하이오주 9개 지역사회, 2020-09~2021-06, 주 2회 표본 총 620건 | 소규모 데이터셋, 16시점 슬라이딩 윈도우의 단기예측만 가능, 저상관 지역(Athens) 포함 시 성능 저하, 과적합 위험 |
| 7 | Jeng, H.A., Singh, R., Diawara, N. et al. (2023). *Science of the Total Environment*. | ARMA + 가우스 코플라(Copula) 결합 2단계 시계열 모형, 포아송/음이항 주변분포 | 모델이 임상 확진 파동보다 **최소 3~5일 선행**해 추세를 예측 | 미국 체서피크(VA) 5개 하수관거, 2021-06~2022-06 | 소규모 데이터셋, 주 1회 표본으로 시간 해상도 낮음, 백신접종률 등 교란변수 미포함, 공간 이질성 평가 제한 |
| 8 | Karthikeyan, S. et al. (2021). *mSystems*. "High-Throughput Wastewater SARS-CoV-2 Detection Enables Forecasting of Community Infection Dynamics in San Diego County." | 다변량 ARIMA (과거 확진자 수 + 하수 농도 + 채취일) | 1~3주 앞선 확진자 수 예측에 활용(정성적 확인, 시차별 정확한 오차지표는 원문 상세 미확인) | 캘리포니아 샌디에이고 카운티, 고빈도(거의 매일) 표본 | 예측 지평이 길어질수록 오차 증가(정성적 보고), 대규모 대학 캠퍼스 중심이라 일반 지역사회 외삽 제한 |
| 9 | Zhao, L. et al. (2022, 추정). 디트로이트 지역 ARIMA·SARIMA·VAR 비교 연구 (2차 출처만 확인, 원 서지정보 미확정) | ARIMA vs SARIMA vs VAR 비교 | 2차 출처 기준 1주 선행예측에서 VAR·SARIMA(상관≈0.94~0.96)가 단순 ARIMA(상관≈0.4~0.67)보다 크게 우수 — **원문 미확인, 수치는 검색 스니펫 인용이라 낮은 신뢰도로 취급** | 미시간주 디트로이트 지역, 약 1년(2020-09~2021-08) | 원문 미확인으로 정밀 검증 불가; 단일 도시 사례 |
| 10 | (저자 미확인). *Journal of Environmental Engineering* 150(1), 2024. "Tracking the Time Lag between SARS-CoV-2 Wastewater Concentrations and Three COVID-19 Clinical Metrics: A 21-Month Case Study in the Tricounty Detroit Area, Michigan." | 하수 농도와 확진자·입원·ICU 입원 3개 임상지표 간 시차 전용 추적 설계 | 논문 제목·초록 수준에서 "시차 추적"이 핵심 결과이나 **본문이 유료 장벽에 막혀 지표별 구체적 일수는 확인하지 못함** | 미시간주 트라이카운티(디트로이트권), 2020-09~2022-10(21개월) | 원문 미확인 — 본 리뷰에서는 연구설계·존재만 인용, 수치는 인용하지 않음 |
| 11 | 정규화(normalisation) 방법론 그룹(예: Medema 등 계열). medRxiv 2021.11.30.21266889 및 관련 Journal of Water and Health 논문들. | 유량(flow)·전기전도도(EC)·crAssphage를 이용한 하수 농도 정규화 방법 비교 | 예측/선행시차 논문은 아니지만, 정규화 없이는 강우·희석 효과가 신호를 왜곡해 **단기 추세 판단(=사실상 조기경보 신뢰도)이 흔들림**을 보고. EC 정규화가 임상자료와의 상관을 소폭 개선 | 유럽 다수 도시 사례(코호트별로 상이) | 정규화 변수(유량계) 자체가 없는 처리장이 많아 실무 적용 제약 |

> 표 안의 "2차 출처"·"원문 미확인" 표기는 §"가정 및 전제"의 원칙에 따라 신뢰도를 낮춰 참고용으로만 남긴 것이다. 서술 요약(§2)에서는 원문을 확인한 1~8번 연구를 중심으로 논지를 전개했다.

---

## 2. 종합 서술 요약 (수업 중간보고서 "문헌 리뷰" 섹션 초안, 약 600단어)

하수 기반 역학(wastewater-based epidemiology, WBE)은 감염자가 증상을 인지하고 검사를 받기 전부터 배출하는 바이러스 유전물질을 하수에서 검출함으로써, 임상 신고 체계보다 앞서 지역사회 감염 동향을 포착할 수 있다는 전제에서 출발한다. 이 전제는 팬데믹 초기부터 폭넓게 검증되어 왔으며, 763편 중 92편을 선별한 체계적 문헌고찰(Li et al., 2022)은 34개국·26,197건 표본을 아우르는 연구들에서 하수 신호가 임상 확진보다 먼저 나타난 사례를 다수 보고했다고 정리한다. 다만 이런 초기 보고 중 "수개월 선행"류의 극단값은 대개 지역사회 첫 유행이 시작되기 전 저빈도 검사 체계의 사각지대를 하수가 메운 사례이지, 정상 가동 중인 감시체계에서 반복적으로 관찰되는 예측 리드타임은 아니다.

실제로 예측/시차를 직접 정량화한 개별 연구들의 수치는 훨씬 보수적으로 수렴한다. San Diego 다변량 ARIMA 연구(Karthikeyan et al., 2021)는 1~3주 지평의 예측에 하수 자료를 활용했고, Ohio 9개 지역사회를 LSTM·Prophet 등으로 비교한 연구(Ai et al., 2022)는 5일 시차를 넣었을 때 예측 오차가 개선됨을 보였다. Chesapeake 지역의 코플라 시계열 모형(Jeng et al., 2023)은 3~5일의 선행 추세 포착을, 56개 카운티 입원자 예측 GLMM(Hill et al., 2023)은 10일 지연에서 상관이 최고였음을 보고했다. 이를 종합하면 문헌에서 반복적으로 확인되는 선행 시차는 대체로 **며칠에서 최대 2주 내외**이며, arXiv 서베이(Chen et al., 2024)도 이를 "대체로 1~2주 선행"으로 요약한다. 즉 WBE의 조기경보 가치는 실재하지만 그 폭은 생각보다 좁고, 방법론(정규화 여부, 채취 빈도, 예측모형 종류)에 따라 크게 흔들린다는 것이 문헌의 공통된 함의다.

이 지점에서 이번 KOWAS-EPI README §6의 수치(하수·임상 로그 상관이 시차 0주와 +1주에서 동일하게 최댓값 r=0.919, 최근 52주 구간은 +1주에서 r=0.936으로 소폭 더 높음)를 문헌과 나란히 놓고 읽을 필요가 있다. 먼저 상관계수의 크기 자체는 문헌에 견주어 이례적으로 높다 — 개별 연구들의 상관은 대개 0.5~0.9대에 분포하는데(예: Kim et al. 2024의 한국 다병원체 연구는 병원체별로 ρ=−0.18~0.92로 매우 넓게 분산), r=0.919는 그 상한에 가깝다. 그러나 상관계수의 크기와 "선행 시차"는 서로 다른 개념이다. README 표(§6)에서 r이 최대가 되는 지점이 "시차 0주"와 "+1주"라는 사실은, 하수 신호가 임상 신고를 앞서는 것이 아니라 **거의 동시에 움직이거나, 오히려 임상 지표가 하수보다 최대 1주 정도 먼저 나타날 수도 있음**을 시사한다(표의 k는 "하수 t주 대 임상 t+k주" 상관이므로 k>0에서 r이 더 크다는 것은 임상이 하수보다 먼저인 조합에서 더 잘 맞는다는 뜻이다). 이는 문헌에서 흔히 보고되는 "하수가 임상보다 며칠~2주 선행"이라는 배출·하수관 이동시간(shedding/hydraulic) 기반의 기대와는 방향이 다르다.

공교롭게도 이 결과는 고립된 사례가 아니다. KOWAS를 직접 운영하는 기관의 전국 단위 분석(Choi et al., 2025)도 우측정렬 이동평균 기준 **교차상관 최고점이 시차 0(동시성)**에서 나타난다고 보고해, README의 패턴과 방향이 일치한다. 반면 같은 한국 내에서도 용인시 6개 처리장 단위 연구(Kim et al., 2024)는 SARS-CoV-2에 대해 상관이 사실상 없었다(ρ=−0.18)고 보고해, 공간 집계 단위(전국·시·도 대 개별 처리장)에 따라 결과가 크게 달라질 수 있음을 보여준다. 종합하면, 이 데이터셋의 높은 상관계수를 "강한 선행 신호"로 과잉 해석하지 않는 것이 중요하다. r=0.919는 하수 지표가 임상 유행과 밀접히 동조한다는 근거이지, 그 자체로 몇 주 앞선 예측력을 보장하는 근거는 아니다. t+2주 예측이라는 이 과제의 목표 지평은 문헌이 보고하는 전형적 선행 폭(며칠~2주)의 상단 근처에 있어, 순수한 통계적 지연만으로는 쉽게 달성되기 어려운 도전적인 설정이라고 봐야 한다.

방법론적으로도 문헌은 이번 과제의 두 가지 실무적 함의를 뒷받침한다. 첫째, 정규화(normalization)가 조기경보 신뢰도를 좌우한다. 유량·전기전도도·crAssphage 등으로 희석을 보정한 연구군은 그렇지 않은 연구보다 임상자료와의 상관이 더 안정적이라고 보고하며(정규화 방법론 그룹, medRxiv 2021), Hill et al.(2023)은 유량 자료 부재를 자신들의 핵심 한계로 꼽는다. 이는 README §5-4가 지적한 "시·도 집계에서는 강수 희석 효과가 보이지 않는다"는 현상과 맞닿아 있다 — 개별 처리장·유역 단위에서는 존재할 수 있는 희석 신호가, 여러 유역이 섞인 시·도 집계 단계에서 정규화 없이 상쇄되었을 가능성을 문헌이 뒷받침한다. 둘째, 표본 규모와 과적합 문제다. 리뷰한 연구 대부분은 수개월~2년, 한 자릿수~두 자릿수의 지역(San Diego 1개 카운티, Chesapeake 5개 관거, Ohio 9개 지역사회, Yongin 6개 처리장)을 다루며, Ai et al.(2022)은 소규모 데이터셋과 과적합 위험을 명시적 한계로 적었다. KOWAS-EPI 패널도 독립 시계열은 17개 시·도 × 179주에 불과해 README §5-6이 "대규모 딥러닝·GNN이 반드시 유리하지 않다"고 경고한 것과 문헌의 우려가 정확히 겹친다.

결론적으로 이번 리뷰가 시사하는 실천적 방향은 세 가지다. (1) 목표 지평 t+2주는 문헌상 전형적 선행 폭의 상단에 위치하므로, 순수 상관·리드타임에만 의존하기보다 계절성·추세 등 시계열 자체의 예측가능한 구조를 함께 활용해야 한다. (2) README의 r=0.919는 방향(동시~임상 소폭 선행)까지 함께 읽어야 하며, "하수가 임상을 앞선다"는 문헌의 일반적 기대를 이 데이터에 그대로 투영하면 안 된다. (3) 정규화·집계 단위 문제와 소규모 표본에 따른 과적합 위험은 모델 설계 단계에서부터 반영해야 할 구조적 제약이다.

---

## 3. 보강 조사 — README 특정 이슈별 문헌 심화

사용자 요청으로 README.md의 4개 구체적 이슈(강수 희석 미검출, 급증 경보 임계값, 행정구역 단위 집계 타당성, DataON 이종 도메인 융합)를 문헌으로 추가 조사했다. 검색은 2026-09 WebSearch/WebFetch로 수행했고, ScienceDirect·Springer(link.springer.com)·PubMed 다수가 쿠키/구독 장벽으로 본문 접근이 막혀 **검색 스니펫 수준**으로만 확인된 항목은 "(원문 미확인)"으로 표시했다. §1~3(비교표·600단어 서술·참고문헌)은 수정하지 않았다.

### (A)+(C) 강수 희석 미검출 & 행정구역 단위 집계의 타당성

두 주제는 사실상 같은 방법론적 뿌리(공간 집계 단위 선택의 영향)를 공유해 함께 정리한다.

- **MAUP과 하수 감시** *(원문 미확인, Science of the Total Environment, 2024-12 게재로 확인)* — "The effect of the modifiable areal unit problem (MAUP) on spatial aggregation of COVID-19 wastewater surveillance data." 행정구역·격자 등 **집계 단위(areal unit)의 모양·크기 선택 자체가 집계값을 바꾸는 통계적 편향**(MAUP)이 COVID-19 하수 감시 자료에서도 나타남을 보고. 여러 처리장 값을 중앙값·비가중평균·인구가중평균 등 서로 다른 방식으로 합칠 때 결과가 달라진다는 점도 다룸.
- **관할구역 단위 해석을 위한 공간집계 방법 비교** *(원문 미확인, Research Square/Discover Public Health)* — "Spatial aggregation methods for interpreting wastewater concentrations at jurisdictional scales: Insights from two SARS-CoV-2 monitoring programs." 두 개의 실제 운영 중인 감시 프로그램에서 서로 다른 집계 방식(관할구역 단위 vs 처리장 단위)이 해석에 미치는 영향을 비교. 처리장 간 인구·비인간 기여(강수·산업폐수 등)가 달라 **"여러 유역을 그대로 합산해도 되는지" 자체가 자명하지 않다**고 지적.
- **하위-유역(sub-sewershed) 수준 시공간 감시 리뷰** *(원문 미확인, MDPI *Environments*, doi:10.3390/environments13070382)* — 제목·초록 수준에서 sub-sewershed 해상도 없이는 "공중보건상 가장 의미 있는 차이가 보이지 않게 된다"는 취지의 비판적 리뷰로 확인(검색 스니펫 근거, 본문 미확인).
- **England 대형 하수처리장 통계분석** *(원문 미확인, PubMed ID 42381572)* — "Drivers of wastewater dynamics: a statistical analysis of England's large wastewater treatment works." 제목상 대형 처리장 단위 하수 동태의 통계적 요인 분석이나, 쿠키 장벽으로 본문 수치는 확인하지 못함.

**소결론**: 문헌은 하수 신호를 광역 행정구역처럼 여러 유역이 섞인 단위로 집계하면 MAUP류 편향과 유역 간 이질성(강수 민감도·산업폐수 비중 차이 등)이 신호를 희석·상쇄시킬 수 있다는 것을 일관되게 지적한다. 이는 README §5-4가 "한 시·도 안에 여러 유역이 섞여 신호가 상쇄되는 것으로 봅니다"라고 적은 **가설을 직접 검증하지는 못하지만, 메커니즘적으로 개연성 있는 설명으로 뒷받침**한다. 다만 이 KOWAS-EPI 데이터가 시·도 단위로만 제공되는 이상, 그 가설 자체를 이 데이터만으로 검증할 방법은 없고 처리장 단위 재집계나 DataON 유역 자료 결합이 있어야 검증 가능하다는 점도 문헌이 시사한다(→ (D)와 연결).

### (B) 급증 경보 임계값 방법론

- **CDC Wastewater Viral Activity Level (WVAL)** *(원문 확인 완료, 공식 CDC 페이지, https://www.cdc.gov/wastewater/about/wval.html)* — 미국 National Wastewater Surveillance System의 공식 경보 지표. 방식은 **표준편차 기반 z-score**: `(현재값 − 기준선) / 표준편차`. 기준선은 원칙적으로 **최근 24개월(COVID-19) 자료**에서 산출하고(신규 사이트는 182~365일 지나야 자체 기준선으로 전환), 바이러스별로 다른 z-score 구간(예: COVID-19는 ≤2.6/2.6~4.9/4.9~7.9/7.9~11.6/>11.6의 5단계)을 적용한다.
- **KOWAS-EPI의 정의(README §2, §4-2)** — `target_conc_t2 ≥ 1.3 × conc_base_avg(t)`, 여기서 `conc_base_avg`는 t−3~t의 **단 4개 주** 이동평균이다.

**소결론**: CDC WVAL과 비교하면 KOWAS-EPI의 경보 정의는 (i) 기준선 산출 기간이 24개월이 아니라 4주로 훨씬 짧아 계절적 기저 수준 변화에 취약하고, (ii) 변동성(표준편차)을 전혀 반영하지 않는 단순 배수(1.3배) 규칙이라 원래 변동이 큰 시·도(예: 소규모 표본 지역)와 안정적인 시·도를 동일 기준으로 판정한다는 차이가 있다. README도 §2에서 "대회용 조작적 정의이며 보건당국의 공식 경보 기준이 아니다"라고 명시하므로 이 차이는 설계상 알려진 단순화로 봐야 하며, 모델링 시에는 이 임계값이 표준편차를 무시한 규칙임을 감안해 분류 성능(Macro-F1)이 시·도별 변동성 차이에 민감할 수 있음을 염두에 두는 것이 좋다.

### (D) 이종 도메인 융합(DataON, §7) 관련 선행연구

- 이번 조사에서는 "하수처리장 위경도를 유역에 공간조인해 산출한 유역 단위 강수가 하수 기반 감염병 예측력을 실제로 향상시켰다"는 것을 직접 검증한 동료심사 논문은 찾지 못했다. 관련성이 있는 인접 문헌은 다음과 같다.
  - 하수 농도 **정규화(유량·전기전도도·crAssphage)** 문헌(§1의 11번, medRxiv 2021)은 유역별 물리적 특성을 반영한 보정이 임상자료와의 상관을 개선한다고 보고하지만, 이는 강수-유역 매핑이 아니라 처리장 자체의 유량 측정치를 쓰는 접근이라 DataON이 제안하는 "위경도 기반 유역 매핑"과는 방법론이 다르다.
  - 도시 유역 경계 설정(watershed/catchment delineation) 관련 문헌은 다수 존재하지만(예: GIS 기반 도시 집수구역 정교화, Springer *Discover Water* 2024), **하수 감시와 직접 결합해 예측 성능을 검증한 사례는 이번 검색에서 확인되지 않았다.**

**소결론**: README §7이 이 융합을 "검증되지 않은 가설이며 핵심 도전 과제"라고 명시한 것은 문헌 현황과 정확히 부합한다. 즉 유역 단위 강수 결합이 예측력을 높일 것이라는 **이론적 근거(유역 이질성이 신호를 희석시킨다는 (A)의 발견)는 있지만, 이를 실제로 구현·검증한 선행연구는 이번 조사 범위에서 발견되지 않았다.** 따라서 이 부분을 시도한다면 KOWAS-EPI 프로젝트 자체가 관련 실증사례가 드문 영역에서 새로운 시도를 하는 것이며, 검증 안 된 가설이라는 README의 신중한 표현이 과장이 아니라는 점을 확인했다.

---

## 4. 참고문헌 (근거 URL)

1. Li, X. et al. (2022). *Science of the Total Environment*. Wastewater surveillance to infer COVID-19 transmission: A systematic review. https://pubmed.ncbi.nlm.nih.gov/34798721/ · https://www.sciencedirect.com/science/article/pii/S0048969721051354
2. Chen, C. et al. (2024). arXiv:2403.15291. Wastewater-based Epidemiology for COVID-19 Surveillance and Beyond: A Survey. https://arxiv.org/html/2403.15291v2
3. Choi, Y.-J. et al. (2025). *J Korean Med Sci*. National Wastewater Surveillance of SARS-CoV-2 Across Provinces and Regions in the Republic of Korea From January to August 2023. https://pmc.ncbi.nlm.nih.gov/articles/PMC12322592/
4. Kim, Y.-T. et al. (2024). *Scientific Reports* 14:24544. Development of a wastewater based infectious disease surveillance research system in South Korea. https://pmc.ncbi.nlm.nih.gov/articles/PMC11490628/
5. Hill, D.T. et al. (2023). *Infectious Disease Modelling* 8(4):1138–1150. https://pmc.ncbi.nlm.nih.gov/articles/PMC10665827/
6. Ai, Y., He, F., Lancaster, E., Lee, J. (2022). *PLOS ONE*. Application of machine learning for multi-community COVID-19 outbreak predictions with wastewater surveillance. https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0277154
7. Jeng, H.A. et al. (2023). *Science of the Total Environment*. https://pmc.ncbi.nlm.nih.gov/articles/PMC10122554/
8. Karthikeyan, S. et al. (2021). *mSystems*. High-Throughput Wastewater SARS-CoV-2 Detection Enables Forecasting of Community Infection Dynamics in San Diego County. https://journals.asm.org/doi/10.1128/msystems.00045-21
9. (원문 미확인, 2차 출처) Zhao, L. et al. Detroit ARIMA/SARIMA/VAR 비교 연구 — 검색 스니펫 근거.
10. (원문 미확인) Tracking the Time Lag between SARS-CoV-2 Wastewater Concentrations and Three COVID-19 Clinical Metrics: A 21-Month Case Study in the Tricounty Detroit Area, Michigan. *J Environ Eng* 150(1), 2024. https://ascelibrary.org/doi/10.1061/JOEEDU.EEENG-7509
11. 하수 정규화 방법론(유량·EC·crAssphage). medRxiv 2021.11.30.21266889. https://www.medrxiv.org/content/10.1101/2021.11.30.21266889.full.pdf

### §3(보강 조사)에서 새로 인용한 문헌

12. (원문 미확인) The effect of the modifiable areal unit problem (MAUP) on spatial aggregation of COVID-19 wastewater surveillance data. *Science of the Total Environment*, 2024-12. https://www.sciencedirect.com/science/article/abs/pii/S0048969724078331
13. (원문 미확인) Spatial aggregation methods for interpreting wastewater concentrations at jurisdictional scales: Insights from two SARS-CoV-2 monitoring programs. *Discover Public Health* / Research Square. https://link.springer.com/article/10.1186/s12982-026-02934-7 · https://www.researchsquare.com/article/rs-8205614/v1
14. (원문 미확인) Toward Sub-Sewershed Spatio-Temporal Wastewater Surveillance: A Critical Review and a Candidate Multimodal Foundation-Model Framework. *Environments* 13(7):382. https://www.mdpi.com/2076-3298/13/7/382
15. (원문 미확인) Drivers of wastewater dynamics: a statistical analysis of England's large wastewater treatment works. PubMed ID 42381572. https://pubmed.ncbi.nlm.nih.gov/42381572/
16. (원문 확인 완료, 공식 기관 자료) CDC. Using the Wastewater Viral Activity Level (WVAL). National Wastewater Surveillance System. https://www.cdc.gov/wastewater/about/wval.html
