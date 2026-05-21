# PROGRESS — 진행 추적

## 2026-05-21

### 09:00 — 프로젝트 시작
- 사용자(석리송)가 계획서(`PROJECT_BRIEF.md`) 제출
- 새 프로젝트 폴더 `~/greatsong-project/climate-action-365/` 생성
- 폴더 구조 세팅: docs/, reference/, prototype/{firmware,server,dashboard}/
- 기본 문서 작성: README.md, PLAN.md, PROGRESS.md

### 다음 행동
- 리서치 트랙 A/B/C/D 병렬 launch (background agents)
- 산출물: `reference/01~04-*.md`

## 리서치 트랙 상태

| 트랙 | 주제 | 상태 | 산출물 |
|------|------|------|--------|
| A | 센서 비교 | ✅ 완료 | `reference/01-sensor-comparison.md` |
| B | 네트워크 설계 | ✅ 완료 | `reference/02-network-design.md` |
| C | 대시보드 + 기준 + 운영 | ✅ 완료 | `reference/03-dashboard-and-standards.md` |

## 트랙 C 핵심 발견 (2026-05-21)

1. **대시보드는 "Streamlit + Grafana 하이브리드"가 정답** — 단일 도구로는 4대 요구사항(학생 수정 용이 + 24/7 알림 + 다중 동시접속 + Pandas 분석)을 모두 못 만족. InfluxDB 단일 소스로 두고 양쪽이 같은 데이터를 보는 구조. Node-RED는 조립팀 교육용, Superset은 2년차 분석팀 SQL 트랙으로.
2. **학교보건법 시행규칙 정확한 수치 확보**:
   - 별표 2: 온도 18~28℃, 습도 30~80%, 조도 책상면·칠판면 300 lux 이상(조도비 3:1), 환기량 1인당 21.6 ㎥/h
   - 별표 4의2: CO₂ 1,000 ppm(기계환기 1,500), PM10 75 / PM2.5 35 / HCHO 80 / TVOC 400 ㎍/㎥, 라돈 148 Bq/㎥
   - **PM1.0·상시 TVOC는 학교 명문 기준 없음** → 분석팀이 자체 임계값을 데이터로 제안 (교육적 가치).
3. **국내 선도 사례 부재** — 16교실급 학생 운영 IoT 모니터링 사례 미발견. 당곡고가 선도 사례가 될 가능성 → 처음부터 keep.go.kr 우수동아리 공모전·탄소중립 중점학교 자료집 출품을 산출물 목표로 잡을 것 권장.

## 다음 단계
4개 트랙 모두 완료. 통합 추천 A/B/C안 작성 시작 → `docs/PHASE1-RECOMMENDATIONS.md`

## 2026-05-21 (오후) — 통합 추천안 작성 완료

산출물: [`docs/PHASE1-RECOMMENDATIONS.md`](docs/PHASE1-RECOMMENDATIONS.md)

3가지 안 요약:
- **A. 빠른 시작 (~₩1.5M)** — HTTP + SQLite + Streamlit 단독. 학생 코드 전영역 접근.
- **B. 표준 권장 (~₩2.3M) ⭐** — MQTT + InfluxDB + Streamlit/Grafana 하이브리드. 트랙 4개 공통 권장.
- **C. 정밀·연구형 (~₩3.5~4M)** — 전 SPS30 + 실외 1대 + 클라우드 미러. 공모전·논문 출품용.

선결 액션 아이템 6개 + 발주 전 재확인 3개 식별. 사용자 결정 대기.

## 2026-05-21 (오후) — D안 (Phase 1) 확정 + 프로토타입 코드 작성

사용자 결정: A/B/C 모두 비싸므로 **D안 (단계 시작)** 으로 변경.
- 측정: 온습도(SHT40) + 조도(BH1750)만, CO2/PM은 Phase 2/3
- 인프라: HTTP + SQLite + Streamlit (확장 시에도 그대로)
- 예상 총액: 약 92만 원 (16노드 + 라즈베리파이4 서버 + 예비 10%)

