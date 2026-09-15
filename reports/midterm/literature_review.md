# 문헌 리뷰 (중간보고서 제출용)

## 가정 및 전제

- 영어 키워드(wastewater-based epidemiology forecasting, SARS-CoV-2 wastewater surveillance lead time 등) 중심 WebSearch/WebFetch 조사, 2026-09 시점 기준. 원문을 직접 확인한 연구만 수치를 인용했고, 확인 못한 항목은 본문에서 배제했다.
- 모든 인용은 DOI(또는 검증된 안정 기관 URL)를 WebFetch로 직접 열어 제목·저자가 일치함을 재확인한 것만 남겼다 — 링크가 열리지 않거나 서지정보가 불일치한 항목은 제외했다.
- 상세 비교표·참고문헌 전체 목록·검색 방법론은 `docs/literature/review.md`에 있다. 이 문서는 그중 서술형 종합 요약(중간보고서 "문헌 리뷰" 섹션 초안)만 담는다.

---

## 문헌 리뷰

하수 기반 역학(wastewater-based epidemiology, WBE)은 감염자가 증상을 인지하고 검사를 받기 전부터 배출하는 바이러스 유전물질을 하수에서 검출함으로써, 임상 신고 체계보다 앞서 지역사회 감염 동향을 포착할 수 있다는 전제에서 출발한다. 이 전제는 팬데믹 초기부터 폭넓게 검증되어 왔으며, 763편 중 92편을 선별한 체계적 문헌고찰(Shah et al., 2021)은 34개국·26,197건 표본을 아우르는 연구들에서 하수 신호가 임상 확진보다 먼저 나타난 사례를 다수 보고했다고 정리한다. 다만 이런 초기 보고 중 "수개월 선행"류의 극단값은 대개 지역사회 첫 유행이 시작되기 전 저빈도 검사 체계의 사각지대를 하수가 메운 사례이지, 정상 가동 중인 감시체계에서 반복적으로 관찰되는 예측 리드타임은 아니다.

실제로 예측/시차를 직접 정량화한 개별 연구들의 수치는 훨씬 보수적으로 수렴한다. San Diego 다변량 ARIMA 연구(Karthikeyan et al., 2021)는 1~3주 지평의 예측에 하수 자료를 활용했고, Ohio 9개 지역사회를 LSTM·Prophet 등으로 비교한 연구(Ai et al., 2022)는 5일 시차를 넣었을 때 예측 오차가 개선됨을 보였다. Chesapeake 지역의 코플라 시계열 모형(Jeng et al., 2023)은 3~5일의 선행 추세 포착을, 56개 카운티 입원자 예측 GLMM(Hill et al., 2023)은 10일 지연에서 상관이 최고였음을 보고했다. 이를 종합하면 문헌에서 반복적으로 확인되는 선행 시차는 대체로 **며칠에서 최대 2주 내외**이며, arXiv 서베이(Chen et al., 2024)도 이를 "대체로 1~2주 선행"으로 요약한다. 즉 WBE의 조기경보 가치는 실재하지만 그 폭은 생각보다 좁고, 방법론(정규화 여부, 채취 빈도, 예측모형 종류)에 따라 크게 흔들린다는 것이 문헌의 공통된 함의다.

이 지점에서 이번 KOWAS-EPI README §6의 수치(하수·임상 로그 상관이 시차 0주와 +1주에서 동일하게 최댓값 r=0.919, 최근 52주 구간은 +1주에서 r=0.936으로 소폭 더 높음)를 문헌과 나란히 놓고 읽을 필요가 있다. 먼저 상관계수의 크기 자체는 문헌에 견주어 이례적으로 높다 — 개별 연구들의 상관은 대개 0.5~0.9대에 분포하는데(예: Kim et al. 2024의 한국 다병원체 연구는 병원체별로 ρ=−0.18~0.92로 매우 넓게 분산), r=0.919는 그 상한에 가깝다. 그러나 상관계수의 크기와 "선행 시차"는 서로 다른 개념이다. README 표(§6)에서 r이 최대가 되는 지점이 "시차 0주"와 "+1주"라는 사실은, 하수 신호가 임상 신고를 앞서는 것이 아니라 **거의 동시에 움직이거나, 오히려 임상 지표가 하수보다 최대 1주 정도 먼저 나타날 수도 있음**을 시사한다(표의 k는 "하수 t주 대 임상 t+k주" 상관이므로 k>0에서 r이 더 크다는 것은 임상이 하수보다 먼저인 조합에서 더 잘 맞는다는 뜻이다). 이는 문헌에서 흔히 보고되는 "하수가 임상보다 며칠~2주 선행"이라는 배출·하수관 이동시간(shedding/hydraulic) 기반의 기대와는 방향이 다르다.

공교롭게도 이 결과는 고립된 사례가 아니다. KOWAS를 직접 운영하는 기관의 전국 단위 분석(Choi et al., 2025)도 우측정렬 이동평균 기준 **교차상관 최고점이 시차 0(동시성)**에서 나타난다고 보고해, README의 패턴과 방향이 일치한다. 반면 같은 한국 내에서도 용인시 6개 처리장 단위 연구(Kim et al., 2024)는 SARS-CoV-2에 대해 상관이 사실상 없었다(ρ=−0.18)고 보고해, 공간 집계 단위(전국·시·도 대 개별 처리장)에 따라 결과가 크게 달라질 수 있음을 보여준다. 종합하면, 이 데이터셋의 높은 상관계수를 "강한 선행 신호"로 과잉 해석하지 않는 것이 중요하다. r=0.919는 하수 지표가 임상 유행과 밀접히 동조한다는 근거이지, 그 자체로 몇 주 앞선 예측력을 보장하는 근거는 아니다. t+2주 예측이라는 이 과제의 목표 지평은 문헌이 보고하는 전형적 선행 폭(며칠~2주)의 상단 근처에 있어, 순수한 통계적 지연만으로는 쉽게 달성되기 어려운 도전적인 설정이라고 봐야 한다.

