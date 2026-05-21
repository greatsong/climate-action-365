# 서버 업그레이드: Raspberry Pi 5 16GB

작성: 2026-05-21
변경: 서버를 **Raspberry Pi 4 (4GB)** → **Raspberry Pi 5 (16GB)** 로 교체

> 이 문서는 BOM.md·Unit 2 본문은 **그대로 두고**, Pi 5 16GB로 갈 때 달라지는 부분만 별도로 정리합니다. Pi 4 기준 셋업 흐름(SETUP-02 / Unit 2)은 거의 그대로 적용되고, 부품·전원·쿨링·일부 명령만 다릅니다.

## 1. 왜 Pi 5 16GB인가

Phase 1(온습도+조도)에서 Pi 5 16GB는 **남는 자원**입니다. 그러나 다음 시나리오를 1~3년 안에 모두 굴리려면 16GB가 합리적입니다.

| 시나리오 | 예상 메모리 | Pi 4 4GB | Pi 5 16GB |
|---|---|---|---|
| Phase 1 (FastAPI + SQLite + Streamlit) | < 1 GB | 여유 | 여유 |
| Phase 2 (CO2 추가, 동일 인프라) | < 1 GB | 여유 | 여유 |
| Phase 3 (미세먼지 추가) | < 1.5 GB | 여유 | 여유 |
| InfluxDB 2.x + Grafana 함께 운영 | 2~3 GB | 빡빡함 | 여유 |
| 분석팀 Jupyter + Pandas 대용량 데이터 | 2~6 GB | 부족 | 여유 |
| 로컬 ML 추론(scikit-learn·작은 LLM) | 4~10 GB | 불가 | 여유 |
| 학생용 Jupyter 다중 동시접속(5~10명) | 4~8 GB | 부족 | 여유 |

결론: Phase 1만 보면 과투자지만, 2~3학년 분석·R&D 트랙·다음 세대 인계까지 보면 **‘한 번 사고 잊는’ 결정**이 됩니다.

## 2. Pi 4 vs Pi 5 핵심 비교