산출물:
- BOM 확정: [`docs/BOM.md`](docs/BOM.md)
- 펌웨어: [`prototype/firmware/`](prototype/firmware/) — `main.py`, `sensors.py`, `secrets.py`
- 서버: [`prototype/server/`](prototype/server/) — FastAPI + SQLite (`co2_ppm`, `pm25`, `pm10` 컬럼 예약)
- 대시보드: [`prototype/dashboard/`](prototype/dashboard/) — Streamlit 3탭 (전체 그리드 / 교실 상세 / 분석팀 작업장)
- 통합 가이드: [`prototype/README.md`](prototype/README.md)

## 다음 단계
사용자가 1교실 파일럿 테스트 → 부품 발주 → 16교실 확장.
Phase 2(CO2) 추가는 코드 골격 그대로 두고 센서 드라이버·필드만 추가.

## 2026-05-21 — Astro + Starlight 사이트 생성 완료

- 위치: [`site/`](site/) — 피코 책과 동일한 Starlight 0.30 + Pretendard 톤
- 빌드 검증: `npm run build` → 8페이지 출력 성공
- dev 서버: `npm run dev` → http://localhost:4321 (랜딩·Unit 1·교사용 모두 200 OK)
- 콘텐츠: 단원 4편 + 교사용 + 소개 + 랜딩 = 7페이지

다음 단계 (선택):
- GitHub Pages·Vercel·Netlify 중 하나로 외부 공개
- 또는 라즈베리 파이 4에 nginx로 학교 내부망 공개 (대시보드와 같은 서버 공유)

## 2026-05-21 — 피코 북 형식 교재 작성 완료

학생용 4 단원 + 교사용 통합 지도서 + INDEX 작성. V-파이썬 톤·4종 리터러시 박스·그림 박스(자리표시) 형식.

학생용 단원:
- [`docs/book/Unit_1_파일럿_한_대_세팅.md`](docs/book/Unit_1_파일럿_한_대_세팅.md) — 펌웨어·Thonny·배선·검증 / 그림 7장
- [`docs/book/Unit_2_서버_라즈베리파이4.md`](docs/book/Unit_2_서버_라즈베리파이4.md) — OS·고정 IP·systemd·cron / 그림 6장
- [`docs/book/Unit_3_16대_조립과_설치.md`](docs/book/Unit_3_16대_조립과_설치.md) — 매핑·자동 배포·페어 워크숍 / 그림 4장
- [`docs/book/Unit_4_운영과_장애대응.md`](docs/book/Unit_4_운영과_장애대응.md) — 일일·주간·월간 점검·SQL / 그림 4장

교사용:
- [`docs/book/teacher/교사용_통합_지도서.md`](docs/book/teacher/교사용_통합_지도서.md) — 16주 일정, 단원별 지도안, 교육과정 매핑, 평가 루브릭, FAQ, 인계 패키지

INDEX:
- [`docs/book/INDEX.md`](docs/book/INDEX.md)

## 2026-05-21 — 세팅 가이드 3종 작성 완료

- [`docs/SETUP-01-NODE.md`](docs/SETUP-01-NODE.md) — 1대 파일럿 (MicroPython 플래시 → 배선 → 코드 → 검증)
- [`docs/SETUP-02-SERVER.md`](docs/SETUP-02-SERVER.md) — Pi 4 서버 (OS 굽기 → 고정 IP → systemd → cron 백업 → 방화벽)
- [`docs/SETUP-03-16-NODES.md`](docs/SETUP-03-16-NODES.md) — 16대 운영 (MAC 수집 → 일괄 배포 → 조립 워크플로우 → 모니터링 → 장애 대응)

## 2026-05-21 (오후) — 예산·보유 자산 확정

- **보유**: Pico 2 WH × 16, Grove Shield × 16 (구매 불필요, 약 30만원 절감)
- **예산 상한**: 60만 원
- **서버**: 라즈베리파이 4(4GB) 신규 구매 결정
- **신규 구매 총액**: 약 60만 원 (정확히 예산 내)
  - 노드 16개분 (센서·케이블·전원·케이스·부자재): 432,000원
  - Pi4 서버 (Pi + microSD + 케이스+전원): 115,000원
  - 예비 부품 10%: 53,000원

