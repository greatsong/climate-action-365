# 02 — 네트워크 및 통신 설계 리서치

작성: 2026-05-21
대상: 당곡고 16개 교실 IoT 환경 모니터링 시스템 (Pico 2 WH × 16, 30~60초 측정 주기)

---

## 요약 (TL;DR)

- **통신 프로토콜: MQTT (umqtt.robust2) 추천.** 16노드 영구 연결, 자동 재연결, retained 메시지로 마지막 값 보존 가능. 단, 학교망이 1883/8883 포트를 막을 경우 **MQTT over WebSocket (port 443)** 또는 **HTTPS POST** 폴백 필요.
- **서버 호스팅: 라즈베리파이 4 (학교 내) + Mosquitto + InfluxDB + Grafana 스택 추천.** 초기 비용 ~15만원, 운영비 ~0원, 학생이 직접 만질 수 있음, 데이터 주권 학교에 있음. UPS(소형 무정전 전원장치) 추가로 정전 대응. 장기 백업은 주 1회 클라우드 동기화(선택).
- **학교망 대응 — 사용자 확인 필수 (현재 시점에서 추측 금지):**
  - 학교 무선망 인증 방식(WPA2-PSK / WPA2-Enterprise / 캡티브 포털) 확인
  - **만약 WPA2-Enterprise(EAP-PEAP, MSCHAPv2 등)라면 Pico 2 W는 현재 MicroPython에서 지원하지 않음** — 별도 SSID(WPA2-PSK 또는 IoT 전용 VLAN) 발급 요청이 사실상 필수.
  - 16개 MAC 사전 등록 정책 여부 확인

---

## B-1. Pico 2 W WiFi 안정성

### 칩셋과 Pico W(1세대)와의 관계
- Pico 2 W는 RP2350 기반이지만 무선은 **Infineon CYW43439 동일 칩**을 사용 → WiFi 동작 관점에서는 Pico W와 동일한 제약/특성이 그대로 적용된다.
- 2.4GHz 802.11n only (5GHz 미지원), Bluetooth 5.2.
- MicroPython 측면에서도 Pico W와 동일 드라이버(`network.WLAN`) 사용.

### 24/7 상시 가동 시 알려진 문제
- **자동 재연결이 보장되지 않는다.** WiFi 신호가 끊긴 뒤 신호가 돌아와도 MicroPython 펌웨어가 알아서 다시 연결해주는 동작은 신뢰할 수 없다는 보고가 라즈베리파이 공식 포럼에 다수 존재.
- 장시간(수 시간 이상) idle 상태로 두면 `wlan.isconnected()`가 True를 반환해도 실제로는 ping이 안 가는 "유령 연결" 상태가 보고됨 — MicroPython 1.20대 펌웨어에서 빈번, 이후 개선 진행 중이나 완전히 해결되었다고 단정할 근거 없음.
- **결론: 애플리케이션 레벨에서 주기적 헬스체크 + 재연결 루프 필수.**

### 16대 동시 운영 시 AP 부하
- 1분당 16건, 페이로드 ~200바이트 → 전송 자체의 트래픽 부하는 무시 가능(약 50KB/min).
- **실제 부담은 동시 associated 클라이언트 수.** 학교 AP가 학생 BYOD 기기까지 합쳐 이미 수십~수백 클라이언트를 들고 있는 경우, IoT 16대 추가가 클라이언트 테이블/DHCP 풀에 영향을 줄 수 있음. AP 모델별 권장 동시 접속 수(보통 50~250) 확인 필요.
- MQTT 영구 연결 방식은 TCP 세션을 계속 유지 → 학교가 idle TCP 세션을 강제로 끊는 정책이 있는지 확인 필요(keepalive 60초 권장).

