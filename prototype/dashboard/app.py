"""
교실 환경 대시보드 — Streamlit (학교 전체 인사이트형).

탭 구성:
1. 🏫 학교 전체 — KPI + 학년별 그리드(현재값 + 30분 5칸 추세) + 위반 + 환기 추천
2. 🔍 교실 상세 — 1개 노드의 시계열
3. 🧪 분석팀 작업장 — 다중 교실 비교·누적 위반
4. 🔥 패턴 히트맵 — 시간대 × 교실 히트맵 (캠페인 우선순위 발견 도구)

설계 의도:
- ‘지금 우리 학교가 어디서 안 좋은가’가 1초 안에 보이게
- 카드 안의 5칸 추세 띠로 ‘방금 환기 효과가 있었나’가 즉시 보이게
- 위반 시간 누적·히트맵으로 데이터 기반 캠페인 의사결정 지원
"""

from datetime import datetime, timezone, timedelta

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

SERVER_URL = "http://localhost:8000"

# 학교 구조 (당곡고 16개 교실 = 1학년 8반 + 2학년 8반)
GRADES = [1, 2]
ROOMS_PER_GRADE = 8

LIMITS = {
    "temperature": {"min": 18, "max": 28, "unit": "°C", "label": "온도"},
    "humidity":    {"min": 30, "max": 80, "unit": "%RH", "label": "습도"},
    "light":       {"min": 30, "max": None, "unit": "%", "label": "조도"},
}

# 추세 띠 설정
TREND_WINDOW_MIN = 30   # 카드 안의 띠가 다루는 시간 범위
TREND_SLOTS = 5         # 5칸 (각 6분 평균)


st.set_page_config(page_title="기후행동365 대시보드",
                   page_icon="🌱", layout="wide")