→ [`docs/BOM.md`](docs/BOM.md) 갱신 완료.
| D | 예산 + 케이스 + 사례 | ✅ 완료 | `reference/04-budget-and-cases.md` |

## 트랙 D 핵심 발견 (2026-05-21)

1. **표준형 16노드 총예산 ≈ ₩2.3M, 노드 단가 ≈ ₩116k** — 디바이스마트·아이씨뱅큐 시세 기준. 단가 최상위는 SCD41 CO₂(₩35k)·PMS7003(₩28k). Pico 2 WH 한국 정식가 미공개라 Pico 2 W(₩11.9k) + 헤더 마진 추정. **예산 확보 경로**: 학교회계 단독 + 환경부 keep.go.kr 환경교육 우수학교 공모 병행.
2. **케이스: 자체 3D 프린팅 + 벽걸이 거치** — Thingiverse 4974448(WeatherDuino PMS7003 indoor case) 흡·배기 슬릿 패턴 참고, AirGradient(MIT 라이선스) 리믹스 가능. **천장 거치 X** — PM2.5는 호흡 높이 1.0~1.5 m가 원칙.
3. **참고 사례**: AirGradient(태국 학교 자원봉사 → 글로벌 오픈소스 키트, 구조 유사) + Montana "PurpleAirs in Schools"($425k 보조금, **실내+실외 2센서** 운영). 국내 교육부 300억 사업(2019~2023)의 교훈: "측정만으로 부족, 환기·정화·데이터 공개 행동 루프와 묶여야 의미". → 분석팀·운영팀 활동에 데이터→행동 루프 명시적 설계 필요.

## 트랙 A 핵심 발견 (2026-05-21)

1. **미세먼지 혼합 전략** — 16노드는 PMS7003(₩35k, 가성비)로 가되 시간 변화 추적용. 기준점용 SPS30(₩55k, ±10% MCERTS) 1~2대 추가 → 학생 분석팀이 캘리브레이션 학습 가능. **레이저 수명 8000시간(약 1년 연속)** 주의 — 펌웨어에 측정 사이 sleep 패턴 필수.
2. **CO2는 SCD41 권장** — I2C 통일 가능(PMS7003만 UART). 단 ABC 자가보정이 7일 내 외기 400 ppm 노출을 가정 → 교실은 어려울 수 있으니 **학기 시작 수동 FRC 보정**을 운영 매뉴얼에 포함.
3. **추정 총액 (16노드 센서)**: 절감형 ₩1.17M ~ 기본형 ₩1.74M (TVOC 제외). 단 디바이스마트 동적 페이지에서 자동 가격 추출 실패 → **발주 전 실시간 가격 재확인 필수**. 미해결 8개 결정 항목은 산출물 끝에.

## 트랙 B 핵심 발견 (2026-05-21)

1. **🚨 Pico 2 W는 WPA2-Enterprise 미지원** — CYW43439 드라이버 단에서 EAP-PEAP/MSCHAPv2 미구현 (MicroPython·Pico SDK·CircuitPython 모두). 학교 교직원망이 EAP면 사실상 사용 불가 → **별도 IoT용 WPA2-PSK SSID 발급 요청** 또는 라즈베리파이/공유기로 자체 AP 구축이 Plan B.
2. **MQTT 포트 1883/8883 방화벽 차단 가능성** — MQTT-over-WebSocket(443) 또는 HTTPS POST 폴백 설계 미리 준비.
3. **추천 스택**: 라즈베리파이 4 + Mosquitto + InfluxDB 2.x + Grafana (학교 LAN 내, 초기 12~18만원, 운영비 ~0). 안정성은 WDT(8초) + umqtt.robust2 + LWT + JSONL 오프라인 버퍼 + pico-OTA 조합.

→ 사용자 액션 아이템: 학교 네트워크 관리자에게 (1) 인증 방식, (2) outbound 포트 정책, (3) IoT 전용 SSID 발급 가능 여부 문의.
