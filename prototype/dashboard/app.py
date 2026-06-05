"""
교실 환경 대시보드 — Streamlit (학교 전체 한눈에).

레이아웃:
- 상단 KPI 6칸 (총 노드 / 위반 / 평균 T·RH·Light / 마지막 갱신)
- 학년별 행 그리드 (1학년 1~8반, 2학년 1~8반, 3학년 1~8반)
  각 셀: NODE_ID + 온도·습도·조도 한 줄씩, 기준 색상
- 학교 전체 최근 1시간 시계열 (온도·습도·조도)
- 🚨 현재 기준 위반 노드 테이블

학교보건법 시행규칙 기준 (별표 2):
- 온도 18~28°C / 습도 30~80% / 조도 권장 30%+ (자체)
"""

from datetime import datetime, timezone, timedelta

import pandas as pd
import requests
import streamlit as st

SERVER_URL = "http://localhost:8000"

# 학교 구조 (당곡고 16개 교실)
GRADES = [1, 2, 3]
ROOMS_PER_GRADE = 8

LIMITS = {
    "temperature": {"min": 18, "max": 28, "unit": "°C", "label": "온도"},
    "humidity":    {"min": 30, "max": 80, "unit": "%RH", "label": "습도"},
    "light":       {"min": 30, "max": None, "unit": "%", "label": "조도(상대)"},
}

st.set_page_config(page_title="기후행동365 대시보드",
                   page_icon="🌱", layout="wide")

# ---------- 스타일 ----------
st.markdown("""<style>
.block-container{padding-top:1.5rem;padding-bottom:1rem;}
.grade-header{font-size:1.05em;color:#444;font-weight:700;
              border-left:5px solid #2ecc71;padding:0.35em 0.7em;
              margin:1.2em 0 0.4em;background:#f6fbf8;border-radius:3px;}
.room-card{background:#fff;padding:0.6em 0.3em 0.5em;border-radius:8px;
           box-shadow:0 1px 3px rgba(0,0,0,0.06);text-align:center;
           min-height:7em;border:1px solid #eee;}
.room-card.stale{background:#fff5f5;border:1px solid #fcc;}
.room-id{font-size:0.78em;color:#666;font-weight:700;margin-bottom:0.3em;}
.room-empty{color:#bbb;font-size:0.78em;padding-top:1.4em;}
.metric-row{font-size:0.95em;padding:0.05em 0;font-weight:600;
            font-variant-numeric:tabular-nums;line-height:1.4;}
.metric-row .lab{font-size:0.7em;color:#aaa;font-weight:400;margin-right:0.15em;}
</style>""", unsafe_allow_html=True)


# ---------- 데이터 ----------
@st.cache_data(ttl=15)
def fetch_nodes():
    r = requests.get(f"{SERVER_URL}/nodes", timeout=5)
    r.raise_for_status()
    return r.json()


@st.cache_data(ttl=15)
def fetch_readings(node_id=None, since_minutes=60):
    params = {"since_minutes": since_minutes, "limit": 20000}
    if node_id:
        params["node_id"] = node_id
    r = requests.get(f"{SERVER_URL}/readings", params=params, timeout=10)
    r.raise_for_status()
    df = pd.DataFrame(r.json())
    if not df.empty:
        df["received_at"] = pd.to_datetime(df["received_at"])
    return df


def status_for(metric, value):
    """기준 대비 (색상, 레벨)."""
    if value is None:
        return ("#bbb", "없음")
    lim = LIMITS[metric]
    if lim["min"] is not None and value < lim["min"]:
        return ("#3498db", "낮음")
    if lim["max"] is not None and value > lim["max"]:
        return ("#e74c3c", "높음")
    return ("#2ecc71", "적정")


def is_stale(last_seen_iso, threshold_min=5):
    if not last_seen_iso:
        return True
    try:
        last = datetime.fromisoformat(last_seen_iso.replace("Z", "+00:00"))
    except ValueError:
        return True
    return (datetime.now(timezone.utc) - last) > timedelta(minutes=threshold_min)


# ---------- 헤더 ----------
st.title("🌱 당곡고 기후행동365 — 학교 전체 환경")
st.caption("학교보건법 시행규칙 별표 2 기준 · Phase 1 (온습도 + 조도)")

tab1, tab2, tab3 = st.tabs(["🏫 학교 전체", "🔍 교실 상세", "🧪 분석팀 작업장"])

