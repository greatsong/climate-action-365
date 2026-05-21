# 01 — 센서 비교 리서치

작성: 2026-05-21
범위: 16노드 × 4~6종 센서 = 약 64~96개 구매 전제
대상 MCU: Raspberry Pi Pico 2 WH + Grove Shield for Pi Pico (Grove I2C/UART 4구씩)

> ⚠️ **가격 확인 주의**: 본 문서의 한국 쇼핑몰 가격은 검색결과·과거 시세·해외 단가 환산에 근거한 **추정 가격대**이며, WebFetch로 디바이스마트 동적 페이지의 실시간 가격은 직접 추출하지 못했습니다. 구매 전 반드시 디바이스마트/엘레파츠 페이지에서 재확인이 필요합니다. 가격을 확신할 수 없는 행은 `≈` 또는 "확인 필요"로 표기했습니다.

---

## 요약 (3분 안에 읽을 수 있는 결론)

- **온습도**: `SHT40` 1순위. 정확도(±1.8% RH, ±0.2°C)가 DHT20·BME280보다 한 단계 위이고, 교실 환경 모니터링의 "기본 데이터"로 손색이 없습니다. 다만 단가는 DHT20의 약 3~5배. 예산 압박이 크면 차선책 `DHT20`로 내려도 교실 단위 측정에는 무난합니다. `BME280`은 기압이 굳이 필요한 단원이 있을 때만(예: 기상 단원). [Sensirion SHT40](https://sensirion.com/products/catalog/SHT40)
- **조도**: `BH1750` 1순위. 가격이 압도적으로 싸고(모듈당 1,500~3,000원대), 1~65535 lux의 표준 범위와 검증된 MicroPython 라이브러리가 풍부합니다. 교실 조도(보통 300~1000 lux)에서는 BH1750의 정확도로 충분합니다. `VEML7700`은 저조도·고정밀이 필요할 때만 추천.
- **미세먼지**: 1순위는 `SPS30`(I2C/UART, ±10% PM2.5, 자체 청소 알고리즘 내장, 수명 8년 회전 팬), 가성비 1순위는 `PMS7003`(UART, 8000시간 = 약 1년 연속 운전 수명). **교실은 저오염 환경이라 정확도 차이가 크게 벌어집니다 → SPS30 권장**. 다만 SPS30 단가가 PMS7003의 3~4배여서 16노드 전체에 SPS30을 박는 건 부담. **권장: 16노드 모두 PMS7003 + 기준점 검증용 SPS30 1~2대 별도 운영**.
- **CO2**: 1순위 `SCD41`(PASens, 작고 저전력, ±40 ppm + 5%, MicroPython 라이브러리 풍부). `SCD30`은 NDIR 정통파로 더 정확하지만 크고 전류 19 mA로 부담. `MH-Z19B`는 UART 1개를 고정으로 점유해 Grove Shield의 UART 4구 중 1구가 PMS7003과 충돌 가능성이 있으므로 비추.
- **TVOC**: **선택사항이며 1차 BOM에서는 제외 권장**. 교실 IAQ 교육 가치는 "냄새/환기 효과" 시연용 정도이고, eCO2가 SCD41과 중복되며, SGP30/40 모두 수개월~1년 단위로 베이스라인 학습이 필요해 운영 부담이 늘어납니다. 꼭 넣겠다면 `SGP40`(TVOC 인덱스 단일 출력, 10년 공급 보장).

**노드당 센서비 추정(권장 BOM)**: 약 ₩45,000~50,000 (16노드 총 ₩720,000~800,000)

---

## 1. 온습도 센서

### 후보 비교 (표)

| 항목 | DHT20 (AHT20) | SHT40 | BME280 |
|------|---------------|-------|--------|
| 인터페이스 | I2C, 3.3V/5V | I2C, 3.3V (1.08~3.6V) | I2C/SPI, 3.3V |
| 정확도 (RH) | ±3% RH | **±1.8% RH (max 3.5%)** | ±3% RH (드리프트 큼) |
| 정확도 (T) | ±0.5°C | **±0.2°C** | ±1°C |
| 부가 측정 | 없음 | 없음 | **기압 300~1100 hPa (±1 hPa)** |
| 한국 가격 (1개) | ≈ ₩3,000~4,000 (디바이스마트, [ada-5183 페이지](https://www.devicemart.co.kr/goods/view?no=14600420)) | ≈ ₩9,000~13,000 (브레이크아웃, 한국 가격 확인 필요. DigiKey 단품 $2.58, Adafruit STEMMA QT $8.16) | ≈ ₩4,000~7,000 (GY-BME280, [디바이스마트](https://www.devicemart.co.kr/goods/view?no=12733519)) |
| Grove 호환 | 비공식 (I2C라 Grove-점퍼 변환 가능) | **공식 Grove 모듈 존재** ([Seeed 101020891](https://www.seeedstudio.com/Grove-Temp-Humi-Sensor-SHT40-p-5384.html), ~$11) | Crowtail/Grove 변형 모듈 존재 ([디바이스마트 CT010928S](https://www.devicemart.co.kr/goods/view?no=12147816)) |
| MicroPython 라이브러리 | 다수, AHT20 호환 (예: `pimoroni-pico`, `aht10/aht20.py`) | 다수, 공식 Sensirion + 커뮤니티 (예: `adafruit_sht4x` 포팅) | 매우 풍부, 표준 라이브러리 수준 |
| 수명 | 반영구 (CMOS) | 반영구 (CMOSens) | 반영구 (장기 드리프트 ±1% RH/년 보고) |
| 보정 | 공장 보정, 사용자 보정 불필요 | 공장 보정 (캘리브레이션 인증서) | 공장 보정, 다만 장기 드리프트 보고 사례 다수 |
| 단점 | 정확도 평범, DHT22 대비 큰 개선은 없음 | 가격, 외관에 핀헤더 없어서 브레이크아웃 선택 중요 | 습도 100% 포화 보고 등 신뢰성 이슈 보고(Medium 비교 글), 기압 필요 없으면 과한 스펙 |

### 추천: SHT40

근거:
1. 본 프로젝트는 "데이터 리터러시" 교육이 목표 — 노드 간 데이터를 비교하려면 정확도가 균일해야 합니다. SHT40의 ±1.8% RH는 교실 비교에서 의미 있는 차이를 만들 수 있는 수준.
2. Sensirion CMOSens 계열은 장기 드리프트가 적어 16노드를 3~5년 운영하기에 가장 안전.
3. Seeed 공식 Grove SHT40 모듈이 있어 Grove Shield와 케이블 1개로 즉시 연결 가능.

출처: [Sensirion SHT40 datasheet](https://sensirion.com/products/catalog/SHT40), [Grove SHT40](https://www.seeedstudio.com/Grove-Temp-Humi-Sensor-SHT40-p-5384.html), [Medium I2C 센서 비교](https://medium.com/@jj.underwood/comparing-i2c-sensors-e451c4a447ab)

### 차선: DHT20

- 단가가 SHT40의 1/3 수준. 16노드 전체 차이가 약 ₩100,000 차이 — 절감 효과 있음.
- AHT20 코어라 MicroPython 코드도 짧고 학생이 읽기 쉬움 (교육적 장점).
- 단, 정확도 ±3%는 노드 간 비교 단원에서 "노이즈"로 보일 수 있음.

### 비추: BME280 (단독 채택)

- 기압이 본 프로젝트의 교육 시나리오(실내 환경, AI 데이터셋 구축)와 직접 연결되지 않음.
- 습도 신뢰성 이슈 사례가 보고됨 ([포럼](https://forum.allaboutcircuits.com/threads/what-is-best-overall-humidity-temperature-sensor-for-indoors-outdoors-use.194083/)).
- 기상 단원 확장 시 1~2노드에 옵션으로 추가하는 정도면 충분.

---

## 2. 조도 센서

### 후보 비교 (표)

| 항목 | BH1750 | VEML7700 |
|------|--------|----------|
| 인터페이스 | I2C, 3.3V/5V | I2C, 3.3V/5V |
| 측정 범위 | 1 ~ 65,535 lux (16-bit) | 0 ~ 120,000 lux, 해상도 0.0036 lx/ct (저조도에서 압도) |
| 정확도 | ±20% (일반적인 lux 정확도), 채널 1개 | 고정밀, 가변 게인/적분시간 |
| 한국 가격 (1개) | ≈ ₩1,500~3,500 ([디바이스마트 GY-302](https://www.devicemart.co.kr/goods/view?no=1289977), [SEN340207](https://www.devicemart.co.kr/goods/view?no=10825464)) | ≈ ₩6,000~10,000 (Adafruit 브레이크아웃 $5~7 + 환율) |
| Grove 호환 | Grove 모듈 존재 (Seeed 비공식·서드파티 다수) | Adafruit STEMMA QT/Qwiic — 별도 Grove-Qwiic 어댑터 필요 |
| MicroPython 라이브러리 | [`micropython-bh1750`](https://github.com/PinkInk/upylib/tree/master/bh1750) 등 매우 풍부, 표준 수준 | `adafruit_veml7700` CircuitPython 포트 |
| 수명 | 반영구 | 반영구 |
| 보정 | 공장 보정 | 공장 보정 |
| 단점 | 조도 약 65,535 lux에서 포화 (직사광 영역) — 교실은 무관 | 단가, 라이브러리 선택지가 BH1750보다 적음 |

### 추천: BH1750

근거:
1. 교실 조도는 보통 300~1500 lux 범위, BH1750의 1~65535 lux로 충분.
2. 학생용 코드 작성 시 라이브러리 한 줄로 끝남 → 교육 친화적.
3. 가격이 VEML7700의 1/3~1/4. 16노드에 박아도 부담 없음.

출처: [디바이스마트 BH1750 GY-302](https://www.devicemart.co.kr/goods/view?no=1289977), [eduino BH1750](https://eduino.kr/product/detail.html?product_no=581)

### 차선: VEML7700 (저조도 단원 추가 시)

- "암실 실험", "야간 조도" 같은 단원을 넣으면 VEML7700이 우월.
- 16노드 중 1~2개에만 박는 옵션도 검토 가능.

---

## 3. 미세먼지 센서 ⭐ (가장 중요)

### 후보 비교 (표)

| 항목 | PMS7003 | SPS30 | PMSA003I |
|------|---------|-------|----------|
| 인터페이스 | UART 3.3V, 구동 5V | **I2C 또는 UART**, 5V | **I2C**, 5V (5V boost on 3.3V) |
| 측정 항목 | PM1.0 / PM2.5 / PM10 | PM1.0 / 2.5 / 4 / 10 + 입경 분포 + 평균입경 | PM1.0 / 2.5 / 10 + 입자 카운트 0.3~10μm |
| 정확도 (PM2.5) | ±10 µg/m³ (0~100), ±10% (100~500); 실내 저농도에서 부정확하다는 다수 보고 | **±10% (전 범위), MCERTS 인증** — 저농도 정확도 우수 | PMS5003/7003과 동일 코어 (Plantower) → PMS7003급 |
| 한국 가격 (1개) | **≈ ₩30,000~40,000** ([디바이스마트 PLANTOWER](https://www.devicemart.co.kr/goods/view?no=10917688)) | **≈ ₩50,000~65,000** ([DigiKey KR ₩52,571](https://www.digikey.kr/ko/products/detail/sensirion-ag/SPS30/9598990)) | ≈ ₩40,000~55,000 ([Adafruit $44.95](https://www.adafruit.com/product/4632)) |
| Grove 호환 | Grove 어댑터 케이블 없음 (별도 케이블/점퍼) | Grove 어댑터 없음; **공식 Sensirion 5핀 ZH 1.5mm 케이블** | **STEMMA QT/Qwiic → Grove-Qwiic 어댑터로 I2C Grove에 직결 가능** |
| MicroPython 라이브러리 | [`pkucmus/micropython-pms7003`](https://github.com/pkucmus/micropython-pms7003) (검증됨, UART 필요) | 비공식 다수, Sensirion 공식 Python(라즈베리파이용)은 포팅 필요 | `adafruit_pm25` MicroPython 포팅 (I2C — Pico에서 가장 쉬움) |
| 수명 | **레이저 다이오드 약 8,000시간** (≈ 1년 연속) — [aqicn.org 실험](https://aqicn.org/sensor/pms5003-7003/) | **8년** (Sensirion 공식 사양, 자체 청소 알고리즘) | PMS7003과 동일 (8,000시간) |
| 보정 | 공장 보정, 사용자 보정 불가 (오프셋만 가능) | 공장 보정 + 자체 fan auto-clean 매주 | 공장 보정 |
| 단점 | 저농도(<50 µg/m³)에서 평균화 심함, 노이즈, 60초 측정주기 권장 | 가격, 큰 사이즈 | I2C라 편리하지만 Plantower 코어 → 저농도 정확도는 PMS7003과 동일한 한계 |

### 추천 (혼합 전략): PMS7003 × 16노드 + SPS30 × 1~2대 (기준점)

근거:
1. **저오염 교실에서 PM2.5는 보통 5~30 µg/m³**. 이 영역은 Plantower 계열의 약점 — 그러나 본 프로젝트의 핵심은 "교실 간 비교"와 "환기 전후 변화" → 절대값보다 상대값과 시간 변화가 더 중요. PMS7003도 시간변화 추적에는 충분.
2. SPS30을 1~2대 두면 "교사실에서 보정용 기준 측정" 단원을 만들 수 있음 — AI 데이터 단원에서 "어느 센서가 옳을까?" 토론 소재.
3. PMS7003은 UART라 Grove Shield의 UART 슬롯 1개를 점유. SCD41(I2C)과 충돌 없음. Pico 2의 UART는 2개라 여유 있음.
4. **수명 이슈 필수 안내**: 30~60초 측정주기 + 측정 사이 sleep 명령으로 팬·레이저를 끄면 8000시간 → 3~5년으로 늘릴 수 있음 ([AirGradient 포럼](https://forum.airgradient.com/t/extending-the-life-span-of-the-pms5003-sensor/114)).

### 대안: PMSA003I × 16노드 (Grove I2C 완전 통합 우선)

- 모든 센서를 I2C로 통일하면 학생 코드가 간결해짐 (UART 설정 단원 생략 가능).
- 단가가 PMS7003보다 1.5배 정도 높지만, 케이블·배선 단원의 수고를 줄일 가치가 있음.
- **검증 필요**: 한국 총판 정식 유통이 약함 — Adafruit 직수입(통관·환율) 부담 있음.

출처: [SPS30 vs PMS7003 정확도 비교 (ResearchGate)](https://www.researchgate.net/publication/396780261), [Plantower 8000시간 수명](https://aqicn.org/sensor/pms5003-7003/), [PMSA003I Adafruit Learn](https://learn.adafruit.com/pmsa003i)

---

## 4. CO2 센서

### NDIR vs PASens (간단 설명)

- **NDIR (Non-Dispersive Infrared)**: 가스 셀에 IR 광을 통과시키고 흡수되지 않은 양을 검출. SCD30, MH-Z19B가 대표. **장점**: 검증된 방식, 정확도 안정. **단점**: 크고 전류가 큼.
- **PASens (Photoacoustic Sensing)**: IR로 가스를 펄스 가열 → 압력파(소리) → 마이크로폰 검출. SCD40/41이 채택. **장점**: 작은 크기(2.4×2.9 mm), 저전력(평균 <0.4 mA), 응답 빠름. **단점**: 외부 진동/소음 환경에서 영향 가능.

### 후보 비교 (표)

| 항목 | SCD30 | SCD41 | MH-Z19B |
|------|-------|-------|---------|
| 인터페이스 | I2C, 3.3V/5V | I2C, 3.3V | **UART**, 5V (PWM 가능) |
| 방식 | NDIR | PASens (PA-NDIR) | NDIR |
| 측정 범위 | 400 ~ 10,000 ppm | 400 ~ 5,000 ppm | 0 ~ 5,000 ppm |
| 정확도 | **±(30 ppm + 3%)** — 최고 | ±(40 ppm + 5%) | ±(50 ppm + 5%) |
| 부가 측정 | T/RH 내장 | T/RH 내장 | 없음 |
| 전류 | ≈ 19 mA (높음) | **평균 <0.4 mA** | ≈ 18 mA |
| 한국 가격 (1개) | ≈ ₩60,000~75,000 (Grove SCD30 [디바이스마트 101020634](https://www.devicemart.co.kr/goods/view?no=10918824)) | ≈ ₩55,000~70,000 (Grove SCD41 모듈) | **≈ ₩30,000~35,000** ([디바이스마트 13194967](https://www.devicemart.co.kr/goods/view?no=13194967), [Interpark ₩31,830](http://m.shop.interpark.com/product/6791634111/0000100000)) |
| Grove 호환 | **공식 Grove 모듈** ([Seeed 101020634](https://wiki.seeedstudio.com/Grove-CO2_Temperature_Humidity_Sensor-SCD30/)) | **공식 Grove 모듈** ([Seeed 101020952](https://wiki.seeedstudio.com/Grove-CO2_&_Temperature_&_Humidity_Sensor-SCD41/)) | Grove 없음, UART 4핀 점퍼 |
| MicroPython 라이브러리 | 다수 (`scd30` PyPI 포팅), Pimoroni 지원 | [`mikan/rpi-pico-scd4x`](https://github.com/mikan/rpi-pico-scd4x), Pimoroni 공식 지원, Adafruit 포팅 | UART 직접 파싱 (간단), 라이브러리도 있음 |
| 수명 | 15년 (Sensirion 공식) | 10년+ | 5년 (Winsen 공식) |
| 보정 | ABC 7일 또는 수동 FRC | ABC 7일 또는 수동 FRC | ABC 7일 또는 수동 |
| 단점 | 크고 전류 큼, Grove 모듈 단가 높음 | PA 원리상 외부 소음에 민감하다는 보고 (실측 영향은 미미) | UART 슬롯 점유, T/RH 없음, 정확도 한 단계 낮음 |

### 추천: SCD41 (Grove 모듈)

근거:
1. **저전력**: 16노드 × USB 5V 상시구동이라 전류는 큰 이슈는 아니지만, Pico+Grove Shield의 5V 라인 부담을 줄임.
2. **I2C 통일**: PMS7003만 UART를 쓰고 나머지를 모두 I2C로 묶을 수 있음 → 학생 코드가 통일됨.
3. **T/RH 내장**: SHT40과 일부 중복되지만 SCD41의 T/RH는 CO2 보정용 — SHT40과 비교 단원도 가능 ("같은 교실의 두 센서 차이").
4. **MicroPython 지원 풍부**: Pimoroni, Adafruit, `mikan/rpi-pico-scd4x` 모두 RP2040 검증.

### ABC 보정 — 교실에서의 주의사항

ABC는 7일 이내에 한 번이라도 외기 수준(~400 ppm)에 노출되어야 정상 작동. **교실은 주말 환기에 의존하거나, 학기 중 항상 사람이 있어 400 ppm까지 안 떨어질 수 있음** → ABC가 잘못된 베이스라인을 학습할 수 있음. 권장:
- 학기 시작 시 외기에서 수동 FRC 보정 1회 (학생 활동으로도 가능)
- ABC는 유지하되, 주말/방학에 창문 개방 정책으로 강제 환기

출처: [SCD30 ABC field calibration PDF](https://sensirion.com/media/documents/33C09C07/620638B8/Sensirion_SCD30_Field_Calibration.pdf), [SCD30 vs SCD40/41 비교 (eMariete)](https://emariete.com/en/sensor-co2-sensirion-scd40-scd41/)

### 차선: SCD30

- 정확도 ±(30 ppm + 3%)가 매력적, 교육적으로 "정통 NDIR" 설명에 좋음.
- 모듈이 크고 단가가 SCD41과 비슷하거나 약간 비쌈 → 단가 차이가 작다면 정확도 우선으로 SCD30 선택도 가능.

### 비추: MH-Z19B

- 가격이 매력적이지만 T/RH가 없어 SHT40과 별도 보정 부담.
- UART 점유 — PMS7003과 함께 쓰면 UART 2개 모두 점유, Pico 2 여유 없음.

---

## 5. TVOC 센서

### 후보 비교 (표)

| 항목 | SGP30 | SGP40 |
|------|-------|-------|
| 인터페이스 | I2C, 1.62~1.98V (보드 레귤레이터로 3.3V) | I2C, 1.7~3.6V |
| 출력 | TVOC (ppb) + eCO2 (ppm, 계산값) | **VOC 인덱스 (1~500, 100=일반)** — Sensirion 가스 인덱스 알고리즘 필요 |
| 정확도 | TVOC: 정확도 미공개, 트렌드용; eCO2는 NDIR 대비 부정확 | TVOC 인덱스 (절대값 아님) |
| 한국 가격 (1개) | ≈ ₩15,000~25,000 (Grove SGP30) | ≈ ₩15,000~25,000 (Grove SGP40/41) |
| Grove 호환 | Grove 모듈 있음 (Seeed SGP30, 일부 단종 진행) | **Grove SGP41 권장** (SGP40 후속) |
| MicroPython 라이브러리 | [`alexmrqt/micropython-sgp30`](https://github.com/alexmrqt/micropython-sgp30), [`fantasticdonkey/uSGP30`](https://github.com/fantasticdonkey/uSGP30) | DFRobot/Sparkfun Python 포팅 필요 |
| 수명 | 10년 (Sensirion 공급 보장) | **10년 (Sensirion 공식 공급 계획)** |
| 보정 | **초기 12시간 베이스라인 학습 필요**, 베이스라인 NVRAM 저장 권장 | 자체 학습, 24시간~14일 학습 권장 |
| 단점 | eCO2 부정확 (TVOC에서 추정), 초기 학습 시간 부담 | 절대값 아님 — "상대 인덱스"만 — 교육적 해석이 어려움 |

### TVOC 포함 여부에 대한 판단

**1차 BOM에서는 제외 권장.** 이유:

1. **교육적 가치 모호**: TVOC는 "총 VOC"라 어떤 가스인지 특정 불가. 학생이 데이터로 추론할 수 있는 게 "냄새가 났을 때 올라간다" 정도 → 흥미는 있지만 데이터 리터러시 단원으로 발전시키기 어려움.
2. **CO2와 중복**: 환기 효과는 CO2가 더 명확하게 보여줌. TVOC 추가는 변수만 늘림.
3. **운영 부담**: 12시간~14일 베이스라인 학습 + 베이스라인 NVRAM 저장 코드 — Pico의 flash에 저장 가능하지만 학생 코드가 복잡해짐.
4. **예산**: 16노드 × ₩20,000 = ₩320,000 추가 — SHT40 업그레이드와 비슷한 비용.

**그래도 넣겠다면**: SGP40 (Grove SGP41 보드 사용). 인덱스 단일 출력이라 "환기 시 인덱스 변화"를 시각화하기 쉽고, Sensirion 10년 공급 보장이라 장기 운영 안정.

출처: [SGP30 12h 베이스라인 학습 안내](https://learn.adafruit.com/adafruit-sgp30-gas-tvoc-eco2-mox-sensor/circuitpython-wiring-test), [SGP40 DFRobot wiki](https://wiki.dfrobot.com/SGP40_Air_Quality_Sensor_SKU_SEN0392)

---

## 최종 권장 BOM (16노드 기준)

기본형 (각 노드: 온습도 + 조도 + 미세먼지 + CO2 = 4종)

| 항목 | 추천 모델 | 인터페이스 | 단가 (추정) | 16노드 합계 |
|------|----------|-----------|-------------|-------------|
| 온습도 | SHT40 (Grove) | I2C | ₩11,000 | ₩176,000 |
| 조도 | BH1750 (모듈) | I2C | ₩2,500 | ₩40,000 |
| 미세먼지 | PMS7003 | UART | ₩35,000 | ₩560,000 |
| CO2 | SCD41 (Grove) | I2C | ₩60,000 | ₩960,000 |
| **노드당 센서비** | | | **≈ ₩108,500** | |
| **16노드 센서 총액** | | | | **≈ ₩1,736,000** |
| 기준점 검증용 | SPS30 × 1~2대 | I2C/UART | ₩55,000 | ₩55,000~110,000 |
| **총계 (보정용 포함)** | | | | **≈ ₩1,790,000~1,850,000** |

비용 절감안 (SHT40 → DHT20, SCD41 → MH-Z19B):

| 항목 | 모델 | 단가 | 16노드 합계 |
|------|------|------|-------------|
| 온습도 | DHT20 | ₩3,500 | ₩56,000 |
| 조도 | BH1750 | ₩2,500 | ₩40,000 |
| 미세먼지 | PMS7003 | ₩35,000 | ₩560,000 |
| CO2 | MH-Z19B | ₩32,000 | ₩512,000 |
| **노드당** | | **≈ ₩73,000** | |
| **16노드 합계** | | | **≈ ₩1,168,000** |

차이는 약 ₩620,000 — 정확도와 I2C 통일성을 살 만한 가치가 있다고 판단됨 (기본형 권장).

TVOC 옵션 추가 시: +₩320,000 (SGP40 × 16)

---

## 미해결 질문 / 사용자 확인 필요

1. **TVOC 포함 여부?** — 현재 권장은 "제외". 교육적 가치를 명확히 정의한 단원이 있다면 SGP40 추가 검토.
2. **미세먼지 센서 수명 3년 후 교체 예산 반영?** — PMS7003은 8000시간 권장 수명. 30초 간격 + 측정 사이 sleep 코드를 기본 골격에 넣을 것인지, 아니면 상시 가동 후 3년 교체 정책으로 갈 것인지.
3. **Grove 호환 미세먼지 센서가 없으면 어떻게 배선?** — PMS7003은 8핀 1.25mm 커넥터, Grove Shield의 UART는 4핀 2.0mm. **별도 점퍼 케이블 또는 자작 어댑터 필요**. 16노드 × 어댑터 비용 별도 산정.
4. **SPS30 기준점 1대 vs 2대?** — 본관/별관 각 1대씩 둘 것인지, 1대만으로 충분한지.
5. **PMSA003I (I2C 미세먼지)로 통일하면?** — 단가 +₩80,000~150,000 (16노드)로 모든 센서를 I2C로 통일 가능. 학생 코드 단순화 vs 비용 트레이드오프 결정 필요.
6. **디바이스마트 실시간 가격 재확인 필요** — 본 문서의 가격은 추정·과거 시세 기반. 발주 직전 모든 모델 가격을 디바이스마트/엘레파츠에서 직접 확인 권장.
7. **외부 기상 비교용 노드 (BME280)?** — 학교 옥상에 기압·실외 기온 측정 노드를 1대 두면 "실내-실외 비교" 단원이 가능. BME280 1대 추가 검토.
8. **케이블 길이·확장**: Grove 케이블은 보통 20~50cm. 교실 천장/벽 설치 시 1m 이상 필요할 수 있음 — Grove 1m 케이블 별도 발주 필요.

---

## 출처

### 온습도
- [Sensirion SHT40 공식](https://sensirion.com/products/catalog/SHT40)
- [Grove SHT40 Seeed Wiki](https://wiki.seeedstudio.com/K1100-Temp-Humi-Sensor-Grove-LoRa-E5/)
- [DHT20 디바이스마트 페이지](https://www.devicemart.co.kr/goods/view?no=14600420)
- [GY-BME280 디바이스마트](https://www.devicemart.co.kr/goods/view?no=12733519)
- [Medium: I2C 센서 비교 (AHT21, SHT35, SHT41, BME280)](https://medium.com/@jj.underwood/comparing-i2c-sensors-e451c4a447ab)
- [SHT31 vs DHT22 vs BME280 (Zbotic)](https://zbotic.in/sht31-vs-dht22-vs-bme280-best-humidity-sensor-for-your-project/)

### 조도
- [BH1750 GY-302 디바이스마트](https://www.devicemart.co.kr/goods/view?no=1289977)
- [BH1750 SEN340207 디바이스마트](https://www.devicemart.co.kr/goods/view?no=10825464)
- [Adafruit VEML7700](https://learn.adafruit.com/adafruit-veml7700/overview)
- [eduino BH1750 모듈](https://eduino.kr/product/detail.html?product_no=581)

### 미세먼지
- [PLANTOWER PMS7003 디바이스마트](https://www.devicemart.co.kr/goods/view?no=10917688)
- [DigiKey KR SPS30 ₩52,571](https://www.digikey.kr/ko/products/detail/sensirion-ag/SPS30/9598990)
- [Sensirion SPS30 공식](https://sensirion.com/products/catalog/SPS30)
- [Adafruit PMSA003I (I2C)](https://www.adafruit.com/product/4632)
- [PMSA003I Adafruit Learn](https://learn.adafruit.com/pmsa003i)
- [PMS7003 vs SPS30 정확도 (ResearchGate)](https://www.researchgate.net/publication/396780261)
- [Plantower 8000시간 수명 (aqicn.org)](https://aqicn.org/sensor/pms5003-7003/)
- [AirGradient PMS 수명 연장 방법](https://forum.airgradient.com/t/extending-the-life-span-of-the-pms5003-sensor/114)
- [pkucmus/micropython-pms7003](https://github.com/pkucmus/micropython-pms7003)
- [Low-cost PM 센서 비교 (ScienceDirect)](https://www.sciencedirect.com/science/article/abs/pii/S0021850221005607)

### CO2
- [Sensirion SCD30 공식](https://sensirion.com/products/catalog/SCD30)
- [Sensirion SCD41 공식](https://sensirion.com/products/catalog/SCD41)
- [SCD30/40/41 비교 (eMariete)](https://emariete.com/en/sensor-co2-sensirion-scd40-scd41/)
- [SCD30 Field Calibration PDF](https://sensirion.com/media/documents/33C09C07/620638B8/Sensirion_SCD30_Field_Calibration.pdf)
- [SCD30/SCD4x 비교 (Data-Driven Engineering)](https://apmonitor.com/dde/index.php/Main/CO2Sensor)
- [SCD40 PASens 소개 (Sensirion)](https://sensirion.com/products/product-insights/specialist-articles/breaking-the-size-barrier-in-co2-sensing)
- [PAS vs NDIR vs TVOC (SparkFun)](https://news.sparkfun.com/8952)
- [Grove SCD30 디바이스마트](https://www.devicemart.co.kr/goods/view?no=10918824)
- [Grove SCD41 Wiki](https://wiki.seeedstudio.com/Grove-CO2_&_Temperature_&_Humidity_Sensor-SCD41/)
- [MH-Z19B 디바이스마트](https://www.devicemart.co.kr/goods/view?no=13194967)
- [MH-Z19B 엘레파츠](https://eleparts.co.kr/goods/view?no=3175853)
- [mikan/rpi-pico-scd4x (MicroPython)](https://github.com/mikan/rpi-pico-scd4x)
- [Pimoroni Pico SCD41 예제](https://github.com/pimoroni/pimoroni-pico/blob/main/micropython/examples/breakout_scd41/scd41_demo.py)
- [ChronSyn rpi-picow-scd41-env-monitor](https://github.com/ChronSyn/rpi-picow-scd41-env-monitor)

### TVOC
- [Sensirion SGP30](https://sensirion.com/products/catalog/SGP30)
- [Sensirion SGP40](https://sensirion.com/products/catalog/SGP40)
- [Adafruit SGP30 Python Library](https://learn.adafruit.com/adafruit-sgp30-gas-tvoc-eco2-mox-sensor/circuitpython-wiring-test)
- [alexmrqt/micropython-sgp30](https://github.com/alexmrqt/micropython-sgp30)
- [fantasticdonkey/uSGP30](https://github.com/fantasticdonkey/uSGP30)
- [SGP40 DFRobot wiki](https://wiki.dfrobot.com/SGP40_Air_Quality_Sensor_SKU_SEN0392)

### 한국 총판/리테일
- [디바이스마트](https://www.devicemart.co.kr/)
- [엘레파츠 Sensirion 카테고리](https://www.eleparts.co.kr/goods/brand?cate_code=00170031&brand_code=0212)
- [가치창조기술 vctec](https://vctec.co.kr/)

### 일반
- [Sensirion Partner Spotlight: Seeed Studio](https://developer.sensirion.com/partner-spotlight-overview/seeed-studio)
- [Then Try This: 저비용 공기질 센서 노트](https://thentrythis.org/notes/2021/09/17/notes-on-sensor-components-for-a-low-cost-air-quality-monitoring-device/)
- [AirGradient: PM 센서 선택 기준](https://www.airgradient.com/blog/choosing-the-airgradient-go-pm-sensor)
