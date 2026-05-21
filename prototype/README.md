# 프로토타입 — Phase 1

1개 교실 파일럿 → 16개 교실 확장까지 가는 최소 동작 코드.

## 전체 구조

```
[교실 Pico] ──HTTP POST(JSON)──> [라즈베리파이4 FastAPI]
                                    ↓
                                  [SQLite data.db]
                                    ↑
                              [Streamlit 대시보드]
```

- 펌웨어: `firmware/` (MicroPython, Pico 2 WH)
- 서버: `server/` (FastAPI + SQLite, Python 3.10+)
- 대시보드: `dashboard/` (Streamlit)

## 빠른 실행 순서 (1교실 파일럿)

### 1. 서버 (라즈베리파이 또는 노트북)

```bash
cd server
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8000
```

서버 IP 확인 (예: `192.168.0.10`).

### 2. Pico 펌웨어

1. Pico 2 WH에 MicroPython 1.24+ 플래시
2. `firmware/secrets.py` 편집:
   ```python
   WIFI_SSID = "DanggokIoT"
   WIFI_PASSWORD = "실제_패스워드"
   NODE_ID = "1-1"
   SERVER_URL = "http://192.168.0.10:8000/reading"
   ```
3. Thonny로 `secrets.py`, `sensors.py`, `main.py`를 Pico에 복사
4. SHT40·BH1750을 Grove Shield I2C0 슬롯에 연결
5. Pico 재부팅 → 30초마다 콘솔에 측정 로그

### 3. 대시보드

```bash
cd dashboard
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

브라우저에서 `http://localhost:8501` → 첫 측정값이 들어오면 그리드에 노드 표시.

## 동작 확인 체크리스트

- [ ] Pico 콘솔에 `WiFi 연결됨: IP=...` 표시
- [ ] Pico 콘솔에 `측정: T=... RH=... lux=...` 표시
- [ ] `curl http://서버IP:8000/nodes` 응답에 노드 보임
- [ ] Streamlit 대시보드의 "전체 교실" 탭에 노드 카드 표시
- [ ] 교실 상세 탭에 시계열 차트 표시

## 16교실 확장

1개 교실에서 1주 안정 운영 후:
1. Pico 노드 15개 추가 조립 (조립팀)
2. 각 노드의 `secrets.py`에서 `NODE_ID`만 변경 (예: `1-2`, `1-3`, ..., `3-8`)
3. 동일 SSID·서버 URL 사용
4. 대시보드는 코드 변경 없이 자동으로 16개 표시

## 알려진 한계 (Phase 1)

- 동시접속 수십 명 이상에서 Streamlit이 느려질 수 있음 (운영팀 모니터링 + 분석팀 작업만이라면 충분)
- 알림은 수동 확인 (Phase 2에서 슬랙·이메일 알림 추가 예정)
- OTA 업데이트 없음 — 펌웨어 수정 시 USB 재플래시 필요

## Phase 2 (CO2) 추가 시 변경

- `firmware/sensors.py`: SCD41 드라이버 추가
- `firmware/main.py`: 측정 함수에 `co2_ppm` 추가
- `server/server.py`: 변경 없음 (이미 컬럼 예약됨)
- `dashboard/app.py`: `LIMITS`에 `co2_ppm: {min: None, max: 1000}` 추가