# ---------- 스타일 ----------
st.markdown("""<style>
.block-container{padding-top:1.5rem;padding-bottom:1rem;max-width:1500px;}
.grade-header{font-size:1.05em;color:#444;font-weight:700;
              border-left:5px solid #2ecc71;padding:0.35em 0.7em;
              margin:1.2em 0 0.5em;background:#f6fbf8;border-radius:3px;}

/* ----- 라이브 카드 ----- */
.room-card{background:#fff;padding:0.6em 0.5em;border-radius:12px;
           box-shadow:0 2px 6px rgba(0,0,0,0.06);text-align:left;
           min-height:9.5em;border:1px solid #f0f0f0;
           transition:all 0.25s ease;}
.room-card:hover{box-shadow:0 4px 12px rgba(0,0,0,0.12);
                 transform:translateY(-2px);border-color:#e0e0e0;}
.room-card.stale{background:#fff5f5;border:1px solid #fcc;}
.room-card.empty{background:#fafafa;border:1px dashed #ddd;}
.room-card.empty:hover{transform:none;box-shadow:0 2px 6px rgba(0,0,0,0.06);}
.room-card.danger{border-color:#e74c3c;
                  box-shadow:0 0 0 1px rgba(231,76,60,0.2),
                             0 2px 8px rgba(231,76,60,0.15);}

/* ----- 헤더 + 라이브 도트 ----- */
.room-id{font-size:0.9em;color:#333;font-weight:700;margin-bottom:0.4em;
         display:flex;justify-content:space-between;align-items:center;gap:0.3em;}
.live-dot{display:inline-block;width:7px;height:7px;border-radius:50%;
          background:#2ecc71;margin-right:0.3em;vertical-align:middle;
          box-shadow:0 0 0 0 rgba(46,204,113,0.6);
          animation:pulse-dot 1.8s ease-in-out infinite;}
@keyframes pulse-dot {
  0%   { box-shadow:0 0 0 0 rgba(46,204,113,0.6); opacity:1; }
  70%  { box-shadow:0 0 0 7px rgba(46,204,113,0);   opacity:0.85; }
  100% { box-shadow:0 0 0 0 rgba(46,204,113,0);     opacity:1; }
}
.live-dot.danger{background:#e74c3c;
                 box-shadow:0 0 0 0 rgba(231,76,60,0.6);
                 animation:pulse-dot-danger 1.2s ease-in-out infinite;}
@keyframes pulse-dot-danger {
  0%   { box-shadow:0 0 0 0 rgba(231,76,60,0.7); opacity:1; }
  70%  { box-shadow:0 0 0 8px rgba(231,76,60,0);   opacity:0.85; }
  100% { box-shadow:0 0 0 0 rgba(231,76,60,0);     opacity:1; }
}

/* ----- 태그 ----- */
.room-tag{font-size:0.65em;color:#888;background:#f0f0f0;padding:1px 5px;
          border-radius:8px;font-weight:500;}
.room-tag.vent{background:#fff3cd;color:#856404;
               animation:tag-glow 2s ease-in-out infinite;}
@keyframes tag-glow {
  0%,100% { background:#fff3cd; }
  50%     { background:#ffe69c; }
}
.room-empty{color:#bbb;font-size:0.8em;padding:2em 0;text-align:center;}

/* ----- 지표 행 ----- */
.metric-row{display:flex;align-items:center;gap:0.35em;
            font-size:0.88em;padding:0.12em 0;
            font-variant-numeric:tabular-nums;}
.metric-lab{font-size:0.7em;color:#999;font-weight:500;width:1em;}
.metric-val{font-weight:700;width:3em;text-align:right;
            transition:color 0.3s ease;}
.metric-val.danger{animation:val-pulse 1.4s ease-in-out infinite;}
@keyframes val-pulse {
  0%,100% { opacity:1; }
  50%     { opacity:0.55; }
}
.metric-unit{font-size:0.7em;color:#aaa;}

/* ----- 5칸 추세 띠 (마지막 칸 = 현재 라이브) ----- */
.trend-strip{display:inline-flex;gap:2px;margin-left:0.3em;align-items:center;}
.trend-cell{width:9px;height:12px;border-radius:2px;
            transition:background 0.3s ease;}
.trend-cell.live{width:11px;height:14px;border-radius:3px;
                 box-shadow:0 0 0 0 currentColor;
                 animation:cell-live 1.6s ease-in-out infinite;}
@keyframes cell-live {
  0%   { box-shadow:0 0 0 0 currentColor; transform:scale(1); }
  60%  { box-shadow:0 0 0 4px transparent; transform:scale(1.08); }
  100% { box-shadow:0 0 0 0 transparent; transform:scale(1); }
}
</style>""", unsafe_allow_html=True)


# ---------- 데이터 fetch ----------
@st.cache_data(ttl=15)
def fetch_nodes():
    r = requests.get(f"{SERVER_URL}/nodes", timeout=5)
    r.raise_for_status()
    return r.json()


@st.cache_data(ttl=15)
def fetch_all_recent(since_minutes=60):
    """모든 노드 + 모든 컬럼 최근 N분. 한 번에."""
    r = requests.get(f"{SERVER_URL}/readings",
                     params={"since_minutes": since_minutes, "limit": 50000},
                     timeout=15)
    r.raise_for_status()
    df = pd.DataFrame(r.json())
    if not df.empty:
        df["received_at"] = pd.to_datetime(df["received_at"])
    return df


@st.cache_data(ttl=15)
def fetch_node_readings(node_id, since_minutes=1440):
    r = requests.get(f"{SERVER_URL}/readings",
                     params={"node_id": node_id,
                             "since_minutes": since_minutes,
                             "limit": 50000},
                     timeout=15)
    r.raise_for_status()
    df = pd.DataFrame(r.json())
    if not df.empty:
        df["received_at"] = pd.to_datetime(df["received_at"])
    return df


