# 04 — 예산·케이스·참고 사례

작성: 2026-05-21
대상: 당곡고 기후행동365 IoT 환경 모니터링 시스템 (16교실 × 1노드)

> 본 문서의 가격은 디바이스마트·아이씨뱅큐·엘레파츠 등 한국 전자부품 쇼핑몰의 2026년 5월 공개 데이터를 기준으로 한 **추정치**이며, 실제 구매 시점·수량·할인 조건에 따라 달라질 수 있다. 일부 항목(Pico 2 WH 신제품, Grove Shield 한국 가격)은 단가가 비공개여서 해외 가격(USD)에서 환산하거나 인접 모델로 대체 추정했고, 그런 경우 "추정"으로 표시했다.

---

## 요약 (TL;DR)

- **16노드 + 서버 + 예비 = 약 ₩2,400,000 (표준형 권장 시나리오)**
  - 저가형 ₩1,650,000 / 표준형 ₩2,400,000 / 고급형 ₩3,650,000
- **케이스: 자체 3D 프린팅 + 콘센트·벽 거치 겸용 시안 권장**
  - Thingiverse 4974448(WeatherDuino AQMIII PMS7003 indoor case) 패턴을 베이스로 학교에서 Grove 슬롯형으로 리믹스
- **핵심 참고 사례 3개**
  1. **Montana PurpleAirs in Schools** — 학교 1곳당 실내·실외 2개 센서, 연방 보조금 \$425k 모델
  2. **AirGradient (북부 태국 학교 시작 → 글로벌 오픈소스 학교 키트)** — 우리 프로젝트와 가장 구조가 비슷한 DIY 키트 사례
  3. **에너지·환경 통합형 학교 미세먼지 관리 기술개발사업 (교육부·과기부, 2019~2023, 약 300억 원)** — 국내 학교 미세먼지 정책 맥락 + 측정·환기 통합의 교훈

---

## D-1. 예산 산정

### 노드 1개당 BOM

| 항목 | 모델 (예) | 단가(원) | 비고 |
|------|-----------|---------:|------|
| Pico 2 WH | Raspberry Pi Pico 2 WH (헤더 포함, 무선) | **15,000 (추정)** | Pico 2 W가 디바이스마트 ≈ ₩11,900, WH는 통상 +₩2~3k. 신제품이라 공식 한국 가격 미확정 |
| Grove Shield for Pi Pico | Seeed v1.0 | **7,000 (추정)** | 글로벌 \$4 ≈ ₩5.5k + 한국 유통 마진. 디바이스마트 직접가 미공개 |
| Grove 케이블 × 5 | Grove Universal 4-pin 40cm (5 PCs Pack) | **6,000** | 아이씨뱅큐 5,900원/팩 — 1팩으로 노드 1개분 충족 |
| 온습도 센서 | SHT30 모듈 (SCHT-M30) | **7,500** | 디바이스마트 7,500원 (Grove 변환은 점퍼 직결로 흡수) |
| 조도 센서 | BH1750 (GY-302) | **3,000** | 아이씨뱅큐 2,500~2,700원 + 결선 여유 |
| 미세먼지 센서 | Plantower PMS7003 | **28,000** | 11번가 ≈ 28,000원, 다나와 시세 28~43k. PMS7003M(슬림형)도 동급 |
| CO₂ 센서 | Sensirion SCD41 모듈 (저가형 I2C 보드) | **35,000** | 11번가 ≈ 35,840원. DFRobot Gravity SCD41은 87,200원이라 학교 단가에는 부적합 |
| 케이스 (3D 프린팅, 자체 제작) | PLA 약 80~120 g | **2,500** | 1 kg ₩20~25k(국내 시세) → 100 g당 약 2,000~2,500원 |
| USB 케이블 + 5V 전원 | 5V 3A C타입 KC인증 어댑터 | **9,000** | 디바이스마트 KC인증 어댑터 8~10k대 (Pico 2 WH는 5V 2A로도 충분) |
| 부자재 (M2/M3 나사·점퍼선·실리콘·라벨) | — | **3,000** | 16노드 분량 일괄 구매 분담분 |
| **노드 1개 합계** |  | **₩116,000** | 표준형 기준 |

