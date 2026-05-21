# Server — FastAPI + SQLite

라즈베리파이 4(또는 학교 PC)에서 돌리는 수집 서버.

## 설치

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 실행

```bash
uvicorn server:app --host 0.0.0.0 --port 8000
```

라즈베리파이에서 부팅 시 자동 시작하려면 systemd 서비스 등록:

```ini
# /etc/systemd/system/climate365.service
[Unit]
Description=Climate Action 365 collector
After=network.target

[Service]
User=pi
WorkingDirectory=/home/pi/climate-action-365/prototype/server
ExecStart=/home/pi/climate-action-365/prototype/server/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable climate365 && sudo systemctl start climate365
```

## API

| 메서드 | 경로 | 용도 |
|---|---|---|
| POST | `/reading` | Pico가 측정값 전송 |
| GET | `/readings?node_id=1-1&since_minutes=60` | 조회 |
| GET | `/nodes` | 노드 목록 + 최근 수신 |
| GET | `/health` | 헬스체크 |
| GET | `/docs` | Swagger UI (자동 생성) |

## 데이터 확인

```bash
sqlite3 data.db "SELECT node_id, received_at, temperature, humidity, lux FROM readings ORDER BY received_at DESC LIMIT 20;"
```

## 백업

`data.db` 파일을 주기적으로 USB·NAS로 복사. cron으로 매일 자동 백업 권장:

```cron
0 2 * * * cp /home/pi/climate-action-365/prototype/server/data.db /mnt/backup/data-$(date +\%Y\%m\%d).db
```

## Phase 2/3 확장

`co2_ppm`, `pm25`, `pm10` 컬럼은 이미 스키마에 들어 있음. Pico 펌웨어와 `Reading` 모델에 필드만 추가하면 바로 됨. 스키마 마이그레이션 불필요.
