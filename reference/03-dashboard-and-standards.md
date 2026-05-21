# 03 — 대시보드·환경 기준·운영 사례

작성: 2026-05-21
대상 프로젝트: 당곡고 기후행동365 (16개 교실 환경 모니터링)
조사 범위: ① 대시보드 비교 ② 한국 학교 환경 기준값 ③ 학생 활동 운영 사례

---

## 요약 (TL;DR)

- **대시보드 추천: Streamlit(메인) + Grafana(보조) 하이브리드.**
  - 메인 화면(학생·교사·학부모용)은 **Streamlit**: 정보교사 친숙도 + Python(Pandas) 분석팀이 직접 수정 가능 + 빠른 프로토타이핑.
  - 24/7 상시 모니터링·알림은 **Grafana + InfluxDB**: 시계열 표준, 임계값 알림 내장. 분석팀이 InfluxDB Flux/SQL을 일부 익히는 교육 효과도 있음.
  - 데이터는 **InfluxDB 단일 저장소**에 모으고 두 대시보드가 같은 소스를 본다.
- **핵심 기준값(학교보건법 시행규칙)**:
  - 온도 18~28℃ (난방기 18~20℃, 냉방기 26~28℃)
  - 상대습도 30~80%
  - 조도 책상면·칠판면 300 lux 이상, 조도비 3:1 이하
  - CO₂ 1,000 ppm 이하 (기계환기 시 1,500 ppm)
  - PM10 75 ㎍/㎥, PM2.5 35 ㎍/㎥, 폼알데하이드 80 ㎍/㎥, TVOC 400 ㎍/㎥(신·증축 시)
- **운영 사례 참고**:
  - **서울학생기후행동365** (서울시교육청 사업) — 학교별 운영진·캠페인 체계.
  - **탄소중립 중점학교**: 연무여중(녹색성장 환경 동아리 + AI 융합), 목포혜인여고(CO₂ 저감장치 개발) 등.
  - **국가환경교육 통합플랫폼(keep.go.kr)** 우수 환경 동아리 공모전 — 산출물 양식 참고.

---

## C-1. 대시보드 비교

### Streamlit

**장점**
- Python 한 파일로 UI·데이터 처리·차트 모두 가능. 정보교사·분석팀(Pandas 사용자)이 그대로 확장 가능.
- 코드 수정 → 즉시 새로고침. 학습 곡선이 가장 낮음.
- Plotly/Altair/matplotlib 등 Python 차트 라이브러리 모두 사용 가능.
- "16개 교실 카드 그리드" 같은 커스텀 레이아웃이 30~50줄로 구현됨.

**단점·한계**
- **다중 사용자 동시 접속에 약함.** Tornado WebSocket 기반이라 이론상은 가능하지만, 각 세션이 별도 스레드 + 메모리를 잡으므로 수십 명을 넘기면 서버 사양에 크게 의존. 전교생(800명+) 동시 접속은 권장하지 않음.
- 실시간성은 `st.autorefresh`(예: 30초) 또는 `st_autorefresh` 컴포넌트로 폴링하는 방식. 진정한 푸시(WebSocket subscribe)는 아님.
- 알림(임계값 초과 → 메신저/이메일)은 직접 코드 작성 필요. Grafana만큼 깔끔한 알림 룰 UI는 없음.
- 모바일 대응은 가능하지만 사이드바·차트 간격이 좁아져 그리드 레이아웃 튜닝 필요.

