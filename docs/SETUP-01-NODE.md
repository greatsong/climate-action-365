# SETUP-01 — 1개 노드 세팅 (파일럿)

> 16대 운영 전에 **반드시 1대 먼저** 이 과정을 완료해서 코드·배선·서버 통신을 검증합니다.

## 준비물

| 항목 | 비고 |
|---|---|
| Raspberry Pi Pico 2 WH | 1개 |
| Grove Shield for Pi Pico | 1개 |
| SHT40 Grove 모듈 | 1개 |
| BH1750 GY-302 모듈 | 1개 |
| Grove 4핀 케이블 20cm | 1개 (SHT40용) |
| Grove-점퍼 변환 케이블 | 1개 (BH1750용) |
| 마이크로 USB 케이블 | 1개 |
| 컴퓨터 (Win/Mac/Linux) | Thonny 실행용 |
| 학교 WiFi 정보 (SSID/PW) | 동일망에 Pi 서버가 있어야 함 |
| 라즈베리파이 서버 IP | SETUP-02 완료 후 확보 |

---

## 단계 1 · MicroPython 펌웨어 플래시

1. **펌웨어 다운로드**
   - https://micropython.org/download/RPI_PICO2_W/
   - 최신 stable `.uf2` 파일 다운로드 (예: `RPI_PICO2_W-20251225-v1.24.0.uf2`)
2. **Pico를 BOOTSEL 모드로 진입**
   - Pico의 **BOOTSEL** 버튼을 누른 채로 컴퓨터에 USB 연결
   - 컴퓨터에 `RPI-RP2` 또는 `RP2350` 라는 이름의 USB 드라이브가 마운트됨
   - 마운트되면 BOOTSEL 버튼 떼기
3. **.uf2 파일을 그 드라이브에 드래그&드롭**
   - 복사 끝나면 Pico가 자동 재부팅됨
   - USB 드라이브가 사라지면 펌웨어 설치 성공
4. **Pico 본체 LED가 켜져 있으면 정상** (대기 상태)

> ⚠️ Pico 2 W (1세대 Pico W와 다른 모델). 펌웨어 파일이 `RPI_PICO_W` 가 아니라 `RPI_PICO2_W` 임을 반드시 확인.

---

## 단계 2 · Thonny 설치 및 연결

1. **Thonny 다운로드**: https://thonny.org (Win/Mac/Linux 무료)
2. 설치 후 실행
3. **인터프리터 설정**: 메뉴 → `Tools` → `Options` → `Interpreter` 탭
   - **Interpreter**: `MicroPython (Raspberry Pi Pico)` 선택
   - **Port**: 자동 인식되면 그대로, 안 되면 수동 선택
     - Windows: `COM3`, `COM5` 등
     - macOS: `/dev/cu.usbmodem*`
     - Linux: `/dev/ttyACM0`
   - OK 클릭
4. **연결 확인**: Thonny 우측 하단의 빨간 STOP 버튼 클릭 (재시작)
   - 아래쪽 **Shell** 영역에 `>>>` 프롬프트가 나타나면 연결 성공
5. **간단 테스트**: Shell에 `print("hello")` 입력 → `hello` 출력되면 OK

---

## 단계 3 · 센서 배선 (Grove Shield)

### 핀맵 이해

Grove Shield의 I2C 슬롯은 Pico의 **GP4 (SDA)** 와 **GP5 (SCL)** 에 연결되어 있습니다. 슬롯이 여러 개 있어도 모두 같은 I2C 버스(GP4/GP5)에 병렬로 묶여 있어, **어느 I2C 슬롯에 꽂아도 동일하게 동작**합니다.

### SHT40 연결

1. **SHT40 Grove 모듈**의 한쪽 4핀 커넥터 ↔ **Grove-Grove 케이블** ↔ Grove Shield의 **I2C 슬롯 (아무거나 1개)**
2. 양쪽 다 일반 Grove 커넥터라 한 방향만 끼워짐. 무리해서 끼우지 말 것.

### BH1750 GY-302 연결 (변환 케이블 사용)

GY-302는 일반 4핀 점퍼 모듈입니다. 점퍼 핀 4개에 변환 케이블의 점퍼 쪽을 매핑하세요:

| GY-302 핀 | Grove 변환 케이블 색상 (표준) |
|---|---|
| VCC | **빨강** |
| GND | **검정** |
| SCL | **노랑** |
| SDA | **흰색** |

→ 변환 케이블의 Grove 커넥터 쪽 ↔ Grove Shield의 **다른 I2C 슬롯**에 끼웁니다.

> ⚠️ 변환 케이블 제조사마다 색상 매핑이 다를 수 있습니다. **첫 노드 조립 시 반드시 실측**:
> - Grove 커넥터의 1번 핀 = GND, 2번 핀 = VCC, 3번 핀 = SDA, 4번 핀 = SCL (Grove 표준)
> - 변환 케이블 점퍼 쪽의 어느 색이 어느 핀인지 멀티미터로 확인

### 배선 점검

- 모든 모듈은 **3.3V**에서 동작 (Grove Shield가 3.3V 공급)
- VCC와 GND가 바뀌면 모듈이 즉시 손상될 수 있으니 전원 켜기 전 두 번 확인

---

## 단계 4 · 코드 업로드

1. Thonny 좌측 패널에서 **View → Files** 선택
2. 두 개의 패널이 보임:
   - 위: `This computer` (내 컴퓨터)
   - 아래: `MicroPython device` (Pico)
3. 위 패널에서 다음 폴더로 이동:
   ```
   ~/greatsong-project/climate-action-365/prototype/firmware/
   ```
