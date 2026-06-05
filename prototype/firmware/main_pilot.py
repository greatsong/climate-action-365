"""
Unit 1 파일럿 모드 — Pico 자체를 임시 HTTP 서버로.

Unit 2의 라즈베리 파이 서버가 아직 없을 때, Pico가 직접 HTTP를 서빙해
폰·노트북 브라우저에서 측정값을 5초마다 자동 갱신되는 페이지로 볼 수 있습니다.

사용:
1. Thonny로 sensors.py / secrets.py / main_pilot.py 세 파일을 올립니다.
2. 보드 안에서 main_pilot.py를 main.py로 이름 바꿔도 되고, REPL에서
   `import main_pilot`으로 직접 실행해도 됩니다.
3. 셸에 'HTTP 준비: http://192.168.x.x/' 가 보이면 같은 망의 폰 브라우저로 접속.

Unit 2 라즈베리 파이 서버를 완성한 뒤에는 main.py(HTTP POST 클라이언트)로 전환합니다.

⭐ 핵심 레슨런: srv.settimeout(0.03)
   accept를 완전 논블로킹(timeout=0)으로 두면 main 루프가 5ms마다 미친 듯이 회전해
   CYW43(WiFi) 칩이 일할 틈을 못 얻어 'do_ioctl: timeout' 이 반복되고 접속이 끊깁니다.
   30ms 타임아웃을 주면 요청이 없을 때 그 30ms 동안 WiFi 스택이 숨을 쉽니다.
"""

import network
import socket
import time
from machine import WDT, reset

import secrets
import sensors


wdt = WDT(timeout=8000)


def log(msg):
    print("[{}] {}".format(time.ticks_ms(), msg))


def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        log("WiFi 연결 시도: " + secrets.WIFI_SSID)
        wlan.connect(secrets.WIFI_SSID, secrets.WIFI_PASSWORD)
        deadline = time.time() + 30
        while not wlan.isconnected() and time.time() < deadline:
            wdt.feed()
            time.sleep(1)
    if not wlan.isconnected():
        log("WiFi 30초 내 실패 → reset")
        reset()
    log("WiFi 연결됨: IP=" + wlan.ifconfig()[0])
    return wlan


HTML = """<!DOCTYPE html><html lang="ko"><head>
<meta charset="utf-8">
<meta http-equiv="refresh" content="5">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{node} 교실 환경</title>
<style>
*{{box-sizing:border-box;}}
body{{font-family:-apple-system,'Pretendard',sans-serif;text-align:center;
     background:#f5f5f7;margin:0;padding:1.5em 1em;color:#222;}}
h1{{font-size:1.1em;color:#666;margin:0 0 1em;font-weight:600;}}
.card{{display:inline-block;background:#fff;padding:1.3em 1.6em;margin:0.4em;
       border-radius:14px;box-shadow:0 1px 4px rgba(0,0,0,0.06);min-width:7em;}}
.label{{color:#888;font-size:0.85em;}}
.value{{font-size:2.3em;font-weight:700;margin:0.15em 0;}}
.unit{{color:#888;font-size:0.85em;}}
.foot{{margin-top:1.5em;color:#bbb;font-size:0.8em;}}
</style></head><body>
<h1>🌱 교실 환경 · NODE {node}</h1>
<div class="card"><div class="label">온도</div><div class="value">{t}</div><div class="unit">°C</div></div>
<div class="card"><div class="label">습도</div><div class="value">{rh}</div><div class="unit">%RH</div></div>
<div class="card"><div class="label">조도(상대)</div><div class="value">{light}</div><div class="unit">%</div></div>
<p class="foot">5초마다 자동 갱신 · Pico 직접 서빙 · Unit 1 파일럿 모드</p>
</body></html>"""


def make_page(t, rh, light):
    return HTML.format(
        node=secrets.NODE_ID,
        t="{:.1f}".format(t),
        rh="{:.1f}".format(rh),
        light="{:.1f}".format(light),
    )


def main():
    log("부팅 (파일럿 모드): node_id=" + secrets.NODE_ID)
    log("I2C 스캔: " + str(sensors.scan()))
    wlan = connect_wifi()

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("0.0.0.0", 80))
    srv.listen(1)
    srv.settimeout(0.03)  # ⭐ 30ms — CYW43에 숨 쉴 틈. 0이면 WiFi 죽음.
    log("HTTP 준비: http://" + wlan.ifconfig()[0] + "/")

    last_t = last_rh = last_light = 0.0
    last_measure = 0

    while True:
        wdt.feed()
        now = time.ticks_ms()

        if time.ticks_diff(now, last_measure) > 1000:
            try:
                last_t, last_rh, last_light = sensors.read_all()
                log("측정: T={:.2f} RH={:.1f} light={:.1f}%".format(
                    last_t, last_rh, last_light))
            except Exception as e:
                log("측정 오류: " + str(e))
            last_measure = now

        try:
            client, addr = srv.accept()
        except OSError:
            continue  # accept timeout — 정상

        try:
            client.recv(1024)
            body = make_page(last_t, last_rh, last_light)
            resp = ("HTTP/1.1 200 OK\r\n"
                    "Content-Type: text/html; charset=utf-8\r\n"
                    "Connection: close\r\n\r\n" + body)
            client.send(resp.encode())
        except Exception as e:
            log("응답 오류: " + str(e))
        finally:
            try:
                client.close()
            except Exception:
                pass


main()
