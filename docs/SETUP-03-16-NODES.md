# SETUP-03 — 16대 동시 운영 가이드

> SETUP-01(1대 파일럿)과 SETUP-02(서버)가 검증 완료된 다음 진행합니다.
> 학생 조립팀과 함께 작업하는 것을 전제로 합니다.

## 사전 조건 체크

- [ ] SETUP-01 파일럿 1대가 서버에 데이터 보내고 대시보드에 정상 표시
- [ ] SETUP-02 서버·대시보드가 systemd로 24/7 가동 중
- [ ] 부품 일괄 발주 완료 (구글 시트 BOM 기준)
- [ ] 학생 조립팀 모집 + 1차 오리엔테이션 완료

---

## 단계 1 · 부품 입고 점검

### 1.1 수령 직후 (조립팀 책임자가 직접)

발주 시트의 각 행마다 수량 확인:
- SHT40 18개 (16 + 예비 2)
- BH1750 GY-302 18개
- Grove-Grove 케이블 5pcs × 4팩 = 20개
- Grove-점퍼 변환 케이블 5pcs × 4팩 = 20개
- 마이크로 USB 케이블 19개
- USB 어댑터 16개
- ABS 박스 18개
- 부자재(케이블타이·라벨)

### 1.2 무작위 표본 동작 점검 (5대 정도)

파일럿 Pico에 5개 SHT40·BH1750을 돌려가며 끼워 보면서 I2C 스캔으로 `0x44`·`0x23`이 잡히는지 확인. 불량 모듈이 섞여 있으면 발주처에 교체 요청.

---

## 단계 2 · NODE_ID ↔ 교실 매핑표 만들기

### 2.1 구글 시트로 매핑표 작성

```
NODE_ID | 교실      | 담당 학생 | MAC 주소 | 조립일 | 설치일 | 비고
1-1     | 1학년 1반 | 김OO     |          |        |        |
1-2     | 1학년 2반 | 이OO     |          |        |        |
...
3-8     | 3학년 8반 | 박OO     |          |        |        |
```

NODE_ID 명명 규칙(권장): `학년-반` 또는 `층-호` 등 학교에서 통용되는 단위로.

---

## 단계 3 · MAC 주소 일괄 수집

> 학교 망이 MAC 등록제이거나, 어떤 Pico가 어느 교실에 있는지 추적이 필요할 때.

### 3.1 펌웨어에 MAC 출력 코드 한 줄 추가

`prototype/firmware/main.py` 의 `connect_wifi()` 함수 안, `wlan.active(True)` 바로 다음 줄에 추가:

```python
import ubinascii
mac = ubinascii.hexlify(wlan.config('mac'), ':').decode()
log("MAC: {}".format(mac))
```

> 이 코드는 이미 추가해 둬도 무방 (운영 중에도 부팅 로그에 MAC이 찍힘 → 추적에 유리).

### 3.2 16대 MAC 일괄 수집 절차

각 Pico를 차례로 컴퓨터에 USB로 연결하면서:

```bash
# 컴퓨터에 mpremote 설치 (1회)
pip install mpremote

# 각 Pico에 대해 실행 (USB 연결 후):
mpremote exec "
import network, ubinascii
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
print(ubinascii.hexlify(wlan.config('mac'), ':').decode())
"
```

출력 예:
```
28:cd:c1:0e:5f:42
```

→ 이 MAC을 매핑표의 해당 NODE_ID 행에 기록 + Pico 본체에 라벨 부착 (예: `1-1 / 28:cd:c1:0e:5f:42`).

### 3.3 라벨 부착

- ABS 박스 외부에 큰 라벨 (예: `1-1 1학년 1반`)
- Pico 본체에 작은 라벨 (예: `1-1`)
- 박스 내부에 MAC 라벨 (분실 대비)

---

## 단계 4 · 일괄 펌웨어 배포 자동화

### 4.1 16개 `secrets.py` 미리 생성

본인 컴퓨터에서:

```bash
mkdir -p /tmp/climate365-configs

ROOMS=("1-1" "1-2" "1-3" "1-4" "1-5" "1-6" "1-7" "1-8" \
       "2-1" "2-2" "2-3" "2-4" "2-5" "2-6" "2-7" "2-8")
# 또는 실제 교실 16개 — 3학년이면 위 배열에 추가

SRC=~/greatsong-project/climate-action-365/prototype/firmware/secrets.py

for room in "${ROOMS[@]}"; do
  sed "s/NODE_ID = \"1-1\"/NODE_ID = \"$room\"/" "$SRC" \
    > /tmp/climate365-configs/secrets_$room.py
done

ls /tmp/climate365-configs/
# secrets_1-1.py  secrets_1-2.py  ...
```

