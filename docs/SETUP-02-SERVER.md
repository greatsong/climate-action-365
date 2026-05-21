# SETUP-02 — 라즈베리파이 4 서버 설치

> 16개 교실 노드의 데이터를 수집·저장·시각화하는 중앙 서버를 만듭니다.
> 한 번 셋업하면 24/7 자동 가동되도록 systemd 서비스로 등록합니다.

## 준비물

| 항목 | 비고 |
|---|---|
| Raspberry Pi 4 (4GB) | 정품 |
| microSD 64GB (Sandisk High Endurance) | 산업용 권장, 24/7 쓰기 견딤 |
| 5V/3A USB-C 어댑터 | Pi4 정품급 |
| Micro HDMI → HDMI 케이블 | 초기 설정만 사용 |
| 모니터 + USB 키보드 | 초기 설정만 사용 (없으면 헤드리스 가능) |
| 컴퓨터 (Raspberry Pi Imager 실행용) | |
| LAN 케이블 또는 학교 WiFi 정보 | 유선 강력 권장 |

---

## 단계 1 · Raspberry Pi OS 설치 (microSD 굽기)

### 1.1 Raspberry Pi Imager 다운로드

- https://www.raspberrypi.com/software/
- 본인 컴퓨터 OS 맞춰 설치

### 1.2 OS 굽기

1. microSD를 컴퓨터에 연결 (USB 어댑터 사용)
2. **Raspberry Pi Imager** 실행
3. 세 가지 선택:
   - **CHOOSE DEVICE**: Raspberry Pi 4
   - **CHOOSE OS**: `Raspberry Pi OS (other)` → **Raspberry Pi OS Lite (64-bit)** 선택
     - GUI 불필요 (헤드리스 운영)
     - "Lite"는 데스크탑 환경 없는 가벼운 버전
   - **CHOOSE STORAGE**: 연결된 microSD 선택
4. **NEXT** 클릭

### 1.3 ⭐ 사전 설정 (반드시 입력)

"Edit Settings" 또는 "OS Customization" 다이얼로그가 뜸. **반드시 입력**:

**General 탭:**
| 항목 | 값 |
|---|---|
| Set hostname | `climate365` |
| Set username and password | username: `pi` / password: (안전한 것) |
| Configure wireless LAN | 학교 WiFi SSID/PW (유선 쓰면 생략 가능) |
| Wireless LAN country | KR |
| Set locale settings | Time zone: `Asia/Seoul`, Keyboard layout: `kr` 또는 `us` |

**Services 탭:**
| 항목 | 값 |
|---|---|
| Enable SSH | ✅ 체크 |
| 인증 방식 | Use password authentication |

**Options 탭:** 기본값 유지.

→ **Save** → **Yes, apply OS customisation settings** → **YES (덮어쓰기)**

쓰기 진행 (10~15분). 완료되면 microSD 제거.

---

## 단계 2 · 첫 부팅

### 2.1 하드웨어 연결

1. microSD를 Pi 4에 삽입 (보드 아래쪽 슬롯)
2. HDMI 모니터 연결 (Micro HDMI는 Pi의 **HDMI0** 포트)
3. USB 키보드 연결
4. **LAN 케이블 연결 (강력 권장)** — 학교 망 유선 콘센트
5. 5V/3A USB-C 어댑터 연결 → 자동 부팅

### 2.2 첫 부팅 (5~10분)

- 화면에 부팅 로그가 흐르다가 자동 재부팅 1~2회
- 최종적으로 로그인 프롬프트:
  ```
  climate365 login:
  ```
- 위에서 설정한 username/password로 로그인

### 2.3 네트워크 확인

```bash
hostname -I
# 출력 예: 192.168.0.123  (혹은 학교 망 대역)
```

이 IP를 기억해 둡니다. 이게 **서버 IP**입니다.

---

## 단계 3 · SSH 접속 (이후 헤드리스 작업)

본인 컴퓨터의 터미널에서:

```bash
ssh pi@192.168.0.123
# 처음 접속 시 yes 입력
# 패스워드 입력
```

> 이 시점부터 모니터·키보드 분리 가능. 모든 작업은 SSH로 합니다.

---

