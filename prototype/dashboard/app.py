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
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

import schedule as sched      # 학급별 시간표 + 낭비 감지

SERVER_URL = "http://localhost:8000"

# 학교 구조 (당곡고 16개 교실 = 1학년 8반 + 2학년 8반)
GRADES = [1, 2]
ROOMS_PER_GRADE = 8

# 경고 기준 — schedule.py의 thresholds.json에서 로드 (사이드바에서 편집)
LIMITS = sched.load_thresholds()["limits"]

# 추세 띠 설정
TREND_WINDOW_MIN = 30   # 카드 안의 띠가 다루는 시간 범위
TREND_SLOTS = 5         # 5칸 (각 6분 평균)


st.set_page_config(page_title="기후행동365 대시보드",
                   page_icon="🌱", layout="wide")

# ---------- 스타일 ----------
st.markdown("""<style>
.block-container{padding-top:2rem;padding-bottom:0.5rem;max-width:1500px;
                 padding-left:0.7rem;padding-right:0.7rem;}
/* ----- 제목: 절대 잘리지 않게 ----- */
h1, .stMarkdown h1{
  font-size:1.55rem !important;
  line-height:1.6 !important;
  margin:0 0 0.3em !important;
  padding:0.15em 0 0.05em !important;
  font-weight:700 !important;
  overflow:visible !important;
  white-space:normal !important;
  display:block !important;
  -webkit-line-clamp:unset !important;
}
[data-testid="stCaptionContainer"]{margin-bottom:0.2em;}
/* 빈 markdown 헤더(### ) 간격 줄이기 */
h3{margin-top:0.4em !important;margin-bottom:0.2em !important;}
/* KPI metric 컴팩트 */
[data-testid="stMetric"]{padding:0.2em 0.4em;}
[data-testid="stMetricLabel"]{font-size:0.78em !important;}
[data-testid="stMetricValue"]{font-size:1.4em !important;}
/* 탭 컴팩트 */
.stTabs [data-baseweb="tab-list"]{gap:0.5em;}
.stTabs [data-baseweb="tab"]{padding:0.3em 0.6em;}

.grade-header{font-size:1em;color:#444;font-weight:700;
              border-left:4px solid #2ecc71;padding:0.2em 0.6em;
              margin:0.5em 0 0.3em;background:#f6fbf8;border-radius:3px;}

/* ----- 반응형 카드 그리드 ----- */
.room-grid{display:grid;
           grid-template-columns:repeat(auto-fit, minmax(130px, 1fr));
           gap:0.35em;margin-bottom:0.3em;}
@media (max-width:480px){
  .room-grid{grid-template-columns:repeat(2, minmax(0, 1fr));gap:0.3em;}
}

/* ----- 라이브 카드 (컴팩트) ----- */
.room-card{background:#fff;padding:0.5em 0.5em 0.4em;border-radius:10px;
           box-shadow:0 1px 4px rgba(0,0,0,0.05);text-align:left;
           min-height:7.5em;border:1px solid #f0f0f0;
           transition:all 0.25s ease;overflow:hidden;
           display:flex;flex-direction:column;}
.room-card:hover{box-shadow:0 4px 12px rgba(0,0,0,0.12);
                 transform:translateY(-2px);border-color:#e0e0e0;}
.room-card.stale{background:#fff5f5;border:1px solid #fcc;}
.room-card.empty{background:#fafafa;border:1px dashed #ddd;}
.room-card.empty:hover{transform:none;box-shadow:0 2px 6px rgba(0,0,0,0.06);}
.room-card.danger{border-color:#e74c3c;
                  box-shadow:0 0 0 1px rgba(231,76,60,0.2),
                             0 2px 8px rgba(231,76,60,0.15);}

/* ----- 헤더 + 라이브 도트 ----- */
.room-id{font-size:0.9em;color:#333;font-weight:700;margin-bottom:0.25em;
         display:flex;align-items:center;gap:0.3em;
         white-space:nowrap;overflow:hidden;}
.room-id .nid{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;}
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

/* ----- 태그 (헤더 아래 별도 줄) ----- */
.room-tags{display:flex;flex-wrap:wrap;gap:3px;margin-bottom:0.35em;
           min-height:0;}
.room-tag{font-size:0.62em;color:#888;background:#f0f0f0;padding:1px 5px;
          border-radius:8px;font-weight:500;white-space:nowrap;
          line-height:1.4;}
.room-tag.vent{background:#fff3cd;color:#856404;
               animation:tag-glow 2s ease-in-out infinite;}
.room-tag.waste{background:#ffe5e5;color:#c0392b;font-weight:600;
                animation:tag-pulse 1.4s ease-in-out infinite;}
@keyframes tag-glow {
  0%,100% { background:#fff3cd; }
  50%     { background:#ffe69c; }
}
@keyframes tag-pulse {
  0%,100% { background:#ffe5e5; box-shadow:0 0 0 0 rgba(192,57,43,0); }
  50%     { background:#ffc9c9; box-shadow:0 0 0 3px rgba(192,57,43,0.1); }
}
.room-empty{color:#bbb;font-size:0.8em;padding:2em 0;text-align:center;}

/* ----- 지표 행 ----- */
.metric-row{display:flex;align-items:center;gap:0.3em;
            font-size:0.85em;padding:0.1em 0;
            font-variant-numeric:tabular-nums;
            flex-wrap:nowrap;}
.metric-lab{font-size:0.68em;color:#999;font-weight:500;
            width:0.9em;flex-shrink:0;}
.metric-emoji{font-size:0.95em;width:1.3em;flex-shrink:0;
              text-align:center;}
.metric-emoji.glow{filter:drop-shadow(0 0 4px rgba(243,156,18,0.7));
                   animation:bulb-glow 2.5s ease-in-out infinite;}
@keyframes bulb-glow {
  0%,100% { filter:drop-shadow(0 0 3px rgba(243,156,18,0.5)); }
  50%     { filter:drop-shadow(0 0 7px rgba(243,156,18,0.9)); }
}
.metric-val{font-weight:700;min-width:2.4em;text-align:right;
            transition:color 0.3s ease;flex-shrink:0;}
.metric-val.danger{animation:val-pulse 1.4s ease-in-out infinite;}
@keyframes val-pulse {
  0%,100% { opacity:1; }
  50%     { opacity:0.55; }
}
.metric-unit{font-size:0.65em;color:#aaa;flex-shrink:0;}

/* ----- 5칸 추세 띠 (마지막 칸 = 현재 라이브) ----- */
.trend-strip{display:inline-flex;gap:2px;margin-left:auto;
             align-items:center;flex-shrink:0;}
.trend-cell{width:8px;height:11px;border-radius:2px;
            transition:background 0.3s ease;flex-shrink:0;}
.trend-cell.live{width:10px;height:13px;border-radius:3px;
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


def kst_now():
    """현재 시각 (Pi 5 timezone이 Asia/Seoul로 설정되어 있다고 가정)."""
    return datetime.now()


# ---------- 헤더 ----------
st.title("🚀 우주최강 당곡고 기후행동365 🌱 — 학교 전체 환경")
now_kst = kst_now()
current_class = sched.current_period(now_kst)
class_label = f"📚 {current_class} 중" if current_class else "🛌 비수업 시간"
weekday_kr = ["월", "화", "수", "목", "금", "토", "일"][now_kst.weekday()]
st.caption(
    f"🌡️ 온도 · 💧 습도 · 💡 조도 · 📈 5칸 띠 = 최근 30분 · "
    f"**지금: {now_kst.strftime('%m/%d')} ({weekday_kr}) "
    f"{now_kst.strftime('%H:%M')} · {class_label}** ✨"
)

# ---------- 사이드바: 시간표 ----------
with st.sidebar:
    st.header("📅 학교 시간표")
    st.caption(f"오늘은 **{weekday_kr}요일**입니다.")

    # ----- 경고 기준(LIMITS) + 낭비 임계값 슬라이더 -----
    with st.expander("🎚️ 경고 기준 조정 (적정 범위 + 낭비 감지)"):
        cur_th = sched.load_thresholds()
        with st.form("th_form", border=False):
            st.markdown("**🌡️ 온도 적정 범위 (°C)**")
            t_min, t_max = st.slider(
                "온도", 0, 40,
                (int(cur_th["limits"]["temperature"]["min"]),
                 int(cur_th["limits"]["temperature"]["max"])),
                label_visibility="collapsed",
            )

            st.markdown("**💧 습도 적정 범위 (%RH)**")
            h_min, h_max = st.slider(
                "습도", 0, 100,
                (int(cur_th["limits"]["humidity"]["min"]),
                 int(cur_th["limits"]["humidity"]["max"])),
                label_visibility="collapsed",
            )

            st.markdown("**💡 조도 권장 하한 (%)**")
            l_min = st.slider(
                "조도", 0, 100,
                int(cur_th["limits"]["light"]["min"]),
                label_visibility="collapsed",
            )

            st.divider()
            st.markdown("**⚡ 에너지 낭비 감지 임계값** (비수업 시간 적용)")
            light_on = st.slider(
                "💡 조명 ON 의심 — 조도 ≥",
                0, 100, int(cur_th["light_on"]),
            )
            aircon = st.slider(
                "❄️ 에어컨 ON 의심 — 온도 ≤ (여름)",
                15.0, 28.0, float(cur_th["aircon"]), 0.5,
            )
            heater = st.slider(
                "🔥 난방 ON 의심 — 온도 ≥ (겨울)",
                18.0, 30.0, float(cur_th["heater"]), 0.5,
            )

            cA, cB = st.columns([3, 1])
            saved_th = cA.form_submit_button("💾 저장", type="primary",
                                             use_container_width=True)
            reset_th = cB.form_submit_button("↺ 기본",
                                             use_container_width=True)
            if saved_th:
                new_limits = {
                    "temperature": {**cur_th["limits"]["temperature"],
                                    "min": t_min, "max": t_max},
                    "humidity":    {**cur_th["limits"]["humidity"],
                                    "min": h_min, "max": h_max},
                    "light":       {**cur_th["limits"]["light"],
                                    "min": l_min, "max": None},
                }
                sched.save_thresholds(new_limits, light_on, aircon, heater)
                st.success("✅ 저장됨. 다시 로드합니다…")
                st.rerun()
            elif reset_th:
                sched.reset_thresholds()
                st.success("✅ 기본값으로 복귀. 다시 로드합니다…")
                st.rerun()

    # ----- 교시·점심시간 편집 -----
    with st.expander("⚙️ 교시·점심시간 설정 (학교별 조정)"):
        from datetime import time as dtime

        def _t(s):
            h, m = s.split(":")
            return dtime(int(h), int(m))

        cur = sched.load_config()
        with st.form("sched_cfg_form", border=False):
            st.caption("학교 시간표를 본인 학교에 맞게 조정한 뒤 **저장**을 누르세요.")

            st.markdown("**🍱 점심시간**")
            lc1, lc2 = st.columns(2)
            l_start = lc1.time_input("시작", value=_t(cur["lunch"][0]),
                                     key="lunch_start", step=300,
                                     label_visibility="collapsed")
            l_end = lc2.time_input("종료", value=_t(cur["lunch"][1]),
                                   key="lunch_end", step=300,
                                   label_visibility="collapsed")
            lc1.caption("점심 시작")
            lc2.caption("점심 종료")

            st.markdown("**🍱 점심시간 사용 정책**")
            cur_policy = cur.get("lunch_policy", "out_of_class")
            lunch_policy = st.radio(
                "점심시간 사용 정책",
                options=["out_of_class", "in_class"],
                index=0 if cur_policy == "out_of_class" else 1,
                format_func=lambda v: {
                    "out_of_class": (
                        "🏃 학생들이 급식실로 — 점심시간 = 비수업 "
                        "(에어컨·조명 켜져 있으면 낭비 의심)"),
                    "in_class": (
                        "🍱 교실에서 점심 — 점심시간 = 수업처럼 정상 사용 "
                        "(낭비 감지 안 함)"),
                }[v],
                label_visibility="collapsed",
            )

            st.markdown("**📚 교시 시작·종료**")
            new_periods = []
            for s, e, num in cur["periods"]:
                pc1, pc2, pc3 = st.columns([0.6, 1, 1])
                pc1.markdown(f"<div style='padding-top:0.5em;font-weight:600;'>"
                             f"{num}교시</div>", unsafe_allow_html=True)
                ns = pc2.time_input(f"{num}교시 시작", value=_t(s),
                                    key=f"p{num}_s", step=300,
                                    label_visibility="collapsed")
                ne = pc3.time_input(f"{num}교시 종료", value=_t(e),
                                    key=f"p{num}_e", step=300,
                                    label_visibility="collapsed")
                new_periods.append((ns.strftime("%H:%M"),
                                    ne.strftime("%H:%M"), num))

            colA, colB = st.columns([3, 1])
            saved = colA.form_submit_button("💾 저장", type="primary",
                                            use_container_width=True)
            reset = colB.form_submit_button("↺ 기본",
                                            use_container_width=True)

            if saved:
                sched.save_config(
                    new_periods,
                    (l_start.strftime("%H:%M"), l_end.strftime("%H:%M")),
                    lunch_policy=lunch_policy,
                )
                st.success("✅ 저장됨. 다시 로드합니다…")
                st.rerun()
            elif reset:
                sched.reset_config()
                st.success("✅ 기본값으로 복귀. 다시 로드합니다…")
                st.rerun()

    # 학급별 엑셀 업로드
    sched.load_class_schedule()    # 저장된 파일 자동 로드
    class_sched = sched.get_class_schedule()
    if class_sched:
        st.success(f"✅ 학급별 시간표 인식: {len(class_sched)}개 학급")
        view_node = st.selectbox(
            "학급별 시간표 미리보기",
            sorted(class_sched.keys()),
        )
        df_view = sched.class_schedule_for_node(view_node)
        if df_view is not None:
            st.dataframe(df_view, use_container_width=True, height=280)
    else:
        st.info("학교 공통 시간표 사용 중. 학급별 시간표 엑셀을 "
                "업로드하면 학급마다 공강 시간도 자동 인식합니다.")
        rows = sched.schedule_as_table()
        for r in rows:
            is_now = (current_class == r["교시"])
            is_lunch = (r["교시"] == "🍱 점심")
            prefix = "▶️ " if is_now else "  "
            if is_now:
                style = "color:#2ecc71;font-weight:700;"
            elif is_lunch:
                style = "color:#f39c12;font-weight:600;"
            else:
                style = "color:#666;"
            st.markdown(
                f'<div style="{style}font-size:0.92em;padding:0.15em 0;">'
                f'{prefix}<b>{r["교시"]}</b> · {r["시간"]}</div>',
                unsafe_allow_html=True,
            )

    st.divider()
    upload = st.file_uploader(
        "📤 시간표 엑셀/CSV 업로드",
        type=["xlsx", "xls", "csv"],
        help=("행=학급(예 1-1), 열=요일+교시(예 월1, 월2, ..., 금7). "
              "셀에 과목명이 있으면 수업, 빈 셀은 공강(=비수업)."),
    )
    if upload is not None:
        suffix = Path(upload.name).suffix.lower() or ".xlsx"
        save_path = sched.SCHEDULE_DIR / f"schedule_data{suffix}"
        with open(save_path, "wb") as f:
            f.write(upload.getbuffer())
        loaded = sched.load_class_schedule(save_path, force=True)
        if loaded:
            st.success(
                f"✅ {upload.name} 저장 · {len(loaded)}개 학급 인식. "
                "페이지를 새로 고침하세요."
            )
        else:
            st.error("❌ 파일을 읽었지만 학급 데이터를 찾지 못했습니다. "
                     "첫 행에 학급/월1/월2/.../금7 형태로 헤더를 두세요.")

    with st.expander("📝 엑셀 형식 가이드"):
        st.markdown(
            """**행** : 학급 (예: `1-1`, `1-2`, ...)
**열** : 요일+교시 (예: `월1`, `월2`, ..., `금7`)
**셀** : 과목명 (빈 셀 = 공강/비수업)

예시:
| 학급 | 월1 | 월2 | 월3 | … | 금7 |
|---|---|---|---|---|---|
| 1-1 | 국어 | 수학 | 영어 | … |  |
| 1-2 | 수학 | 국어 |  | … | 체육 |"""
        )
        if st.button("📥 빈 템플릿 엑셀 만들기"):
            path = sched.make_template_excel()
            with open(path, "rb") as f:
                st.download_button(
                    "schedule_template.xlsx 받기",
                    data=f.read(),
                    file_name="schedule_template.xlsx",
                    mime=("application/vnd.openxmlformats-officedocument"
                          ".spreadsheetml.sheet"),
                )

    st.divider()
    st.caption(
        "비수업 시간에 다음이 켜져 있으면 ‘낭비 의심’ 라벨이 카드에 뜹니다:\n\n"
        f"- 💡 조도 ≥ {sched.LIGHT_ON_THRESHOLD}% → 조명 ON\n"
        f"- ❄️ 온도 ≤ {sched.AIRCON_TEMP_THRESHOLD}°C (여름) → 에어컨 ON\n"
        f"- 🔥 온도 ≥ {sched.HEATER_TEMP_THRESHOLD}°C (겨울) → 난방 ON\n\n"
        "임계값 조정은 위쪽 **🎚️ 경고 기준 조정**에서."
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

    # 위반 + 평균 집계 + 에너지 낭비 감지
    violations = []
    all_t, all_rh, all_lt = [], [], []
    vent_nodes = []
    waste_alerts = []        # [(node_id, [(icon, label), ...]), ...]
    for n in nodes:
        if is_stale(n["last_seen"]):
            continue
        latest = n.get("latest") or {}
        if needs_ventilation(latest):
            vent_nodes.append(n["node_id"])
        wastes = sched.detect_waste(latest, now_kst, node_id=n["node_id"])
        if wastes:
            waste_alerts.append((n["node_id"], wastes))
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
                    "기준": (f"{lim['min']}-{lim['max']}{lim['unit']}"
                             if lim['max'] else f"≥{lim['min']}{lim['unit']}"),
                })
            if metric == "temperature": all_t.append(v)
            elif metric == "humidity": all_rh.append(v)
            elif metric == "light":   all_lt.append(v)

    danger_rooms = len({v["교실"] for v in violations})

    # ---------- KPI ----------
    c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
    c1.metric("📡 온라인", f"{online} / {total}",
              help="최근 5분 내 수신 / 예상 전체")
    c2.metric("🚨 기준 초과", f"{danger_rooms} 교실",
              delta=f"{len(violations)}건" if violations else None,
              delta_color="inverse")
    c3.metric("⚡ 에너지 낭비", f"{len(waste_alerts)} 교실",
              help=("비수업 시간인데 조명·에어컨·난방이 켜져 있다고 "
                    "의심되는 노드 수"),
              delta="비수업 시간" if not current_class else "수업 중",
              delta_color="inverse" if not current_class else "off")
    c4.metric("💨 환기 권장", f"{len(vent_nodes)} 교실",
              help="현재 온도·습도 모두 기준 가까이")
    c5.metric("🌡️ 평균 온도",
              f"{np.mean(all_t):.1f}°C" if all_t else "—")
    c6.metric("💧 평균 습도",
              f"{np.mean(all_rh):.0f}%" if all_rh else "—")
    c7.metric("💡 평균 조도",
              f"{np.mean(all_lt):.0f}%" if all_lt else "—")

    # ---------- 학년별 반응형 그리드 (현재값 + 5칸 추세 띠) ----------
    for grade in GRADES:
        st.markdown(
            f'<div class="grade-header">📚 {grade}학년</div>',
            unsafe_allow_html=True,
        )

        cards = ['<div class="room-grid">']
        for room in range(1, ROOMS_PER_GRADE + 1):
            node_id = f"{grade}-{room}"
            node = node_by_id.get(node_id)

            if node is None:
                cards.append(
                    f'<div class="room-card empty">'
                    f'<div class="room-id"><span class="nid">{node_id}</span></div>'
                    f'<div class="room-empty">미설치</div></div>'
                )
                continue

            stale = is_stale(node["last_seen"])
            latest = node.get("latest") or {}

            if (df_recent_by_node is not None
                    and node_id in df_recent_by_node.groups):
                df_n = df_recent_by_node.get_group(node_id)
            else:
                df_n = pd.DataFrame()

            # 태그들 (헤더 옆이 아닌 별도 줄)
            tag_parts = []
            if needs_ventilation(latest):
                tag_parts.append('<span class="room-tag vent">💨 환기</span>')
            for icon, label in sched.detect_waste(latest, now_kst,
                                                  node_id=node_id):
                tag_parts.append(
                    f'<span class="room-tag waste">{icon} {label}</span>'
                )
            tags_html = (f'<div class="room-tags">{"".join(tag_parts)}</div>'
                         if tag_parts else "")

            card_danger = any(
                status_for(m, latest.get(m))[1] in ("높음", "낮음")
                for m in ("temperature", "humidity", "light")
                if latest.get(m) is not None
            )
            if stale:
                cls = "room-card stale"
            elif card_danger:
                cls = "room-card danger"
            else:
                cls = "room-card"

            if stale:
                dot = ""
                badge = "🚨 "
            else:
                dot_cls = "live-dot danger" if card_danger else "live-dot"
                dot = f'<span class="{dot_cls}"></span>'
                badge = ""

            parts = [
                f'<div class="{cls}">',
                f'<div class="room-id">{dot}'
                f'<span class="nid">{badge}{node_id}</span></div>',
                tags_html,
            ]

            for emoji, val, fmt, unit, metric in [
                ("🌡️", latest.get("temperature"), "{:.1f}", "°", "temperature"),
                ("💧", latest.get("humidity"),    "{:.0f}", "%", "humidity"),
                ("💡", latest.get("light"),       "{:.0f}", "%", "light"),
            ]:
                color, lvl = status_for(metric, val)
                cells = trend_colors(df_n, metric)
                strip_parts = []
                for i, c in enumerate(cells):
                    if i == len(cells) - 1 and c != "#e8e8e8":
                        strip_parts.append(
                            f'<span class="trend-cell live" '
                            f'style="background:{c};color:{c}"></span>'
                        )
                    else:
                        strip_parts.append(
                            f'<span class="trend-cell" style="background:{c}"></span>'
                        )
                strip = ''.join(strip_parts)
                val_s = fmt.format(val) if val is not None else "—"
                val_cls = ("metric-val danger" if lvl in ("높음", "낮음")
                           else "metric-val")
                # 💡 조도가 충분히 밝으면 노랑 빛나는 효과
                emoji_cls = "metric-emoji"
                if metric == "light" and val is not None and val >= 50:
                    emoji_cls += " glow"
                parts.append(
                    f'<div class="metric-row">'
                    f'<span class="{emoji_cls}">{emoji}</span>'
                    f'<span class="{val_cls}" style="color:{color}">{val_s}</span>'
                    f'<span class="metric-unit">{unit}</span>'
                    f'<span class="trend-strip">{strip}</span>'
                    f'</div>'
                )
            parts.append('</div>')
            cards.append("".join(parts))

        cards.append('</div>')
        st.markdown("".join(cards), unsafe_allow_html=True)

    # 5칸 추세 띠 범례
    st.caption(
        "📖 카드 안의 5칸 띠 = 최근 30분을 6분씩 5구간 평균 (좌→우 = 과거→현재). "
        "🟩 적정 · 🟧/🟥 기준 밖 · ⬜ 데이터 없음. "
        f"적정 범위: 🌡️ {LIMITS['temperature']['min']}-{LIMITS['temperature']['max']}°C · "
        f"💧 {LIMITS['humidity']['min']}-{LIMITS['humidity']['max']}%RH · "
        f"💡 ≥{LIMITS['light']['min']}% "
        "(사이드바 ‘🎚️ 경고 기준 조정’에서 변경)"
    )

    # ---------- 학교 전체 1시간 시계열 (plotly) ----------
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

        def line_with_bands(series, color, ymin=None, ymax=None):
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=series.index, y=series.values, mode="lines",
                name="",                                        # placeholder 제거
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
                showlegend=False,
                title=dict(text=""),                            # 'undefined' 방지
                xaxis_title=None, yaxis_title=None,
                plot_bgcolor="#fafafa",
                hovermode="x unified",
            )
            return fig

        t_lim = LIMITS["temperature"]; h_lim = LIMITS["humidity"]; l_lim = LIMITS["light"]
        if "temperature" in minute_avg.columns:
            with cc1:
                st.caption(f"🌡️ 온도 (°C) · 적정 {t_lim['min']}-{t_lim['max']}")
                st.plotly_chart(
                    line_with_bands(minute_avg["temperature"],
                                    "#e74c3c", ymin=t_lim['min'], ymax=t_lim['max']),
                    use_container_width=True,
                )
        if "humidity" in minute_avg.columns:
            with cc2:
                st.caption(f"💧 습도 (%RH) · 적정 {h_lim['min']}-{h_lim['max']}")
                st.plotly_chart(
                    line_with_bands(minute_avg["humidity"],
                                    "#3498db", ymin=h_lim['min'], ymax=h_lim['max']),
                    use_container_width=True,
                )
        if "light" in minute_avg.columns:
            with cc3:
                st.caption(f"💡 조도 (%) · 권장 ≥{l_lim['min']}")
                st.plotly_chart(
                    line_with_bands(minute_avg["light"],
                                    "#f39c12", ymin=l_lim['min']),
                    use_container_width=True,
                )

    # ---------- 오늘 누적 위반 시간 (캠페인 우선순위) ----------
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

    # ---------- 에너지 낭비 알림 ----------
    if current_class:
        st.subheader(f"⚡ 에너지 낭비 의심 — 지금은 {current_class} 중")
        st.caption(
            "지금은 수업 시간이라 에어컨·조명이 켜져 있는 게 정상입니다. "
            "비수업 시간(쉬는 시간·점심·하교 후)에 다시 확인하세요."
        )
    else:
        st.subheader("⚡ 에너지 낭비 의심 — 비수업 시간")
        if waste_alerts:
            rows = []
            for nid, wastes in waste_alerts:
                node = node_by_id.get(nid, {})
                latest = node.get("latest") or {}
                rows.append({
                    "교실": nid,
                    "감지": " ".join(f"{i} {l}" for i, l in wastes),
                    "온도": f"{latest.get('temperature', 0):.1f}°C"
                            if latest.get('temperature') is not None else "—",
                    "조도": f"{latest.get('light', 0):.0f}%"
                            if latest.get('light') is not None else "—",
                    "마지막 수신": (node.get("last_seen") or "")[:19].replace("T", " "),
                })
            st.dataframe(
                pd.DataFrame(rows),
                hide_index=True, use_container_width=True,
            )
            st.info(
                "💡 캠페인 아이디어: 위 교실로 직접 가서 에너지 끄기 + 메모 "
                "기록(언제·누가·껐을 때 효과 30분 후 데이터 확인)"
            )
        else:
            st.success(
                "✅ 비수업 시간인데 모든 노드가 ‘에너지 OFF’ 상태입니다. "
                "에너지 절약 잘 되고 있어요."
            )

    # ---------- 현재 기준 위반 ----------
    st.subheader("🚨 지금 기준 위반 중")
    if violations:
        st.dataframe(
            pd.DataFrame(violations).sort_values(["상태", "교실"]),
            hide_index=True, use_container_width=True,
        )
    else:
        st.success("✅ 모든 온라인 노드가 적정 범위 안에 있습니다. 🎉")


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
                    name="",
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
                    title=dict(text=""),
                    xaxis_title=None, yaxis_title=None,
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
                    title=dict(text=""),
                    xaxis_title=None, yaxis_title=None,
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
            title=dict(text=""),
            xaxis=dict(side="top", title=None),
            yaxis=dict(autorange="reversed", title=None),
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
            title=dict(text=""),
            xaxis_title=None, yaxis_title="위반 건수",
        )
        st.plotly_chart(fig, use_container_width=True)
