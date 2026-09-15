# 문헌 리뷰 — 하수 기반 역학(WBE)을 이용한 감염병 조기예측

작성일: 2026-09-15 (최초) · 2026-09-15 개정(DOI 전수 재검증 + 논문 확충 + 알고리즘 비교)

## 가정 및 전제

- **검색 도구**: WebSearch(2026-09 시점 웹 인덱스) + WebFetch(개별 논문 페이지 확인). `parallel-cli`는 이 환경에 설치되어 있지 않아 사용하지 못했다.
- **검색 키워드**: "wastewater-based epidemiology forecasting", "SARS-CoV-2 wastewater surveillance lead time", "wastewater viral load early warning", "wastewater epidemiology time series model", "wastewater surveillance machine learning forecast", "Korea wastewater surveillance SARS-CoV-2", "wastewater precipitation dilution normalization", "wastewater SARS-CoV-2 LSTM ARIMA comparison forecasting", "wastewater surveillance alert threshold z-score" 등 영어 키워드를 주력으로 사용했다. 한국어 키워드는 WebSearch가 미국 기반이라 결과가 거의 없어 "Korea wastewater surveillance"로 대체했다.
- **포함 기준**: (1) 동료심사 학술지 또는 arXiv/medRxiv 등 검증 가능한 프리프린트, (2) 하수 바이러스(주로 SARS-CoV-2) 농도와 임상 지표 간의 시차·예측·상관관계 또는 예측 알고리즘 비교를 다룬 연구, (3) 2021년 이후 발표.
- **DOI 검증 원칙(2026-09-15 개정 — 이번 재검증의 핵심 기준)**: 모든 인용은 DOI가 있으면 `https://doi.org/<DOI>`를 WebFetch로 직접 열어(또는 CrossRef/Semantic Scholar API로 서지정보를 대조해) 제목·저자·저널이 일치함을 확인했다. **링크가 열리지 않거나(404/403/타임아웃), 서지정보가 불일치하거나, 애초에 실존을 확인하지 못한 항목은 목록에서 제외했다** — "원문 미확인"이라는 회색지대 표시로 남겨두지 않았다. DOI가 없는 정당한 자료(정부기관 공식 페이지 등)는 안정적 기관 URL을 DOI 대신 쓰되 동일하게 WebFetch로 직접 확인했다.
- 이 재검증 과정에서 기존 인용 1건의 **저자 오류**(아래 §1 각주 참고)를 발견해 정정했고, 근거를 확인하지 못한 인용 1건을 제거했다.

---

## 1. 논문 비교표

