"""
SHT40 (온습도) + BH1750 (조도) MicroPython 드라이버.

Grove Shield for Pi Pico의 I2C0 슬롯에 두 센서를 Grove 케이블로 연결한다고 가정한다.
- I2C0: SDA=GP4, SCL=GP5
- SHT40 주소: 0x44
- BH1750 주소: 0x23 (ADDR 핀 LOW일 때)
"""

from machine import I2C, Pin
import time

I2C_ID = 0
SDA_PIN = 4
SCL_PIN = 5
I2C_FREQ = 100_000

SHT40_ADDR = 0x44
SHT40_CMD_HIGHPRECISION = b"\xFD"

BH1750_ADDR = 0x23
BH1750_CMD_CONTINUOUS_HIGH_RES = b"\x10"  # 1 lux 분해능, 약 120ms 대기


_i2c = I2C(I2C_ID, sda=Pin(SDA_PIN), scl=Pin(SCL_PIN), freq=I2C_FREQ)


def scan():
    """연결된 I2C 주소 목록. 디버깅용."""
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


def read_bh1750():
    """BH1750에서 조도(lux)를 읽는다."""
    _i2c.writeto(BH1750_ADDR, BH1750_CMD_CONTINUOUS_HIGH_RES)
    time.sleep_ms(180)
    data = _i2c.readfrom(BH1750_ADDR, 2)
    raw = (data[0] << 8) | data[1]
    return raw / 1.2
