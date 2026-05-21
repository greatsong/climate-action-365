# Firmware — Pico 2 WH (MicroPython)

교실 노드 펌웨어. Phase 1은 SHT40 + BH1750만 측정.

## 배선 (Grove Shield for Pi Pico)

| 센서 | Grove 슬롯 | Pico 핀 |
|---|---|---|
| SHT40 | I2C0 | SDA=GP4, SCL=GP5 |
| BH1750 | I2C0 (또는 같은 버스 분기) | SDA=GP4, SCL=GP5 |

> Grove Shield I2C 슬롯이 2개 이상이면 둘 다 I2C0 그룹에 꽂으면 됩니다. I2C 주소가 다르므로(0x44 / 0x23) 같은 버스에 같이 붙어도 충돌 없음.

## 설치

1. Pico 2 WH에 MicroPython 1.24+ 펌웨어 플래시
   - https://micropython.org/download/RPI_PICO2_W/ 에서 `.uf2` 다운로드
   - BOOTSEL 누른 채로 USB 연결 → 드라이브에 `.uf2` 복사
2. Thonny 또는 mpremote로 다음 파일을 Pico에 복사:
   - `secrets.py` (각 노드별로 NODE_ID 수정!)
   - `sensors.py`
   - `main.py`
3. Pico 재부팅 → 자동 실행

## 교실별 설치 순서

각 교실 노드는 `secrets.py`의 `NODE_ID`만 다르게 설정:

```python
NODE_ID = "1-1"   # 1학년 1반
# NODE_ID = "1-2"   # 1학년 2반
# ...
# NODE_ID = "3-8"   # 3학년 8반
```

## 디버깅

Thonny REPL에서:

```python
import sensors
print(sensors.scan())          # I2C 스캔 (0x44, 0x23 보여야 함)
print(sensors.read_sht40())    # (온도, 습도)
print(sensors.read_bh1750())   # lux
```

## 동작 확인

WiFi·서버 정상 시 30초마다 콘솔 로그:
```
[12345] 측정: T=24.31 RH=45.2 lux=287.5
```

## 트러블슈팅

- I2C 스캔에 아무것도 안 나옴 → 케이블 연결, Grove 슬롯이 진짜 I2C인지 확인
- SHT40만 안 보임 → 다른 슬롯에 꽂아보기 (간혹 Grove Shield 슬롯에 풀업이 없는 경우)
- WiFi 5분 안에 못 붙으면 자동 reset → SSID·패스워드 재확인
- `buffer.jsonl`이 200줄로 가득 차면 → 서버 다운 의심