# ---------- 헬퍼 ----------
def status_for(metric, value):
    """(색상, 레벨) 반환."""
    if value is None or pd.isna(value):
        return ("#e8e8e8", "없음")
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


def trend_colors(df_node, metric, slots=TREND_SLOTS,
                 window_min=TREND_WINDOW_MIN):
    """노드 데이터프레임에서 최근 window_min분을 slots칸으로 나눠
    각 칸의 평균값에 해당하는 색상 리스트 반환. 데이터 없으면 회색."""
    if df_node.empty or metric not in df_node.columns:
        return ["#e8e8e8"] * slots
    end = datetime.now(timezone.utc)
    start = end - timedelta(minutes=window_min)
    df_w = df_node[(df_node["received_at"] >= start)
                   & (df_node["received_at"] <= end)]
    if df_w.empty:
        return ["#e8e8e8"] * slots
    slot_min = window_min / slots
    out = []
    for i in range(slots):
        s_start = start + timedelta(minutes=slot_min * i)
        s_end = start + timedelta(minutes=slot_min * (i + 1))
        mask = ((df_w["received_at"] >= s_start)
                & (df_w["received_at"] < s_end))
        slot_df = df_w[mask]
        if slot_df.empty:
            out.append("#e8e8e8")
            continue
        mean = slot_df[metric].mean()
        color, _ = status_for(metric, mean)
        out.append(color)
    return out


def violation_minutes_today(df_node, metric):
    """오늘 기준 위반 누적 시간(분). 측정 주기를 1건당 30초로 가정."""
    if df_node.empty or metric not in df_node.columns:
        return 0
    today_start = datetime.now(timezone.utc).replace(
        hour=15, minute=0, second=0, microsecond=0
    ) - timedelta(days=1)
    # KST 자정 = UTC 전날 15:00. 단순화를 위해 24h만.
    today_start = datetime.now(timezone.utc) - timedelta(hours=24)
    df_t = df_node[df_node["received_at"] >= today_start]
    if df_t.empty:
        return 0
    lim = LIMITS[metric]
    cnt = 0
    if lim["max"] is not None:
        cnt += int((df_t[metric] > lim["max"]).sum())
    if lim["min"] is not None:
        cnt += int((df_t[metric] < lim["min"]).sum())
    # 30초 주기 기준
    return cnt * 0.5  # 분 단위


def needs_ventilation(latest):
    """단순 환기 추천: 온도↑ 그리고 습도↑ 동시 발생."""
    t = latest.get("temperature")
    rh = latest.get("humidity")
    if t is None or rh is None:
        return False
    return (t > LIMITS["temperature"]["max"] - 1.5
            and rh > LIMITS["humidity"]["max"] - 5)


# ---------- 헤더 ----------
st.title("🌱 당곡고 기후행동365 — 학교 전체 환경")
st.caption(
    "학교보건법 시행규칙 별표 2 기준 · Phase 1 (온습도 + 조도) · "
    "5칸 띠 = 최근 30분(6분씩 5구간 평균)"
)

tab1, tab2, tab3, tab4 = st.tabs([
    "🏫 학교 전체",
    "🔍 교실 상세",
    "🧪 분석팀 작업장",
    "🔥 패턴 히트맵",
])


