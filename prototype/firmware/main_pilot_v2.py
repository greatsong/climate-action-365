"""
Unit 1 파일럿 모드 v2 — 라이브 시각화 + 메모 + CSV 다운로드.

설계:
- 3초마다 측정 → 최근 30분 ring buffer(600건) + flash data.csv 누적
- SVG 시계열 그래프 3장 (X축: 최근 30분, 5분 간격 시간 격자)
- 메모 입력 폼 + 최근 5건 표시 + 이벤트 기록 (창문 열음·환기 등)
- 다운로드: /data.csv, /notes.csv (학생이 폰·PC로 즉시 받아 엑셀에서 분석)
- 페이지 3초 auto-refresh + 라이브 도트
- KST(UTC+9) 자동 동기화
- data.csv가 200KB 넘으면 절반 자동 rotate (flash 보호)

'테스트 + 재미' 모드 — 본격 운영은 main.py가 서버에 POST.
"""

import gc
import network
import socket
import time
import os
from machine import WDT, reset

try:
    import ntptime
    HAS_NTP = True
except ImportError:
    HAS_NTP = False

import secrets
import sensors


wdt = WDT(timeout=8000)

# ---------- 설정 ----------
KST_OFFSET = 9 * 3600
INTERVAL_SEC = 3
WINDOW_SEC = 30 * 60                         # 30분 윈도우
RECENT_MAX = WINDOW_SEC // INTERVAL_SEC      # 600건
DATA_CSV = "data.csv"
NOTES_CSV = "notes.csv"
DATA_CSV_MAX = 200_000                       # 200KB 초과 시 절반 rotate
REFRESH_SEC = 3

# ---------- 상태 ----------
recent = []          # [(ts, t, rh, light), ...]
recent_notes = []    # [(ts, note), ...]
measure_count = 0
boot_ts = 0

# 메모 textarea 입력 중 refresh를 멈추고 sessionStorage에 임시 보존.
# meta refresh 대신 setInterval로 갈아탔기에 가능.
SCRIPT_HTML = """<script>
(function () {
  var INTERVAL = 3000;
  var KEY = 'pico_note_draft';
  var timer = null;
  function startTimer() {
    if (timer) return;
    timer = setInterval(function () { location.reload(); }, INTERVAL);
  }
  function stopTimer() {
    if (timer) { clearInterval(timer); timer = null; }
  }
  document.addEventListener('DOMContentLoaded', function () {
    var ta = document.querySelector('textarea[name=note]');
    if (ta) {
      var saved = sessionStorage.getItem(KEY);
      if (saved && !ta.value) ta.value = saved;
      ta.addEventListener('focus', stopTimer);
      ta.addEventListener('input', function () {
        sessionStorage.setItem(KEY, ta.value);
        stopTimer();
      });
      ta.addEventListener('blur', function () {
        // 입력 후 5초간 사용자가 가만히 있으면 다시 자동 갱신
        setTimeout(startTimer, 5000);
      });
    }
    var form = document.querySelector('form');
    if (form) {
      form.addEventListener('submit', function () {
        sessionStorage.removeItem(KEY);
      });
    }
    startTimer();
  });
})();
</script>"""


def log(msg):
    print("[{}] {}".format(time.ticks_ms(), msg))


def now_kst():
    return time.time() + KST_OFFSET


def fmt_time(ts):
    t = time.localtime(ts)
    return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
        t[0], t[1], t[2], t[3], t[4], t[5])


def fmt_hms(ts):
    t = time.localtime(ts)
    return "{:02d}:{:02d}:{:02d}".format(t[3], t[4], t[5])


# ---------- WiFi · NTP ----------
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        log("WiFi 연결: " + secrets.WIFI_SSID)
        wlan.connect(secrets.WIFI_SSID, secrets.WIFI_PASSWORD)
        deadline = time.time() + 30
        while not wlan.isconnected() and time.time() < deadline:
            wdt.feed()
            time.sleep(1)
    if not wlan.isconnected():
        log("WiFi 실패 → reset")
        reset()
    log("WiFi: " + wlan.ifconfig()[0])
    return wlan


def sync_ntp():
    if not HAS_NTP:
        log("ntptime 없음 — 시간은 부팅 후 경과로 표시")
        return
    for _ in range(3):
        try:
            ntptime.host = "pool.ntp.org"
            ntptime.settime()
            log("NTP 동기화: " + fmt_time(now_kst()))
            return
        except Exception as e:
            log("NTP 재시도: " + str(e))
            time.sleep(2)
    log("NTP 실패 (계속 진행)")