> `secrets.py` 안에 NODE_ID = "1-1" 디폴트로 잡혀 있다고 가정. 다른 값이면 sed 패턴 조정.

### 4.2 배포 스크립트 작성

`~/climate365-deploy.sh` 만들기:

```bash
#!/bin/bash
# 사용법: ./climate365-deploy.sh 1-1
set -e

if [ -z "$1" ]; then
  echo "사용법: $0 <NODE_ID>  (예: 1-1)"
  exit 1
fi

NODE_ID=$1
FW_DIR=~/greatsong-project/climate-action-365/prototype/firmware
CFG_DIR=/tmp/climate365-configs

echo "==> $NODE_ID 배포 시작"

# 기존 파일 정리 (선택)
mpremote rm :main.py || true
mpremote rm :sensors.py || true
mpremote rm :secrets.py || true
mpremote rm :buffer.jsonl || true

# 새 파일 업로드
mpremote cp "$FW_DIR/sensors.py" :
mpremote cp "$FW_DIR/main.py" :
mpremote cp "$CFG_DIR/secrets_$NODE_ID.py" :secrets.py

echo "==> $NODE_ID 배포 완료. 5초 후 재부팅..."
sleep 1
mpremote reset

echo "==> $NODE_ID OK"
```

실행 권한:
```bash
chmod +x ~/climate365-deploy.sh
```

### 4.3 16대 일괄 배포 흐름

작업장 한 자리에서 16번 반복:

1. **Pico 1대를 USB 연결** (라벨 확인, 예: `1-1`)
2. 터미널에서:
   ```bash
   ~/climate365-deploy.sh 1-1
   ```
3. 5초 안에 `OK` 메시지 → USB 분리
4. 다음 Pico 연결, NODE_ID 바꿔서 반복

→ 16대 배포 약 15~20분 소요.

### 4.4 배포 검증

각 노드 배포 후, 컴퓨터 브라우저로:
```
http://192.168.0.10:8000/nodes
```
방금 배포한 NODE_ID가 보이는지 (WiFi가 작업장에 잡힌다고 가정).

---

## 단계 5 · 조립 작업장 워크플로우 (학생 조립팀)

### 5.1 작업대 셋업

- 4~6명 작업할 수 있는 큰 테이블
- 부품 상자 카테고리별 분류 (모듈·케이블·박스·USB)
- 멀티탭 (작업 중 동작 검증용)
- 노트북 1대 (mpremote 배포 + 대시보드 확인)
- 절연 매트 (정전기 방지)

### 5.2 노드 1개 조립 표준 절차 (학생용)

> **페어 워크 권장**: 1명 조립, 1명 검증.

**Step 1 — Pico에 Grove Shield 끼우기**
- Pico 헤더 핀과 Shield의 소켓 방향 정렬
- 무리해서 끼우지 말 것. 약간 비뚤어지면 핀 휘어짐
- 안 끼워지면 잠시 빼고 정렬 다시

**Step 2 — SHT40 연결**
- SHT40 모듈 ↔ Grove-Grove 케이블 (한쪽만 끼워짐)
- 케이블 반대쪽 → Shield의 **I2C 슬롯 (인쇄 'I2C')** 중 하나

**Step 3 — BH1750 GY-302 연결**
- 변환 케이블의 점퍼 4개를 GY-302 핀에 매핑:
  - VCC ← 빨강
  - GND ← 검정
  - SCL ← 노랑
  - SDA ← 흰색
- 변환 케이블 Grove 쪽 → Shield의 **다른 I2C 슬롯**

**Step 4 — 마이크로 USB 케이블 연결 + 전원**
- USB 어댑터 → 멀티탭
- 마이크로 USB → Pico 본체 USB 포트
- Pico LED가 들어오면 OK

**Step 5 — 동작 검증 (학생이 노트북에서)**
- 노트북 브라우저로 `http://192.168.0.10:8501` (Streamlit 대시보드)
- "전체 교실" 탭에서 방금 조립한 NODE_ID(예: `1-1`)가 보이는지 확인 (1분 이내)
- 측정값 합리적인지 확인

**Step 6 — ABS 박스에 고정**
- 박스 안쪽에 양면테이프로 Pico+Shield 부착
- SHT40·BH1750은 박스 안 빈 공간에 배치 (모듈 부품끼리 안 닿게)
- 케이블 정리는 케이블타이로
- 박스 뚜껑 덮기 전 통기 구멍 확인 (조도·온도 측정에 영향)
  - 조도용: 박스 측면에 직경 5~10mm 작은 구멍 1개 (BH1750 위치 쪽)
  - 온도용: 박스 측면·상면에 슬릿 (실내 공기 순환)

