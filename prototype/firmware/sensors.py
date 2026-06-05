"""
SHT40 (온습도, I2C) + Grove Light Sensor (P) v1.1 (아날로그) MicroPython 드라이버.

Grove Shield for Pi Pico 매핑 (당곡고 부품 기준, 실측 검증):
- I2C0: SDA=GP8, SCL=GP9  → SHT40 (주소 0x44)
- Analog A0: GP26          → Grove Light Sensor (SIG)

⚠️ Shield 전원 스위치는 반드시 3.3V로 둡니다.
   5V로 두면 Light Sensor SIG 출력이 최대 5V까지 올라가 Pico ADC 입력(최대 3.3V)을
   초과해 핀이 손상될 수 있습니다.

레슨런 (다른 세션):
- scan()은 hex 문자열 리스트로 반환합니다(['0x44']). 정수 [68]보다 헷갈리지 않습니다.
- SHT40 측정 대기는 10ms로 충분하지 않을 수 있어 20ms로 늘렸습니다.
- 리부트 직후 첫 측정에서 NAK가 나는 경우가 있어 최대 3회 재시도합니다.
- read_all()이 한 번 호출로 (T, RH, light%)를 돌려줘 main.py가 단순해집니다.
"""

from machine import I2C, Pin, ADC
import time

# ---------- SHT40 (I2C) ----------
I2C_ID = 0
SDA_PIN = 8
SCL_PIN = 9
I2C_FREQ = 100_000

SHT40_ADDR = 0x44
SHT40_CMD_HIGHPRECISION = b"\xFD"
SHT40_WAIT_MS = 20      # 데이터시트 8.2ms + 안정 여유. 10ms는 가끔 부족.
SHT40_RETRIES = 3       # 부팅 직후 NAK 대응

_i2c = I2C(I2C_ID, sda=Pin(SDA_PIN), scl=Pin(SCL_PIN), freq=I2C_FREQ)


# ---------- Grove Light Sensor (ADC) ----------
LIGHT_ADC_PIN = 26  # A0 (= GP26 = ADC0)
_light_adc = ADC(Pin(LIGHT_ADC_PIN))


def scan():
    """I2C 주소 목록 — hex 문자열로 반환. SHT40만 있으면 ['0x44']."""
    return [hex(a) for a in _i2c.scan()]


def read_sht40():
    """SHT40에서 (온도°C, 습도%RH). 최대 3회 재시도."""
    last_err = None
    for _ in range(SHT40_RETRIES):
        try:
            _i2c.writeto(SHT40_ADDR, SHT40_CMD_HIGHPRECISION)
            time.sleep_ms(SHT40_WAIT_MS)
            data = _i2c.readfrom(SHT40_ADDR, 6)
            t_raw = (data[0] << 8) | data[1]
            rh_raw = (data[3] << 8) | data[4]
            temperature = -45.0 + 175.0 * (t_raw / 65535.0)
            humidity = -6.0 + 125.0 * (rh_raw / 65535.0)
            if humidity < 0:
                humidity = 0.0
            elif humidity > 100:
                humidity = 100.0
            return temperature, humidity
        except OSError as e:
            last_err = e
            time.sleep_ms(50)
    raise last_err


def read_light_raw():
    """Grove Light Sensor의 raw ADC 값(0~65535). 보정·디버깅용."""
    return _light_adc.read_u16()


def read_light():
    """Grove Light Sensor의 상대 밝기(0~100%)."""
    raw = _light_adc.read_u16()
    pct = (raw / 65535.0) * 100.0
    if pct < 0:
        pct = 0.0
    elif pct > 100:
        pct = 100.0
    return pct


def read_all():
    """한 번 호출로 모든 센서 측정. (온도°C, 습도%RH, 조도%) 반환."""
    t, rh = read_sht40()
    light = read_light()
    return t, rh, light