### 16노드 총 부품비
**16 × ₩116,000 = ₩1,856,000**

(저가형: SCD41 → MH-Z19B(약 ₩22k) 또는 CO₂ 미탑재로 약 ₩87k/노드 × 16 = ₩1,392,000)

### 서버·인프라

| 항목 | 모델 | 단가(원) | 수량 | 합계 |
|------|------|---------:|----:|-----:|
| 라즈베리파이 4 (4GB) + 방열판 | Pi 4 Model B 4GB | 75,000 (추정, 디바이스마트 ≈ 7~8만 원대) | 1 | 75,000 |
| microSD 64GB (A1, U3) | SanDisk Ultra 등 | 12,000 | 1 | 12,000 |
| Pi 4 케이스 | 알루미늄 또는 기본 케이스 | 10,000 | 1 | 10,000 |
| 5V 3A USB-C 어댑터 (KC) | — | 9,000 | 1 | 9,000 |
| 이더넷 케이블 Cat5e 3m | — | 4,000 | 1 | 4,000 |
| UPS (선택, 정전 대비) | Pi UPS HAT 또는 소형 ATX UPS | 40,000~80,000 | 1 | 60,000 |
| 네트워크 스위치 (선택) | 8포트 기가 스위치 | 25,000 | 1 | 25,000 |
| 3D 프린터 필라멘트 16노드 분 | PLA 1.75 mm, 1 kg | 22,000 | 2~3롤 | 60,000 |
| **합계 (표준형, UPS·스위치 포함)** |  |  |  | **₩255,000** |

> 학교에 3D 프린터가 이미 있다는 가정. 없으면 외주 3D 프린팅은 케이스 1개당 8,000~15,000원이라 16 × 약 12,000 = 약 ₩192,000 추가.

### 예비 부품 (≈ 10%)

| 항목 | 단가 | 수량 | 합계 |
|------|-----:|----:|-----:|
| Pico 2 WH 예비 | 15,000 | 2 | 30,000 |
| PMS7003 예비 | 28,000 | 2 | 56,000 |
| SCD41 예비 | 35,000 | 2 | 70,000 |
| SHT30 예비 | 7,500 | 2 | 15,000 |
| BH1750 예비 | 3,000 | 2 | 6,000 |
| Grove 케이블·점퍼선 일괄 | 10,000 | — | 10,000 |
| **예비 부품 합계** |  |  | **₩187,000** |

### 총 예산 시나리오

| 시나리오 | 노드 부품비(16개) | 서버·인프라 | 예비 | **총합** | 비고 |
|----------|----------------:|-----------:|-----:|--------:|------|
| **저가형** (CO₂ 생략, UPS·스위치 생략, 케이스 자체 프린팅) | 1,392,000 | 110,000 | 130,000 | **₩1,632,000** | 입문·시범용. PM2.5+온습도+조도만 |
| **표준형 (권장)** | 1,856,000 | 255,000 | 187,000 | **₩2,298,000** | 4종 센서 풀 구성 + UPS + 16 케이스 자체 프린팅 + 10% 예비 |
| **고급형** (정밀 SCD30/Sensirion SPS30 + UPS + 1년 클라우드 + 외주 케이스) | 2,720,000 | 480,000 | 250,000 | **₩3,450,000** | SPS30 미세먼지(₩60k) + SCD30(₩65k) + AirGradient·ThingsBoard 클라우드 +외주 케이스 |

> **트레이드오프**
> - 저가형은 학생 조립의 첫 사이클에 적합. CO₂는 Ch2 학습에서 SCD41 한두 대만 시연용으로 확보해도 됨.
> - 표준형은 16교실 균질 데이터 + 학교회계 단일 항목으로 끊기 좋은 금액대(약 230만 원).
> - 고급형은 환경부·교육청 공모로 별도 예산이 잡힐 때만 의미가 있음. 학생 조립 난이도가 급격히 올라가므로 학습 목적과 충돌.

### 예산 확보 경로

