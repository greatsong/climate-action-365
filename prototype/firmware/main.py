"""
교실 환경 모니터링 노드 — Phase 1 (온습도 + 조도).

동작:
1. WiFi 연결 (실패 시 지수 백오프 재시도, 5분 넘으면 reset)
2. SHT40로 온습도, BH1750으로 조도 측정
3. JSON으로 서버에 HTTP POST
4. INTERVAL_SEC 만큼 대기 후 반복

장애 대응:
- 와치독 타이머 8초로 무한루프 방지
- 네트워크 끊김 시 측정값을 flash에 버퍼링(최대 200건)했다가 재전송
"""

import json
import time
import network
import urequests
from machine import WDT, reset

import secrets
import sensors


BUFFER_FILE = "buffer.jsonl"
BUFFER_MAX = 200

wdt = WDT(timeout=8000)


def log(msg):
    print("[{}] {}".format(time.ticks_ms(), msg))


def connect_wifi():
    """WiFi 연결. 지수 백오프로 재시도. 5분 넘으면 reset."""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if wlan.isconnected():
        return wlan

    delay = 2
    deadline = time.time() + 300  # 5분
    while not wlan.isconnected():
        wdt.feed()
        log("WiFi 연결 시도: {}".format(secrets.WIFI_SSID))
        try:
            wlan.connect(secrets.WIFI_SSID, secrets.WIFI_PASSWORD)
        except OSError as e:
            log("connect 오류: {}".format(e))

        for _ in range(10):
            wdt.feed()
            if wlan.isconnected():
                break
            time.sleep(1)

        if wlan.isconnected():
            break

        if time.time() > deadline:
            log("5분 내 연결 실패 → reset")
            reset()

        log("{}초 후 재시도".format(delay))
        for _ in range(delay):
            wdt.feed()
            time.sleep(1)
        delay = min(delay * 2, 60)

    log("WiFi 연결됨: IP={}".format(wlan.ifconfig()[0]))
    return wlan


def buffer_append(payload):
    """전송 실패한 측정값을 flash에 추가 저장."""
    try:
        # 라인 수 제한 (오래된 것부터 버림)
        try:
            with open(BUFFER_FILE, "r") as f:
                lines = f.readlines()
        except OSError:
            lines = []
        lines.append(json.dumps(payload) + "\n")
        if len(lines) > BUFFER_MAX:
            lines = lines[-BUFFER_MAX:]
        with open(BUFFER_FILE, "w") as f:
            f.writelines(lines)
    except OSError as e:
        log("buffer 쓰기 실패: {}".format(e))


def buffer_flush():
    """버퍼링된 측정값을 한 번씩 재전송 시도. 성공하면 파일 비움."""
    try:
        with open(BUFFER_FILE, "r") as f:
            lines = f.readlines()
    except OSError:
        return

    if not lines:
        return

    log("버퍼 {}건 재전송 시도".format(len(lines)))
    survivors = []
    for line in lines:
        wdt.feed()
        try:
            payload = json.loads(line)
            if not send_once(payload, retry=False):
                survivors.append(line)
        except ValueError:
            pass  # 깨진 라인 버림

    try:
        with open(BUFFER_FILE, "w") as f:
            f.writelines(survivors)
    except OSError:
        pass


def send_once(payload, retry=True):
    """payload를 서버에 한 번 전송. 성공하면 True."""
    try:
        r = urequests.post(
            secrets.SERVER_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=5,
        )
        ok = 200 <= r.status_code < 300
        r.close()
        return ok
    except Exception as e:
        log("전송 실패: {}".format(e))
        return False


def measure():
    """센서 1회 측정. 실패하면 None 필드로 반환."""
    payload = {
        "node_id": secrets.NODE_ID,
        "ts": time.time(),
        "temperature": None,
        "humidity": None,
        "light": None,
    }
    try:
        t, rh = sensors.read_sht40()
        payload["temperature"] = round(t, 2)
        payload["humidity"] = round(rh, 2)
    except Exception as e:
        log("SHT40 오류: {}".format(e))

    try:
        payload["light"] = round(sensors.read_light(), 1)
    except Exception as e:
        log("Light 센서 오류: {}".format(e))

    return payload


def main():
    log("부팅: node_id={}".format(secrets.NODE_ID))
    # sensors.scan()이 이제 hex 문자열 리스트(['0x44'])를 그대로 반환하므로
    # 추가로 hex() 변환하지 않습니다.
    log("I2C 스캔: {} (0x44 = SHT40 하나만 보이면 정상)".format(sensors.scan()))

    connect_wifi()

    while True:
        wdt.feed()

        payload = measure()
        log("측정: T={} RH={} light={}%".format(
            payload["temperature"], payload["humidity"], payload["light"]))

        if send_once(payload):
            buffer_flush()  # 그 동안 쌓인 것도 함께
        else:
            buffer_append(payload)
            # WiFi 자체가 끊겼을 가능성 → 재연결
            wlan = network.WLAN(network.STA_IF)
            if not wlan.isconnected():
                connect_wifi()

        # INTERVAL만큼 대기 (WDT 피드하면서)
        elapsed = 0
        while elapsed < secrets.INTERVAL_SEC:
            wdt.feed()
            time.sleep(1)
            elapsed += 1


main()