| # | 서지정보 | 방법론 | 선행 시차(lead time) / 성능 결과 | 데이터 규모 | 주요 한계점 |
|---|---|---|---|---|---|
| 1 | Shah, S., Gwee, S.X.W., Ng, J., Lau, N., Koh, J.-E., Pang, J. (2021). *Science of the Total Environment*. "Wastewater surveillance to infer COVID-19 transmission: A systematic review." DOI: [10.1016/j.scitotenv.2021.150060](https://doi.org/10.1016/j.scitotenv.2021.150060) | 체계적 문헌고찰(PRISMA), 763편 중 92편 선별 | 다수 연구가 임상 사례 확진 이전 하수 양성을 보고(초기 팬데믹 연구 일부는 지역사회 첫 확진 이전 최대 수개월 선행 사례 포함); 정량적 분포는 원문 결과표 미확인 | 34개국 92개 연구, 표본 26,197건, 대상 인구 321명~1,140만 명 | 연구 간 정규화·채취방법 이질성 커서 메타분석적 lead time 통합이 어려움 |
| 2 | Chen, C., Wang, Y., Kaur, G. et al. (2024). arXiv:2403.15291. "Wastewater-based Epidemiology for COVID-19 Surveillance and Beyond: A Survey." DOI: [10.48550/arXiv.2403.15291](https://doi.org/10.48550/arXiv.2403.15291) | 방법론 분류 서베이 — 모델 기반(배출모델·SEIR) vs 데이터 기반(ARIMA/SARIMA/VAR, 회귀·GAM, RF/SVR, ANN/ANFIS) | "하수 바이러스량은 대체로 임상 데이터보다 1~2주 선행"(정성적 결론); 어떤 모델군이 더 우수한지에 대한 정량 비교는 서베이 자체에 없음 | 2,567편 중 137편 선별, 75개국 이상 공개 데이터셋 목록화 | 배출량 개인차, 손실·희석에 따른 과소추정, 임상자료와의 시간 해상도 불일치 |
| 3 | Choi, Y.-J., Kim, L.H., Jang, J. et al. (2025). *Journal of Korean Medical Science*. "National Wastewater Surveillance of SARS-CoV-2 Across Provinces and Regions in the Republic of Korea From January to August 2023." DOI: [10.3346/jkms.2025.40.e94](https://doi.org/10.3346/jkms.2025.40.e94) | KOWAS 운영기관(질병관리청) 자체 분석 — 우측정렬 3주 이동평균 기반 교차상관 | 전국 상관 r=0.85(P<0.001), 부산 r=0.90(지역 최고); **교차상관 최고점이 시차 0(동시)에서 발생** | 17개 시·도, 62개 하수처리장, 34주(2023-01~08), 표본 2,176건 | 처리장 포함률 50% 미만 지역은 유의한 상관 없음; 강우 희석(합류식 관거); 인구이동 |
| 4 | Kim, Y.-T. et al. (2024). *Scientific Reports* 14:24544. "Development of a wastewater based infectious disease surveillance research system in South Korea." DOI: [10.1038/s41598-024-76614-4](https://doi.org/10.1038/s41598-024-76614-4) | 실시간 PCR 기반 47종 병원체 동시 감시, 스피어만 상관분석 | SARS-CoV-2는 **상관 없음**(ρ=−0.18, p=0.4); 노로바이러스 GII(ρ=0.92)·인간코로나바이러스(ρ=0.90)는 강한 상관 | 용인시 하수처리장 6개소, 2022-12~2023-11(1년), 표본 144건 | 6개 처리장 권역의 지역사회 임상자료와 직접 비교 불가; 병원체별 이질적 결과 |
| 5 | Hill, D.T. et al. (2023). *Infectious Disease Modelling* 8(4):1138–1150. "Wastewater surveillance provides 10-days forecasting of COVID-19 hospitalizations superior to cases and test positivity: A prediction study." DOI: [10.1016/j.idm.2023.10.004](https://doi.org/10.1016/j.idm.2023.10.004) | 일반화선형혼합모델(GLMM), 포아송 카운트 모형으로 입원 예측 | 병원 입원과의 상관이 **10일 지연에서 최고**(r=0.415); 예측값-관측값 상관 r=0.77 — 제목 자체가 사례·양성률보다 우수한 10일 예측력을 주장 | 56개 카운티·109개 처리장, 인구 약 1,380만 명, 2020-04~2022-06 | 대부분 지점 유량 자료 없어 정규화 곤란; 실험실 간 분석법 이질성 |
| 6 | Ai, Y., He, F., Lancaster, E., Lee, J. (2022). *PLOS ONE*. "Application of machine learning for multi-community COVID-19 outbreak predictions with wastewater surveillance." DOI: [10.1371/journal.pone.0277154](https://doi.org/10.1371/journal.pone.0277154) | 비시계열(선형회귀·GBDT·DNN) vs 시계열(Prophet·LSTM) 비교 | **LSTM 최고**(train R²=0.94, test R²=0.81) vs Prophet(train R²=0.83, test R²=0.63); 5일 시차 반영 시 RMSE 10% 개선 | 오하이오주 9개 지역사회, 2020-09~2021-06, 표본 620건 | 소규모 데이터셋, 저상관 지역(Athens) 포함 시 성능 저하, 과적합 위험 |
| 7 | Jeng, H.A., Singh, R., Diawara, N. et al. (2023). *Science of the Total Environment* 885. "Application of wastewater-based surveillance and copula time-series model for COVID-19 forecasts." DOI: [10.1016/j.scitotenv.2023.163655](https://doi.org/10.1016/j.scitotenv.2023.163655) | ARMA + 가우스 코플라(Copula) 결합 2단계 시계열 모형 | 모델이 임상 확진 파동보다 **최소 3~5일 선행**해 추세를 예측 | 미국 체서피크(VA) 5개 하수관거, 2021-06~2022-06 | 소규모 데이터셋, 주 1회 표본, 교란변수 미포함 |
| 8 | Karthikeyan, S. et al. (2021). *mSystems*. "High-Throughput Wastewater SARS-CoV-2 Detection Enables Forecasting of Community Infection Dynamics in San Diego County." DOI: [10.1128/msystems.00045-21](https://doi.org/10.1128/msystems.00045-21) | 다변량 ARIMA(과거 확진자 수 + 하수 농도 + 채취일) | 1~3주 앞선 확진자 수 예측에 활용(정성적 확인) | 캘리포니아 샌디에이고 카운티, 고빈도(거의 매일) 표본 | 예측 지평이 길어질수록 오차 증가, 대학 캠퍼스 중심이라 외삽 제한 |
| 9 | Alhassan, F., Karami, H., Bleichrodt, A., Hyman, J.M., Fung, I.C.H., Luo, R., Chowell, G. (2025). arXiv:2512.01074. "COVID-19 Forecasting from U.S. Wastewater Surveillance Data: A Retrospective Multi-Model Study (2022-2024)." DOI: [10.48550/arXiv.2512.01074](https://doi.org/10.48550/arXiv.2512.01074) | **회고적 다중모델 비교** — ARIMA, GAM, 단순선형회귀, Prophet, n-sub-epidemic 앙상블(가중치별 여러 버전) | 지평별로 최적 모델이 다름: **1~2주는 ARIMA·GAM이 최고**, **3~4주는 n-sub-epidemic 비가중앙상블이 최고**(특히 전국·중서부·서부); Prophet·단순회귀는 지역·지평 불문 지속적으로 최하위 | 미국 전역·권역별, 2022~2024년 회고 분석, 평가지표 MAE/MSE/WIS/95%PI커버리지 | 리드타임 자체는 다루지 않음(지평별 정확도만 비교); 모형 순위가 평가지표에 따라 다를 수 있음 |
| 10 | Schenk, H., Rauch, W., Zulli, A., Boehm, A.B. (2024). *PLOS ONE*. "SARS-CoV-2 surveillance in US wastewater: Leading indicators and data variability analysis in 2023–2024." DOI: [10.1371/journal.pone.0313927](https://doi.org/10.1371/journal.pone.0313927) | 대규모 교차상관·피크타이밍 분석 | 하수가 입원 지표보다 **2~12일 선행**; 모니터링 상위 10개 주 기준 중앙값 피크선행 7.5일, 중앙값 교차상관 지연 4일 | 미국 40개 주 189개 처리장, 약 29,364건 일별 표본, 2023-05~2024-06 | 주별 편차 매우 큼(−12~+7.5일); 데이터 변동성이 리드타임 추정 신뢰도를 낮춤 |
| 11 | Mustapha, M.M., Choi, L.E., Bergroth, T. et al. (2025). *Frontiers in Public Health*. "Association between SARS-CoV-2 in wastewater and COVID-19 hospitalizations in three countries, 2022–2024." DOI: [10.3389/fpubh.2025.1679596](https://doi.org/10.3389/fpubh.2025.1679596) | 3개국(미국·덴마크·네덜란드) 비교, 회귀 기반 입원 예측 | 덴마크·네덜란드는 최대상관 시 약 **1주 지연**(임상이 하수보다 늦음), 미국은 lag 0; 1주 앞선 입원 예측 MAPE 11.2~22.6%(4주 앞은 32.5~62.3%로 악화) | 미국·덴마크·네덜란드 3개국, 2022~2024 | 국가 간 인프라·검사체계 차이로 일반화 제한; 지평이 길어질수록 오차 급증 |
| 12 | Li, X., Wu, C., Jiang, J. et al. (2026). *Journal of Water and Health*. "A dual-branch deep learning framework for tiered early warning of COVID-19 utilizing wastewater data." DOI: [10.2166/wh.2026.150](https://doi.org/10.2166/wh.2026.150) | 이중분기(dual-branch) 딥러닝 + 환경공변량 + FFT | 창저우(중국) 사례 **R²=0.99**, 외부검증에서 **3주 앞선 경보단계**를 정확히 예측했다고 보고 | 중국 창저우 단일 도시 사례 | 단일 도시 검증(교차 지역 일반화 미검증); 접근 제한으로 비교모형·표본 상세 미확인 |
| 13 | Meadows, T., Coats, E.R., Narum, S., Top, E.M., Ridenhour, B.J., Stalder, T. (2024). *Water Research*. "Epidemiological model can forecast COVID-19 outbreaks from wastewater-based surveillance in rural communities." DOI: [10.1016/j.watres.2024.122671](https://doi.org/10.1016/j.watres.2024.122671) | 역학모형(SEIR류) 기반 예측, 농촌 지역 특화 | 평균 **6±4일** 리드타임(범위 0~11일); 9~15일 예측이 신뢰할 만하다고 보고 | 미국 농촌 지역사회(도시 대비 표본·인프라 제한) | 농촌 소규모 처리장 특유의 낮은 표본빈도; 도시지역 외삽 제한 |
| 14 | Zhao, L., Faust, R.A., David, R.E., Norton, J., Xagoraraki, I. (2024). *Journal of Environmental Engineering* 150(1). "Tracking the Time Lag between SARS-CoV-2 Wastewater Concentrations and Three COVID-19 Clinical Metrics: A 21-Month Case Study in the Tricounty Detroit Area, Michigan." DOI: [10.1061/JOEEDU.EEENG-7509](https://doi.org/10.1061/JOEEDU.EEENG-7509) | 하수 농도와 확진자·입원·ICU 입원 3개 임상지표 간 시차 전용 추적 설계 | 서지정보(제목·전체 저자명)는 CrossRef로 확인했으나 **본문이 구독장벽(ASCE)에 막혀 지표별 구체적 일수는 확인하지 못함** | 미시간주 트라이카운티(디트로이트권), 2020-09~2022-10(21개월) | 원문 상세 미확인 — 존재·서지정보만 검증된 인용 |
| 15 | Langeveld, J., Schilperoort, R., Heijnen, L. et al. (2021). medRxiv preprint 2021.11.30.21266889. "Normalisation of SARS-CoV-2 concentrations in wastewater: the use of flow, conductivity and CrAssphage." DOI: [10.1101/2021.11.30.21266889](https://doi.org/10.1101/2021.11.30.21266889) | 유량(flow)·전기전도도(EC)·crAssphage를 이용한 하수 농도 정규화 방법 비교, 9개 지점 | 예측/선행시차 논문은 아니지만, 정규화 없이는 강우·희석 효과가 신호를 왜곡해 단기 추세 판단(=조기경보 신뢰도)이 흔들림을 보고 | 네덜란드 9개 모니터링 지점 | 정규화 변수(유량계) 없는 처리장이 많아 실무 적용 제약; 프리프린트(정식 출판 여부 미확인) |

> **정정 사항**: 개정 전 문서는 1번 논문의 저자를 "Li, X. et al."로 잘못 표기했었다. CrossRef·Semantic Scholar로 재검증한 결과 실제 저자는 Shah, Gwee, Ng, Lau, Koh, Pang이며 본 개정판에서 정정했다(§2 서술 요약의 인용도 함께 수정). 개정 전 9번 항목("Zhao, L. et al., 2차 출처만 확인, ARIMA/SARIMA/VAR 비교")은 DOI·원 논문을 찾지 못해 제거했다 — 다만 재검증 과정에서 "Zhao, L."이 실제로는 14번 논문(Tracking the Time Lag..., Tricounty Detroit)의 제1저자임을 확인해, 그쪽에 정확한 서지정보로 통합했다.

---

## 2. 종합 서술 요약 (수업 중간보고서 "문헌 리뷰" 섹션 초안, 약 670단어 — 제출용 `reports/midterm/literature_review.md`는 650단어로 별도 편집됨)

하수 기반 역학(wastewater-based epidemiology, WBE)은 감염자가 증상을 인지하고 검사를 받기 전부터 배출하는 바이러스 유전물질을 하수에서 검출함으로써, 임상 신고 체계보다 앞서 지역사회 감염 동향을 포착할 수 있다는 전제에서 출발한다. 이 전제는 팬데믹 초기부터 폭넓게 검증되어 왔으며, 763편 중 92편을 선별한 체계적 문헌고찰(Shah et al., 2021)은 34개국·26,197건 표본을 아우르는 연구들에서 하수 신호가 임상 확진보다 먼저 나타난 사례를 다수 보고했다고 정리한다. 다만 이런 초기 보고 중 "수개월 선행"류의 극단값은 대개 지역사회 첫 유행이 시작되기 전 저빈도 검사 체계의 사각지대를 하수가 메운 사례이지, 정상 가동 중인 감시체계에서 반복적으로 관찰되는 예측 리드타임은 아니다.

실제로 예측/시차를 직접 정량화한 개별 연구들의 수치는 훨씬 보수적으로 수렴한다. San Diego 다변량 ARIMA 연구(Karthikeyan et al., 2021)는 1~3주 지평의 예측에 하수 자료를 활용했고, Ohio 9개 지역사회를 LSTM·Prophet 등으로 비교한 연구(Ai et al., 2022)는 5일 시차를 넣었을 때 예측 오차가 개선됨을 보였다. Chesapeake 지역의 코플라 시계열 모형(Jeng et al., 2023)은 3~5일의 선행 추세 포착을, 56개 카운티 입원자 예측 GLMM(Hill et al., 2023)은 10일 지연에서 상관이 최고였음을 보고했다. 최근 대규모 미국 전역 분석(Schenk et al., 2024, 189개 처리장)도 2~12일 선행(중앙값 약 4~7.5일)을 재확인했다. 이를 종합하면 문헌에서 반복적으로 확인되는 선행 시차는 대체로 **며칠에서 최대 2주 내외**이며, arXiv 서베이(Chen et al., 2024)도 이를 "대체로 1~2주 선행"으로 요약한다. 즉 WBE의 조기경보 가치는 실재하지만 그 폭은 생각보다 좁고, 방법론(정규화 여부, 채취 빈도, 예측모형 종류)에 따라 크게 흔들린다는 것이 문헌의 공통된 함의다.

이 지점에서 이번 KOWAS-EPI README §6의 수치(하수·임상 로그 상관이 시차 0주와 +1주에서 동일하게 최댓값 r=0.919, 최근 52주 구간은 +1주에서 r=0.936으로 소폭 더 높음)를 문헌과 나란히 놓고 읽을 필요가 있다. 먼저 상관계수의 크기 자체는 문헌에 견주어 이례적으로 높다 — 개별 연구들의 상관은 대개 0.5~0.9대에 분포하는데(예: Kim et al. 2024의 한국 다병원체 연구는 병원체별로 ρ=−0.18~0.92로 매우 넓게 분산), r=0.919는 그 상한에 가깝다. 그러나 상관계수의 크기와 "선행 시차"는 서로 다른 개념이다. README 표(§6)에서 r이 최대가 되는 지점이 "시차 0주"와 "+1주"라는 사실은, 하수 신호가 임상 신고를 앞서는 것이 아니라 **거의 동시에 움직이거나, 오히려 임상 지표가 하수보다 최대 1주 정도 먼저 나타날 수도 있음**을 시사한다(표의 k는 "하수 t주 대 임상 t+k주" 상관이므로 k>0에서 r이 더 크다는 것은 임상이 하수보다 먼저인 조합에서 더 잘 맞는다는 뜻이다). 이는 문헌에서 흔히 보고되는 "하수가 임상보다 며칠~2주 선행"이라는 배출·하수관 이동시간(shedding/hydraulic) 기반의 기대와는 방향이 다르다. 3개국 비교 연구(Mustapha et al., 2025)도 덴마크·네덜란드는 임상이 하수보다 1주 늦지만 미국은 동시(lag 0)라고 보고해, "선행 방향"조차 국가·데이터 특성에 따라 갈릴 수 있음을 뒷받침한다.

공교롭게도 이 결과는 고립된 사례가 아니다. KOWAS를 직접 운영하는 기관의 전국 단위 분석(Choi et al., 2025)도 우측정렬 이동평균 기준 **교차상관 최고점이 시차 0(동시성)**에서 나타난다고 보고해, README의 패턴과 방향이 일치한다. 반면 같은 한국 내에서도 용인시 6개 처리장 단위 연구(Kim et al., 2024)는 SARS-CoV-2에 대해 상관이 사실상 없었다(ρ=−0.18)고 보고해, 공간 집계 단위(전국·시·도 대 개별 처리장)에 따라 결과가 크게 달라질 수 있음을 보여준다. 종합하면, 이 데이터셋의 높은 상관계수를 "강한 선행 신호"로 과잉 해석하지 않는 것이 중요하다. t+2주 예측이라는 이 과제의 목표 지평은 문헌이 보고하는 전형적 선행 폭(며칠~2주)의 상단 근처에 있어, 순수한 통계적 지연만으로는 쉽게 달성되기 어려운 도전적인 설정이라고 봐야 한다.

방법론적으로도 문헌은 이번 과제의 실무적 함의를 뒷받침한다. 첫째, 정규화(normalization)가 조기경보 신뢰도를 좌우한다 — 유량·전기전도도·crAssphage로 희석을 보정한 연구군(Langeveld et al., 2021)은 그렇지 않은 연구보다 임상자료와의 상관이 더 안정적이라고 보고하며, Hill et al.(2023)도 유량 자료 부재를 핵심 한계로 꼽는다. 둘째, 표본 규모와 과적합 문제다 — 리뷰한 연구 대부분은 한 자릿수~두 자릿수의 지역을 다루며 소규모 데이터셋·과적합 위험을 명시적 한계로 적는다. 셋째, **알고리즘 선택도 예측 지평에 따라 갈린다** — 미국 전역 회고적 다중모델 비교(Alhassan et al., 2025)는 1~2주 지평에서 ARIMA·GAM이 Prophet·단순회귀보다 꾸준히 우수했고, 3~4주 이상에서는 앙상블 기법이 우위를 보였다. KOWAS-EPI 패널의 독립 시계열은 17개 시·도×179주에 불과해(README §5-6) 소규모 표본에서 복잡한 모델이 과적합되기 쉽다는 문헌의 경고와 겹치며, t+2주라는 짧은 지평엔 단순 통계모형을 견고한 기준으로 우선 삼는 것이 문헌의 경향과 부합한다.

결론적으로 이번 리뷰가 시사하는 실천적 방향은 네 가지다. (1) 목표 지평 t+2주는 문헌상 전형적 선행 폭의 상단에 위치하므로, 순수 상관·리드타임에만 의존하기보다 계절성·추세 등 시계열 자체의 예측가능한 구조를 함께 활용해야 한다. (2) README의 r=0.919는 방향(동시~임상 소폭 선행)까지 함께 읽어야 하며, "하수가 임상을 앞선다"는 문헌의 일반적 기대를 이 데이터에 그대로 투영하면 안 된다. (3) 정규화·집계 단위 문제와 소규모 표본에 따른 과적합 위험은 모델 설계 단계에서부터 반영해야 할 구조적 제약이다. (4) 짧은 예측 지평(1~2주급)에서는 ARIMA·GAM류의 단순 통계모형이 문헌상 우세하다는 근거가 있으므로, 복잡한 신경망보다 이를 견고한 출발점으로 삼아야 한다.

---

## 3. 보강 조사 — README 특정 이슈별 문헌 심화

사용자 요청으로 README.md의 4개 구체적 이슈(강수 희석 미검출, 급증 경보 임계값, 행정구역 단위 집계 타당성, DataON 이종 도메인 융합)를 문헌으로 추가 조사했다. 아래 인용은 모두 2026-09-15 재검증에서 DOI/CrossRef로 서지정보를 다시 확인했다(§"가정 및 전제" 참고). 본문 상세까지 확인한 항목과 서지정보만 확인한 항목을 구분해 표기했다.

### (A)+(C) 강수 희석 미검출 & 행정구역 단위 집계의 타당성

두 주제는 사실상 같은 방법론적 뿌리(공간 집계 단위 선택의 영향)를 공유해 함께 정리한다.

- **MAUP과 하수 감시** *(서지정보 DOI 검증 완료, 본문 상세는 구독장벽으로 미확인)* — Zhu, Y., Hill, D.T., Zhou, Y., Larsen, D.A. (2024). *Science of the Total Environment* 957. "The effect of the modifiable areal unit problem (MAUP) on spatial aggregation of COVID-19 wastewater surveillance data." DOI: [10.1016/j.scitotenv.2024.177676](https://doi.org/10.1016/j.scitotenv.2024.177676). 행정구역·격자 등 **집계 단위(areal unit)의 모양·크기 선택 자체가 집계값을 바꾸는 통계적 편향**(MAUP)이 COVID-19 하수 감시 자료에서도 나타남을 보고. 저자 중 Hill, D.T.는 §1의 5번 논문과 동일 연구자.
- **관할구역 단위 해석을 위한 공간집계 방법 비교** *(서지정보 DOI 검증 완료, 본문 상세는 구독장벽으로 미확인)* — Chan, E.M.G., Burnor, E., Zulli, A., Lu, C., Yu, A.T., Boehm, A.B. (2026). *Discover Public Health* 23(1):1461. "Spatial aggregation methods for interpreting wastewater concentrations at jurisdictional scales: Insights from two SARS-CoV-2 monitoring programs." DOI: [10.1186/s12982-026-02934-7](https://doi.org/10.1186/s12982-026-02934-7). 두 개의 실제 운영 중인 감시 프로그램에서 서로 다른 집계 방식(관할구역 단위 vs 처리장 단위)이 해석에 미치는 영향을 비교.
- **하위-유역(sub-sewershed) 수준 시공간 감시 리뷰** *(원문 초록 확인 완료)* — Cuadros, D., Chen, X., Tang, M. (2026). *Environments* 13(7):382. "Toward Sub-Sewershed Spatio-Temporal Wastewater Surveillance: A Critical Review and a Candidate Multimodal Foundation-Model Framework." DOI: [10.3390/environments13070382](https://doi.org/10.3390/environments13070382). 현재 방법들이 하수관망 내 세밀한 지리적 해상도에서 질병 패턴을 짚어내지 못하는 한계를 지적하고, 시간 예측·공간 분석·수리(hydraulic) 모델링·교차사이트 학습을 결합한 파운데이션모델 프레임워크를 제안.
- **England 대형 하수처리장 통계분석** *(서지정보 DOI 검증 완료, 검색스니펫으로 주요 결과 확인)* — Maes-Prior, R., Dobson, B., Mijic, A. (2026). *Water Science & Technology*. "Drivers of wastewater dynamics: a statistical analysis of England's large wastewater treatment works." DOI: [10.2166/wst.2026.295](https://doi.org/10.2166/wst.2026.295). 잉글랜드 951개 하수처리구역(sewershed)의 전국 규모 데이터셋을 구축해 다중선형회귀·랜덤포레스트로 일별 처리인구당 유출량·월류(spill) 발생의 주 요인을 분석 — **강수량이 유출량 변동과 월류 발생 모두에 지배적 영향**을 미친다고 보고(정상적 처리장 유출 단계에서는 강수-유량 관계가 뚜렷함을 시사).

**소결론**: 문헌은 하수 신호를 광역 행정구역처럼 여러 유역이 섞인 단위로 집계하면 MAUP류 편향과 유역 간 이질성(강수 민감도·산업폐수 비중 차이 등)이 신호를 희석·상쇄시킬 수 있다는 것을 일관되게 지적한다. 특히 England 연구가 개별 처리장 단위에서는 강수가 유출량의 지배적 요인이라고 보고한 것은, README §5-4가 시·도 집계 단계에서 강수 효과가 사라진다고 밝힌 것과 **대조적** — 개별 처리장 신호는 강수에 민감하지만 여러 유역을 섞은 시·도 집계에서 그 신호가 상쇄된다는 README의 가설과 정확히 부합하는 대비다. 다만 이 KOWAS-EPI 데이터가 시·도 단위로만 제공되는 이상, 그 가설 자체를 이 데이터만으로 검증할 방법은 없고 처리장 단위 재집계나 DataON 유역 자료 결합이 있어야 검증 가능하다는 점도 문헌이 시사한다(→ (D)와 연결).

### (B) 급증 경보 임계값 방법론

- **CDC Wastewater Viral Activity Level (WVAL)** *(원문 확인 완료, 공식 CDC 페이지)* — https://www.cdc.gov/wastewater/about/wval.html. 미국 National Wastewater Surveillance System의 공식 경보 지표. 방식은 **표준편차 기반 z-score**: `(현재값 − 기준선) / 표준편차`. 기준선은 원칙적으로 **최근 24개월(COVID-19) 자료**에서 산출하고(신규 사이트는 182~365일 지나야 자체 기준선으로 전환), 바이러스별로 다른 z-score 구간(예: COVID-19는 ≤2.6/2.6~4.9/4.9~7.9/7.9~11.6/>11.6의 5단계)을 적용한다.
- **KOWAS-EPI의 정의(README §2, §4-2)** — `target_conc_t2 ≥ 1.3 × conc_base_avg(t)`, 여기서 `conc_base_avg`는 t−3~t의 **단 4개 주** 이동평균이다.

**소결론**: CDC WVAL과 비교하면 KOWAS-EPI의 경보 정의는 (i) 기준선 산출 기간이 24개월이 아니라 4주로 훨씬 짧아 계절적 기저 수준 변화에 취약하고, (ii) 변동성(표준편차)을 전혀 반영하지 않는 단순 배수(1.3배) 규칙이라 원래 변동이 큰 시·도와 안정적인 시·도를 동일 기준으로 판정한다는 차이가 있다. README도 §2에서 "대회용 조작적 정의이며 보건당국의 공식 경보 기준이 아니다"라고 명시하므로 이 차이는 설계상 알려진 단순화로 봐야 하며, 모델링 시에는 분류 성능(Macro-F1)이 시·도별 변동성 차이에 민감할 수 있음을 염두에 두는 것이 좋다.

### (D) 이종 도메인 융합(DataON, §7) 관련 선행연구

- 이번 조사에서는 "하수처리장 위경도를 유역에 공간조인해 산출한 유역 단위 강수가 하수 기반 감염병 예측력을 실제로 향상시켰다"는 것을 직접 검증한, DOI로 검증 가능한 동료심사 논문은 찾지 못했다.
- 관련성이 있는 인접 문헌: 하수 농도 **정규화(유량·전기전도도·crAssphage)** 문헌(§1의 15번, Langeveld et al. 2021)은 유역별 물리적 특성을 반영한 보정이 임상자료와의 상관을 개선한다고 보고하지만, 이는 강수-유역 매핑이 아니라 처리장 자체의 유량 측정치를 쓰는 접근이라 DataON이 제안하는 "위경도 기반 유역 매핑"과는 방법론이 다르다. England 연구(위 (A)+(C))도 강수-유출량 관계를 통계적으로 다루지만 감염병 예측과는 직접 결합하지 않았다.

**소결론**: README §7이 이 융합을 "검증되지 않은 가설이며 핵심 도전 과제"라고 명시한 것은 이번에 확충된 문헌 현황과도 정확히 부합한다. 유역 단위 강수 결합이 예측력을 높일 것이라는 **이론적 근거(유역 이질성이 신호를 희석시킨다는 (A)의 발견, England 연구의 강수-유출량 직접 연관성)는 있지만, 이를 실제로 구현·검증한 선행연구는 이번 확충 조사에서도 발견되지 않았다.** 따라서 이 부분을 시도한다면 KOWAS-EPI 프로젝트 자체가 관련 실증사례가 드문 영역에서 새로운 시도를 하는 것이다.

---

## 4. 알고리즘 성능 비교 (문헌 종합)

이번 확충 조사에서 새로 확인한 논문들을 포함해, "이 과제(단기 하수-임상 시계열 예측)에서는 어떤 알고리즘류가 상대적으로 우수하다고 보고되는가"를 종합한다. 수치는 모두 §1 표에서 DOI로 검증한 논문이 실제로 보고한 것만 인용했다.

- **개별 논문 내 모델 비교**: Ai et al.(2022)은 선형회귀·GBDT·DNN·Prophet·LSTM 5개 모델을 오하이오 9개 지역사회 데이터로 비교해 **LSTM이 최고**(train R²=0.94, test R²=0.81)였고 Prophet(train R²=0.83, test R²=0.63)이 근소하게 뒤따랐다고 보고했다.
- **지평별 다중모델 비교**: Alhassan et al.(2025)은 미국 전역 회고 데이터로 ARIMA, GAM, 단순선형회귀, Prophet, n-sub-epidemic 앙상블을 비교해 **1~2주 지평에서는 ARIMA·GAM이 최고**, **3~4주 지평에서는 n-sub-epidemic 비가중앙상블이 최고**라고 보고했다. Prophet과 단순선형회귀는 지역·지평을 불문하고 지속적으로 최하위였다 — Ai et al.의 결과(Prophet이 LSTM보다 열세)와도 방향이 일치한다.
- **딥러닝 특화 사례**: Li, X. et al.(2026)의 이중분기(dual-branch) 딥러닝 프레임워크는 중국 창저우 단일 도시에서 R²=0.99라는 매우 높은 성능과 3주 앞선 경보 예측을 보고했지만, 단일 사례이고 비교 대상 모델·교차검증 결과를 확인하지 못해 일반화 여부는 판단 보류가 필요하다.
- **분류 체계 수준의 서베이**: Chen et al.(2024)은 모델 기반(SEIR/배출모델)과 데이터 기반(ARIMA류/회귀·GAM/RF·SVR/ANN·ANFIS)을 분류했을 뿐, 어느 쪽이 전반적으로 우수한지에 대한 정량적 결론은 제시하지 않는다.

**종합 경향**: (1) 예측 지평이 짧을수록(1~2주) ARIMA·GAM 등 **비교적 단순한 통계모형이 안정적으로 경쟁력을 유지**한다는 보고가 반복된다(Alhassan et al. 2025). (2) LSTM 등 신경망 계열은 표본이 어느 정도 확보되면(Ai et al.의 9개 지역사회·620건) 우수한 성능을 내지만, 표본이 매우 작은 단일·소수 사례(Li, X. et al.의 단일 도시)에서는 성능이 과장되었을 가능성을 배제하기 어렵다. (3) 앙상블(n-sub-epidemic)은 예측 지평이 길어질수록(3~4주) 유리해지는 경향이 있다. (4) Prophet과 단순선형회귀는 이 과제 계열에서 반복적으로 하위권으로 보고된다.

**KOWAS-EPI에 대한 시사점**: 독립 시계열이 17개 시·도 × 179주로 작고(README §5-6), t+2주(약 2주) 예측 지평이 문헌에서 "ARIMA·GAM 우세" 구간으로 보고되는 1~2주 구간과 정확히 겹친다. 따라서 처음부터 LSTM 등 복잡한 신경망에 의존하기보다, **ARIMA류·GAM·트리 기반 모형을 견고한 기준선으로 먼저 확보하고, 데이터가 누적되는 후기 평가 창에서만 신경망 계열을 보조적으로 시도**하는 전략이 문헌의 경향과 부합한다.

---

## 5. 참고문헌 (근거 URL, 20편 — DOI/기관 URL 전수 검증 완료)

1. Shah, S., Gwee, S.X.W., Ng, J., Lau, N., Koh, J.-E., Pang, J. (2021). *Science of the Total Environment*. Wastewater surveillance to infer COVID-19 transmission: A systematic review. https://doi.org/10.1016/j.scitotenv.2021.150060
2. Chen, C., Wang, Y., Kaur, G. et al. (2024). arXiv:2403.15291. Wastewater-based Epidemiology for COVID-19 Surveillance and Beyond: A Survey. https://doi.org/10.48550/arXiv.2403.15291
3. Choi, Y.-J., Kim, L.H., Jang, J. et al. (2025). *J Korean Med Sci*. National Wastewater Surveillance of SARS-CoV-2 Across Provinces and Regions in the Republic of Korea From January to August 2023. https://doi.org/10.3346/jkms.2025.40.e94
4. Kim, Y.-T. et al. (2024). *Scientific Reports* 14:24544. Development of a wastewater based infectious disease surveillance research system in South Korea. https://doi.org/10.1038/s41598-024-76614-4
5. Hill, D.T. et al. (2023). *Infectious Disease Modelling* 8(4):1138–1150. Wastewater surveillance provides 10-days forecasting of COVID-19 hospitalizations superior to cases and test positivity. https://doi.org/10.1016/j.idm.2023.10.004
6. Ai, Y., He, F., Lancaster, E., Lee, J. (2022). *PLOS ONE*. Application of machine learning for multi-community COVID-19 outbreak predictions with wastewater surveillance. https://doi.org/10.1371/journal.pone.0277154
7. Jeng, H.A., Singh, R., Diawara, N. et al. (2023). *Science of the Total Environment* 885. Application of wastewater-based surveillance and copula time-series model for COVID-19 forecasts. https://doi.org/10.1016/j.scitotenv.2023.163655
8. Karthikeyan, S. et al. (2021). *mSystems*. High-Throughput Wastewater SARS-CoV-2 Detection Enables Forecasting of Community Infection Dynamics in San Diego County. https://doi.org/10.1128/msystems.00045-21
9. Alhassan, F., Karami, H., Bleichrodt, A., Hyman, J.M., Fung, I.C.H., Luo, R., Chowell, G. (2025). arXiv:2512.01074. COVID-19 Forecasting from U.S. Wastewater Surveillance Data: A Retrospective Multi-Model Study (2022-2024). https://doi.org/10.48550/arXiv.2512.01074
10. Schenk, H., Rauch, W., Zulli, A., Boehm, A.B. (2024). *PLOS ONE*. SARS-CoV-2 surveillance in US wastewater: Leading indicators and data variability analysis in 2023–2024. https://doi.org/10.1371/journal.pone.0313927
11. Mustapha, M.M., Choi, L.E., Bergroth, T. et al. (2025). *Frontiers in Public Health*. Association between SARS-CoV-2 in wastewater and COVID-19 hospitalizations in three countries, 2022–2024. https://doi.org/10.3389/fpubh.2025.1679596
12. Li, X., Wu, C., Jiang, J. et al. (2026). *Journal of Water and Health*. A dual-branch deep learning framework for tiered early warning of COVID-19 utilizing wastewater data. https://doi.org/10.2166/wh.2026.150
13. Meadows, T., Coats, E.R., Narum, S., Top, E.M., Ridenhour, B.J., Stalder, T. (2024). *Water Research*. Epidemiological model can forecast COVID-19 outbreaks from wastewater-based surveillance in rural communities. https://doi.org/10.1016/j.watres.2024.122671
14. Zhao, L., Faust, R.A., David, R.E., Norton, J., Xagoraraki, I. (2024). *Journal of Environmental Engineering* 150(1). Tracking the Time Lag between SARS-CoV-2 Wastewater Concentrations and Three COVID-19 Clinical Metrics: A 21-Month Case Study in the Tricounty Detroit Area, Michigan. https://doi.org/10.1061/JOEEDU.EEENG-7509
15. Langeveld, J., Schilperoort, R., Heijnen, L. et al. (2021). medRxiv 2021.11.30.21266889. Normalisation of SARS-CoV-2 concentrations in wastewater: the use of flow, conductivity and CrAssphage. https://doi.org/10.1101/2021.11.30.21266889
16. Zhu, Y., Hill, D.T., Zhou, Y., Larsen, D.A. (2024). *Science of the Total Environment* 957. The effect of the modifiable areal unit problem (MAUP) on spatial aggregation of COVID-19 wastewater surveillance data. https://doi.org/10.1016/j.scitotenv.2024.177676
17. Chan, E.M.G., Burnor, E., Zulli, A., Lu, C., Yu, A.T., Boehm, A.B. (2026). *Discover Public Health* 23(1):1461. Spatial aggregation methods for interpreting wastewater concentrations at jurisdictional scales: Insights from two SARS-CoV-2 monitoring programs. https://doi.org/10.1186/s12982-026-02934-7
18. Cuadros, D., Chen, X., Tang, M. (2026). *Environments* 13(7):382. Toward Sub-Sewershed Spatio-Temporal Wastewater Surveillance: A Critical Review and a Candidate Multimodal Foundation-Model Framework. https://doi.org/10.3390/environments13070382
19. Maes-Prior, R., Dobson, B., Mijic, A. (2026). *Water Science & Technology*. Drivers of wastewater dynamics: a statistical analysis of England's large wastewater treatment works. https://doi.org/10.2166/wst.2026.295
20. CDC. Using the Wastewater Viral Activity Level (WVAL). National Wastewater Surveillance System (기관 공식 페이지, DOI 없음). https://www.cdc.gov/wastewater/about/wval.html
