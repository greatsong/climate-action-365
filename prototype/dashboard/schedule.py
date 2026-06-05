"""
학급별 시간표 + 에너지 낭비 임계값.

두 가지 시간표 모드를 지원합니다:

(1) 기본 학교 시간표 — SCHEDULE_DEFAULT
    학교 전체가 같은 시간 운영(1~7교시) 가정.

(2) 학급별 엑셀 시간표 — 사이드바에서 업로드 가능
    행=학급(예 '1-1'), 열=요일+교시(예 '월1', '월2', ..., '금7').
    셀에 과목명이 있으면 그 시간에 수업, 빈 셀이면 공강(비수업).

학급별 시간표가 업로드되면 그 데이터가 우선이고,
업로드된 학급에 없으면 SCHEDULE_DEFAULT로 fallback.

학교마다 시간이 다르면 이 파일의 SCHEDULE_DEFAULT를 편집하세요.
시간은 KST(한국 표준시) 'HH:MM' 문자열.
"""

from pathlib import Path

import pandas as pd


# ---------- 기본 시간표 (월~금, 1~7교시) ----------
SCHEDULE_DEFAULT = {
    "weekdays": [0, 1, 2, 3, 4],         # 0=월 ... 4=금
    "periods": [
        # (시작, 끝, 라벨, 교시번호)
        ("08:50", "09:40", "1교시", 1),
        ("09:50", "10:40", "2교시", 2),
        ("10:50", "11:40", "3교시", 3),
        ("11:50", "12:40", "4교시", 4),
        # 점심 12:40~13:30 — 비수업
        ("13:30", "14:20", "5교시", 5),
        ("14:30", "15:20", "6교시", 6),
        ("15:30", "16:20", "7교시", 7),
    ],
}


# ---------- 에너지 낭비 임계값 ----------
LIGHT_ON_THRESHOLD = 40        # %
AIRCON_TEMP_THRESHOLD = 24     # °C 미만 (여름 적용)
HEATER_TEMP_THRESHOLD = 23     # °C 초과 (겨울 적용)
SUMMER_MONTHS = {5, 6, 7, 8, 9}
WINTER_MONTHS = {11, 12, 1, 2, 3}


# ---------- 학급별 엑셀 시간표 ----------
WEEKDAY_KR_TO_INT = {"월": 0, "화": 1, "수": 2, "목": 3, "금": 4,
                     "토": 5, "일": 6}

# 자동 탐색 후보 (사이드바 업로드 시 이 이름으로 저장)
SCHEDULE_DIR = Path(__file__).resolve().parent
SCHEDULE_FILE_CANDIDATES = [
    SCHEDULE_DIR / "schedule_data.xlsx",
    SCHEDULE_DIR / "schedule_data.csv",
]

# 모듈 캐시: {학급: {(weekday, period): 과목명}}
_class_schedule_cache = None
_class_schedule_path = None


def _parse_col_name(col):
    """엑셀 컬럼명 '월1' → (weekday=0, period=1). 실패 시 (None, None)."""
    if col is None:
        return None, None
    s = str(col).strip()
    if len(s) < 2:
        return None, None
    wd_char = s[0]
    period_str = s[1:]
    if wd_char not in WEEKDAY_KR_TO_INT:
        return None, None
    try:
        period = int(period_str)
    except ValueError:
        return None, None
    return WEEKDAY_KR_TO_INT[wd_char], period


def load_class_schedule(file_path=None, force=False):
    """엑셀 또는 CSV에서 학급별 시간표 로드 → 모듈 캐시.
    Returns: dict[학급][(weekday, period)] = 과목명(빈문자 = 공강)"""
    global _class_schedule_cache, _class_schedule_path

    if file_path is None:
        for p in SCHEDULE_FILE_CANDIDATES:
            if p.exists():
                file_path = p
                break
        if file_path is None:
            _class_schedule_cache = {}
            _class_schedule_path = None
            return {}

    path = Path(file_path)
    if not force and _class_schedule_path == path and _class_schedule_cache:
        return _class_schedule_cache

    try:
        if path.suffix.lower() in (".xlsx", ".xls"):
            df = pd.read_excel(path)
        else:
            df = pd.read_csv(path)
    except Exception:
        _class_schedule_cache = {}
        return {}

    if df.empty or len(df.columns) < 2:
        _class_schedule_cache = {}
        return {}

    class_col = df.columns[0]
    out = {}
    for _, row in df.iterrows():
        node_id = str(row[class_col]).strip()
        if not node_id or node_id.lower() in ("nan", "none", ""):
            continue
        out[node_id] = {}
        for col in df.columns[1:]:
            wd, period = _parse_col_name(col)
            if wd is None or period is None:
                continue
            value = row[col]
            value = "" if pd.isna(value) else str(value).strip()
            out[node_id][(wd, period)] = value

    _class_schedule_cache = out
    _class_schedule_path = path
    return out