**16노드 실시간(1분 갱신) 표시 가능 여부**
- 가능. 1분 폴링이면 부하 매우 낮음. InfluxDB나 CSV에서 16개 교실 최신값을 한번에 읽어 4×4 카드로 표시하는 것이 표준 패턴.
- 참고 사례: [Building a real-time live dashboard with Streamlit (Streamlit blog)](https://blog.streamlit.io/how-to-build-a-real-time-live-dashboard-with-streamlit), [Anedya IoT Streamlit dashboard (GitHub)](https://github.com/anedyaio/anedya-streamlit-dashboard-example).

**학생 친화도: ★★★★★ (Pandas 분석팀이 그대로 수정 가능)**

**추천 시나리오**
- 학교 내부용 모니터링 화면(교무실 모니터, 교사용 노트북, 동아리실 TV) 한두 화면.
- 분석팀이 만드는 월간 리포트 페이지(주별 평균, 환기 권고 횟수, CO₂ 패턴 시각화).

---

### Grafana

**장점**
- 시계열 데이터의 사실상 표준. 패널 수십 개를 드래그로 배치, 다중 노드 멀티라인 차트가 클릭 몇 번.
- **임계값 초과 알림 내장**: CO₂ > 1000ppm이 N분간 지속 → 슬랙/이메일/웹훅 자동 발송.
- InfluxDB와 가장 호환성 높음(Flux/InfluxQL 쿼리 빌더 GUI).
- 모바일 반응형 대시보드 기본 제공.
- 동시 접속 안정성이 Streamlit보다 훨씬 좋음(읽기 전용 대시보드는 수백 명 동시 접속도 무난).

**단점·한계**
- **학생이 직접 만들기는 어렵다.** Flux 쿼리, 패널 옵션, 변수(Template variables) 등 학습할 양이 적지 않음.
- Python 분석 코드를 끼워 넣기 어렵다(고급 통계·ML은 별도 백엔드 필요).
- "16개 교실 카드 4×4 그리드" 같은 학교 친화적 UI는 가능하지만 손이 좀 감(Stat 패널 반복 + repeat).

**16노드 실시간 표시 가능 여부**
- 매우 적합. Grafana의 `repeat` 옵션으로 교실 1개 패널을 16개로 자동 복제. 1분 간격은 무난, 10초 갱신도 가능.
- 참고 사례: [Air-quality-monitor (PM2.5/PM10/CO2 → MQTT → InfluxDB → Grafana, GitHub)](https://github.com/jlofw/air-quality-monitor), [InfluxDB Air Quality Monitor template](https://www.influxdata.com/influxdb-templates/air-quality-monitor/).

**학생 친화도: ★★☆☆☆ (보기만 한다면 ★★★★, 만들려면 ★★)**

**추천 시나리오**
- 24/7 상시 모니터링 + 임계값 자동 알림.
- 운영팀(시설·기획 학생)이 "환기 알람이 오늘 몇 번 울렸나"를 보고 출동.
- 전교생·학부모 공개 보드(읽기 전용 URL).

---

### 자체 웹앱 (React/Vue + 차트 라이브러리)

**장점**
- 자유도 무제한. 학교 캐릭터·디자인·인터랙션을 자유롭게.
- 다중 사용자 동시 접속 최강(정적 호스팅 + API 분리 시 거의 무한).

**단점**
- **학생 진입장벽 매우 높음.** React/Next.js + 상태관리 + 차트 라이브러리(Plotly·Recharts·ECharts) + 백엔드 API + 배포 파이프라인. 정보교사가 풀스택을 책임지는 모델이 됨.
- 1분 갱신 + 알림 + 인증 + 권한관리까지 전부 직접 구현.
- 기능 한 줄 추가에 PR·빌드·배포가 따라옴 → 학생이 일상적으로 손대기 어렵다.

**16노드 실시간 표시 가능 여부**
- 가능하지만 오버킬. WebSocket(Socket.IO 등) + Plotly/ECharts 조합이 표준. Next.js + Plotly 사례 다수.

**학생 친화도: ★☆☆☆☆**

**추천 시나리오**
- 외부 공개용 "당곡고 기후 대시보드 닷컴" 같은 1년 후 결과물 단계.
- 1차 운영(올해) 단계에서는 비추천.

---

### Node-RED 대시보드 (보너스)

**장점**
- **노코드 흐름 기반**. 센서 입력 → 함수 노드 → 대시보드 게이지/차트로 드래그로 연결.
- MQTT 브로커 연동이 기본. 16개 교실 발행자(publisher)를 받아 그래프로 뿌리는 흐름이 10분이면 완성.
- 학생이 "센서 → 처리 → 알림"의 데이터 흐름을 시각적으로 이해하는 교육 효과가 큼.
- IoT 교육용 노드도 존재: [node-red-contrib-iot4school](https://flows.nodered.org/node/node-red-contrib-iot4school).

**단점**
- 다중 사용자 동시 접속·인증은 약함(기본은 단일 대시보드 가정).
- UI 커스터마이징 자유도가 낮음(예쁜 카드 그리드는 Streamlit/Grafana보다 약함).
- Pandas 같은 고급 분석은 어색함(별도 함수 노드 안에서 JS로).

**16노드 실시간 표시 가능 여부**
- 적합. MQTT subscribe 노드 → 게이지/차트 노드. 1분 갱신은 기본, 초 단위도 가능.

**학생 친화도: ★★★★☆ (만드는 재미 + 흐름 이해)**

**추천 시나리오**
- "조립팀이 자기 노드 데이터가 어떻게 들어오는지 눈으로 확인하는 디버깅 보드."
- 컴퓨터실 수업에서 "데이터 파이프라인이 뭔지" 한 시간에 보여주기.

---

### Apache Superset (보너스)

**장점**
- 대시보드 + SQL Lab(SQL 에디터)이 결합. 분석팀이 **SQL을 익히는 교육 효과**가 가장 큼.
- 차트 종류 풍부(48종 이상), 드래그&드롭으로 차트 생성.
- 사용자/역할/권한 관리, 대시보드 임베드, 알림(Alerts & Reports) 등 BI 도구 기능.

**단점**
- **설치·운영이 무겁다.** Docker Compose 4~5개 컨테이너(Superset, Redis, Postgres, Celery worker, Celery beat). 학교 서버 한 대에서는 가능하나 정보교사가 운영해야 함.
- 시계열 실시간 모니터링용이라기보단 분석/BI 도구. 1분 자동갱신은 가능하지만 본질은 "정해진 시점의 보고서".
- 학생이 직접 만들 SQL이 점점 복잡해지면 "분석팀 수업 자체"가 됨(나쁘다는 뜻은 아님).
- 참고: [OpenSchoolMaps Introduction to Apache Superset](https://openschoolmaps.ch/lehrmittel/en_introduction_to_apache_superset/introduction_to_apache_superset.html).

**16노드 실시간 표시 가능 여부**
- 가능하지만 본 용도 아님. 월간/주간 리포트 보드로는 매우 강력.

**학생 친화도: ★★★☆☆ (SQL 학습 의지가 있는 분석팀에게)**

**추천 시나리오**
- "분석팀 SQL 트레이닝 + 월간 리포트 자동 생성" 별도 트랙.
- 1차 운영(올해) 메인 보드로는 비추천. 2년차 분석팀 전문화 단계에서 고려.

---

### 종합 비교표

| 기준 | Streamlit | Grafana | 자체 웹앱 | Node-RED | Superset |
|---|---|---|---|---|---|
| 실시간성(1분) | ◯ (폴링) | ◎ (네이티브) | ◎ (WS) | ◎ (MQTT) | △ (폴링) |
| 학생 수정 용이성 | ◎ Python 한 파일 | △ JSON·Flux 학습 | × 풀스택 | ◎ 노코드 흐름 | ○ SQL 학습 |
| 동시 접속(전교생) | △ 수십명 | ◎ 수백명+ | ◎ 무한 | △ 수십명 | ◯ 수십~수백 |
| 알림 기능 | × 직접 코드 | ◎ 내장 | × 직접 코드 | ○ 노드 조합 | ○ 내장 |
| 모바일 대응 | ○ 튜닝 필요 | ◎ 반응형 | ◎ 직접 설계 | △ 좁음 | ◯ 반응형 |
| 초기 구축 시간 | 1~2일 | 2~3일(+ Influx) | 1~2주+ | 0.5~1일 | 2~3일(+운영) |
| 학생 교육 효과 | Python·Pandas | 시계열·알림 | 풀스택(과부하) | 데이터 파이프라인 | SQL·BI |
| 추천 역할 | 메인 화면 | 상시감시·알림 | (1년차 비추) | 디버깅·교육 | 분석팀 트랙 |

(◎ 매우 좋음 / ○ 좋음 / △ 가능하나 한계 / × 부적합)

**최종 권장 아키텍처**:
```
센서노드 16개 ──MQTT──> Mosquitto ──> Telegraf ──> InfluxDB
                                                    │
                              ┌─────────────────────┼─────────────────────┐
                              ▼                     ▼                     ▼
                         Streamlit              Grafana              (선택) Superset
                       (메인·분석팀)         (상시감시·알림)         (월간리포트·SQL)
```

---

## C-2. 한국 학교 환경 기준값

### 학교보건법 시행규칙 — 별표 2 (환기·채광·조명·온습도의 조절기준)

근거: **학교보건법 시행규칙 제3조제1항** 및 **별표 2**.
출처(법제처): [학교보건법 시행규칙(law.go.kr)](https://www.law.go.kr/%EB%B2%95%EB%A0%B9/%ED%95%99%EA%B5%90%EB%B3%B4%EA%B1%B4%EB%B2%95%20%EC%8B%9C%ED%96%89%EA%B7%9C%EC%B9%99), 정리: [서울특별시교육청 보건안전진흥원](https://bogun.sen.go.kr/fus/MI000000000000000054/html/cont0010v.do).

| 항목 | 기준 | 비고 |
|---|---|---|
| 실내온도 | **18 ~ 28 ℃** | 난방기 18~20℃, 냉방기 26~28℃ |
| 비교습도 | **30 ~ 80 %** | |
| 환기량 | **1인당 21.6 ㎥/h 이상** | |
| 자연채광(주광율) | **2% 이상**(최소), 5% 확보 권장 | 최대·최소 조도비 10:1 이하 |
| 인공조명(책상면) | **300 lux 이상** | 조도비 3:1 이하 |
| 인공조명(칠판면) | **300 lux 이상** | 책상면과 동일 |
| 소음 | **55 dB(A) 이하** | |

### 학교보건법 시행규칙 — 별표 4의2 (공기 질 등의 유지·관리기준)

근거: **학교보건법 시행규칙 제3조제1항제3호의2** 및 **별표 4의2**.
출처: 위 동일 + [한국공기청정협회 — 실내공기질 관리기준](https://kaca.or.kr/kaca_information/indoor_environment/content/?pagen=1348).

| 오염물질 | 기준값 | 적용 시설 |
|---|---|---|
| **CO₂ (이산화탄소)** | **1,000 ppm 이하** | 교사·급식시설 |
| **CO₂ (기계환기 시)** | **1,500 ppm 이하** | 자연환기 불가 시설 |
| **PM10** | **75 ㎍/㎥ 이하** | 교사·급식시설 |
| **PM2.5** | **35 ㎍/㎥ 이하** | 교사·급식시설 |
| **폼알데하이드 (HCHO)** | **80 ㎍/㎥ 이하** | 교사·급식시설 |
| **TVOC (총휘발성유기화합물)** | **400 ㎍/㎥ 이하** | 신·증축 시설 |
| 일산화탄소 (CO) | 10 ppm 이하 | 직접연소 난방교실 |
| 이산화질소 (NO₂) | 0.05 ppm 이하 | 직접연소 난방교실 |
| 라돈 | 148 Bq/㎥ 이하 | 1층·지하 교사 |
| 총부유세균 | 800 CFU/㎥ 이하 | 교사·보건실 |
| 낙하세균 | 10 CFU/실 이하 | 보건실·급식시설 |

**PM1.0과 TVOC 상시 측정값**은 학교보건법에 직접 명문화된 기준이 **없음**. (PM1.0은 PM2.5에 포함되어 관리, TVOC는 신·증축 시설에 대한 400 ㎍/㎥ 기준만 존재.)

### 실내공기질 관리법 적용 여부

- 학교는 **「실내공기질 관리법」의 다중이용시설에 포함되지 않음** (어린이집·의료기관·노인요양시설 등은 포함).
- 학교는 **「학교보건법」 단독 적용**. 다만 학교 기준값은 실내공기질 관리법의 "민감군 시설(어린이집·의료기관 등)" 기준과 거의 동일하거나 더 엄격함.
- 근거: [찾기쉬운 생활법령정보 — 학교 공기질 관리](https://easylaw.go.kr/CSP/CnpClsMain.laf?popMenu=ov&csmSeq=1394&ccfNo=4&cciNo=3&cnpClsNo=2).

### 알림 임계값 설계 제안 (3단계 + 색)

> **원칙**: 법정 기준은 "위험"으로 매핑하고, 그 아래에 "주의/경고" 두 단계를 둔다. 학교 실측 데이터로 분석팀이 다음 분기에 임계값을 조정한다(데이터 기반 거버넌스).

| 항목 | 정상 🟢 | 주의 🟡 | 경고 🟠 | 위험 🔴 | 비고 |
|---|---|---|---|---|---|
| 온도 (℃) | 19~27 | 18~19 또는 27~28 | 17~18 또는 28~30 | <17 또는 ≥30 | 법정 18~28 |
| 습도 (%) | 40~70 | 30~40 또는 70~80 | 25~30 또는 80~85 | <25 또는 ≥85 | 법정 30~80 |
| 조도 책상면 (lux) | ≥500 | 300~500 | 200~300 | <200 | 법정 ≥300 |
| **CO₂ (ppm)** | <800 | 800~1000 | 1000~1500 | ≥1500 | 법정 1000 (기계환기 1500) |
| PM10 (㎍/㎥) | <50 | 50~75 | 75~150 | ≥150 | 법정 75 |
| PM2.5 (㎍/㎥) | <25 | 25~35 | 35~75 | ≥75 | 법정 35 |
| TVOC (㎍/㎥) | <250 | 250~400 | 400~1000 | ≥1000 | 신증축 400 |

**색 매핑(대시보드 LED·UI 공통)**:
- 🟢 정상: 표시만, 알림 X
- 🟡 주의: 카드 노란색, 권고 메시지("창 살짝 열기")
- 🟠 경고: 카드 주황색, 운영팀 메신저 알림, 권고 메시지("환기 5분")
- 🔴 위험: 카드 빨간색 + 깜빡임, 운영팀+담임 알림, 즉시 환기 권고

**행동 트리거 예시**:
- CO₂ 🟠(1000~1500ppm) 10분 지속 → "이 교실 환기 5분" 메신저 자동발송.
- PM2.5 🔴(≥75) → "오늘 창문 닫기 + 공기청정기 ON" 전교 공지.
- 조도 🟡(200~300lux) 흐린 날 → 동·서편 교실 조명 단계 조정 권고.

---

## C-3. 학생 운영 사례

### 기후행동365 — 서울학생기후행동 365

- **운영주체**: 서울특별시교육청. 학생·교사·학부모/시민 세 트랙으로 구성.
- **학생 트랙 구조**: 신청 학생 = 자동 학교 위원, 학교별 대표 2~3명 선정 → 운영진 위촉. 초·중·고 각 5명, 총 15명의 운영위원회.
- **활동 유형**: 365일 실천, 친구들과 프로젝트, 캠페인·워크숍·인증활동, 포럼.
- **2022 서울학생기후행동365 포럼** — 미래세대 의견 청취·기후정의·기업 책임 등이 주제.
- 출처:
  - [서울교육청 기후위기 대응 행동365 발대식](https://enews.sen.go.kr/news/view.do?bbsSn=172804&step1=3&step2=1)
  - [서울학생기후행동365 카카오톡 채널](https://pf.kakao.com/_dvxexcb/100184831)
  - [2022 서울학생기후행동 365 포럼](https://enews.sen.go.kr/news/view.do?bbsSn=177481&step1=3&step2=1)

### 탄소중립 중점학교 / 환경 동아리 우수사례

- **연무여자중학교**: '미래생태교육' 비전. 녹색성장 환경 동아리 + 탄소중립 교사 동아리. ESD 교과중점 + AI 융합 교육과정 2개 체계, 6개 영역·21개 하위 프로그램.
- **목포혜인여자고등학교**: 계란껍질을 이용한 CO₂ 저감장치 개발, 조력발전 탐구, 기후위기 골든벨, 환경 UCC 대회, 월출산 플로깅·기후 생물 지표종 탐사.
- **국가환경교육 통합플랫폼(keep.go.kr)** — 탄소중립 실천학교 + 우수 환경동아리 공모전.
- 출처:
  - [탄소중립 중점학교 현황 (학교환경교육정보센터)](https://www.seeic.kr/tanso/school_list.do)
  - [국가환경교육 통합플랫폼 탄소중립 실천학교](https://www.keep.go.kr/front/seeic/tanso/school_list.html)
  - [교육부 행복한 교육 — 학교 기후·환경교육 특별기획](https://happyedu.moe.go.kr/happy/bbs/selectHappyArticle.do?bbsId=BBSMSTR_000000000191&nttId=10363)
  - [2022 경기 탄소중립실천 우수사례집(PDF)](https://www.goe.go.kr/resource/old/BBSMSTR_000000030137/BBS_202411050307439770.pdf)
  - [2025 우수 환경 동아리 공모전 (keep.go.kr)](https://www.keep.go.kr/front/cntst/cntstDetailForm.html?cntstid=13)

### 학생 IoT 환경 모니터링 국내 사례 (참고)

- 학교실내공기질 지수(IAQI-S) 개발 — 전국 46개 학교 123개 학급(2017~2020) 데이터로 PM10·PM2.5·CO₂ 기반 어린이용 공기질 지수 산출. ([KCI 논문](https://journal.kci.go.kr/kseia/archive/articlePdf?artiId=ART002789241))
- [학교 미세먼지 빅데이터 사례 분석 — KIIT Conference (DBpia)](https://www.dbpia.co.kr/journal/articleDetail?nodeId=NODE10664586)
- [경기도교육청 학교 공기질 측정·관리 업무 매뉴얼(PDF)](https://www.goe.go.kr/resource/old/BBSMSTR_000000030132/BBS_202206220914023430.pdf) — 학교 측정·관리 절차의 표준 워크플로(분석팀 보고서 양식 참고용).
- 학교 차원 CO₂ 모니터링 가이드: [IQAir — CO2 학교 모니터링](https://www.iqair.com/ko/newsroom/air-pollution-and-co2-monitoring-in-schools).

### 분석팀 교육자료 참고 (Pandas·시각화)

- [Velog — 미세먼지 데이터 분석(분석편)](https://velog.io/@godeok24/%EB%8D%B0%EC%9D%B4%ED%84%B0%EB%B6%84%EC%84%9D-%ED%94%84%EB%A1%9C%EC%A0%9D%ED%8A%B8%EB%AF%B8%EC%84%B8%EB%A8%BC%EC%A7%80-%EB%B6%84%EC%84%9D%ED%8E%B8)
- [Velog — 미세먼지 발표편(시각화·결론 도출 양식)](https://velog.io/@godeok24/%EB%8D%B0%EC%9D%B4%ED%84%B0%EB%B6%84%EC%84%9D%EB%AF%B8%EC%84%B8%EB%A8%BC%EC%A7%80-%EB%B0%9C%ED%91%9C%ED%8E%B8-65cdwmdi)
- [기상청 KMA — Python을 활용한 분석 교육자료](https://bd.kma.go.kr/kma2020/dta/edu/KBP57200_Python.do)
- [에어코리아 PM2.5 대기환경기준 안내](https://www.airkorea.or.kr/web/board/1/387/?pMENU_NO=143) — 분석 보고서의 비교 기준선용.

활용 패턴:
1. **데이터 수집** — InfluxDB → `influxdb-client` 또는 CSV export → `pandas.DataFrame`.
2. **시간 인덱싱** — `df.set_index('time').resample('1H').mean()` 등 시계열 리샘플링.
3. **시각화** — Plotly(인터랙티브) 또는 matplotlib(보고서 PDF). 지도화는 folium(교실 배치도에 색 매핑).
4. **상관 분석** — CO₂ vs 인원·시간대·요일, PM vs 외부 미세먼지(에어코리아) 비교.

### 월간 리포트 템플릿(예시 골격)

```
당곡고 환경 모니터링 월간 리포트 — YYYY년 MM월

1. 한 달 요약
   - 16개 교실 평균/중앙값(온·습·CO₂·PM2.5)
   - 법정 기준 초과 횟수 (항목·교실별 표)
2. 이번 달 하이라이트
   - 가장 환기 부족했던 교실 Top 3
   - 가장 미세먼지 영향 컸던 날 (외부 미세먼지와 함께)
3. 패턴
   - 요일·시간대별 CO₂ 곡선 (히트맵)
   - 1·2·3교시 vs 4·5·6교시 비교
4. 권고
   - 다음 달 환기 캠페인 대상 교실
   - 공기청정기 우선배치 제안
5. 운영
   - 노드 가동률 (다운타임 분석)
   - 다음 달 조립팀 점검 대상
```

### 캠페인 사례·아이디어

- **데이터 기반 환기 캠페인**: 매시 50분 "환기타임" 자동 알림 + 월간 환기 성적표(교실별 CO₂ 평균 비교).
- **데이터 기반 소등 캠페인**: 조도 충분한 시간대(주광율 ≥2%) 자동 감지 → 점심시간 소등 권고.
- **공기 알림 봉사단**: PM 🔴 시점에 학교 메신저로 전교 공지를 학생이 직접 운영.
- **외부 비교 캠페인**: 에어코리아 인근 측정소 값과 교실값을 비교해 "오늘은 밖이 더 나쁨 → 창 닫기" 같은 데이터 기반 메시지.

---

## 미해결 / 사용자 확인 필요

- [ ] **법령 원문 PDF 확보**: 법제처 law.go.kr에서 학교보건법 시행규칙 별표 2·별표 4의2 PDF 다운로드. 본 문서의 수치는 서울시교육청 보건안전진흥원·한국공기청정협회 정리표 기반(2024년 개정 반영). 2026년 5월 현재 최신 개정 여부 재확인 권장.
- [ ] **조도 칠판면 별도 기준**: 별표 2 본문에서 "책상면·칠판면 300 lux 이상, 조도비 3:1 이하"로 통합 표기되어 있음. 더 세분화된 칠판면 단독 기준(예: 500lux)이 있는지 원문 재확인 필요.
- [ ] **PM1.0 학교 기준**: 학교보건법·실내공기질 관리법에 **명문화된 PM1.0 기준 없음** — 자체 임계값을 분석팀이 데이터로 제안하는 것으로 처리할지 결정 필요.
- [ ] **TVOC 상시 측정 기준**: 신·증축 시설(400 ㎍/㎥) 외에 상시 운영 학교에 적용되는 명문 기준 없음 — 운영 시 자체 임계값(상기 표 250/400/1000) 사용 여부 결정 필요.
- [ ] **학부모 접근 권한**: 대시보드를 학부모에게 공개할지(읽기 전용 Grafana 링크 vs Streamlit), 개인정보·교실 식별 정보 익명화 정책 결정 필요.
- [ ] **알림 채널**: 학교 메신저(클래스팅·하이클래스·카톡·텔레그램) 중 운영팀 채널 선정. 슬랙 웹훅 호환성 확인.
- [ ] **2022 경기 탄소중립실천 우수사례집 PDF**: 본 조사에서 PDF 본문 추출 실패. 16개 교실급 IoT 모니터링 사례가 포함되어 있는지 사람 눈으로 재확인 필요.

---

## 출처

### 법령·공식 자료
- [학교보건법 시행규칙 (국가법령정보센터)](https://www.law.go.kr/%EB%B2%95%EB%A0%B9/%ED%95%99%EA%B5%90%EB%B3%B4%EA%B1%B4%EB%B2%95%20%EC%8B%9C%ED%96%89%EA%B7%9C%EC%B9%99)
- [학교보건법 시행규칙 (위키문헌)](https://ko.wikisource.org/wiki/%ED%95%99%EA%B5%90%EB%B3%B4%EA%B1%B4%EB%B2%95_%EC%8B%9C%ED%96%89%EA%B7%9C%EC%B9%99)
- [서울특별시교육청 보건안전진흥원 — 학교 환경위생 관리기준](https://bogun.sen.go.kr/fus/MI000000000000000054/html/cont0010v.do)
- [한국공기청정협회 — 실내공기질 관리기준](https://kaca.or.kr/kaca_information/indoor_environment/content/?pagen=1348)
- [찾기쉬운 생활법령정보 — 학교 공기질 관리](https://easylaw.go.kr/CSP/CnpClsMain.laf?popMenu=ov&csmSeq=1394&ccfNo=4&cciNo=3&cnpClsNo=2)
- [경기도교육청 학교 공기질 측정·관리 업무 매뉴얼 (PDF)](https://www.goe.go.kr/resource/old/BBSMSTR_000000030132/BBS_202206220914023430.pdf)
- [실내공기질 관리법 시행규칙 별표 2 — 실내공기질 유지기준 (law.go.kr)](https://www.law.go.kr/lsBylInfoPLinkR.do?lsiSeq=250165&lsNm=%EC%8B%A4%EB%82%B4%EA%B3%B5%EA%B8%B0%EC%A7%88+%EA%B4%80%EB%A6%AC%EB%B2%95+%EC%8B%9C%ED%96%89%EA%B7%9C%EC%B9%99&bylNo=0002&bylBrNo=00&bylCls=BE&bylEfYd=20230417&bylEfYdYn=Y)
- [에어코리아 — PM2.5 대기환경기준 개정 안내](https://www.airkorea.or.kr/web/board/1/387/?pMENU_NO=143)

### 대시보드 비교
- [Streamlit — How to build a real-time live dashboard](https://blog.streamlit.io/how-to-build-a-real-time-live-dashboard-with-streamlit)
- [Streamlit Docs — Architecture](https://docs.streamlit.io/develop/concepts/architecture/architecture)
- [Streamlit Forum — Concurrent users](https://discuss.streamlit.io/t/maximum-number-of-concurrent-users-for-streamlit-app/22438)
- [Streamlit IoT dashboard example (GitHub)](https://github.com/anedyaio/anedya-streamlit-dashboard-example)
- [Air-quality-monitor PM2.5/PM10/CO2 → MQTT → InfluxDB → Grafana (GitHub)](https://github.com/jlofw/air-quality-monitor)
- [InfluxDB Air Quality Monitor template](https://www.influxdata.com/influxdb-templates/air-quality-monitor/)
- [Grafana PM2.5 dashboard](https://grafana.com/grafana/dashboards/13603-pm2-5/)
- [Streamlit vs Grafana 비교 (Fastero)](https://fastero.com/blog/streamlit-vs-grafana-when-to-use-each)
- [node-red-contrib-iot4school](https://flows.nodered.org/node/node-red-contrib-iot4school)
- [Node-RED IoT Dashboard Tutorial (ThinkRobotics)](https://thinkrobotics.com/blogs/learn/node-red-iot-dashboard-tutorial-build-interactive-real-time-dashboards)
- [Showing Sensor data in Node-RED Dashboard (Hackaday)](https://hackaday.io/project/167438-showing-sensor-data-in-node-red-dashboard)
- [Apache Superset 공식](https://superset.apache.org/)
- [OpenSchoolMaps — Introduction to Apache Superset](https://openschoolmaps.ch/lehrmittel/en_introduction_to_apache_superset/introduction_to_apache_superset.html)

### 학생 운영 사례
- [서울특별시교육청 — 기후위기 대응 행동365 발대식](https://enews.sen.go.kr/news/view.do?bbsSn=172804&step1=3&step2=1)
- [서울학생기후행동365 카카오톡 채널](https://pf.kakao.com/_dvxexcb/100184831)
- [2022 서울학생기후행동365 포럼](https://enews.sen.go.kr/news/view.do?bbsSn=177481&step1=3&step2=1)
- [내친구서울 — 서울학생기후행동 365](https://kids.seoul.go.kr/board/boardDetail.do?p_bbsSn=2134505004)
- [교육부 행복한교육 — 학교 기후·환경교육 특별기획](https://happyedu.moe.go.kr/happy/bbs/selectHappyArticle.do?bbsId=BBSMSTR_000000000191&nttId=10363)
- [탄소중립 중점학교 현황 (학교환경교육정보센터)](https://www.seeic.kr/tanso/school_list.do)
- [국가환경교육 통합플랫폼 — 학교환경교육 우수사례](https://www.keep.go.kr/front/seeic/best/bestPracticesListForm.html)
- [국가환경교육 통합플랫폼 — 탄소중립 실천학교](https://www.keep.go.kr/front/seeic/tanso/school_list.html)
- [2025 우수 환경 동아리 공모전](https://www.keep.go.kr/front/cntst/cntstDetailForm.html?cntstid=13)
- [2022 경기 탄소중립실천 우수사례집 (PDF)](https://www.goe.go.kr/resource/old/BBSMSTR_000000030137/BBS_202411050307439770.pdf)
- [학교환경교육정보센터](https://www.seeic.kr/tanso/school_list.do)

### 분석·연구 자료
- [학교 교실 공기질 관리를 위한 건강영향 기반 실내공기질지수(IAQI-S) 개발 (KCI)](https://journal.kci.go.kr/kseia/archive/articlePdf?artiId=ART002789241)
- [학교 미세먼지 빅데이터 사례 분석 (DBpia)](https://www.dbpia.co.kr/journal/articleDetail?nodeId=NODE10664586)
- [Velog — 미세먼지 데이터 분석(분석편)](https://velog.io/@godeok24/%EB%8D%B0%EC%9D%B4%ED%84%B0%EB%B6%84%EC%84%9D-%ED%94%84%EB%A1%9C%EC%A0%9D%ED%8A%B8%EB%AF%B8%EC%84%B8%EB%A8%BC%EC%A7%80-%EB%B6%84%EC%84%9D%ED%8E%B8)
- [Velog — 미세먼지 발표편](https://velog.io/@godeok24/%EB%8D%B0%EC%9D%B4%ED%84%B0%EB%B6%84%EC%84%9D%EB%AF%B8%EC%84%B8%EB%A8%BC%EC%A7%80-%EB%B0%9C%ED%91%9C%ED%8E%B8-65cdwmdi)
- [기상청 — Python을 활용한 분석 교육자료](https://bd.kma.go.kr/kma2020/dta/edu/KBP57200_Python.do)
- [IQAir — CO2 학교 모니터링](https://www.iqair.com/ko/newsroom/air-pollution-and-co2-monitoring-in-schools)
- [KHARN — 학교 공기질 해법 '환기'](http://www.kharn.kr/news/article.html?no=8670)
