"""
SHT40 (온습도, I2C) + Grove Light Sensor (P) v1.1 (아날로그) MicroPython 드라이버.

Grove Shield for Pi Pico 매핑 (당곡고 부품 기준):
- I2C0: SDA=GP8, SCL=GP9  → SHT40 (주소 0x44)
- Analog A0: GP26          → Grove Light Sensor (SIG)

⚠️ Shield 전원 스위치는 반드시 3.3V로 둡니다.
   5V로 두면 Light Sensor SIG 출력이 최대 5V까지 올라가 Pico ADC 입력(최대 3.3V)을
   초과해 핀이 손상될 수 있습니다.

Grove Light Sensor (P) v1.1은 LS06-S 포토트랜지스터 기반 아날로그 모듈입니다.
lux가 아니라 ‘상대 밝기(0~100%)’를 반환합니다. 절대 lux를 쓰려면 별도 BH1750(I2C)
모듈이 필요합니다.
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

_i2c = I2C(I2C_ID, sda=Pin(SDA_PIN), scl=Pin(SCL_PIN), freq=I2C_FREQ)


# ---------- Grove Light Sensor (ADC) ----------
LIGHT_ADC_PIN = 26  # A0 (= GP26 = ADC0)
_light_adc = ADC(Pin(LIGHT_ADC_PIN))


def scan():
    """I2C 주소 목록. SHT40만 사용하므로 [0x44] 한 개가 정상."""
    return _i2c.scan()


def read_sht40():
    """SHT40에서 온도(°C)와 상대습도(%RH)를 읽는다."""
    _i2c.writeto(SHT40_ADDR, SHT40_CMD_HIGHPRECISION)
    time.sleep_ms(10)
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


def read_light_raw():
    """Grove Light Sensor의 raw ADC 값(0~65535) 반환. 보정·디버깅용."""
    return _light_adc.read_u16()


def read_light():
    """Grove Light Sensor의 상대 밝기(0~100%)를 반환."""
    raw = _light_adc.read_u16()
    pct = (raw / 65535.0) * 100.0
    if pct < 0:
        pct = 0.0
    elif pct > 100:
        pct = 100.0
    return pct