## 단계 4 · 시스템 업데이트 + 기본 패키지

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y python3-venv python3-pip git sqlite3 ufw htop
```

(5~10분 소요)

---

## 단계 5 · 고정 IP 설정 ⭐ (중요)

Pico 펌웨어의 `SERVER_URL`이 서버 IP를 박아두고 있으므로 IP가 바뀌면 16대가 모두 못 붙습니다. **고정 IP 필수**.

### 5.1 현재 네트워크 인터페이스 확인

```bash
nmcli con show
# 출력 예:
# NAME                UUID                                  TYPE      DEVICE
# Wired connection 1  abc...                                ethernet  eth0
```

### 5.2 정적 IP 설정

학교 망 대역이 `192.168.0.x`이고 고정으로 쓸 IP가 `192.168.0.10`이라고 가정 (망 관리자=본인이 결정):

```bash
sudo nmcli con mod "Wired connection 1" \
    ipv4.addresses 192.168.0.10/24 \
    ipv4.gateway 192.168.0.1 \
    ipv4.dns "8.8.8.8 1.1.1.1" \
    ipv4.method manual

sudo systemctl restart NetworkManager
```

### 5.3 적용 확인

```bash
ip addr show eth0
# eth0 inet 192.168.0.10/24 가 보여야 함
ping -c 3 8.8.8.8
# 인터넷 연결 확인
```

→ SSH 세션이 끊겼으면 새 IP로 다시 접속:
```bash
ssh pi@192.168.0.10
```

> 무선으로 운영할 거면 `"preconfigured"` 또는 무선 연결 이름으로 동일하게 적용. 단 **유선이 훨씬 안정적** — 서버는 유선 권장.

---

## 단계 6 · 프로젝트 파일 복사

본인 컴퓨터에서 (SSH 세션 말고 본인 컴퓨터 터미널에서) 프로젝트 폴더를 Pi로 복사:

```bash
# 본인 맥에서:
scp -r ~/greatsong-project/climate-action-365 pi@192.168.0.10:/home/pi/
```

또는 git에 올려두었다면 Pi에서:
```bash
cd /home/pi
git clone https://github.com/본인계정/climate-action-365.git
```

복사 확인 (Pi에서):
```bash
ls /home/pi/climate-action-365/prototype/server/
# server.py  requirements.txt  README.md
```

---

## 단계 7 · 서버 가상환경 + 의존성 설치

```bash
cd /home/pi/climate-action-365/prototype/server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

(2~3분 소요)

설치 확인:
```bash
pip list | grep -E "fastapi|uvicorn|pydantic"
# fastapi   0.110.0
# uvicorn   0.27.0
# pydantic  2.5.x
```

---

## 단계 8 · 서버 수동 실행 (테스트)

```bash
# venv 활성화 상태에서:
uvicorn server:app --host 0.0.0.0 --port 8000
```

다음과 같은 로그가 보이면 OK:
```
INFO:     Started server process [1234]
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### 동작 확인

본인 컴퓨터 브라우저에서:
```
http://192.168.0.10:8000/health    → {"ok":true}
http://192.168.0.10:8000/docs      → Swagger UI 표시
http://192.168.0.10:8000/nodes     → [] (아직 노드 없음)
```

확인되면 `Ctrl+C` 로 종료.

---

## 단계 9 · 서버를 systemd 서비스로 등록 (자동 시작)

### 9.1 서비스 파일 작성

```bash
sudo nano /etc/systemd/system/climate365.service
```

다음 내용 입력 (그대로 복붙):

```ini
[Unit]
Description=Climate Action 365 collector
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/climate-action-365/prototype/server
ExecStart=/home/pi/climate-action-365/prototype/server/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

`Ctrl+O` → `Enter` (저장) → `Ctrl+X` (닫기)

### 9.2 서비스 활성화 및 시작

```bash
sudo systemctl daemon-reload
sudo systemctl enable climate365
sudo systemctl start climate365
sudo systemctl status climate365
```

`active (running)` 이 보이면 성공.

### 9.3 재부팅 후 자동 시작 검증

```bash
sudo reboot
# 1분 대기 후 다시 SSH 접속
ssh pi@192.168.0.10
sudo systemctl status climate365   # 여전히 active 인지
curl http://localhost:8000/health   # {"ok":true}
```

---

## 단계 10 · 대시보드 (Streamlit) 설치 및 서비스 등록

### 10.1 대시보드 의존성

