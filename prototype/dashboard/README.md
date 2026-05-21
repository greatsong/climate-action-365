# Dashboard — Streamlit

전교생·교사가 보는 실시간 환경 대시보드.

## 설치

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 실행

```bash
streamlit run app.py
```

기본적으로 `http://localhost:8501` 에서 열림. 학교 LAN에 공개하려면:

```bash
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

## 구성

| 탭 | 누가 | 무엇을 |
|---|---|---|
| 📊 전체 교실 | 전교생·교사 | 16교실 그리드. 적정/높음/낮음 색상. |
| 🔍 교실 상세 | 운영팀 | 교실 1개의 최근 24~72시간 시계열 |
| 🧪 분석팀 작업장 | 분석팀 | 여러 교실 비교, 기준 위반 통계 |

## 학생이 손댈 만한 곳

- `LIMITS` 딕셔너리 → 학교 자체 임계값 설계 (분석팀 R&D)
- `status_color()` → 단계 더 세분화 (주의/경고/위험 3단계)
- 새로운 탭 추가 (월간 리포트 자동 생성 등)

## 서버 주소 변경

`SERVER_URL = "http://localhost:8000"` 을 라즈베리파이 IP로 변경.