| 경로 | 예상 금액 | 비고 |
|------|---------:|------|
| 학교회계 (기본운영비·과학실험실 운영비) | 30~100만 원 | 기본 라인. 표준형 일부 충당 |
| 교육청 미래교육·디지털교육 공모 | 100~300만 원 | 메이커스페이스/디지털 새싹 라인 |
| 환경부 「환경교육 우수학교」/지역 환경교육센터 | 100~500만 원 | keep.go.kr 통합플랫폼 공모 활용 |
| 기후행동365 자체 지원금 | — | 학교가 이미 지정된 경우 우선 사용 |
| 학부모회·동문회 매칭 펀드 | 30~50만 원 | 케이스·예비부품 등 소모성 |

> 단일 공모 사업 한 건으로 표준형(약 230만 원) 전액을 잡기보다 **학교회계 + 환경부/교육청 공모**의 2개 라인을 동시에 신청하는 게 현실적이다(공모 탈락 리스크 분산).

---

## D-2. 케이스 설계

### 3D 프린팅 권장 사례 (Thingiverse / Printables)

| 제목 | 링크 | 활용 포인트 |
|------|------|------------|
| WeatherDuino AQMIII Plantower PMS7003 indoor case | https://www.thingiverse.com/thing:4974448 | PMS7003 + MH-Z19(CO₂) + OLED를 같이 담은 2-part 실내용 케이스. **흡기·배기 슬릿 패턴이 가장 참고할 만함.** SCD41은 위치만 살짝 옮기면 그대로 적용 가능 |
| Adapter for PMS7003 (awalach) | https://www.thingiverse.com/thing:3327444 | 사각형 흡·배기구 대신 **원형 12 mm 홀** 어댑터. 학생이 핸드드릴로도 다듬을 수 있어 안전 |
| Thingiverse "Pms7003" 태그 목록 | https://www.thingiverse.com/tag:pms7003 | 우천 외장형까지 다양한 변형 카탈로그 |
| Raspberry Pi Pico Case by GrevTech | https://www.printables.com/model/143745-raspberry-pi-pico-case | 핀 방향(상·하) 2종 — Grove Shield 결합형 리믹스의 베이스 |
| Slim modular Raspberry Pi Pico Case | https://www.printables.com/model/61680-slim-modular-raspberry-pi-pico-case | **모듈형** 디자인이라 학교에서 센서 슬롯을 옆에 붙이는 리믹스에 적합 |
| Adafruit 3D Printed Case for Raspberry Pi Pico | https://learn.adafruit.com/raspberry-pi-pico-case/overview | 공식 가이드 + STL. 안전 모서리(라운드) 처리 잘 됨 |
| Instructables: DIY Air Quality Sensor + 3D Printed Case | https://www.instructables.com/DIY-Air-Quality-Sensor-3D-Printed-Case/ | 학생 조립 수준의 step-by-step 사진 가이드. **수업 자료로 직접 인용 가능** |

### 미세먼지 센서 흡기·배기 처리 — 핵심 원칙

1. **흡기·배기 분리**: PMS7003은 자체 팬으로 측면에서 흡입 → 반대편 배기. **두 슬릿을 한쪽으로 모으면 안 됨**(자가 재순환으로 측정값이 천천히 변함).
2. **수동 흡기로 충분**: 실내 교실 환경(난기류·환기 자연 발생)에서는 PMS7003 내장 팬만으로 충분. 외부 팬은 결로·먼지 누적 부작용 큼.
3. **능동 흡기(소형 팬) 검토는 외장형에 한정**: 복도·창문 외부에 두는 경우만 5V 3 cm 팬 추가 — 본 프로젝트(16교실 실내)에는 불필요.
4. **결로 방지**: 케이스 하단·바닥에 1~2 mm 환기 슬릿 별도. 난방 직하 ↔ 창가 온도차 큰 위치 회피.
5. **안전성**: 모든 외부 모서리 ≥ 2 mm 라운드 처리, USB-C 외에 노출 부품 없음, Pico LED는 작은 광확산 창으로 보여주기만.

### 거치 방식 비교

