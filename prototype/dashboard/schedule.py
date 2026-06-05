"""
학교 시간표 + 학급별 엑셀 시간표 + 에너지 낭비 임계값.

시간 정보 흐름:
1. 기본값: SCHEDULE_DEFAULT (이 파일 상단)
2. 사용자가 사이드바에서 편집 → schedule_config.json 저장
3. 학급별로 다른 시간표는 schedule_data.xlsx 업로드

런타임 우선순위: 학급별 엑셀 > config.json > SCHEDULE_DEFAULT
"""

import json
from pathlib import Path

import pandas as pd


SCHEDULE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = SCHEDULE_DIR / "schedule_config.json"


# ---------- 기본값 (점심 12:20~13:10) ----------
SCHEDULE_DEFAULT = {
    "weekdays": [0, 1, 2, 3, 4],     # 월~금
    "periods": [
        # (시작, 끝, 교시번호)
        ("08:50", "09:40", 1),
        ("09:50", "10:40", 2),
        ("10:50", "11:40", 3),
        ("11:30", "12:20", 4),
        # 점심 12:20~13:10 — 비수업
        ("13:10", "14:00", 5),
        ("14:10", "15:00", 6),
        ("15:10", "16:00", 7),
    ],
    "lunch": ("12:20", "13:10"),
}

# ---------- 기본 적정 범위 + 에너지 낭비 임계값 ----------
DEFAULT_LIMITS = {
    "temperature": {"min": 18, "max": 28, "unit": "°C", "label": "온도"},
    "humidity":    {"min": 30, "max": 80, "unit": "%RH", "label": "습도"},
    "light":       {"min": 30, "max": None, "unit": "%", "label": "조도"},
}
DEFAULT_LIGHT_ON_THRESHOLD = 40        # %
DEFAULT_AIRCON_TEMP_THRESHOLD = 24     # °C 미만 (여름)
DEFAULT_HEATER_TEMP_THRESHOLD = 23     # °C 초과 (겨울)

# Backwards-compat (모듈 외부에서 직접 참조 가능)
LIGHT_ON_THRESHOLD = DEFAULT_LIGHT_ON_THRESHOLD
AIRCON_TEMP_THRESHOLD = DEFAULT_AIRCON_TEMP_THRESHOLD
HEATER_TEMP_THRESHOLD = DEFAULT_HEATER_TEMP_THRESHOLD

SUMMER_MONTHS = {5, 6, 7, 8, 9}
WINTER_MONTHS = {11, 12, 1, 2, 3}


THRESHOLDS_FILE = SCHEDULE_DIR / "thresholds.json"


def load_thresholds():
    """경고 기준 + 낭비 임계값 로드. 파일 없으면 DEFAULT."""
    if THRESHOLDS_FILE.exists():
        try:
            with open(THRESHOLDS_FILE, encoding="utf-8") as f:
                data = json.load(f)
            limits = {
                k: {**DEFAULT_LIMITS[k], **data.get("limits", {}).get(k, {})}
                for k in DEFAULT_LIMITS
            }
            return {
                "limits": limits,
                "light_on": int(data.get(
                    "light_on", DEFAULT_LIGHT_ON_THRESHOLD)),
                "aircon": float(data.get(
                    "aircon", DEFAULT_AIRCON_TEMP_THRESHOLD)),
                "heater": float(data.get(
                    "heater", DEFAULT_HEATER_TEMP_THRESHOLD)),
            }
        except Exception:
            pass
    return {
        "limits": {k: dict(v) for k, v in DEFAULT_LIMITS.items()},
        "light_on": DEFAULT_LIGHT_ON_THRESHOLD,
        "aircon": DEFAULT_AIRCON_TEMP_THRESHOLD,
        "heater": DEFAULT_HEATER_TEMP_THRESHOLD,
    }