| 항목 | Pi 4 (4GB) | **Pi 5 (16GB)** |
|---|---|---|
| CPU | BCM2711 · Cortex-A72 @ 1.5 GHz × 4 | **BCM2712 · Cortex-A76 @ 2.4 GHz × 4** |
| 단일코어 성능 | 기준 | **약 2~3배** |
| RAM | 4 GB LPDDR4 | **16 GB LPDDR4X-4267** |
| 전원 입력 | 5V/3A USB-C | **5V/5A USB-C PD (27W)** |
| HDMI | micro HDMI × 2 (4K@60) | 동일 |
| USB | USB 3.0 × 2 + USB 2.0 × 2 | 동일 |
| Ethernet | Gigabit | Gigabit (PoE+ HAT 가능) |
| PCIe | 없음 | **PCIe 2.0 × 1 레인 (NVMe HAT)** |
| 쿨링 | 패시브로도 운영 가능 | **액티브 쿨러 필수 권장** |
| WiFi/BT | Dual-band 802.11ac / BT 5.0 | 동일 |
| 디바이스마트 | 약 100,000원 (4GB 기준) | 약 200,000~250,000원 (16GB · [상품 페이지](https://www.devicemart.co.kr/goods/view?no=15666226)) |

> 단일 코어 성능이 2~3배 빨라진 점이 FastAPI 응답 지연·SQLite write·Grafana 그래프 렌더링 전부에 직접 효과를 냅니다.

## 3. 변경된 BOM (서버 부분만)

| 부품 | Pi 4 안 | **Pi 5 16GB 안** | 변동 |
|---|---|---|---|
| 본체 | Pi 4 4GB ≈ 100,000원 | **Pi 5 16GB ≈ 230,000원** | **+130,000** |
| microSD 64GB 산업용 | 15,000원 | 동일 | — |
| 전원 어댑터 | 5V/3A USB-C ≈ 10,000원 | **공식 5V/5A USB-C PD 27W ≈ 18,000원** | **+8,000** |
| 케이스 | 일반 알루미늄 10,000원 | **액티브 쿨러 포함 케이스 ≈ 25,000원** (예: Argon NEO 5 또는 공식 Active Cooler + 알루미늄 케이스) | **+15,000** |
| Micro HDMI 케이블 | 6,000원 | 동일 | — |
| **서버 소계** | 약 141,000원 | **약 296,000원** | **+155,000** |

> 어댑터·케이스·쿨러는 Pi 5 전용 제품을 써야 합니다. Pi 4 액세서리를 그대로 끼우면 발열·전압 부족 문제가 일어납니다.

### 발주 링크 (디바이스마트 후보)

- 본체: [라즈베리파이5 16GB + PDF 가이드북](https://www.devicemart.co.kr/goods/view?no=15666226)
- 전원: [디바이스마트 ‘라즈베리파이5 어댑터 27W’ 검색](https://www.devicemart.co.kr/goods/search?keyword=%EB%9D%BC%EC%A6%88%EB%B2%A0%EB%A6%AC%ED%8C%8C%EC%9D%B45+27W+%EC%96%B4%EB%8C%91%ED%84%B0)
- 쿨러: [공식 Raspberry Pi Active Cooler 검색](https://www.devicemart.co.kr/goods/search?keyword=Raspberry+Pi+Active+Cooler)
- 케이스: [Argon NEO 5 검색](https://www.devicemart.co.kr/goods/search?keyword=Argon+NEO+5)

## 4. 예산 영향

기존 60만 예산(Pi 4 기준)에서 **약 15만 원 추가** → 총 약 73만 원.

조정 옵션:
- microSD 예비 1개 빼기: −15,000
- USB 어댑터 멀티포트 묶음 구매: −10,000~20,000
- ABS 박스 단가 절감(3,500 → 2,500): −16,000

위 세 가지 조합으로 다시 60만 원선에 맞출 수 있으나, **15만 원 정도는 그대로 추가 편성하는 편**이 운영 부담이 가장 적습니다. Pi 4 → Pi 5 교체는 ‘1년 안에 후회하지 않는 결정’입니다.

## 5. 셋업 시 달라지는 부분 (Unit 2 / SETUP-02 대비)

### 5.1 OS 설치 — **동일**

Raspberry Pi Imager에서 ‘Raspberry Pi 5’를 디바이스로 선택하는 것만 다르고, 나머지 사전 설정(Hostname·SSH·시간대·WiFi)은 같습니다. OS는 `Raspberry Pi OS Lite (64-bit)`.

### 5.2 첫 부팅 시 BIOS/Bootloader

Pi 5는 EEPROM 부트로더가 최신이어야 NVMe·5A 전원을 정상 인식합니다. 처음 부팅한 뒤 한 번 실행:

```bash
sudo rpi-eeprom-update -a
sudo reboot
```

### 5.3 전원 메시지

Pi 5는 5A 전원이 아닐 때 부팅 직후 다음 같은 경고를 셸에 띄웁니다.

```
This power supply is not capable of supplying 5A; power to peripherals will be restricted.
```

→ 27W 정품 어댑터를 쓰면 사라집니다. 학교 콘센트에 5V/3A 어댑터를 잘못 꽂으면 USB 포트 전류가 제한되어 외장 USB·키보드가 인식 안 될 수 있습니다.

### 5.4 쿨링 확인

```bash
vcgencmd measure_temp
```

- 평상시 50°C 이하면 정상
- 80°C 넘어가면 쿨링 부족 → 액티브 쿨러 동작 확인 (팬 회전음, 케이스 통풍)

### 5.5 (선택) NVMe로 microSD 대체

Pi 5에는 PCIe 슬롯이 있어 NVMe HAT으로 SSD 부팅이 가능합니다. 24/7 쓰기·읽기 안정성이 microSD보다 압도적입니다.

- HAT: Pimoroni NVMe Base / Pineberry HatDrive 등 (디바이스마트·메카솔루션 검색)
- SSD: M.2 2230/2242 NVMe 256GB~1TB
- 추가 예산: 약 5만 ~ 10만 원

권장 — Phase 1에서는 microSD로 시작하고, Phase 2/3로 갈 때 NVMe 도입.

### 5.6 systemd·cron 설정 — **동일**

Unit 2의 `climate365.service`, `climate365-dashboard.service`, cron 백업 작업은 OS 위에서 돌기 때문에 Pi 4·Pi 5 동일하게 작동합니다.

### 5.7 고정 IP — **동일**

`nmcli con mod` 명령은 Pi 4·5 동일.

## 6. 운영 단계에서 16GB가 직접 이득을 보는 순간

1. **분석팀이 Pandas로 1년치 데이터(약 3.3GB)를 통째로 메모리에 올릴 수 있음** → 그룹화·시각화가 즉시.
2. **Streamlit + Grafana + Jupyter 동시 가동** — 학생 5명이 동시에 다른 화면을 열어도 끊김 없음.
3. **간단한 머신러닝 모델 학습** — Pi 안에서 scikit-learn으로 ‘교실별 환기 패턴 분류’ 같은 학기말 R&D 가능.
4. **로컬 LLM 추론(2~7B 양자화)** — 작은 모델을 Pi 5에 띄워 ‘오늘의 환경 보고서 자동 초안 생성’도 가능. 다만 추론 속도는 GPU 없이 토큰/초 1~3 수준.

## 7. Unit 2 본문 갱신 여부

이번 변경은 **별도 문서로만 두고 Unit 2 본문은 Pi 4 기준 그대로** 유지합니다. 이유:

- Unit 2는 학생이 보는 표준 절차로, 모든 학교가 Pi 5 16GB를 살 수 있는 것은 아닙니다.
- Pi 4와 Pi 5의 차이는 ‘전원·쿨러·BIOS 업데이트 1회’에 집중되어 있고, 이 문서가 그것을 별도로 안내합니다.
- 우리 학교에서 작업하는 학생에게는 이 문서와 Unit 2를 함께 읽으면 됩니다.

다른 학교가 이 시스템을 그대로 빌려갈 때 Pi 4·5 중 어느 쪽으로 시작할지 결정할 수 있도록 두 문서를 **별도**로 두는 것이 본 프로젝트의 ‘선도 사례’ 가치에도 도움이 됩니다.

## 8. 발주 결정 체크리스트

- [ ] 디바이스마트 [Pi 5 16GB 상품 페이지](https://www.devicemart.co.kr/goods/view?no=15666226)에서 발주 시점 가격 재확인
- [ ] 어댑터는 반드시 **5V/5A PD 27W** (Pi 4용 5V/3A 어댑터로는 안 됨)
- [ ] 케이스는 **액티브 쿨러 포함** (Argon NEO 5 또는 공식 Active Cooler + 알루미늄)
- [ ] microSD 64GB 또는 NVMe SSD 256GB+ 결정
- [ ] BOM 합계 약 730,000원 — 예산 추가 편성 또는 다른 라인 조정 결정

## Sources

- [Buy a Raspberry Pi 5 — Raspberry Pi 공식](https://www.raspberrypi.com/products/raspberry-pi-5/)
- [라즈베리파이5 16GB + 가이드북 — 디바이스마트](https://www.devicemart.co.kr/goods/view?no=15666226)
- [라즈베리파이5 16GB + PDF 가이드북 — 엘레파츠](https://m.eleparts.co.kr/goods/view?no=16701768)
- [Raspberry Pi 5 (16GB) — PiShop](https://www.pishop.us/product/raspberry-pi-5-16gb/)