### 재연결 패턴: 무엇이 권장되는가
- **Hard reset (`machine.reset()`) > `wlan.disconnect()` + `wlan.connect()` 재시도** 라는 의견과, 반대로 **소프트 재시도가 충분하다**는 의견이 공존. 실전 권장은 다음 계층 구조:
  1. N회 (예: 5회) 소프트 재시도: `wlan.disconnect()` → 잠시 대기 → `wlan.active(False)` → `wlan.active(True)` → `wlan.connect()`
  2. 그래도 실패 시 `machine.reset()`으로 전체 재부팅
  3. WDT(워치독)로 코드가 hang되어 1·2 단계 자체에 못 들어가는 상황까지 커버

### DHCP vs 고정 IP
- **고정 IP 권장.** 이유:
  - 어떤 노드가 죽었는지 IP로 즉시 식별 가능 (Grafana 대시보드/Mosquitto 로그에서)
  - DHCP 임대 갱신 시점의 미세한 재연결 실패 가능성 제거
  - 학교 네트워크 관리자도 16개 노드 IP를 미리 알 수 있어 방화벽 예외 처리 용이
- 단, **학교가 IP 정책을 통제**한다면 DHCP reservation(관리자에 MAC↔IP 매핑 요청)이 현실적.

### 검증된 재연결 코드 패턴 (참고용)
```python
# main.py 패턴 — production-ready 골격
import network, time, machine, ubinascii

SSID = "DGGOK_IoT"
PSK  = "***"
NODE_ID = "room-101"

def connect_wifi(timeout_s=20):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(SSID, PSK)
        t0 = time.ticks_ms()
        while not wlan.isconnected():
            if time.ticks_diff(time.ticks_ms(), t0) > timeout_s * 1000:
                return None
            time.sleep_ms(200)
    return wlan

def ensure_wifi():
    for attempt in range(5):
        wlan = connect_wifi()
        if wlan and wlan.isconnected():
            return wlan
        time.sleep(2 ** attempt)   # exponential backoff: 1,2,4,8,16s
    machine.reset()                # 마지막 보루: hard reset
```