# ====================================================================
# TAB 1 — 학교 전체
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

    # 최근 30분 모든 노드 데이터 (5칸 띠용)
    df_recent = fetch_all_recent(since_minutes=TREND_WINDOW_MIN)
    df_recent_by_node = (df_recent.groupby("node_id")
                         if not df_recent.empty else None)

    # 오늘 24h 데이터 (누적 위반 시간)
    df_today = fetch_all_recent(since_minutes=24 * 60)
    today_by_node = (df_today.groupby("node_id")
                     if not df_today.empty else None)

    # 위반 + 평균 집계
    violations = []
    all_t, all_rh, all_lt = [], [], []
    vent_nodes = []
    for n in nodes:
        if is_stale(n["last_seen"]):
            continue
        latest = n.get("latest") or {}
        if needs_ventilation(latest):
            vent_nodes.append(n["node_id"])
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

    danger_rooms = len({v["교실"] for v in violations})

    # ---------- KPI ----------
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("📡 온라인", f"{online} / {total}",
              help="최근 5분 내 수신 / 예상 전체")
    c2.metric("🚨 기준 초과", f"{danger_rooms} 교실",
              delta=f"{len(violations)}건" if violations else None,
              delta_color="inverse")
    c3.metric("💨 환기 권장", f"{len(vent_nodes)} 교실",
              help="현재 온도·습도 모두 기준 가까이")
    c4.metric("🌡️ 평균 온도",
              f"{np.mean(all_t):.1f}°C" if all_t else "—")
    c5.metric("💧 평균 습도",
              f"{np.mean(all_rh):.0f}%" if all_rh else "—")
    c6.metric("💡 평균 조도",
              f"{np.mean(all_lt):.0f}%" if all_lt else "—")

    # ---------- 학년별 그리드 (현재값 + 5칸 추세 띠) ----------
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
                        f'<div class="room-card empty">'
                        f'<div class="room-id">{node_id}</div>'
                        f'<div class="room-empty">미설치</div></div>',
                        unsafe_allow_html=True,
                    )
                    continue

                stale = is_stale(node["last_seen"])
                latest = node.get("latest") or {}

                # 노드 30분 데이터
                if (df_recent_by_node is not None
                        and node_id in df_recent_by_node.groups):
                    df_n = df_recent_by_node.get_group(node_id)
                else:
                    df_n = pd.DataFrame()

                # 환기 라벨
                vent_label = ""
                if needs_ventilation(latest):
                    vent_label = '<span class="room-tag vent">💨 환기</span>'

                # 카드 클래스: stale / danger / normal
                card_danger = False
                for m in ("temperature", "humidity", "light"):
                    v = latest.get(m)
                    if v is None: continue
                    _, lvl = status_for(m, v)
                    if lvl in ("높음", "낮음"):
                        card_danger = True
                        break

                if stale:
                    cls = "room-card stale"
                elif card_danger:
                    cls = "room-card danger"
                else:
                    cls = "room-card"

                # 라이브 도트
                if stale:
                    dot = ""
                    badge = "🚨 "
                else:
                    dot_cls = "live-dot danger" if card_danger else "live-dot"
                    dot = f'<span class="{dot_cls}"></span>'
                    badge = ""

                html = (
                    f'<div class="{cls}">'
                    f'<div class="room-id">'
                    f'<span>{dot}{badge}{node_id}</span>{vent_label}</div>'
                )

                for label, val, fmt, unit, metric in [
                    ("T",  latest.get("temperature"), "{:.1f}", "°", "temperature"),
                    ("H",  latest.get("humidity"),    "{:.0f}", "%", "humidity"),
                    ("L",  latest.get("light"),       "{:.0f}", "%", "light"),
                ]:
                    color, lvl = status_for(metric, val)
                    cells = trend_colors(df_n, metric)
                    # 마지막 칸(현재 시점) = .live 펄스. color는 셀 자체 색.
                    strip_parts = []
                    for i, c in enumerate(cells):
                        if i == len(cells) - 1 and c != "#e8e8e8":
                            strip_parts.append(
                                f'<span class="trend-cell live" '
                                f'style="background:{c};color:{c}"></span>'
                            )
                        else:
                            strip_parts.append(
                                f'<span class="trend-cell" '
                                f'style="background:{c}"></span>'
                            )
                    strip = ''.join(strip_parts)
                    val_s = fmt.format(val) if val is not None else "—"
                    val_cls = "metric-val danger" if lvl in ("높음", "낮음") else "metric-val"
                    html += (
                        f'<div class="metric-row">'
                        f'<span class="metric-lab">{label}</span>'
                        f'<span class="{val_cls}" style="color:{color}">{val_s}</span>'
                        f'<span class="metric-unit">{unit}</span>'
                        f'<span class="trend-strip">{strip}</span>'
                        f'</div>'
                    )
                html += '</div>'
                st.markdown(html, unsafe_allow_html=True)

    # 5칸 추세 띠 범례
    st.caption(
        "📖 카드 안의 5칸 띠 = 최근 30분을 6분씩 5구간으로 나눈 평균 색상 (좌→우 = 과거→현재). "
        "🟩 적정 · 🟧/🟥 기준 밖 · ⬜ 데이터 없음. "
        "환기 권장은 온도·습도가 동시에 기준 가까이 닿을 때 자동 표시."
    )

    # ---------- 학교 전체 1시간 시계열 (plotly) ----------
    st.markdown("###  ")
    st.subheader("📈 최근 1시간 · 학교 전체 평균")

    df_1h = fetch_all_recent(since_minutes=60)
    if df_1h.empty:
        st.info("최근 1시간 동안 수신된 데이터가 없습니다.")
    else:
        df_1h = df_1h.sort_values("received_at")
        minute_avg = (df_1h.set_index("received_at")
                            .resample("1min")
                            .mean(numeric_only=True))
        cc1, cc2, cc3 = st.columns(3)

        def line_with_bands(series, color, ymin=None, ymax=None, title=""):
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=series.index, y=series.values, mode="lines",
                line=dict(color=color, width=2.5),
                hovertemplate="%{x|%H:%M}<br>%{y:.1f}<extra></extra>",
            ))
            if ymin is not None:
                fig.add_hline(y=ymin, line_dash="dot",
                              line_color="rgba(52,152,219,0.4)",
                              annotation_text=f"min {ymin}",
                              annotation_position="bottom right",
                              annotation_font_size=10)
            if ymax is not None:
                fig.add_hline(y=ymax, line_dash="dot",
                              line_color="rgba(231,76,60,0.4)",
                              annotation_text=f"max {ymax}",
                              annotation_position="top right",
                              annotation_font_size=10)
            fig.update_layout(
                height=200, margin=dict(l=10, r=10, t=10, b=10),
                showlegend=False, title=None,
                xaxis_title=None, yaxis_title=None,
                plot_bgcolor="#fafafa",
            )
            return fig

        if "temperature" in minute_avg.columns:
            with cc1:
                st.caption("🌡️ 온도 (°C) · 기준 18~28")
                st.plotly_chart(
                    line_with_bands(minute_avg["temperature"],
                                    "#e74c3c", ymin=18, ymax=28),
                    use_container_width=True,
                )
        if "humidity" in minute_avg.columns:
            with cc2:
                st.caption("💧 습도 (%RH) · 기준 30~80")
                st.plotly_chart(
                    line_with_bands(minute_avg["humidity"],
                                    "#3498db", ymin=30, ymax=80),
                    use_container_width=True,
                )
        if "light" in minute_avg.columns:
            with cc3:
                st.caption("💡 조도 (%) · 자체 기준 ≥30")
                st.plotly_chart(
                    line_with_bands(minute_avg["light"],
                                    "#f39c12", ymin=30),
                    use_container_width=True,
                )

    # ---------- 오늘 누적 위반 시간 (캠페인 우선순위) ----------
    st.markdown("###  ")
    st.subheader("⏱️ 오늘 누적 기준 위반 시간 — 환기·소등 캠페인 우선순위")

    if today_by_node is None:
        st.info("오늘 데이터가 없습니다.")
    else:
        rows = []
        for n in nodes:
            nid = n["node_id"]
            if nid not in today_by_node.groups:
                continue
            df_t = today_by_node.get_group(nid)
            rows.append({
                "교실": nid,
                "온도 초과(분)": int(violation_minutes_today(df_t, "temperature")),
                "습도 이탈(분)": int(violation_minutes_today(df_t, "humidity")),
                "조도 부족(분)": int(violation_minutes_today(df_t, "light")),
            })
        if rows:
            df_rank = pd.DataFrame(rows)
            df_rank["합계(분)"] = (df_rank["온도 초과(분)"]
                                   + df_rank["습도 이탈(분)"]
                                   + df_rank["조도 부족(분)"])
            df_rank = df_rank.sort_values("합계(분)", ascending=False)
            st.dataframe(df_rank, hide_index=True, use_container_width=True)
        else:
            st.success("오늘 모든 노드가 기준 안에 있었습니다.")

    # ---------- 현재 기준 위반 ----------
    st.markdown("###  ")
    st.subheader("🚨 지금 기준 위반 중")
    if violations:
        st.dataframe(
            pd.DataFrame(violations).sort_values(["상태", "교실"]),
            hide_index=True, use_container_width=True,
        )
    else:
        st.success("✅ 모든 온라인 노드가 학교보건법 기준 안에 있습니다.")


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
        df = fetch_node_readings(selected, since_minutes=hours * 60)
        if df.empty:
            st.info("해당 기간 데이터 없음")
        else:
            df = df.sort_values("received_at")
            st.subheader(f"📍 {selected} — 최근 {hours}시간")
            c1, c2, c3 = st.columns(3)
            c1.metric("온도 (°C)", f"{df['temperature'].iloc[-1]:.1f}")
            c2.metric("습도 (%RH)", f"{df['humidity'].iloc[-1]:.1f}")
            c3.metric("조도 (%)", f"{df['light'].iloc[-1]:.1f}")
            ts_df = df.set_index("received_at")
            for col, color, ymin, ymax, label in [
                ("temperature", "#e74c3c", 18, 28, "🌡️ 온도 (°C)"),
                ("humidity",    "#3498db", 30, 80, "💧 습도 (%RH)"),
                ("light",       "#f39c12", 30, None, "💡 조도 (%)"),
            ]:
                if col not in ts_df.columns:
                    continue
                st.caption(label)
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=ts_df.index, y=ts_df[col], mode="lines",
                    line=dict(color=color, width=2),
                    hovertemplate="%{x|%m-%d %H:%M}<br>%{y:.1f}<extra></extra>",
                ))
                if ymin is not None:
                    fig.add_hline(y=ymin, line_dash="dot",
                                  line_color="rgba(52,152,219,0.4)")
                if ymax is not None:
                    fig.add_hline(y=ymax, line_dash="dot",
                                  line_color="rgba(231,76,60,0.4)")
                fig.update_layout(
                    height=220, margin=dict(l=10, r=10, t=10, b=10),
                    showlegend=False, plot_bgcolor="#fafafa",
                )
                st.plotly_chart(fig, use_container_width=True)


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
                d = fetch_node_readings(nid, since_minutes=hours * 60)
                if not d.empty:
                    frames.append(d[["received_at", metric]].assign(node_id=nid))
            if frames:
                merged = pd.concat(frames)
                pivot = (merged
                         .pivot_table(index="received_at",
                                      columns="node_id", values=metric)
                         .sort_index())
                fig = go.Figure()
                for col in pivot.columns:
                    fig.add_trace(go.Scatter(
                        x=pivot.index, y=pivot[col], mode="lines",
                        name=col, line=dict(width=1.8),
                        hovertemplate=f"{col}<br>%{{x|%m-%d %H:%M}}"
                                      "<br>%{y:.1f}<extra></extra>",
                    ))
                lim = LIMITS[metric]
                if lim["min"] is not None:
                    fig.add_hline(y=lim["min"], line_dash="dot",
                                  line_color="rgba(52,152,219,0.4)")
                if lim["max"] is not None:
                    fig.add_hline(y=lim["max"], line_dash="dot",
                                  line_color="rgba(231,76,60,0.4)")
                fig.update_layout(
                    height=420, margin=dict(l=10, r=10, t=10, b=10),
                    plot_bgcolor="#fafafa",
                    legend=dict(orientation="h", yanchor="bottom",
                                y=1.02, xanchor="right", x=1),
                )
                st.plotly_chart(fig, use_container_width=True)

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