# ---------- 파일 ----------
def ensure_csv():
    """CSV 파일이 없으면 헤더와 함께 생성. UTF-8 BOM(﻿) 추가 →
    엑셀에서 더블클릭으로 열어도 한글이 안 깨짐."""
    for path, header in [
        (DATA_CSV, "﻿timestamp_kst,t,rh,light\n"),
        (NOTES_CSV, "﻿timestamp_kst,note\n"),
    ]:
        try:
            os.stat(path)
        except OSError:
            with open(path, "w") as f:
                f.write(header)


def rotate_if_big():
    try:
        sz = os.stat(DATA_CSV)[6]
        if sz > DATA_CSV_MAX:
            with open(DATA_CSV, "r") as f:
                lines = f.readlines()
            keep = [lines[0]] + lines[len(lines) // 2:]
            with open(DATA_CSV, "w") as f:
                f.writelines(keep)
            log("data.csv rotate: {}줄 유지".format(len(keep)))
    except OSError:
        pass


def append_data(ts, t, rh, light):
    global measure_count
    rotate_if_big()
    try:
        with open(DATA_CSV, "a") as f:
            f.write("{},{:.2f},{:.1f},{:.1f}\n".format(int(ts), t, rh, light))
    except Exception as e:
        log("CSV 쓰기 실패: " + str(e))
    recent.append((ts, t, rh, light))
    while len(recent) > RECENT_MAX:
        recent.pop(0)
    measure_count += 1


def append_note(ts, note):
    safe = note.replace('"', '""')
    try:
        with open(NOTES_CSV, "a") as f:
            f.write('{},"{}"\n'.format(int(ts), safe))
    except Exception as e:
        log("메모 쓰기 실패: " + str(e))
    recent_notes.append((ts, note))
    while len(recent_notes) > 20:
        recent_notes.pop(0)


# ---------- SVG ----------
def svg_chart(points, ymin, ymax, label, color, w=720, h=130):
    if len(points) < 2:
        return ('<svg width="{}" height="{}" style="background:#fafafa">'
                '<text x="50%" y="50%" font-size="12" fill="#aaa" '
                'text-anchor="middle">측정 시작 중…</text></svg>').format(w, h)
    end = now_kst()
    start = end - WINDOW_SEC

    grid = []
    for i in range(1, 4):
        y = i * h // 4
        grid.append('<line x1="0" y1="{}" x2="{}" y2="{}" stroke="#eee"/>'.format(y, w, y))
    for i in range(1, 6):
        x = i * w // 6
        grid.append('<line x1="{}" y1="0" x2="{}" y2="{}" stroke="#eee"/>'.format(x, x, h))

    coords = []
    for ts, v in points:
        if v is None:
            continue
        x = int((ts - start) / WINDOW_SEC * w)
        if x < 0 or x > w:
            continue
        y = int(h - (v - ymin) / (ymax - ymin) * h)
        y = max(0, min(h, y))
        coords.append("{},{}".format(x, y))

    poly = '<polyline points="{}" fill="none" stroke="{}" stroke-width="2"/>'.format(
        " ".join(coords), color)

    y_labels = []
    for i in range(0, 5):
        v = ymax - i * (ymax - ymin) / 4
        y_labels.append('<text x="3" y="{}" font-size="9" fill="#888">{:.0f}</text>'.format(
            i * h // 4 + 10, v))

    t_labels = []
    for i in range(0, 7):
        x = i * w // 6
        offset_sec = (i - 6) * 5 * 60
        lt = time.localtime(end + offset_sec)
        t_labels.append(
            '<text x="{}" y="{}" font-size="9" fill="#888" text-anchor="middle">'
            '{:02d}:{:02d}</text>'.format(x, h + 12, lt[3], lt[4]))

    last_ts, last_v = points[-1]
    dot = ''
    if last_v is not None:
        cx = int((last_ts - start) / WINDOW_SEC * w)
        cy = int(h - (last_v - ymin) / (ymax - ymin) * h)
        dot = '<circle cx="{}" cy="{}" r="3.5" fill="{}"/>'.format(cx, cy, color)
        dot += ('<text x="{}" y="{}" font-size="10" fill="{}" font-weight="700">'
                '{:.1f}</text>').format(min(cx + 6, w - 30), max(cy - 4, 12), color, last_v)

    return ('<svg width="{}" height="{}" style="background:#fafafa;border-radius:6px">'
            '{}{}{}{}{}'
            '<text x="6" y="11" font-size="10" fill="#555" font-weight="600">{}</text>'
            '</svg>').format(
        w, h + 18,
        "".join(grid), poly, dot, "".join(y_labels), "".join(t_labels),
        label)


# ---------- 페이지 ----------
def html_escape(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def trend_arrow(idx):
    # 1분 전(20건 전) 대비
    if len(recent) < 20:
        return "·"
    cur = recent[-1][idx]
    old = recent[-20][idx]
    diff = cur - old
    if abs(diff) < 0.3:
        return "→"
    return "↑" if diff > 0 else "↓"


def make_page(cur_t, cur_rh, cur_light):
    now = now_kst()
    start = now - WINDOW_SEC

    pts_t = [(ts, t) for ts, t, rh, lt in recent if ts >= start]
    pts_rh = [(ts, rh) for ts, t, rh, lt in recent if ts >= start]
    pts_lt = [(ts, lt) for ts, t, rh, lt in recent if ts >= start]

    svg_t = svg_chart(pts_t, 15, 35, "온도 °C (15~35)", "#e74c3c")
    svg_rh = svg_chart(pts_rh, 0, 100, "습도 %RH (0~100)", "#3498db")
    svg_lt = svg_chart(pts_lt, 0, 100, "조도 % (0~100)", "#f39c12")

    notes_html = ""
    for ts, note in reversed(recent_notes[-5:]):
        notes_html += '<li><time>{}</time> {}</li>'.format(fmt_hms(ts), html_escape(note))
    if not notes_html:
        notes_html = '<li style="color:#aaa">메모 없음 — 아래에서 입력해 보세요</li>'

    uptime_sec = int(now - boot_ts) if boot_ts else 0
    uptime_str = "{}h {}m".format(uptime_sec // 3600, (uptime_sec % 3600) // 60)

    return """<!DOCTYPE html>
<html lang="ko"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{node} 라이브</title>
<style>
*{{box-sizing:border-box;}}
body{{font-family:-apple-system,'Pretendard',sans-serif;background:#f0f2f5;color:#222;margin:0;padding:0.8em;}}
.wrap{{max-width:780px;margin:0 auto;}}
header{{text-align:center;padding:0.3em;}}
h1{{font-size:1em;color:#555;margin:0;font-weight:600;}}
.meta{{color:#aaa;font-size:0.75em;margin-top:0.2em;font-variant-numeric:tabular-nums;}}
.live{{display:inline-block;width:8px;height:8px;background:#2ecc71;border-radius:50%;
       margin-right:0.4em;animation:pulse 1.5s infinite;}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:0.3}}}}
.cards{{display:flex;gap:0.4em;justify-content:center;flex-wrap:wrap;margin:0.6em 0;}}
.card{{background:#fff;padding:0.8em 1em;border-radius:10px;
       box-shadow:0 1px 3px rgba(0,0,0,0.06);min-width:5.5em;text-align:center;
       flex:1;max-width:8em;}}
.label{{font-size:0.75em;color:#999;}}
.value{{font-size:1.7em;font-weight:700;margin:0.1em 0;line-height:1.1;
        font-variant-numeric:tabular-nums;}}
.trend{{font-size:0.7em;color:#888;margin-left:0.2em;}}
.unit{{font-size:0.75em;color:#999;}}
.chart{{background:#fff;padding:0.3em;margin:0.4em 0;border-radius:8px;}}
.chart svg{{width:100%;height:auto;display:block;}}
form{{background:#fff;padding:0.8em;border-radius:8px;margin:0.4em 0;}}
.form-label{{font-size:0.85em;color:#666;margin-bottom:0.3em;}}
textarea{{width:100%;padding:0.5em;border:1px solid #ddd;border-radius:6px;
          font-family:inherit;font-size:0.9em;resize:vertical;}}
button{{background:#3498db;color:#fff;border:0;padding:0.45em 1.4em;border-radius:6px;
        margin-top:0.4em;cursor:pointer;font-size:0.9em;font-weight:600;}}
button:hover{{background:#2980b9;}}
ul.notes{{background:#fff;padding:0.7em 1em 0.7em 2em;border-radius:8px;margin:0.4em 0;
          font-size:0.88em;list-style:none;}}
ul.notes li{{padding:0.2em 0;border-bottom:1px solid #f0f0f0;}}
ul.notes li:last-child{{border:0;}}
ul.notes time{{color:#888;font-size:0.85em;margin-right:0.5em;
                font-variant-numeric:tabular-nums;}}
.foot{{text-align:center;color:#999;font-size:0.78em;margin:0.8em 0;}}
.foot a{{color:#3498db;text-decoration:none;margin:0 0.3em;font-weight:600;}}
.foot a.danger{{color:#e74c3c;}}
</style></head><body>
<div class="wrap">
<header><h1><span class="live"></span>NODE {node} · {now_str}</h1>
<div class="meta">측정 #{count} · uptime {up} · ring {nrec}/{rmax}</div></header>
<div class="cards">
<div class="card"><div class="label">온도</div>
<div class="value">{ct:.1f}<span class="trend">{tr_t}</span></div><div class="unit">°C</div></div>
<div class="card"><div class="label">습도</div>
<div class="value">{crh:.1f}<span class="trend">{tr_rh}</span></div><div class="unit">%RH</div></div>
<div class="card"><div class="label">조도</div>
<div class="value">{clt:.1f}<span class="trend">{tr_lt}</span></div><div class="unit">%</div></div>
</div>
<div class="chart">{svg_t}</div>
<div class="chart">{svg_rh}</div>
<div class="chart">{svg_lt}</div>
<form method="POST" action="/note">
<div class="form-label">📝 관찰 메모 — 창문 열음·환기·전등 ON 등 이벤트</div>
<textarea name="note" rows="2" placeholder="예: 점심시간 환기 시작 / 형광등 끔"></textarea>
<button>저장</button>
</form>
<ul class="notes">{notes_html}</ul>
<div class="foot">
{refresh}초마다 자동 갱신 (입력 중엔 중지) · 측정 {interval}초 주기 · 윈도우 {window}분<br>
📥 <a href="/data.csv">data.csv</a> · <a href="/notes.csv">notes.csv</a>
· <a href="/clear" class="danger" onclick="return confirm('데이터 초기화?')">⚠ 초기화</a>
</div>
</div>{script}</body></html>""".format(
        refresh=REFRESH_SEC, node=secrets.NODE_ID, now_str=fmt_time(now),
        count=measure_count, up=uptime_str, nrec=len(recent), rmax=RECENT_MAX,
        ct=cur_t, crh=cur_rh, clt=cur_light,
        tr_t=trend_arrow(1), tr_rh=trend_arrow(2), tr_lt=trend_arrow(3),
        svg_t=svg_t, svg_rh=svg_rh, svg_lt=svg_lt,
        notes_html=notes_html, interval=INTERVAL_SEC, window=WINDOW_SEC // 60,
        script=SCRIPT_HTML,
    )


# ---------- HTTP ----------
def url_decode(s):
    """URL-encoded 문자열을 UTF-8로 안전 디코딩.
    한글 같은 다바이트 문자는 %EC%82%AC 형태로 3바이트 연속으로 오므로
    바이트 단위로 모은 뒤 마지막에 한 번에 UTF-8 디코딩한다.
    (한 글자씩 chr()로 변환하면 UTF-8 → Latin-1 오해석 모지바케 발생)
    """
    out = bytearray()
    i = 0
    n = len(s)
    while i < n:
        c = s[i]
        if c == '+':
            out.append(0x20)
            i += 1
        elif c == '%' and i + 2 < n:
            try:
                out.append(int(s[i + 1:i + 3], 16))
                i += 3
            except ValueError:
                out.append(ord(c))
                i += 1
        else:
            out.append(ord(c))
            i += 1
    return bytes(out).decode('utf-8', 'replace')


def parse_form(body):
    out = {}
    for pair in body.split('&'):
        if '=' in pair:
            k, v = pair.split('=', 1)
            out[url_decode(k)] = url_decode(v)
    return out


def write_all(client, data, chunk=512, max_retries=200):
    """모든 바이트를 보장 송신. 부분 전송·EAGAIN(-11) 처리.
    chunk 작게(512) + 송신 후 짧은 양보 → CYW43 무선 칩에 시간을 줌."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    n = len(data)
    i = 0
    retries = 0
    while i < n:
        try:
            sent = client.send(data[i:i + chunk])
            if sent is None or sent == 0:
                # 전송 실패 — 잠시 후 재시도
                retries += 1
                if retries > max_retries:
                    return False
                time.sleep_ms(20)
                continue
            i += sent
            retries = 0
        except OSError as e:
            # EAGAIN(-11)·ETIMEDOUT 등 — 잠시 양보 후 재시도
            retries += 1
            if retries > max_retries:
                return False
            time.sleep_ms(20)
    return True


def serve_csv(client, path):
    try:
        gc.collect()
        sz = os.stat(path)[6]
        # 다운로드용으로 타임아웃 넉넉히 (큰 파일 대비)
        try:
            client.settimeout(30)
        except Exception:
            pass

        headers = ("HTTP/1.1 200 OK\r\n"
                   "Content-Type: text/csv; charset=utf-8\r\n"
                   "Content-Length: {}\r\n"
                   "Content-Disposition: attachment; filename=\"{}\"\r\n"
                   "Connection: close\r\n\r\n").format(sz, path)
        if not write_all(client, headers):
            log("CSV 헤더 송신 실패")
            return

        with open(path, "rb") as f:
            sent_bytes = 0
            while True:
                buf = f.read(2048)
                if not buf:
                    break
                if not write_all(client, buf):
                    log("CSV 본문 송신 중단 at {} / {}".format(sent_bytes, sz))
                    return
                sent_bytes += len(buf)
                wdt.feed()      # 큰 파일 송신 중에도 WDT 안전
        log("CSV 송신 완료: {} ({}B)".format(path, sent_bytes))
    except OSError:
        try:
            client.send(b"HTTP/1.1 404 Not Found\r\nConnection: close\r\n\r\n")
        except Exception:
            pass


def handle_request(client, current):
    try:
        req = client.recv(4096).decode("utf-8", "ignore")
    except Exception:
        return
    if not req:
        return

    first = req.split("\r\n", 1)[0]
    parts = first.split(" ")
    if len(parts) < 2:
        return
    method, path = parts[0], parts[1]
    qpos = path.find('?')
    if qpos >= 0:
        path = path[:qpos]

    if method == "GET" and path == "/":
        gc.collect()
        body = make_page(*current)
        body_bytes = body.encode("utf-8")
        headers = ("HTTP/1.1 200 OK\r\n"
                   "Content-Type: text/html; charset=utf-8\r\n"
                   "Content-Length: {}\r\n"
                   "Cache-Control: no-cache\r\n"
                   "Connection: close\r\n\r\n").format(len(body_bytes))
        write_all(client, headers)
        write_all(client, body_bytes)
        del body, body_bytes
        gc.collect()
    elif method == "POST" and path == "/note":
        body_idx = req.find("\r\n\r\n")
        if body_idx >= 0:
            form = parse_form(req[body_idx + 4:])
            note = form.get("note", "").strip()
            if note:
                append_note(now_kst(), note[:200])
                log("📝 메모: " + note[:60])
        client.send(b"HTTP/1.1 303 See Other\r\nLocation: /\r\n"
                    b"Connection: close\r\n\r\n")
    elif method == "GET" and path == "/data.csv":
        serve_csv(client, DATA_CSV)
    elif method == "GET" and path == "/notes.csv":
        serve_csv(client, NOTES_CSV)
    elif method == "GET" and path == "/clear":
        recent.clear()
        recent_notes.clear()
        for p, h in [(DATA_CSV, "﻿timestamp_kst,t,rh,light\n"),
                     (NOTES_CSV, "﻿timestamp_kst,note\n")]:
            try:
                with open(p, "w") as f:
                    f.write(h)
            except Exception:
                pass
        log("초기화 완료")
        client.send(b"HTTP/1.1 303 See Other\r\nLocation: /\r\n"
                    b"Connection: close\r\n\r\n")
    else:
        client.send(b"HTTP/1.1 404 Not Found\r\nConnection: close\r\n\r\n")


# ---------- 메인 ----------
def main():
    global boot_ts
    log("부팅 v2: node_id=" + secrets.NODE_ID)
    log("I2C 스캔: " + str(sensors.scan()))
    ensure_csv()
    wlan = connect_wifi()
    sync_ntp()
    boot_ts = now_kst()

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("0.0.0.0", 80))
    srv.listen(5)               # 폰이 보내는 favicon·prefetch 동시 큐
    srv.settimeout(0.03)
    log("HTTP 준비: http://" + wlan.ifconfig()[0] + "/")

    last_t = last_rh = last_light = 0.0
    last_measure = 0

    while True:
        wdt.feed()
        now_ms = time.ticks_ms()

        if time.ticks_diff(now_ms, last_measure) > INTERVAL_SEC * 1000:
            try:
                last_t, last_rh, last_light = sensors.read_all()
                append_data(now_kst(), last_t, last_rh, last_light)
            except Exception as e:
                log("측정 오류: " + str(e))
            last_measure = now_ms

        try:
            client, addr = srv.accept()
        except OSError:
            continue

        try:
            client.settimeout(5)    # 응답 송신 안전 타임아웃
            handle_request(client, (last_t, last_rh, last_light))
        except Exception as e:
            log("응답 오류: " + str(e))
        finally:
            try:
                client.close()
            except Exception:
                pass
            gc.collect()    # 매 요청 후 청소


main()