| 방식 | 장점 | 단점 | 추천도 |
|------|------|------|:------:|
| **콘센트 거치형** (벽 콘센트 위쪽에 케이스 자체가 걸리는 형태) | 전원선 짧음, 학생 손길 적음, 설치 통일 | 콘센트 위치가 책상·앞 칠판에서 멀 수 있어 데이터 대표성 떨어질 수 있음 | ★★★ |
| **벽걸이형** (M3 나사 2개 + 양면테이프 보조) | 위치 선택 자유, 호흡 높이(약 1.2 m)로 설치 가능 | 학교 벽 시공 허가 필요, USB 전원선 매다는 처리 필요 | ★★★★ (권장) |
| **책상·캐비닛 위 거치형** | 설치 가장 간단, 학생이 보고 만질 수 있음 → 학습 효과↑ | 학생 접촉·이동·낙하 리스크, 데이터 노이즈(입김·낙서) | ★★ |
| **천장 거치** | 시야에서 깔끔 | **미세먼지·CO₂는 호흡 높이(1.0~1.5 m)에서 측정해야 의미 있음.** 천장은 PM2.5 측정에 부적절 | ★ (비권장) |

> **교실 표준 권장**: 칠판 옆 벽면(앞쪽 1/3 지점) 호흡 높이에 **벽걸이형**. 콘센트가 가까운 교실은 **콘센트 거치형**으로 통일. 두 시안을 같은 STL의 어댑터 플레이트로 갈아 끼우게 설계.

### 추천 시안

- **1안 (표준)**: Grove Shield 상부에 PMS7003을 옆으로 눕히고, SCD41/SHT30/BH1750은 후면 측벽에 환기 슬릿과 같이 배치하는 **3-part 케이스**(상·하·후면 슬릿 모듈). 모듈식이라 센서가 바뀌어도 후면만 교체하면 됨.
- **2안 (간소)**: GrevTech Pico 케이스를 베이스로, Grove Shield + 센서 모듈은 본체 옆 **별도 클립 박스**에 두고 Grove 케이블로 연결. 학생 조립 난이도 가장 낮음.

### 시판 케이스 대안

- **Pico 단독 케이스**: Adafruit/Pimoroni의 ABS 케이스 글로벌 \$8~12(약 ₩12~18k). 16개 × 약 ₩15k = **₩240k** → 노드당 단가 +₩15k.
- **AirGradient Pro 케이스**: UV 저항 사출 케이스만 별도 구매 시 약 \$15~20(₩22~30k). 외관 깔끔하지만 단가 부담.
- **결론**: 16개 단위 수량이고 학교에 3D 프린터가 있다면 자체 프린팅이 **단가·교육 효과·디자인 자유도** 모두에서 우위. 단, 학교에 프린터가 없거나 시간이 부족하면 **Adafruit 케이스 + 외장 센서 모듈** 조합이 차선.

---

## D-3. 참고 사례

### 국내 사례

#### 사례 1 — 에너지·환경 통합형 학교 미세먼지 관리 기술개발사업 (교육부·과기부)
- 주관: 교육부 + 과학기술정보통신부 (한국연구재단)
- 기간/규모: **2019~2023, 약 300억 원** 5개년 사업
- 내용: WHO 권고기준 수준 학교 실내 공기질 상시 관리 — 활동도 기반 비산먼지 평가, 학교 맞춤 열·공기환경 통합관리 시스템 실증
- 교훈: **(1)** 환기만으로는 PM2.5 통제가 어렵고 **(2)** "측정 + 환기/정화 + 데이터 공개"가 묶일 때 비로소 학교 단위 의사결정에 쓰임. 우리 프로젝트가 **측정 전용**이라면 환기 행동 가이드(Ch1·Ch7)와 짝지어야 의미가 커진다.
- 출처:
  - https://www.nrf.re.kr/biz/info/info/view?menu_no=378&biz_no=407
  - http://iehs.co.kr/bbs/board.php?bo_table=customer_1&wr_id=24&page=8

#### 사례 2 — 환경교육 우수학교 지정 공모 (기후에너지환경부·국가환경교육 통합플랫폼)
- 주관: 기후에너지환경부 + keep.go.kr
- 내용: 매년 환경교육 우수학교 공모. 학교 자체 환경 프로젝트(미세먼지 측정, 데이터 분석, 시민과학 활동 등)가 지정·지원 대상.
- 활용 포인트: 기후행동365가 이미 학교 단위 사업으로 잡혀 있다면, IoT 시스템 구축 → 데이터 수집 → 보고서까지 **공모 응모용 산출물**과 자연스럽게 정렬됨.
- 출처:
  - https://www.keep.go.kr/portal/137
  - https://www.me.go.kr/home/web/board/read.do?boardId=1728970