**Step 7 — 라벨링**
- 박스 외부에 큰 라벨 (NODE_ID + 교실명)
- 박스 내부에 작은 라벨 (MAC + 조립일 + 담당자)

**Step 8 — 매핑표에 "조립 완료" 체크**

### 5.3 1노드당 예상 시간

- 숙련된 학생: 15분/노드
- 처음 조립하는 학생: 30~40분/노드
- 16노드 전체: 1회 워크숍 (4시간 × 4명 페어) 에 충분

---

## 단계 6 · 교실 설치

### 6.1 설치 위치 원칙

| 원칙 | 이유 |
|---|---|
| **호흡 높이 1.0~1.5m** | 학생이 실제 호흡하는 공기 측정 (WHO·EPA 권장) |
| **직사광선 없는 곳** | 조도 센서 왜곡 + 온도 인공 상승 방지 |
| **콘센트 가까이 (1m 이내)** | USB 어댑터 줄 길이 한계 |
| **에어컨·히터·창문 정통 X** | 국부 온도 영향 |
| **학생 손 안 닿는 곳** | 안전·고장 방지 (캐비닛 위·게시판 옆 벽) |
| **천장 X** | 호흡 높이가 아님, PM 측정에서 특히 부적절 |

### 6.2 설치 절차 (운영팀 학생 + 교사 동행)

1. 교실 진입, 위치 선정
2. 양면테이프 또는 케이블타이로 박스 고정
3. USB 어댑터 콘센트에 꽂기
4. 전원 인가 후 30초~1분 대기
5. 스마트폰으로 대시보드 열어 해당 NODE_ID 확인:
   ```
   http://192.168.0.10:8501
   ```
   "마지막 수신"이 1분 이내면 OK
6. 매핑표에 설치 완료 시각 기록
7. 교실 담임에게 한 줄 안내 ("이 박스는 환경 측정용입니다. 분리하지 말아주세요.")

### 6.3 16교실 설치 소요 시간

- 1교실당 약 5~10분
- 16교실 = **2~3시간** (학생 운영팀 4명이 4교실씩 분담하면 1시간)

---

## 단계 7 · 운영 모니터링 (운영팀 학생 일일 업무)

### 7.1 일일 점검 (등교 직후 5분)

대시보드 "전체 교실" 탭 열기:

- 🚨 표시된 노드가 있나? (5분 이상 미수신)
  - 있으면 → 해당 교실 방문 → 전원 케이블 확인 → 안 되면 박스 열어 USB 재연결
- 모든 노드의 측정값이 합리적인가?
  - 명백히 이상한 값 (예: 온도 -45°C) → 박스 열어 케이블 재연결

### 7.2 주간 점검 (운영팀 회의 시)

- 분석팀과 함께 데이터 무결성 검토
  - 같은 값이 1시간 이상 고정된 노드 = 센서 고정 또는 고장
  - 측정 횟수가 다른 노드보다 현저히 적은 노드 = WiFi 끊김 빈번
- `sudo journalctl -u climate365 -e | grep ERROR` 로 서버 에러 점검

### 7.3 월간 점검

- 데이터베이스 백업 검증:
  ```bash
  ls -lh /mnt/backup/ | tail -5
  ```
- 노드별 측정 횟수 통계 (어떤 노드가 자주 끊겼나):
  ```bash
  sqlite3 /home/pi/climate-action-365/prototype/server/data.db <<EOF
  .mode column
  .headers on
  SELECT node_id, COUNT(*) as count, MAX(received_at) as last
  FROM readings
  WHERE received_at >= date('now','-30 days')
  GROUP BY node_id
  ORDER BY count;
  EOF
  ```
- 분석팀 월간 리포트 작성

---

## 단계 8 · 장애 대응 절차

### 8.1 노드 1개 죽음

**증상:** 대시보드 "전체 교실"에 해당 NODE에 🚨, "마지막 수신"이 10분 이상 전

**대응 흐름:**

1. 해당 교실 방문 (운영팀)
2. 전원 LED 확인
   - LED 꺼짐 → USB 어댑터·콘센트·케이블 의심
   - LED 켜짐 → WiFi 또는 센서 의심
3. USB 케이블 한 번 빼고 다시 꽂기 (소프트 리셋)
4. 5분 기다려 대시보드 갱신
5. 여전히 안 되면 **예비 노드와 즉시 교체**
   - 죽은 노드는 조립팀 작업장으로 회수, 디버깅