# ====================================================================
# TAB 1 — 학교 전체 (학년별 그리드)
# ====================================================================
with tab1:
    try:
        nodes = fetch_nodes()
    except Exception as e:
        st.error(f"서버 연결 실패: {e}")
        st.stop()

    node_by_id = {n["node_id"]: n for n in nodes}
    total = len(GRADES) * ROOMS_PER_GRADE
    online = sum(1 for n in nodes if not is_stale(n["last_seen"]))

    # 위반·평균 집계
    violations = []
    all_t, all_rh, all_lt = [], [], []
    for n in nodes:
        if is_stale(n["last_seen"]):
            continue
        latest = n.get("latest") or {}
        for metric in ("temperature", "humidity", "light"):
            v = latest.get(metric)
            if v is None:
                continue
            _, level = status_for(metric, v)
            if level in ("높음", "낮음"):
                lim = LIMITS[metric]
                violations.append({
                    "교실": n["node_id"],
                    "지표": lim["label"],
                    "현재값": f"{v:.1f}{lim['unit']}",
                    "상태": level,
                    "기준": (f"{lim['min']}~{lim['max']}{lim['unit']}"
                             if lim['max'] else f"≥{lim['min']}{lim['unit']}"),
                })
            if metric == "temperature": all_t.append(v)
            elif metric == "humidity": all_rh.append(v)
            elif metric == "light":   all_lt.append(v)

    danger_nodes = len({v["교실"] for v in violations})

    # ---------- KPI 6칸 ----------
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("📡 온라인 노드", f"{online} / {total}",
              help="최근 5분 내 수신 / 예상 전체")
    c2.metric("🚨 기준 초과", f"{danger_nodes} 교실",
              delta=f"{len(violations)}건" if violations else "—",
              delta_color="inverse")
    c3.metric("🌡️ 평균 온도",
              f"{sum(all_t)/len(all_t):.1f}°C" if all_t else "—")
    c4.metric("💧 평균 습도",
              f"{sum(all_rh)/len(all_rh):.0f}%" if all_rh else "—")
    c5.metric("💡 평균 조도",
              f"{sum(all_lt)/len(all_lt):.0f}%" if all_lt else "—")
    c6.metric("🕐 갱신", datetime.now().strftime("%H:%M:%S"))

    # ---------- 학년별 행 그리드 ----------
    st.markdown("###  ")
    for grade in GRADES:
        st.markdown(
            f'<div class="grade-header">📚 {grade}학년</div>',
            unsafe_allow_html=True,
        )
        cols = st.columns(ROOMS_PER_GRADE)
        for room in range(1, ROOMS_PER_GRADE + 1):
            node_id = f"{grade}-{room}"
            node = node_by_id.get(node_id)
            with cols[room - 1]:
                if node is None:
                    st.markdown(
                        f'<div class="room-card">'
                        f'<div class="room-id">{node_id}</div>'
                        f'<div class="room-empty">미설치</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                    continue
                stale = is_stale(node["last_seen"])
                latest = node.get("latest") or {}
                t = latest.get("temperature")
                rh = latest.get("humidity")
                lt = latest.get("light")

                cls = "room-card stale" if stale else "room-card"
                badge = "🚨 " if stale else ""
                html = (f'<div class="{cls}">'
                        f'<div class="room-id">{badge}{node_id}</div>')

                for label, val, fmt, metric in [
                    ("T",  t,  "{:.1f}", "temperature"),
                    ("RH", rh, "{:.0f}", "humidity"),
                    ("L",  lt, "{:.0f}", "light"),
                ]:
                    if val is None:
                        html += '<div class="metric-row">—</div>'
                    else:
                        color, _ = status_for(metric, val)
                        html += (f'<div class="metric-row" style="color:{color}">'
                                 f'<span class="lab">{label}</span>'
                                 f'{fmt.format(val)}</div>')
                html += '</div>'
                st.markdown(html, unsafe_allow_html=True)

    # ---------- 학교 전체 시계열 ----------
    st.markdown("###  ")
    st.subheader("📈 최근 1시간 · 학교 전체 평균")

    df_all = fetch_readings(since_minutes=60)
    if df_all.empty:
        st.info("최근 1시간 동안 수신된 데이터가 없습니다.")
    else:
        df_all = df_all.sort_values("received_at")
        minute_avg = (df_all.set_index("received_at")
                            .resample("1min")
                            .mean(numeric_only=True))
        cc1, cc2, cc3 = st.columns(3)
        if "temperature" in minute_avg.columns:
            with cc1:
                st.caption("🌡️ 온도 (°C) · 기준 18~28")
                st.line_chart(minute_avg[["temperature"]], height=180)
        if "humidity" in minute_avg.columns:
            with cc2:
                st.caption("💧 습도 (%RH) · 기준 30~80")
                st.line_chart(minute_avg[["humidity"]], height=180)
        if "light" in minute_avg.columns:
            with cc3:
                st.caption("💡 조도 (%) · 자체 기준 ≥30")
                st.line_chart(minute_avg[["light"]], height=180)

    # ---------- 위반 알림 ----------
    st.markdown("###  ")
    st.subheader("🚨 현재 기준 위반")
    if violations:
        st.dataframe(
            pd.DataFrame(violations).sort_values(["상태", "교실"]),
            hide_index=True, use_container_width=True,
        )
    else:
        st.success("✅ 모든 온라인 노드가 학교보건법 기준 안에 있습니다.")

    st.caption(
        f"📊 학교보건법 시행규칙 별표 2 — "
        f"온도 {LIMITS['temperature']['min']}~{LIMITS['temperature']['max']}°C, "
        f"습도 {LIMITS['humidity']['min']}~{LIMITS['humidity']['max']}%RH, "
        f"책상면 조도 300 lux 이상 (Grove Light Sensor는 상대%라 자체 임계값 설계 필요)"
    )


# ====================================================================
# TAB 2 — 교실 상세
# ====================================================================
with tab2:
    nodes = fetch_nodes()
    if not nodes:
        st.info("데이터 없음")
    else:
        node_ids = sorted([n["node_id"] for n in nodes])
        selected = st.selectbox("교실 선택", node_ids)
        hours = st.slider("최근 N시간", 1, 72, 24)
        df = fetch_readings(node_id=selected, since_minutes=hours * 60)

        if df.empty:
            st.info("해당 기간 데이터 없음")
        else:
            df = df.sort_values("received_at")
            st.subheader(f"📍 {selected} — 최근 {hours}시간")

            c1, c2, c3 = st.columns(3)
            c1.metric("온도 (°C)", f"{df['temperature'].iloc[-1]:.1f}")
            c2.metric("습도 (%RH)", f"{df['humidity'].iloc[-1]:.1f}")
            c3.metric("조도 (%)", f"{df['light'].iloc[-1]:.1f}")

            st.line_chart(df.set_index("received_at")[["temperature"]],
                          height=200)
            st.line_chart(df.set_index("received_at")[["humidity"]],
                          height=200)
            st.line_chart(df.set_index("received_at")[["light"]], height=200)


# ====================================================================
# TAB 3 — 분석팀 작업장
# ====================================================================
with tab3:
    st.markdown(
        "여러 교실을 한꺼번에 비교하고 분석해 봅니다. "
        "기준 위반 횟수를 보면 어느 교실·시간대에 환기가 필요한지 보입니다."
    )
    nodes = fetch_nodes()
    if not nodes:
        st.info("데이터 없음")
    else:
        node_ids = sorted([n["node_id"] for n in nodes])
        selected_nodes = st.multiselect(
            "교실 선택 (다중)", node_ids,
            default=node_ids[:min(4, len(node_ids))],
        )
        metric = st.selectbox(
            "지표", list(LIMITS.keys()),
            format_func=lambda m: LIMITS[m]["label"],
        )
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
                         .pivot_table(index="received_at",
                                      columns="node_id", values=metric)
                         .sort_index())
                st.line_chart(pivot, height=400)

                lim = LIMITS[metric]
                st.subheader("기준 위반 횟수 (이 기간)")
                stats = []
                for nid in selected_nodes:
                    d = merged[merged["node_id"] == nid]
                    over = under = 0
                    if lim["max"] is not None:
                        over = int((d[metric] > lim["max"]).sum())
                    if lim["min"] is not None:
                        under = int((d[metric] < lim["min"]).sum())
                    stats.append({"교실": nid, "낮음": under, "높음": over,
                                  "합계": under + over})
                st.dataframe(
                    pd.DataFrame(stats).sort_values("합계", ascending=False),
                    hide_index=True, use_container_width=True,
                )
            else:
                st.info("선택한 교실에 데이터 없음")