```bash
cd /home/pi/climate-action-365/prototype/dashboard
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 10.2 SERVER_URL 수정

대시보드와 서버가 같은 Pi에서 돌므로 `localhost`로:

```bash
nano app.py
```

상단의 다음 줄 확인 (이미 `localhost`로 되어 있으면 그대로):
```python
SERVER_URL = "http://localhost:8000"
```

### 10.3 대시보드 수동 실행 테스트

```bash
streamlit run app.py --server.address 0.0.0.0 --server.port 8501 --server.headless true
```

본인 컴퓨터 브라우저에서:
```
http://192.168.0.10:8501
```

대시보드가 보이면 OK. `Ctrl+C` 로 종료.

### 10.4 대시보드 systemd 서비스

```bash
sudo nano /etc/systemd/system/climate365-dashboard.service
```

```ini
[Unit]
Description=Climate Action 365 dashboard (Streamlit)
After=climate365.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/climate-action-365/prototype/dashboard
ExecStart=/home/pi/climate-action-365/prototype/dashboard/venv/bin/streamlit run app.py --server.address 0.0.0.0 --server.port 8501 --server.headless true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable climate365-dashboard
sudo systemctl start climate365-dashboard
sudo systemctl status climate365-dashboard
```

→ 이제 Pi 재부팅해도 서버·대시보드 둘 다 자동 시작.

---

## 단계 11 · 자동 백업 (cron)

### 11.1 백업 위치 만들기

내장 microSD에 백업하면 카드 고장 시 같이 날아갑니다. **외장 USB 메모리** 권장:

1. USB 메모리(예: 32GB)를 Pi의 USB 포트에 꽂기
2. 마운트 확인:
   ```bash
   lsblk
   # sda1 32G   ... → /media/pi/USB 또는 미마운트
   ```
3. 미마운트면 수동 마운트:
   ```bash
   sudo mkdir -p /mnt/backup
   sudo mount /dev/sda1 /mnt/backup
   sudo chown pi:pi /mnt/backup
   ```
4. 자동 마운트 (`/etc/fstab` 추가):
   ```bash
   sudo blkid /dev/sda1
   # UUID="..." 확인
   echo "UUID=위의UUID /mnt/backup ext4 defaults,nofail 0 2" | sudo tee -a /etc/fstab
   ```

### 11.2 cron 백업 작업

```bash
crontab -e
# 처음이면 nano 선택
```

파일 끝에 추가:

```cron
# 매일 새벽 2시 SQLite 백업
0 2 * * * cp /home/pi/climate-action-365/prototype/server/data.db /mnt/backup/data-$(date +\%Y\%m\%d).db

# 30일 지난 백업 자동 삭제
30 2 * * * find /mnt/backup -name "data-*.db" -mtime +30 -delete
```

저장.

---

## 단계 12 · 방화벽 (선택, 권장)

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp     # SSH
sudo ufw allow 8000/tcp   # FastAPI (Pico 데이터 수신)
sudo ufw allow 8501/tcp   # Streamlit 대시보드
sudo ufw enable
sudo ufw status verbose
```

---

## 단계 13 · 운영 모니터링

### 13.1 로그 확인

```bash
# 서버 로그 (실시간)
sudo journalctl -u climate365 -f

# 대시보드 로그 (실시간)
sudo journalctl -u climate365-dashboard -f

# 종료: Ctrl+C
```

### 13.2 시스템 상태

```bash
htop          # CPU·메모리 (q로 종료)
df -h         # 디스크 여유 (microSD)
du -sh /home/pi/climate-action-365/prototype/server/data.db
              # DB 파일 크기
```

### 13.3 데이터 직접 조회

```bash
sqlite3 /home/pi/climate-action-365/prototype/server/data.db
# 안에서:
.mode column
.headers on
SELECT node_id, received_at, temperature, humidity, lux FROM readings ORDER BY received_at DESC LIMIT 20;
.quit
```

### 13.4 디스크 사용량 추정

- 측정 1건 ≈ 200바이트
- 16노드 × 30초 주기 = 1분당 32건 = **하루 약 9MB**
- **1년 ≈ 3.3GB** → 64GB microSD로 수년 운영 가능

---

## 트러블슈팅

### 서비스가 active 인데 외부에서 못 붙음
- 방화벽 차단: `sudo ufw status` 확인
- 서비스가 `127.0.0.1` 만 듣고 있을 가능성: `--host 0.0.0.0` 확인
- IP가 바뀌었나: `hostname -I` 재확인 (DHCP 풀로 돌아가 있을 수도)

### `sudo systemctl status climate365` 가 failed
- 로그 확인: `sudo journalctl -u climate365 -e`
- 가장 흔한 원인:
  - venv 경로 오타
  - WorkingDirectory 안 맞음
  - pip 설치 실패 (`source venv/bin/activate && pip install -r requirements.txt` 다시)

### 디스크 빠르게 참
- 1년에 약 3GB. 만약 너무 빠르면 → 측정 주기를 늘리거나 (`INTERVAL_SEC = 60`), 오래된 데이터를 압축 백업 후 DB에서 삭제:
  ```sql
  DELETE FROM readings WHERE received_at < '2025-01-01';
  VACUUM;
  ```

### microSD 수명
- High Endurance도 24/7 쓰기에 1~2년 후 약해질 수 있음. **반드시 외장 백업 cron 가동**.
- 1년 주기로 microSD 교체 + 클론하면 안전.