#### 사례 3 — 에어코리아 "우리학교 주변 대기 정보"
- 주관: 환경부 에어코리아
- 내용: 학교 인근 공식 대기측정망 데이터를 학교별로 묶어 조회 가능. **외부 기준값(reference)**으로 학생 데이터의 정합성 검증에 활용.
- 활용 포인트: 학생이 측정한 16교실 PM2.5 ↔ 학교 외부 측정망 PM2.5 비교 = Ch4/Ch6 데이터 분석 단원의 자연스러운 과제.
- 출처: https://www.airkorea.or.kr/web/realschoolSearch?pMENU_NO=99

#### 사례 4 (학술) — 학교 미세먼지 빅데이터 사례 분석
- 한국정보기술학회 (KIIT) 학술논문. 학교 내외 PM 예측 시스템을 다룬 국내 연구로, 학생 프로젝트의 인용·참고 문헌으로 사용 가능.
- 출처: https://www.dbpia.co.kr/journal/articleDetail?nodeId=NODE10664586

### 해외 사례

#### 사례 5 — Montana "PurpleAirs in Schools" Program ⭐
- 주관: Montana DEQ + Montana High School Association + University of Montana
- 규모: **연방 ARPA 보조금 \$425,000**, 학교 1곳당 PurpleAir 센서 2개(실내·실외 각 1) 배포
- 학생 참여: University of Montana "Students Participating in Air Research and Knowledge Translation" 프로그램으로 학생들이 전 주의 실시간 데이터에 접근·연구
- 성과: 산불 연기 침투 데이터를 학교 의사결정(체육수업 야외 여부 등)에 직접 반영
- 교훈: **(1)** 실내·실외를 함께 보면 의미가 훨씬 강해진다. 우리도 16교실 + 운동장 1대 정도의 외부 노드가 있으면 좋다. **(2)** 학생의 데이터 해석 활동을 별도 프로그램으로 묶어야 IoT가 "설치 후 잊혀지는 박스"가 되지 않는다.
- 출처:
  - https://www2.purpleair.com/blogs/blog-home/how-montana-schools-are-using-purpleair-sensors-to-protect-communities-from-wildfire-smoke
  - https://deq.mt.gov/files/Air/AirMonitoring/Documents/PurpleAirs%20in%20Schools%20Flyer.pdf

#### 사례 6 — AirGradient (북부 태국 학교 → 글로벌 오픈소스) ⭐⭐
- 시작: 북부 태국 시즌 산불 연기 대응을 위한 학교 자원봉사 프로젝트
- 현재: PM2.5 + CO₂ + 온습도를 측정하는 오픈소스 DIY 키트(Basic / Pro). 5~10분 조립용 pre-soldered 옵션과 UV 저항 사출 케이스 포함
- 학교 프로그램: 무료 대시보드 체험 + 학교 솔루션 별도 운영
- 가격대: Pro 키트가 약 \$80~150 수준. 단, 디바이스마트 BOM(우리 표준형 ≈ ₩116k/노드 = 약 \$85)과 거의 같은 가격대로, 우리는 **로컬 부품 + 학생 조립 + Pico 학습성**이라는 차별점이 있음.
- 교훈: **(1)** "DIY + 학교 + 오픈소스"의 완성형 레퍼런스. 케이스·UI·대시보드 디자인 톤을 그대로 참고 가능. **(2)** MIT 라이선스라 STL/PCB도 리믹스 가능 — 우리 케이스 1안의 직접적 베이스로 활용 가능.
- 출처:
  - https://www.airgradient.com/
  - https://www.airgradient.com/documentation/diy-v4/

#### 사례 7 — US EPA "Air Sensor Toolbox" & DIY Air Sensor for Educators
- 주관: US EPA
- 내용: 교사·시민과학자용 DIY 공기질 센서 가이드 + 교실 활동 자료. **교사용 활동지·평가 루브릭 형식**이 잘 정리돼 있어 우리 본문 단원 Tip 박스의 톤을 잡을 때 참고하기 좋다.
- 출처:
  - https://www.epa.gov/air-sensor-toolbox/resource-guide-air-sensors-and-related-educational-activities
  - https://www.epa.gov/sciencematters/diy-air-sensor-now-available-use-educators-and-citizen-scientists