4. 폴더의 3개 파일을 한꺼번에 선택 (Cmd/Ctrl+클릭):
   - `main.py`
   - `sensors.py`
   - `secrets.py`
5. 우클릭 → **Upload to /** 선택
6. 아래 패널(Pico)에 3개 파일이 보이면 업로드 성공

---

## 단계 5 · `secrets.py` 수정

1. 아래 패널(Pico)의 `secrets.py` 더블클릭으로 열기
2. 다음 값을 실제 학교 환경에 맞게 수정:

```python
WIFI_SSID = "당곡고_WiFi_이름"       # 실제 SSID
WIFI_PASSWORD = "학교무선망_패스워드"  # 실제 패스워드
NODE_ID = "1-1"                       # 교실 번호 (파일럿은 임시로 "PILOT")
SERVER_URL = "http://192.168.0.10:8000/reading"  # Pi 서버 IP

INTERVAL_SEC = 30
```

3. `Ctrl+S` (또는 `Cmd+S`) 로 저장 → Pico 안에 저장됨

> 서버 IP는 SETUP-02 완료 후 확보된 라즈베리파이 4의 고정 IP를 사용합니다.

---

## 단계 6 · 첫 실행 및 검증

### 6.1 실행

1. Thonny에서 빨간 STOP 버튼 클릭 (Pico 재부팅)
2. 자동으로 `main.py`가 실행됨

### 6.2 Shell 출력 확인

다음과 같은 로그가 약 5~10초 안에 차례로 나와야 합니다:

```
[12345] 부팅: node_id=PILOT
[12450] I2C 스캔: ['0x44', '0x23']
[12500] WiFi 연결 시도: 당곡고_WiFi_이름
[13200] WiFi 연결됨: IP=192.168.0.123
[13800] 측정: T=24.31 RH=45.2 lux=287.5
```

### 6.3 검증 체크리스트

- [ ] `I2C 스캔: ['0x44', '0x23']` — **두 주소 모두** 보여야 함
  - `0x44`만 보임 → BH1750 (GY-302) 배선 문제
  - `0x23`만 보임 → SHT40 배선 문제
  - 둘 다 안 보임 → 케이블·전원 문제
- [ ] `WiFi 연결됨` — SSID·패스워드 정확해야 함
- [ ] `측정: T=... RH=... lux=...` — 30초마다 반복
- [ ] 측정값이 합리적 범위
  - T (온도): 15~35°C (교실 실내)
  - RH (습도): 20~80%
  - lux (조도): 50~2000 (형광등 켜진 교실은 보통 200~800)

---

## 단계 7 · 서버 수신 확인

> SETUP-02 완료 후 서버가 동작 중이어야 함.

1. 컴퓨터 브라우저에서 다음 주소 열기:
   ```
   http://192.168.0.10:8000/nodes
   ```
2. JSON 응답에 다음과 같이 노드가 보이면 성공:
   ```json
   [
     {
       "node_id": "PILOT",
       "last_seen": "2026-05-21T13:45:23+00:00",
       "reading_count": 8,
       "latest": { "temperature": 24.31, "humidity": 45.2, "lux": 287.5, ... }
     }
   ]
   ```
3. 또는 Streamlit 대시보드:
   ```
   http://192.168.0.10:8501
   ```
   → "전체 교실" 탭에 `PILOT` 노드 카드가 표시되면 성공

---

## 트러블슈팅

### Thonny가 Pico를 못 찾는다
- USB 케이블 교체 (마이크로 USB 케이블 중에 **충전 전용**은 데이터 전송 안 됨!)
- 다른 USB 포트 시도
- 펌웨어가 정말 플래시 되었는지: BOOTSEL 모드 한 번 더 들어가 보기

### I2C 스캔에 아무것도 안 나옴
- 모든 Grove 케이블 다시 빼고 끼우기
- Grove Shield의 슬롯이 **I2C 슬롯이 맞는지** 확인 (UART/GPIO 슬롯과 헷갈리기 쉬움 — 보통 슬롯에 `I2C`가 인쇄되어 있음)
- 다른 모듈로 교체 (모듈 자체 불량 가능성)

### `0x23` 만 안 보임 (BH1750 미인식)
- GY-302의 VCC↔GND 또는 SDA↔SCL 매핑이 바뀐 경우 가장 흔함
- 변환 케이블 점퍼 색상 재확인
- ADDR 핀이 HIGH면 주소가 `0x5C`로 바뀜 → Shell에서 확인:
  ```python
  >>> import sensors
  >>> sensors.scan()
  [0x5c, 0x44]   # 만약 이렇게 나오면 sensors.py의 BH1750_ADDR을 0x5C로 수정
  ```

### WiFi 5분 안에 못 붙음 (자동 reset 반복)
- SSID·패스워드 정확히 다시 확인 (특수문자 주의)
- 학교 망이 2.4GHz를 차단했는지 확인 (Pico는 5GHz 미지원)
- 학교 망에 디바이스 등록제가 있는지 확인 → 관리자(=본인)가 등록

### 측정값이 명백히 이상함
- 온도가 -45°C 또는 130°C → 센서 read 오류 (배선 흔들림)
- 습도가 항상 100% → 결로 또는 센서 불량
- 조도가 0 또는 65535 고정 → BH1750 측정 모드 미진입 (`sensors.py` 코드 확인)

### 서버로 데이터 안 감
- `urequests.post 실패` 로그가 보이면 → 서버 IP·포트·방화벽 확인
- Pi 서버에서 `curl http://localhost:8000/health` 로 서버 자체는 살아 있는지 확인
- Pico와 Pi가 같은 서브넷인지 (`192.168.0.x`)
