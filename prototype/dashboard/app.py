"""
교실 환경 대시보드 — Streamlit.

기능:
- 16교실 실시간 그리드 (최신 측정값 + 학교보건법 기준 대비 색상)
- 교실 1개 선택 시 시계열 차트 (최근 24시간)
- 분석팀 작업장: 임의 기간·교실 비교

학교보건법 시행규칙 기준 (별표 2):
- 온도 18~28°C
- 습도 30~80%
- 조도 (책상면) 300 lux 이상
"""

from datetime import datetime, timezone, timedelta
import pandas as pd
import requests
import streamlit as st

SERVER_URL = "http://localhost:8000"

# 임계값 — 온/습도는 학교보건법 시행규칙 별표 2.
# 조도(light)는 Grove Light Sensor의 0~100% 상대값이라 학교보건법 lux 기준
# (책상면 300 lux 이상)을 직접 매핑할 수 없습니다. 분석팀이 학기 초 자체 측정으로
# ‘평일 1교시 형광등 ON 평균 ≈ N%’를 정해 자기 학교 임계값을 결정합니다.
LIMITS = {
    "temperature": {"min": 18, "max": 28, "unit": "°C", "label": "온도"},
    "humidity":    {"min": 30, "max": 80, "unit": "%RH", "label": "습도"},
    "light":       {"min": 30, "max": None, "unit": "%", "label": "조도(상대)"},
}

st.set_page_config(page_title="기후행동365 대시보드", layout="wide")


# ---------- 데이터 ----------

@st.cache_data(ttl=20)
def fetch_nodes():
    r = requests.get(f"{SERVER_URL}/nodes", timeout=5)
    r.raise_for_status()
    return r.json()


@st.cache_data(ttl=20)
def fetch_readings(node_id=None, since_minutes=1440):
    params = {"since_minutes": since_minutes, "limit": 10000}
    if node_id:
        params["node_id"] = node_id
    r = requests.get(f"{SERVER_URL}/readings", params=params, timeout=10)
    r.raise_for_status()
    df = pd.DataFrame(r.json())
    if not df.empty:
        df["received_at"] = pd.to_datetime(df["received_at"])
    return df


# ---------- 헬퍼 ----------

def status_color(metric, value):
    """학교보건법 기준 대비 색상 결정."""
    if value is None:
        return "⬜", "없음"
    lim = LIMITS[metric]
    if lim["min"] is not None and value < lim["min"]:
        return "🟦", "낮음"
    if lim["max"] is not None and value > lim["max"]:
        return "🟥", "높음"
    return "🟩", "적정"


def is_stale(last_seen_iso, threshold_min=5):
    if not last_seen_iso:
        return True
    try:
        last = datetime.fromisoformat(last_seen_iso.replace("Z", "+00:00"))
    except ValueError:
        return True
    age = datetime.now(timezone.utc) - last
    return age > timedelta(minutes=threshold_min)


# ---------- UI ----------

st.title("🌱 당곡고 기후행동365 — 교실 환경 대시보드")
st.caption("학교보건법 시행규칙 별표 2 기준 · Phase 1 (온습도 + 조도)")

tab1, tab2, tab3 = st.tabs(["📊 전체 교실", "🔍 교실 상세", "🧪 분석팀 작업장"])

# === Tab 1: 전체 교실 그리드 ===
with tab1:
    try:
        nodes = fetch_nodes()
    except Exception as e:
        st.error(f"서버 연결 실패: {e}")
        st.stop()

    if not nodes:
        st.warning("아직 등록된 노드가 없습니다. Pico가 처음 데이터를 보내면 여기에 나타납니다.")
    else:
        st.write(f"총 **{len(nodes)}개 노드** · 최근 5분 내 미수신 노드는 🚨로 표시")
        cols = st.columns(4)
        for i, node in enumerate(nodes):
            with cols[i % 4]:
                stale = is_stale(node["last_seen"])
                title = node["node_id"]
                if stale:
                    title = "🚨 " + title
                st.markdown(f"### {title}")

                latest = node.get("latest") or {}
                for metric in ("temperature", "humidity", "light"):
                    val = latest.get(metric)
                    icon, status = status_color(metric, val)
                    lim = LIMITS[metric]
                    val_str = f"{val:.1f} {lim['unit']}" if val is not None else "—"
                    st.markdown(f"{icon} **{lim['label']}**: {val_str} ({status})")

                if node["last_seen"]:
                    st.caption(f"마지막 수신: {node['last_seen'][:19]}")
                st.divider()

# === Tab 2: 교실 상세 ===
with tab2:
    nodes = fetch_nodes()
    if not nodes:
        st.info("데이터 없음")
    else:
        node_ids = [n["node_id"] for n in nodes]
        selected = st.selectbox("교실 선택", node_ids)
        hours = st.slider("최근 N시간", 1, 72, 24)
        df = fetch_readings(node_id=selected, since_minutes=hours * 60)

        if df.empty:
            st.info("해당 기간 데이터 없음")
        else:
            df = df.sort_values("received_at")
            st.subheader(f"교실 {selected} — 최근 {hours}시간")

            c1, c2, c3 = st.columns(3)
            c1.metric("온도 (°C)", f"{df['temperature'].iloc[-1]:.1f}")
            c2.metric("습도 (%RH)", f"{df['humidity'].iloc[-1]:.1f}")
            c3.metric("조도 (%)", f"{df['light'].iloc[-1]:.1f}")

            st.line_chart(df.set_index("received_at")[["temperature"]], height=200)
            st.line_chart(df.set_index("received_at")[["humidity"]], height=200)
            st.line_chart(df.set_index("received_at")[["light"]], height=200)

# === Tab 3: 분석팀 작업장 ===
with tab3:
    st.markdown("""
    여러 교실의 데이터를 한꺼번에 비교하고 분석해 보세요.
    학교보건법 기준값을 시각화하고, 어느 교실·시간대가 가장 환기가 필요한지 찾아봅시다.
    """)

    nodes = fetch_nodes()
    if not nodes:
        st.info("데이터 없음")
    else:
        node_ids = [n["node_id"] for n in nodes]
        selected_nodes = st.multiselect("교실 선택 (다중)", node_ids, default=node_ids[:4])
        metric = st.selectbox("지표", list(LIMITS.keys()),
                              format_func=lambda m: LIMITS[m]["label"])
        hours = st.slider("최근 N시간", 1, 168, 24, key="analysis_hours")

        if selected_nodes:
            frames = []
            for nid in selected_nodes:
                d = fetch_readings(node_id=nid, since_minutes=hours * 60)
                if not d.empty:
                    frames.append(d[["received_at", metric]].assign(node_id=nid))
            if frames:
                merged = pd.concat(frames)
                pivot = (merged
                         .pivot_table(index="received_at", columns="node_id", values=metric)
                         .sort_index())
                st.line_chart(pivot, height=400)

                # 기준 위반 통계
                lim = LIMITS[metric]
                st.subheader("기준 위반 횟수 (이 기간)")
                stats = []
                for nid in selected_nodes:
                    d = merged[merged["node_id"] == nid]
                    over = 0
                    under = 0
                    if lim["max"] is not None:
                        over = (d[metric] > lim["max"]).sum()
                    if lim["min"] is not None:
                        under = (d[metric] < lim["min"]).sum()
                    stats.append({"교실": nid, "낮음": int(under), "높음": int(over)})
                st.dataframe(pd.DataFrame(stats), hide_index=True)
            else:
                st.info("선택한 교실에 데이터 없음")