def save_thresholds(limits, light_on, aircon, heater):
    data = {
        "limits": {
            k: {"min": v["min"], "max": v["max"]} for k, v in limits.items()
        },
        "light_on": int(light_on),
        "aircon": float(aircon),
        "heater": float(heater),
    }
    with open(THRESHOLDS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    # 모듈 전역도 갱신 (기존 detect_waste가 LIGHT_ON_THRESHOLD 직접 참조)
    global LIGHT_ON_THRESHOLD, AIRCON_TEMP_THRESHOLD, HEATER_TEMP_THRESHOLD
    LIGHT_ON_THRESHOLD = int(light_on)
    AIRCON_TEMP_THRESHOLD = float(aircon)
    HEATER_TEMP_THRESHOLD = float(heater)
    return data


def reset_thresholds():
    if THRESHOLDS_FILE.exists():
        THRESHOLDS_FILE.unlink()
    global LIGHT_ON_THRESHOLD, AIRCON_TEMP_THRESHOLD, HEATER_TEMP_THRESHOLD
    LIGHT_ON_THRESHOLD = DEFAULT_LIGHT_ON_THRESHOLD
    AIRCON_TEMP_THRESHOLD = DEFAULT_AIRCON_TEMP_THRESHOLD
    HEATER_TEMP_THRESHOLD = DEFAULT_HEATER_TEMP_THRESHOLD


# 시작 시 한 번 모듈 전역 동기화
_init_th = load_thresholds()
LIGHT_ON_THRESHOLD = _init_th["light_on"]
AIRCON_TEMP_THRESHOLD = _init_th["aircon"]
HEATER_TEMP_THRESHOLD = _init_th["heater"]


# ---------- 시간 설정 JSON (런타임 우선) ----------
# 점심시간 정책:
#   "out_of_class" — 학생들이 급식실로 → 점심시간 비수업으로 처리 (낭비 감지 ON)
#   "in_class"     — 교실에서 점심 → 수업 시간처럼 정상 사용 (낭비 감지 OFF)
DEFAULT_LUNCH_POLICY = "out_of_class"


def load_config():
    """schedule_config.json이 있으면 반환, 없으면 DEFAULT."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, encoding="utf-8") as f:
                data = json.load(f)
            return {
                "weekdays": data.get("weekdays", SCHEDULE_DEFAULT["weekdays"]),
                "periods": [
                    (p["start"], p["end"], int(p["num"]))
                    for p in data["periods"]
                ],
                "lunch": (data["lunch"]["start"], data["lunch"]["end"]),
                "lunch_policy": data.get("lunch_policy",
                                         DEFAULT_LUNCH_POLICY),
            }
        except Exception:
            pass
    return {**SCHEDULE_DEFAULT, "lunch_policy": DEFAULT_LUNCH_POLICY}


def save_config(periods, lunch, lunch_policy=None, weekdays=None):
    data = {
        "weekdays": weekdays or [0, 1, 2, 3, 4],
        "periods": [{"start": s, "end": e, "num": n} for s, e, n in periods],
        "lunch": {"start": lunch[0], "end": lunch[1]},
        "lunch_policy": lunch_policy or DEFAULT_LUNCH_POLICY,
    }
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return data


def reset_config():
    """schedule_config.json 삭제 → DEFAULT로 복귀."""
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()


# ---------- 학급별 엑셀 시간표 ----------
WEEKDAY_KR_TO_INT = {"월": 0, "화": 1, "수": 2, "목": 3, "금": 4,
                     "토": 5, "일": 6}

SCHEDULE_FILE_CANDIDATES = [
    SCHEDULE_DIR / "schedule_data.xlsx",
    SCHEDULE_DIR / "schedule_data.csv",
]

_class_schedule_cache = None
_class_schedule_path = None


def _parse_col_name(col):
    """'월1' → (0, 1). 실패 시 (None, None)."""
    if col is None:
        return None, None
    s = str(col).strip()
    if len(s) < 2:
        return None, None
    wd_char = s[0]
    if wd_char not in WEEKDAY_KR_TO_INT:
        return None, None
    try:
        period = int(s[1:])
    except ValueError:
        return None, None
    return WEEKDAY_KR_TO_INT[wd_char], period


def load_class_schedule(file_path=None, force=False):
    """엑셀/CSV → 학급별 시간표 dict 캐시."""
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
    if _class_schedule_cache is None:
        load_class_schedule()
    return _class_schedule_cache or {}


# ---------- 시간 판단 API ----------
def is_lunch_time(dt, schedule=None):
    """현재가 점심시간인지."""
    if schedule is None:
        schedule = load_config()
    lunch = schedule.get("lunch")
    if not lunch:
        return False
    if dt.weekday() not in schedule["weekdays"]:
        return False
    hm = dt.strftime("%H:%M")
    return lunch[0] <= hm < lunch[1]


def current_period_number(dt, schedule=None):
    """현재 교시 번호(1~7) 또는 None. 점심시간은 None."""
    if schedule is None:
        schedule = load_config()
    if dt.weekday() not in schedule["weekdays"]:
        return None
    if is_lunch_time(dt, schedule):
        return None
    hm = dt.strftime("%H:%M")
    for start, end, num in schedule["periods"]:
        if start <= hm < end:
            return num
    return None


def current_period(dt, schedule=None):
    """현재 교시 라벨('3교시') 또는 None."""
    num = current_period_number(dt, schedule)
    return f"{num}교시" if num else None


def is_class_time(dt, schedule=None):
    return current_period_number(dt, schedule) is not None


def is_class_time_for_node(dt, node_id):
    """학급별 엑셀 시간표 우선 적용."""
    cs = get_class_schedule()
    if node_id and node_id in cs:
        wd = dt.weekday()
        period_num = current_period_number(dt)
        if period_num is None:
            return False
        cell = cs[node_id].get((wd, period_num), "")
        return bool(cell)
    return is_class_time(dt)


# ---------- 에너지 낭비 감지 ----------
def detect_waste(latest, current_dt, node_id=None):
    if is_class_time_for_node(current_dt, node_id):
        return []
    # 점심시간 정책: 교실에서 점심을 먹는 학교면 정상 사용으로 처리
    cfg = load_config()
    if (is_lunch_time(current_dt, cfg)
            and cfg.get("lunch_policy") == "in_class"):
        return []
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
    """시간표를 표 형태로. 점심시간도 한 줄 포함."""
    if schedule is None:
        schedule = load_config()
    rows = []
    for start, end, num in schedule["periods"]:
        rows.append({"교시": f"{num}교시", "시간": f"{start} ~ {end}"})
        # 4교시 다음에 점심 한 줄 끼우기 (있다면)
        lunch = schedule.get("lunch")
        if lunch and num == 4:
            rows.append({"교시": "🍱 점심", "시간": f"{lunch[0]} ~ {lunch[1]}"})
    return rows


def class_schedule_for_node(node_id):
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