#### 사례 8 — Earthwatch "Operation Healthy Air"
- 학생 시민과학 + 학교 공기질 측정 프로그램. **데이터 → 정책 제안**까지의 전체 학습 사이클이 잘 짜여 있다.
- 출처: https://earthwatch.org/stories/air-quality-schools-research

### 교훈 종합 — 실패·주의 사례에서 배울 점

1. **"측정만 있는 시스템"의 함정** — 국내 학교 미세먼지 사업이 환기·정화 통합으로 옮겨간 이유. 우리도 데이터 → 학생 행동(창 열기·공기청정기 가동·체육 위치 조정) 루프를 **Ch4/Ch7에 명시**해야 한다.
2. **위치 선정 실패** — PurpleAir 사례에서도 천장·창문 인접 설치는 외기 영향이 커서 실내 대표성을 잃었다는 보고가 있다. **호흡 높이 + 칠판/창에서 1 m 이상 거리**가 표준.
3. **유지보수 비용 미산정** — PMS7003은 약 2~3년 후 광학부 오염으로 측정값 드리프트가 시작된다. 예비 부품 10%를 매년 갱신해야 함을 **운영 매뉴얼**에 명시.
4. **대시보드 의존 리스크** — AirGradient·PurpleAir 모두 클라우드 의존도가 높다. 우리는 **학교 내 Raspberry Pi 4 로컬 서버**가 1차 저장소이고 클라우드는 선택 — 이 구조가 망 분리 + 개인정보 측면에서도 안전하다.

---

## 미해결 / 사용자 확인 필요

- 학교에 **3D 프린터 보유 여부 + 가용 시간** (없으면 케이스 예산에 약 ₩200k 추가)
- 환경부/교육청 공모 일정 (현재 환경교육 우수학교 공모는 통상 1~3월에 마감) — 2026년 일정 확정 필요
- **예산 확보 시점**: 학교회계 추경(보통 9월)에 맞추려면 D-1 표준형 견적을 8월 말까지 학교 행정실에 제출 필요
- Pico 2 WH의 디바이스마트 정식 입고 시기 (검색 시점 기준 Pico 2 W는 입고, WH는 미확정 → Pico WH(이전 세대) + Pico 2 W 혼용도 옵션)
- 16교실 위치별 콘센트·벽 시공 가능 여부 (행정실·시설 담당 확인 필요)

---

## 출처