# ====================================================================
# TAB 4 — 패턴 히트맵 (신규)
# ====================================================================
with tab4:
    st.markdown(
        "**시간대 × 교실**의 패턴 히트맵입니다. "
        "‘월요일 5교시가 가장 더운가?’ ‘1학년 복도 쪽이 항상 어두운가?’ 같은 "
        "패턴을 한 장으로 가립니다. 캠페인 우선순위 결정의 출발점."
    )
    metric = st.selectbox(
        "지표", list(LIMITS.keys()),
        format_func=lambda m: LIMITS[m]["label"],
        key="heatmap_metric",
    )
    days = st.slider("최근 N일", 1, 14, 7, key="heatmap_days")

    df_h = fetch_all_recent(since_minutes=days * 24 * 60)
    if df_h.empty:
        st.info(f"최근 {days}일 데이터 없음")
    else:
        df_h["hour"] = df_h["received_at"].dt.hour
        pivot = (df_h.pivot_table(index="node_id", columns="hour",
                                  values=metric, aggfunc="mean")
                      .reindex(sorted(df_h["node_id"].unique())))
        # 0~23시 컬럼 모두 보장
        for h in range(24):
            if h not in pivot.columns:
                pivot[h] = np.nan
        pivot = pivot[list(range(24))]

        st.caption(
            f"평균 {LIMITS[metric]['label']} · 행=교실(NODE_ID 정렬) · 열=0~23시"
        )

        # plotly 히트맵 — matplotlib 의존성 없음
        colorscale = ("RdYlGn_r" if metric == "temperature"
                      else ("Blues" if metric == "humidity" else "YlOrBr"))
        fig = go.Figure(data=go.Heatmap(
            z=pivot.values,
            x=[f"{h:02d}시" for h in range(24)],
            y=list(pivot.index),
            colorscale=colorscale,
            hovertemplate=(
                "교실 %{y}<br>%{x}<br>"
                f"평균 {LIMITS[metric]['label']}: " + "%{z:.1f}<extra></extra>"
            ),
            colorbar=dict(title=LIMITS[metric]['unit'], thickness=15),
        ))
        fig.update_layout(
            height=max(300, len(pivot) * 30 + 80),
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis=dict(side="top"),
            yaxis=dict(autorange="reversed"),
        )
        st.plotly_chart(fig, use_container_width=True)

        # 시간대별 위반 빈도 (캠페인 타깃 시간대)
        st.subheader("⏰ 시간대별 위반 빈도 — 어느 교시에 가장 자주 깨지나")
        lim = LIMITS[metric]
        df_h["viol"] = False
        if lim["max"] is not None:
            df_h["viol"] |= (df_h[metric] > lim["max"])
        if lim["min"] is not None:
            df_h["viol"] |= (df_h[metric] < lim["min"])
        per_hour = df_h.groupby("hour")["viol"].sum()
        # 0~23 모두 보장
        per_hour = per_hour.reindex(range(24), fill_value=0)
        fig = go.Figure(go.Bar(
            x=[f"{h:02d}시" for h in per_hour.index],
            y=per_hour.values,
            marker_color="#e74c3c",
            hovertemplate="%{x}<br>%{y}건<extra></extra>",
        ))
        fig.update_layout(
            height=240, margin=dict(l=10, r=10, t=10, b=10),
            showlegend=False, plot_bgcolor="#fafafa",
            xaxis_title=None, yaxis_title="위반 건수",
        )
        st.plotly_chart(fig, use_container_width=True)