6. 매핑표에 장애·교체 이력 기록

### 8.2 여러 노드 동시 죽음

**증상:** 3개 이상 노드가 동시에 🚨

**대응:**

1. 학교 WiFi 망 상태 확인 (관리자 본인이 빠르게 가능)
2. 서버 상태:
   ```bash
   sudo systemctl status climate365
   sudo systemctl status climate365-dashboard
   ```
3. 서버가 죽었으면 → `sudo systemctl restart climate365`
4. WiFi가 끊겼으면 → AP 재부팅 / 학교망 점검
5. 모든 게 정상인데도 노드들 안 붙으면 → 16대 한 번에 죽지는 않으니 원인 더 조사 (전원 회로 등)

### 8.3 측정값 명백히 이상

**케이블 빠짐 의심 (가장 흔함):**
- 박스 열어 Grove 케이블·점퍼 재연결

**센서 고장 (드물지만 발생):**
- 예비 모듈로 교체
- 고장 모듈은 폐기 또는 발주처 교환 요청

---

## 단계 9 · 정기 유지보수

### 9.1 학기 시작 (3월·9월)

- 모든 16노드 동작 검증
- `secrets.py` WiFi 패스워드 변경 여부 확인 (학교가 학기마다 바꾸면 일괄 재배포 필요)
- 분석팀 신입생 교육

### 9.2 매월

- 데이터 백업 검증 (`/mnt/backup/` 파일 목록·크기)
- 노드 표면 먼지 청소 (조도 센서 정확도)
- 데이터베이스 vacuum (선택, 디스크 절약):
  ```bash
  sqlite3 /home/pi/climate-action-365/prototype/server/data.db "VACUUM;"
  ```

### 9.3 학년말 (12월·2월)

- 운영 데이터 압축 보존:
  ```bash
  cp /home/pi/climate-action-365/prototype/server/data.db /mnt/backup/data-final-2026.db
  gzip /mnt/backup/data-final-2026.db
  ```
- 학년 운영 보고서 (조립팀·분석팀·운영팀 각각)
- 졸업생 → 후배에게 인계

### 9.4 방학 중

- 노드 전원 끄지 말고 가동 유지 (방학 환경 데이터도 가치)
- 학교 정전·점검 일정에 맞춰 일시 정전 후 자동 복구 검증

---

## 단계 10 · Phase 2 확장 (CO2 센서 추가)

> Phase 1 안정 운영 1~2학기 후, 예산 확보되면.

### 10.1 SCD41 발주

- 16개 + 예비 2개 = 18개
- 약 ₩56만 (트랙 A 추정)

### 10.2 펌웨어 업데이트

`prototype/firmware/sensors.py` 에 SCD41 드라이버 추가 (별도 작성 필요).

`prototype/firmware/main.py` 의 `measure()` 함수에 한 줄 추가:
```python
try:
    payload["co2_ppm"] = sensors.read_scd41()
except Exception as e:
    log("SCD41 오류: {}".format(e))
```

### 10.3 16대 일괄 재배포

```bash
for room in 1-1 1-2 ... 3-8; do
  ~/climate365-deploy.sh $room
done
```

(배포 전 각 Pico를 USB로 연결해야 함 — 결국 한 대씩 진행)

### 10.4 학기 시작 시 16대 수동 FRC 보정

SCD41은 외기 노출 자가 보정(ABC)이 학교 환경에서 부정확. 학기 시작일 외기에서 5분 대기 후 FRC 명령(420 ppm) 일괄 적용.

→ 별도 매뉴얼 `SETUP-04-PHASE2.md` 추후 작성 예정.

### 10.5 대시보드 임계값 추가

`prototype/dashboard/app.py` 의 `LIMITS` 딕셔너리에:
```python
"co2_ppm": {"min": None, "max": 1000, "unit": "ppm", "label": "CO2"},
```

서버는 변경 불필요 (DB 컬럼 이미 예약됨).

---

## 부록 · 학생 팀별 책임 매트릭스

| 활동 | 조립팀 | 분석팀 | 운영팀 | 교사 |
|---|---|---|---|---|
| 부품 점검·조립 | ⭐ | | | 감독 |
| 펌웨어 배포 | ⭐ | | | 검수 |
| 교실 설치 | ⭐ | | 보조 | 동행 |
| 일일 모니터링 | | | ⭐ | 주간 점검 |
| 장애 1차 대응 | 보조 | | ⭐ | 결재 |
| 데이터 분석·리포트 | | ⭐ | | 검수 |
| 캠페인 기획 | | 보조 | ⭐ | 자문 |
| 시스템 업데이트 | 보조 | | | ⭐ |