### 부품·가격
- [디바이스마트 — 라즈베리파이 피코 2 W](https://www.devicemart.co.kr/goods/view?no=15604429)
- [디바이스마트 — 라즈베리파이 피코 WH](https://www.devicemart.co.kr/goods/view?no=14575955)
- [디바이스마트 — 라즈베리파이 4 4GB + 가이드북](https://www.devicemart.co.kr/goods/view?no=12234534)
- [디바이스마트 — Plantower PMS7003](https://www.devicemart.co.kr/goods/view?no=10917688)
- [디바이스마트 — SCD41 CO₂ Sensor Breakout (PIM587)](https://www.devicemart.co.kr/goods/view?no=14917083)
- [디바이스마트 — SCD40-D-R2](https://www.devicemart.co.kr/goods/view?no=15008091)
- [디바이스마트 — SENSIRION SHT30 SCHT-M30](https://www.devicemart.co.kr/goods/view?no=14597956)
- [디바이스마트 — BH1750 GY-302 (SZH-EK070)](https://www.devicemart.co.kr/goods/view?no=1289977)
- [디바이스마트 — Grove 4 pin Male Jumper 변환 케이블](https://www.devicemart.co.kr/goods/view?no=1153480)
- [디바이스마트 — 5V 4A 라즈베리파이4 KC인증 C타입 아답터](https://www.devicemart.co.kr/goods/view?no=12544959)
- [디바이스마트 — 5V 3A 라즈베리파이4 C타입 아답터 SZH-PSU04](https://www.devicemart.co.kr/goods/view?no=12234996)
- [아이씨뱅큐 — Grove Universal 4 Pin Buckled 40cm Cable 5pcs](https://www.icbanq.com/P006960972)
- [11번가 — 아두이노 정밀 미세먼지 PMS7003](https://www.11st.co.kr/products/3262664941)
- [11번가 — SCD40/SCD41 가스 센서 모듈](https://www.11st.co.kr/products/7307606640)
- [Seeed Studio — Grove Shield for Pi Pico v1.0](https://www.seeedstudio.com/Grove-Shield-for-Pi-Pico-v1-0-p-4846.html)
- [The Pi Hut — Grove Shield for Raspberry Pi Pico v1.0](https://thepihut.com/products/grove-shield-for-raspberry-pi-pico-v1-0)
- [Sensirion SCD41 제품 페이지](https://sensirion.com/products/catalog/SCD41)

### 케이스 / 3D 프린팅
- [Thingiverse — WeatherDuino AQMIII PMS7003 indoor case](https://www.thingiverse.com/thing:4974448)
- [Thingiverse — Adapter for PMS7003](https://www.thingiverse.com/thing:3327444)
- [Thingiverse — tag:pms7003](https://www.thingiverse.com/tag:pms7003)
- [Printables — Raspberry Pi Pico Case by GrevTech](https://www.printables.com/model/143745-raspberry-pi-pico-case)
- [Printables — Slim modular Raspberry Pi Pico Case](https://www.printables.com/model/61680-slim-modular-raspberry-pi-pico-case)
- [Adafruit — 3D Printed Case for Raspberry Pi Pico](https://learn.adafruit.com/raspberry-pi-pico-case/overview)
- [Instructables — DIY Air Quality Sensor + 3D Printed Case](https://www.instructables.com/DIY-Air-Quality-Sensor-3D-Printed-Case/)

### 참고 사례
- [한국연구재단 — 에너지·환경 통합형 학교 미세먼지 관리 기술개발사업](https://www.nrf.re.kr/biz/info/info/view?menu_no=378&biz_no=407)
- [EHS기술연구소 — 교육부 학교 미세먼지 관리기술 개발사업 추진위 출범](http://iehs.co.kr/bbs/board.php?bo_table=customer_1&wr_id=24&page=8)
- [국가환경교육 통합플랫폼 keep.go.kr — 공모전](https://www.keep.go.kr/portal/137)
- [기후에너지환경부 — 2025 환경교육 우수학교 지정공모](https://www.me.go.kr/home/web/board/read.do?boardId=1728970)
- [에어코리아 — 우리학교 주변 대기 정보](https://www.airkorea.or.kr/web/realschoolSearch?pMENU_NO=99)
- [DBpia — 학교 미세먼지 빅데이터 사례 분석 (KIIT)](https://www.dbpia.co.kr/journal/articleDetail?nodeId=NODE10664586)
- [PurpleAir — How Montana Schools Are Using PurpleAir Sensors](https://www2.purpleair.com/blogs/blog-home/how-montana-schools-are-using-purpleair-sensors-to-protect-communities-from-wildfire-smoke)
- [Montana DEQ — PurpleAirs in Schools Flyer (PDF)](https://deq.mt.gov/files/Air/AirMonitoring/Documents/PurpleAirs%20in%20Schools%20Flyer.pdf)
- [PurpleAir — Air Quality in Schools blog](https://www2.purpleair.com/blogs/blog-home/air-quality-in-schools-why-monitoring-matters-for-students-and-staff)
- [AirGradient — Home](https://www.airgradient.com/)
- [AirGradient — DIY v4 Documentation](https://www.airgradient.com/documentation/diy-v4/)
- [US EPA — Air Sensor Toolbox Educational Resources](https://www.epa.gov/air-sensor-toolbox/resource-guide-air-sensors-and-related-educational-activities)
- [US EPA — DIY Air Sensor for Educators and Citizen Scientists](https://www.epa.gov/sciencematters/diy-air-sensor-now-available-use-educators-and-citizen-scientists)
- [Earthwatch — Operation Healthy Air](https://earthwatch.org/stories/air-quality-schools-research)