GitHub 참고 구현:
- [dblanding/pico-OTA](https://github.com/dblanding/pico-OTA) — Pico W용 OTA + 재연결 패턴 포함
- [techtutorialsx — automatic connection to WiFi](https://techtutorialsx.com/2017/06/06/esp32-esp8266-micropython-automatic-connection-to-wifi/) — ESP 계열이지만 동일 패턴

---

## B-2. MQTT vs HTTP 비교

### 비교 표

| 기준 | MQTT (umqtt.robust2) | HTTP POST |
|------|----------------------|-----------|
| **연결 방식** | 영구 TCP 세션 | 매 요청마다 TCP 연결/해제 |
| **페이로드 오버헤드** | 작음 (헤더 2~4바이트) | 큼 (HTTP 헤더 수백 바이트) |
| **양방향 통신** | 자연스러움 (subscribe로 명령 수신) | 폴링 필요 |
| **16노드 fan-in** | 브로커가 자연스럽게 처리 | 서버에 N개 엔드포인트 트래픽 |
| **QoS / retained** | 지원 (QoS 0/1/2, retained) | 직접 구현 필요 |
| **방화벽 친화성** | △ (1883/8883 차단 가능) | ◎ (80/443은 거의 항상 열림) |
| **디버깅 난이도** | 중 (MQTT 클라이언트 도구 필요) | 쉬움 (curl/브라우저) |
| **학생 이해 쉬움** | △ (pub/sub 개념 학습 필요) | ◎ (요청-응답이 직관적) |
| **MicroPython 라이브러리** | umqtt.simple / umqtt.robust(2) | urequests (내장) |
| **장시간 안정성** | 영구연결 끊김 처리 필요 | 매 요청 stateless라 단순 |

### MicroPython MQTT 라이브러리

- **umqtt.simple**: 가장 가벼움. 자동 재연결 없음. 모든 예외 처리는 사용자 책임.
- **umqtt.robust**: simple 위에 `publish()` 실패 시 자동 reconnect 1회. 여전히 한계 있음 — 메시지 손실 가능, 구독 복원은 사용자 책임.
- **umqtt.robust2** (fizista 커뮤니티 포크): 메시지 큐잉, QoS 1 처리, 더 견고한 재연결. **production 권장**.
- 세 가지 모두 펌웨어 내장 아님 → `mip.install("umqtt.robust")` 필요.

### 페이로드 예시 (JSON, ~180바이트)

```json
{
  "node": "room-101",
  "ts": 1747800000,
  "temp_c": 24.3,
  "rh_pct": 52.1,
  "co2_ppm": 820,
  "pm25_ugm3": 18,
  "rssi": -67
}
```

### 학교망 방화벽이 1883/8883을 막을 가능성

- **충분히 있다.** 다수의 기관 방화벽이 MQTT 포트(특히 1883 평문)를 차단하는 것을 디폴트로 두며, 8883도 차단 사례 있음.
- 폴백 옵션:
  - **MQTT over WebSocket on 443** — 학교가 웹 트래픽을 막을 수는 없으므로 가장 확실. Mosquitto가 wss listener 지원.
  - **HTTPS POST** — 더 단순하지만 영구 연결 이점 포기.
- 권장 의사결정 순서:
  1. 학교 망 관리자에게 "1883/8883 outbound가 허용되는가?" 질의
  2. 거부되면 wss(443) 시도
  3. 그것도 거부되면 HTTPS POST + InfluxDB write API 직격

### 짧은 코드 예시

**MQTT 송신 (umqtt.robust2)**
```python
from umqtt.robust2 import MQTTClient
import json
client = MQTTClient(NODE_ID, "192.168.10.50", keepalive=60)
client.connect()
client.publish(b"dggok/room101/env", json.dumps(payload).encode())
```

**HTTP POST 송신 (urequests)**
```python
import urequests, json
r = urequests.post("http://192.168.10.50:8086/api/write",
                   data=json.dumps(payload),
                   headers={"Content-Type":"application/json"})
r.close()
```

---

## B-3. 서버 호스팅 옵션 비교

| 항목 | 학교 PC (Win/Linux) | 라즈베리파이 4 | 클라우드 | 하이브리드 (Pi + Cloud 백업) |
|------|---------------------|----------------|----------|------------------------------|
| **초기 비용** | 0원 (기존 PC 활용) | 약 12~18만원 (Pi4 4GB + SD + 케이스 + 5V 어댑터) | 0원 (HiveMQ Cloud Free) ~ 월 5~20달러 (VPS) | 약 12~18만원 + 클라우드 비용 |
| **운영 비용 (월)** | 전기 ~3,000~5,000원 | 전기 ~500원 (5W) | $0 (Free tier 한도 내) ~ $20 | Pi 전기 + 클라우드 백업 ~$0~3 |
| **24/7 안정성** | △ (Windows 업데이트 재부팅, 학생이 끄는 사고) | ◎ (전용 임베디드) | ◎ (SLA 있음, 단 Free tier는 SLA 없음) | ◎ |
| **학교망 방화벽 영향** | 학교 내부 → 영향 없음 | 학교 내부 → 영향 없음 | **아웃바운드 1883/8883/443 차단 시 사용 불가** | 1차는 내부, 백업만 클라우드 → 가장 안전 |
| **학생 직접 접근** | ◎ (콘솔 직접) | ◎ (SSH/직접) | △ (대시보드 GUI 위주) | ◎ |
| **유지보수 부담** | 중 (OS 업데이트, 백신, 학생 사고) | 낮음 (전용 머신, 자동 업데이트) | 낮음 (관리형) | 중 |
| **데이터 손실 위험** | 중 (학생이 만지다 사고) | 낮음 (SD 백업 정기화 시) | 낮음 | **가장 낮음** |
| **UPS 필요성** | (학교 정전 대비) 권장 | 권장 (소형 UPS 3~5만원) | 불필요 | Pi 측만 권장 |
| **교육적 가치** | 중 | **높음** (학생이 직접 만짐) | 중 (블랙박스 느낌) | 높음 |

### 추천: 라즈베리파이 4 (학교 내) + 선택적 클라우드 백업

- **이유**:
  - 학생이 SSH로 들어가서 `mosquitto_sub`, `journalctl`, Grafana 대시보드 편집까지 직접 다루는 경험 가능 (프로젝트의 학습 가치 핵심)
  - 데이터가 학교 LAN 내에서만 흐르므로 방화벽/개인정보 이슈 최소화
  - 학교 네트워크가 외부 차단되어도 LAN 내부는 동작 보장
- **표준 스택**: Mosquitto + Telegraf + InfluxDB 2.x + Grafana — Pi4 4GB에서 무리 없이 동작하는 조합으로 다수 사례 확인됨.
- **백업**: 주 1회 InfluxDB export → Google Drive/학교 서버. 또는 HiveMQ Cloud Free로 실시간 미러링 (100 세션, 10GB/월 무료).

---

## B-4. 학교망 인증 대응

### Pico 2 W의 인증 지원 현황 (사실 확인됨)

| 인증 방식 | Pico 2 W (MicroPython) 지원 |
|----------|-------------------------------|
| Open (인증 없음) | ◎ |
| WPA2-PSK (가정용/일반 사전공유키) | ◎ |
| WPA3-Personal (SAE) | △ (펌웨어에 따라 다름, 1.24+ 권장) |
| **WPA2/WPA3-Enterprise (EAP-PEAP / EAP-TTLS / MSCHAPv2 등)** | **✗ 미지원** |
| 캡티브 포털 (웹 로그인) | ✗ 미지원 (자동 로그인 별도 구현 필요) |

- 핵심 근거: CYW43439 칩 자체는 WPA Enterprise를 하드웨어적으로는 지원하지만, **MicroPython의 CYW43 드라이버에 EAP 지원 코드가 추가되지 않았다.** Pico SDK, CircuitPython 모두 동일한 한계. (raspberrypi/pico-feedback#303, micropython discussions #10399 참조 — 2026년 5월 시점 여전히 open 이슈)
- 한국 학교 무선망은 학교/지자체/사학재단마다 정책이 천차만별이지만, 교직원망에 EAP-PEAP/MSCHAPv2를 쓰는 사례가 많고, 학생망은 캡티브 포털인 경우가 흔함 — **두 가지 모두 Pico에서는 사실상 불가**.

### 사용자가 학교 네트워크 관리자에게 물어볼 체크리스트

```
[ 학교망 IoT 사전 확인 체크리스트 ]

1. 인증 방식
   □ 교직원 망 인증 방식은? (WPA2-PSK / WPA2-Enterprise / 캡티브 포털)
   □ WPA2-Enterprise라면 EAP 방식은? (PEAP-MSCHAPv2 / EAP-TLS / EAP-TTLS)
   □ IoT 디바이스용 별도 SSID(WPA2-PSK)를 발급받을 수 있는가?
   □ 발급된다면 격리 VLAN인가? 인터넷으로 나갈 수 있는가?

2. 디바이스 등록
   □ 16개 MAC 주소를 사전 등록해야 하는가?
   □ MAC 등록 양식/소요 시간은?
   □ 디바이스 교체 시 재등록 절차는?

3. 네트워크 정책
   □ IoT 디바이스가 학교 LAN 내부 서버(라즈베리파이)에 접근 가능한가?
      (클라이언트 격리 / AP isolation이 켜져 있으면 불가)
   □ Outbound 포트 정책: 1883, 8883, 443 중 어떤 것이 열려 있는가?
   □ 학교 외부에서 학교 LAN의 Grafana에 접근하려면? (VPN / 포트포워딩 / Tailscale 가능?)
   □ 정적 IP / DHCP reservation 발급 가능한가?

4. 운영
   □ 학기 중 무선망 정기 점검 시간? (그때 노드들이 일제히 끊김)
   □ 24/7 콘센트 사용에 대한 안전 점검은 어떻게?
   □ 방학 중에도 망 가동되는가?
```

### Plan B — Enterprise만 가능하다면

- **별도 무선 AP 구축**: 학교 망과 분리된 IoT 전용 WiFi(WPA2-PSK)를 라즈베리파이 4의 AP 모드 또는 별도 소형 라우터(GL.iNet 등)로 구성. 학교 LAN과는 유선으로만 연결. 가장 확실한 우회.
- 별도 망 사용 시 학교 인터넷에는 못 나가지만 **이 프로젝트는 LAN 내부 완결형이라 문제 없음** — 클라우드 백업이 필요할 때만 라즈베리파이가 학교 망에 별도로 합류하도록 설계 가능.

---

## B-5. 운영 안정성 패턴

### (1) WiFi 끊김 시 데이터 버퍼링
- Pico의 내부 flash 일부를 ring buffer로 사용. MicroPython에서 가장 간단한 방법은 **append-only JSONL 파일**:
  ```python
  def store_offline(payload):
      with open("/buffer.jsonl", "a") as f:
          f.write(json.dumps(payload) + "\n")
  ```
- 크기 제한: Pico 2 W 플래시 4MB 중 코드 제외하면 수백 KB 안전. 1건 ~200바이트 × 1분 = 12KB/시간 → 24시간치 ~300KB 보관 가능.
- 재연결되면 buffer 비우며 `publish`. 다 보낸 후 파일 truncate.

### (2) 와치독 (machine.WDT)
- **RP2350(Pico 2)의 WDT 최대 타임아웃은 약 8.3초** (RP2040과 동일 사양, 펌웨어 빌드에 따라). `WDT(timeout=8000)` 정도가 실용 최대치.
- 메인 루프 안에서 `wdt.feed()`를 호출 → 메인 루프가 어떤 이유로든 8초 이상 멈추면 자동 재부팅.
- **주의**: 한 번 활성화하면 끌 수 없고 timeout 재설정 불가. 디버깅 단계에선 끄고, 배포 시에만 활성화 권장.

```python
from machine import WDT
wdt = WDT(timeout=8000)
while True:
    do_measure_and_publish()
    wdt.feed()
    time.sleep(30)
```

### (3) OTA 업데이트 — 16노드 일괄
- Pico W용 OTA는 **펌웨어 자체 OTA는 어렵고**(2nd-stage bootloader 필요, 실수 시 브릭 위험), **MicroPython 애플리케이션 코드 OTA**는 검증된 방법이 존재:
  - `pico-OTA` (dblanding) — GitHub에 호스팅된 `manifest.json` + 파일들을 노드가 부팅마다 풀(pull)해서 갱신.
  - `kevsrobots micropython-ota` — 동일 컨셉 블로그 가이드.
  - PyPI `micropython-ota` 패키지.
- **권장 아키텍처**:
  - 학교 라즈베리파이가 `http://pi.local/ota/manifest.json` 호스팅
  - 노드들은 매일 새벽 3시(부팅 시 또는 cron-like 동작)에 manifest 체크 → 버전이 다르면 새 `.py` 파일들 다운로드 → `machine.reset()`
  - 노드 한 개씩 점진 rollout (manifest에 `min_node_id`/`max_node_id` 필터)으로 16대 일괄 실패 방지
- 펌웨어(uf2) 업그레이드는 학기 초/말 USB로 직접 처리하는 것을 기본으로 두는 것이 안전.

### (4) 헬스체크 — 어떤 노드가 죽었는지 알기
- **MQTT Last Will and Testament (LWT)** 활용:
  ```python
  client.set_last_will(b"dggok/room101/status", b"offline", retain=True)
  client.connect()
  client.publish(b"dggok/room101/status", b"online", retain=True)
  ```
  노드가 깔끔하게 끊기지 않으면 브로커가 자동으로 `offline` 메시지를 retained로 발행 → Grafana에서 상태 패널에 즉시 반영.
- 추가로 매 publish 페이로드에 `rssi`, `uptime`, `free_mem`을 포함 → 노이즈 끼는 교실 식별, OOM 임박 노드 사전 발견 가능.
- 알림: Grafana Alert → 카카오톡 채널/이메일/디스코드 webhook으로 "room-103 5분간 응답 없음" 즉시 통보.

---

## 추천 아키텍처

```
[교실 1 Pico 2 W] ─┐
[교실 2 Pico 2 W] ─┤                                ┌─→ [InfluxDB 2.x]
[교실 3 Pico 2 W] ─┤   학교 WiFi                    │       │
       ...        ─┼─→ (IoT 전용 SSID, WPA2-PSK) ─→ [Mosquitto] ─→ [Telegraf]
[교실 15 Pico]    ─┤        (별도 VLAN 권장)         │       │
[교실 16 Pico]    ─┘                                │       └─→ [Grafana 대시보드]
                                                    │            (학교 LAN: pi.local:3000)
                          모두 라즈베리파이 4 위에서 동작
                          (Docker Compose 1식, UPS 연결)

   주 1회 백업(선택): InfluxDB export → Google Drive 또는 HiveMQ Cloud Free
```

### MQTT 토픽 설계 (제안)
```
dggok/<room_id>/env          ← 측정 데이터 (QoS 0, retain=False)
dggok/<room_id>/status       ← online/offline (QoS 1, retain=True, LWT)
dggok/<room_id>/cmd          ← 서버 → 노드 명령 (예: 측정주기 변경)
dggok/_broadcast/ota         ← OTA 트리거 (전체)
```

---

## 미해결 / 사용자 확인 필요

- [ ] **학교 무선망 인증 방식** — WPA2-PSK 발급 가능 여부 (가장 중요. 이거 안 되면 Plan B로 별도 AP 구축)
- [ ] 학교 망 outbound 포트(1883 / 8883 / 443) 정책
- [ ] AP isolation (클라이언트 간 통신 차단) 여부 — 켜져 있으면 같은 SSID 내 Pico ↔ Pi 통신도 막힘
- [ ] 라즈베리파이 4를 학교 교무실/서버실/교실에 설치 가능한 위치
- [ ] UPS 예산 (3~5만원) 포함 가능 여부
- [ ] 학기 중/방학 중 운영 모드 차이 (방학 중 학교 망 다운 시 데이터 손실 정책)
- [ ] 16개 MAC 사전 등록 필요 여부 및 양식
- [ ] 외부에서 Grafana 접근 필요한가? (필요하면 Tailscale/Cloudflare Tunnel 검토)
- [ ] Pico 2 W의 WPA3-Personal 지원 여부 — MicroPython 1.24/1.25 펌웨어로 실기 테스트 1대 우선 필요

---

## 출처

- [Pico W issues with reconnect after WiFi signal loss — Raspberry Pi Forums](https://forums.raspberrypi.com/viewtopic.php?t=346686)
- [Restoring WLAN connection the right way — Raspberry Pi Forums](https://forums.raspberrypi.com/viewtopic.php?t=339231)
- [Raspberry Pi Pico W: Getting Started with Wi-Fi (MicroPython) — Random Nerd Tutorials](https://randomnerdtutorials.com/raspberry-pi-pico-w-wi-fi-micropython/)
- [Pico W MicroPython WiFi: A Comprehensive Guide](https://www.pythontutorials.net/blog/pico-w-micropython-wifi/)
- [CircuitPython connects WiFi with ease on the Raspberry Pi Pico 2 W — Adafruit blog](https://blog.adafruit.com/2024/11/25/circuitpython-connects-wifi-with-ease-on-the-raspberry-pi-pico-2-w-tomshardware/)
- [micropython-umqtt.simple — PyPI](https://pypi.org/project/micropython-umqtt.simple/)
- [micropython-umqtt.robust — PyPI](https://pypi.org/project/micropython-umqtt.robust/)
- [micropython-umqtt.robust2 — PyPI / fizista GitHub](https://github.com/fizista/micropython-umqtt.robust2)
- [umqtt.robust 소스 — micropython-lib](https://github.com/micropython/micropython-lib/tree/master/micropython/umqtt.robust)
- [Connecting Raspberry Pi Pico W's with MQTT — dev.to](https://dev.to/shilleh/connecting-raspberry-pi-pico-ws-with-mqtt-18gl)
- [Does micropython for Pico W support PEAP/MSCHAPV2? — pico-feedback #303](https://github.com/raspberrypi/pico-feedback/issues/303)
- [Does micropython for Pico W support PEAP/MSCHAPV2? — micropython discussions #10399](https://github.com/orgs/micropython/discussions/10399)
- [Is it possible to add WPA2 enterprise? — pico-sdk #1175](https://github.com/raspberrypi/pico-sdk/issues/1175)
- [Connecting to Enterprise Wi-Fi with Raspberry Pi Pico W — Raspberry Pi Forums](https://forums.raspberrypi.com/viewtopic.php?t=371014)
- [MQTT Ports: Common Ports and How to Configure and Secure Them — EMQ](https://www.emqx.com/en/blog/mqtt-ports)
- [HiveMQ Cloud Free Plan](https://www.hivemq.com/products/mqtt-cloud-broker/)
- [HiveMQ Cloud pay-as-you-go](https://www.hivemq.com/blog/hivemq-cloud-offers-pay-as-you-go-plan/)
- [Raspberry Pi IoT: Sensors, InfluxDB, MQTT, and Grafana — DZone](https://dzone.com/articles/raspberry-pi-iot-sensors-influxdb-mqtt-and-grafana)
- [Datalogging with MQTT, Node-RED, InfluxDB, and Grafana — SuperHouse](https://www.superhouse.tv/41-datalogging-with-mqtt-node-red-influxdb-and-grafana/)
- [Visualize MQTT Data with InfluxDB and Grafana — DIYI0T](https://diyi0t.com/visualize-mqtt-data-with-influxdb-and-grafana/)
- [machine.WDT — MicroPython docs](https://docs.micropython.org/en/latest/library/machine.WDT.html)
- [Watchdog timer on Raspberry Pi Pico — d3noob](http://www.d3noob.org/2024/03/the-watchdog-timer-on-raspberry-pi-pico.html)
- [pico-OTA — dblanding GitHub](https://github.com/dblanding/pico-OTA)
- [Over the Air updates with MicroPython — KevsRobots](https://www.kevsrobots.com/blog/micropython-ota.html)
- [PicoW Remote Firmware Upgrade (OTA) — NullOrigin](https://amiscreant.github.io/tutorials/PicoW/remote_flash)
- [micropython-ota — PyPI](https://pypi.org/project/micropython-ota/)
- [Robust WiFi Connection Script for an ESP8266 in MicroPython — Medium](https://sungkhum.medium.com/robust-wifi-connection-script-for-a-esp8266-in-micropython-239c12fae0de)
- [MicroPython and the Internet of Things, Part IV — Miguel Grinberg](https://blog.miguelgrinberg.com/post/micropython-and-the-internet-of-things-part-iv-wi-fi-and-the-cloud)
- [경희대학교 캠퍼스 WiFi 인증 안내](https://ois.khu.ac.kr/ois/user/contents/view.do?menuNo=14000035)
- [802.1x 기반 Wi-Fi 인증 — NETMANIAS](https://netmanias.com/ko/post/blog/5363/authentication-security-wi-fi/802-1x-based-wi-fi-authentication-and-internet-access)
- [고려대학교 무선랜 eduroam 설정](https://wifi.korea.ac.kr/wifi/eduroam/pc_mac.do)