def get_class_schedule():
    """현재 로드된 학급별 시간표를 반환."""
    if _class_schedule_cache is None:
        load_class_schedule()
    return _class_schedule_cache or {}


# ---------- 시간 판단 API ----------
def current_period(dt, schedule=None):
    """dt(datetime KST)가 어느 교시인지. 수업 중이면 라벨, 아니면 None."""
    if schedule is None:
        schedule = SCHEDULE_DEFAULT
    if dt.weekday() not in schedule["weekdays"]:
        return None
    hm = dt.strftime("%H:%M")
    for start, end, label, _ in schedule["periods"]:
        if start <= hm < end:
            return label
    return None


def current_period_number(dt, schedule=None):
    """현재 교시 번호(1~7) 또는 None."""
    if schedule is None:
        schedule = SCHEDULE_DEFAULT
    if dt.weekday() not in schedule["weekdays"]:
        return None
    hm = dt.strftime("%H:%M")
    for start, end, _, num in schedule["periods"]:
        if start <= hm < end:
            return num
    return None


def is_class_time(dt, schedule=None):
    """기본 학교 시간표 기준 수업 시간인가?"""
    return current_period(dt, schedule) is not None


def is_class_time_for_node(dt, node_id):
    """학급별 시간표를 보고 이 학급이 지금 수업 중인지.
    학급별 시간표가 없으면 기본 시간표로 fallback."""
    cs = get_class_schedule()
    if node_id and node_id in cs:
        wd = dt.weekday()
        period_num = current_period_number(dt)
        if period_num is None:
            return False
        cell = cs[node_id].get((wd, period_num), "")
        # 셀에 과목명이 있으면 수업 중, 비어 있으면 공강
        return bool(cell)
    return is_class_time(dt)


# ---------- 에너지 낭비 감지 ----------
def detect_waste(latest, current_dt, node_id=None):
    """비수업 시간 에너지 낭비 의심 감지.
    Returns: list of (icon, label)."""
    if is_class_time_for_node(current_dt, node_id):
        return []

    cs = get_class_schedule()
    is_weekend = current_dt.weekday() >= 5

    out = []
    light = latest.get("light")
    if light is not None and light >= LIGHT_ON_THRESHOLD:
        label = "조명 ON" if not is_weekend else "조명(주말)"
        out.append(("💡", label))

    temp = latest.get("temperature")
    month = current_dt.month
    if temp is not None:
        if month in SUMMER_MONTHS and temp <= AIRCON_TEMP_THRESHOLD:
            label = "에어컨 ON" if not is_weekend else "에어컨(주말)"
            out.append(("❄️", label))
        elif month in WINTER_MONTHS and temp >= HEATER_TEMP_THRESHOLD:
            label = "난방 ON" if not is_weekend else "난방(주말)"
            out.append(("🔥", label))

    return out


# ---------- 보조 ----------
def schedule_as_table(schedule=None):
    """기본 시간표를 표 형태로."""
    if schedule is None:
        schedule = SCHEDULE_DEFAULT
    return [{"교시": label, "시간": f"{start} ~ {end}"}
            for start, end, label, _ in schedule["periods"]]


def class_schedule_for_node(node_id):
    """특정 학급의 시간표 (요일×교시 표 형태로).
    Returns: DataFrame index=교시(1~7), columns=요일(월~금), values=과목명."""
    cs = get_class_schedule()
    if not cs or node_id not in cs:
        return None
    cells = cs[node_id]
    weekdays = ["월", "화", "수", "목", "금"]
    periods = sorted({p for _, p in cells.keys()})
    data = {wd: ["" for _ in periods] for wd in weekdays}
    for (wd, period), val in cells.items():
        if 0 <= wd < 5 and period in periods:
            data[weekdays[wd]][periods.index(period)] = val
    return pd.DataFrame(data, index=[f"{p}교시" for p in periods])


def make_template_excel(node_ids=None, path=None):
    """업로드용 빈 시간표 엑셀 템플릿 생성.
    학급은 1-1~1-8, 2-1~2-8 (당곡고 기본)."""
    if node_ids is None:
        node_ids = [f"{g}-{r}" for g in (1, 2) for r in range(1, 9)]
    cols = ["학급"]
    for wd in ("월", "화", "수", "목", "금"):
        for p in range(1, 8):
            cols.append(f"{wd}{p}")
    df = pd.DataFrame("", index=range(len(node_ids)), columns=cols)
    df["학급"] = node_ids
    if path is None:
        path = SCHEDULE_DIR / "schedule_template.xlsx"
    df.to_excel(path, index=False)
    return path