방법론적으로도 문헌은 이번 과제의 세 가지 실무적 함의를 뒷받침한다. 첫째, 정규화(normalization)가 조기경보 신뢰도를 좌우한다. 유량·전기전도도·crAssphage로 희석을 보정한 연구군은 그렇지 않은 연구보다 임상자료와의 상관이 더 안정적이라고 보고하며(정규화 방법론 그룹, medRxiv 2021), Hill et al.(2023)도 유량 자료 부재를 핵심 한계로 꼽는다. 이는 README §5-4의 "시·도 집계에서는 강수 희석 효과가 보이지 않는다"는 관찰과 맞닿아 있다 — 개별 처리장·유역 단위의 희석 신호가 여러 유역이 섞인 시·도 집계에서 상쇄되었을 가능성을 문헌이 뒷받침한다. 둘째, 표본 규모와 과적합 문제다. 리뷰한 연구 대부분은 한 자릿수~두 자릿수의 지역을 다루며, Ai et al.(2022)은 소규모 데이터셋과 과적합 위험을 명시적 한계로 적었다 — KOWAS-EPI 패널(17개 시·도×179주)도 README §5-6의 "대규모 딥러닝·GNN이 반드시 유리하지 않다"는 경고와 겹친다. 셋째, 알고리즘도 예측 지평에 따라 갈린다 — 다중모델 비교(Alhassan et al., 2025)는 1~2주 지평에서 ARIMA·GAM이 Prophet·단순회귀보다 우수했다고 보고해, t+2주 과제엔 단순 통계모형을 먼저 견고한 기준으로 두는 전략이 문헌과 부합한다.

결론적으로 이번 리뷰가 시사하는 실천적 방향은 세 가지다. (1) 목표 지평 t+2주는 문헌상 전형적 선행 폭의 상단에 위치하므로, 순수 상관·리드타임에만 의존하기보다 계절성·추세 등 시계열 자체의 예측가능한 구조를 함께 활용해야 한다. (2) README의 r=0.919는 방향(동시~임상 소폭 선행)까지 함께 읽어야 하며, "하수가 임상을 앞선다"는 문헌의 일반적 기대를 이 데이터에 그대로 투영하면 안 된다. (3) 정규화·집계 단위 문제와 소규모 표본에 따른 과적합 위험은 모델 설계 단계에서부터 반영해야 할 구조적 제약이다.

---

## 참고문헌 (핵심 9편, DOI 검증 완료 — 전체 20편 목록은 `docs/literature/review.md` 참고)

1. Shah, S., Gwee, S.X.W., Ng, J., Lau, N., Koh, J.-E., Pang, J. (2021). *Science of the Total Environment*. Wastewater surveillance to infer COVID-19 transmission: A systematic review. https://doi.org/10.1016/j.scitotenv.2021.150060
2. Chen, C. et al. (2024). arXiv:2403.15291. Wastewater-based Epidemiology for COVID-19 Surveillance and Beyond: A Survey. https://doi.org/10.48550/arXiv.2403.15291
3. Choi, Y.-J. et al. (2025). *Journal of Korean Medical Science*. National Wastewater Surveillance of SARS-CoV-2 Across Provinces and Regions in the Republic of Korea. https://doi.org/10.3346/jkms.2025.40.e94
4. Kim, Y.-T. et al. (2024). *Scientific Reports* 14:24544. Development of a wastewater based infectious disease surveillance research system in South Korea. https://doi.org/10.1038/s41598-024-76614-4
5. Hill, D.T. et al. (2023). *Infectious Disease Modelling* 8(4):1138–1150. Wastewater surveillance provides 10-days forecasting of COVID-19 hospitalizations superior to cases and test positivity. https://doi.org/10.1016/j.idm.2023.10.004
6. Ai, Y., He, F., Lancaster, E., Lee, J. (2022). *PLOS ONE*. Application of machine learning for multi-community COVID-19 outbreak predictions with wastewater surveillance. https://doi.org/10.1371/journal.pone.0277154
7. Jeng, H.A. et al. (2023). *Science of the Total Environment* 885. Application of wastewater-based surveillance and copula time-series model for COVID-19 forecasts. https://doi.org/10.1016/j.scitotenv.2023.163655
8. Karthikeyan, S. et al. (2021). *mSystems*. High-Throughput Wastewater SARS-CoV-2 Detection Enables Forecasting of Community Infection Dynamics in San Diego County. https://doi.org/10.1128/msystems.00045-21
9. Alhassan, F., Karami, H., Bleichrodt, A., Hyman, J.M., Fung, I.C.H., Luo, R., Chowell, G. (2025). arXiv:2512.01074. COVID-19 Forecasting from U.S. Wastewater Surveillance Data: A Retrospective Multi-Model Study (2022-2024). https://doi.org/10.48550/arXiv.2512.01074
