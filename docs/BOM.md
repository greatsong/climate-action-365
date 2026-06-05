# BOM — Phase 1 부품 명세서 (v2, URL 포함)

확정: 2026-05-21
시나리오: D안 (Phase 1, 온습도 + 조도)
예산 상한: **60만 원**

> 구글 시트: [기후행동365 구매 리스트 v2 (URL 포함)](https://docs.google.com/spreadsheets/d/1Vu9TtwB73_5AS0gvUzibPNF1fT0R21vB08wvX0qyeCY/edit)

## 보유 자산 (구매 불필요)

| 부품 | 수량 | 가치 (참고) |
|---|---|---|
| Raspberry Pi Pico 2 WH | 16개 ✅ | 약 192,000원 |
| Grove Shield for Pi Pico | 16개 ✅ | 약 112,000원 |
| **보유 자산 가치** | | **약 304,000원** |

## 신규 구매 BOM

### 필수 구매 (16노드 + 서버)

| 구분 | 부품 | 모델 | 단가 | 수량 | 합계 | URL |
|---|---|---|---|---|---|---|
| 센서 | 온습도 | SHT40 Grove [101021032] | 7,900 | 18 | 142,200 | [디바이스마트](https://www.devicemart.co.kr/goods/view?no=13517666) |
| 센서 | 조도 | BH1750 GY-302 [SEN340207] | 4,500 | 18 | 81,000 | [디바이스마트](https://www.devicemart.co.kr/goods/view?no=10825464) |
| 배선 | Grove 4핀 케이블 20cm (SHT40용) | 5pcs 팩 | 5,000 | 4 | 20,000 | [디바이스마트 검색](https://www.devicemart.co.kr/goods/search?keyword=Grove+Universal+4+pin+cable+20cm) |
| 배선 | Grove-점퍼 변환 케이블 (BH1750용) | 5pcs 팩 | 3,500 | 4 | 14,000 | [디바이스마트](https://www.devicemart.co.kr/goods/view?no=1153480) |
| 전원 | 마이크로 USB 케이블 1m | [C3886] | 1,500 | 19 | 28,500 | [디바이스마트](https://www.devicemart.co.kr/goods/view?no=1061716) |
| 전원 | USB 5V/1A 어댑터 | 1포트 | 3,500 | 16 | 56,000 | [쿠팡](https://www.coupang.com/vp/products/6650967648) |
| 케이스 | ABS 프로젝트 박스 80×60×30mm | 하이박스 또는 동등 | 3,500 | 18 | 63,000 | [디바이스마트 검색](https://www.devicemart.co.kr/goods/search?keyword=ABS+%EB%B0%95%EC%8A%A4+80x60) |
| 부자재 | 케이블타이 + 라벨 | 100개·세트 | 10,000 | 1 | 10,000 | [쿠팡 검색](https://www.coupang.com/np/search?q=%EC%BC%80%EC%9D%B4%EB%B8%94%ED%83%80%EC%9D%B4+100mm+100%EA%B0%9C) |
| 서버 | **Raspberry Pi 5 (16GB)** | 정품 | 230,000 | 1 | 230,000 | [디바이스마트](https://www.devicemart.co.kr/goods/view?no=15666226) |
| 서버 | microSD 64GB 산업용 | Sandisk High Endurance | 15,000 | 1 | 15,000 | [쿠팡 검색](https://www.coupang.com/np/search?q=Sandisk+High+Endurance+64GB) |
| 서버 | **Pi 5 액티브 쿨러 포함 케이스** | Argon NEO 5 또는 공식 Active Cooler 세트 | 25,000 | 1 | 25,000 | [디바이스마트 검색](https://www.devicemart.co.kr/goods/search?keyword=Argon+NEO+5) |
| 서버 | **Pi 5 5V/5A USB-C PD 27W 어댑터** | 공식 또는 동등 | 18,000 | 1 | 18,000 | [디바이스마트 검색](https://www.devicemart.co.kr/goods/search?keyword=%EB%9D%BC%EC%A6%88%EB%B2%A0%EB%A6%AC%ED%8C%8C%EC%9D%B45+27W) |
| 서버 | Micro HDMI → HDMI 케이블 | [SZH-CAB16] | 6,000 | 1 | 6,000 | [디바이스마트](https://www.devicemart.co.kr/goods/view?no=12232873) |
| **필수 소계** | | | | | **약 708,700** | |

### 권장 예비 부품

| 부품 | 단가 | 수량 | 합계 |
|---|---|---|---|
| SHT40 예비 | 7,900 | 2 | 15,800 |
| BH1750 GY-302 예비 | 4,500 | 2 | 9,000 |
| Grove 4핀 케이블 예비 | 5,000 | 1 | 5,000 |
| Grove-점퍼 변환 예비 | 3,500 | 1 | 3,500 |
| 마이크로 USB 케이블 예비 | 1,500 | 3 | 4,500 |
| USB 어댑터 예비 | 3,500 | 2 | 7,000 |
| microSD 예비 | 15,000 | 1 | 15,000 |
| **예비 소계** | | | **약 59,800** |

### 총 예산

| 항목 | 금액 |
|---|---|
| 필수 구매 | 약 708,700 |
| 권장 예비 | 약 59,800 |
| **합계 (필수+예비)** | **약 768,500** |
| 예산 상한 (60만) 대비 | **약 +168,500 초과** ⚠️ |

## 예산 조정 옵션

서버를 Pi 5 16GB로 결정한 시점에 60만 예산은 약 17만 원 초과합니다. 다음 중 하나로 조정합니다.

| 옵션 | 절감액 | 영향 |
|---|---|---|
| **예산 약 77만으로 추가 편성** | 0 | 가장 무난. 16GB의 가치를 1년 안에 회수. |
| **microSD 예비 1개 빼기** | -15,000 | 가장 작은 절감, 무난. |
| USB 어댑터를 멀티포트 충전기로 (예: 6포트 ×3개) | -10,000~20,000 | 콘센트 정리도 됨. |
| Pi 4 4GB로 다운그레이드 | -130,000 | Phase 2/3·분석팀 R&D·로컬 ML 가능성 포기. |
| 예비 부품 절반으로 | -30,000 | 운영 안정성 ↓. |

## 주요 변경 사항

- BH1750 Grove 정식 없음 발견 → **GY-302 모듈 + Grove-점퍼 변환 케이블**로 변경 (펌웨어 영향 없음, I2C 0x23 동일)
- 케이스: 3D 프린팅 (PLA 필라멘트) → **ABS 프로젝트 박스 시판**
- **서버: Raspberry Pi 4 4GB → Raspberry Pi 5 16GB** (+153,000원)
  - 어댑터: 5V/3A → **5V/5A PD 27W**
  - 케이스: 일반 알루미늄 → **액티브 쿨러 포함 케이스**
- 모든 부품 URL 추가

## 발주처별 묶음 (배송비 절감)

| 발주처 | 주문 항목 |
|---|---|
| **디바이스마트** | SHT40, BH1750, Grove 케이블 ×2종, 마이크로 USB, **Pi 5 16GB**, **Pi 5 액티브 쿨러 케이스·27W 어댑터**, microHDMI, ABS 박스 |
| **쿠팡** | USB 5V 어댑터, microSD, 케이블타이·라벨 |

→ 디바이스마트 1회 일괄 주문 + 쿠팡 1회 = 배송비 2회분만.

## Phase 2/3 확장 시 (참고)

| 단계 | 추가 부품 | 16노드 추가 비용 |
|---|---|---|
| Phase 2: CO2 | SCD41 (Grove I2C) | 약 560,000 |
| Phase 2: CO2 (저가) | MH-Z19B (UART) | 약 400,000 |
| Phase 3: 미세먼지 | PMS7003 + SPS30 기준점 2대 | 약 558,000 |
