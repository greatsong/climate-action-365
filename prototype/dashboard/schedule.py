"""
학급별 시간표 + 에너지 낭비 임계값.

학교마다 시간표가 다르면 이 파일만 편집하면 됩니다.
시간은 KST(한국 표준시) 기준 'HH:MM' 문자열.

요일: 0=월, 1=화, 2=수, 3=목, 4=금, 5=토, 6=일
"""

# 당곡고 표준 시간표 (1·2학년 공통 가정)
# 학급별로 다르면 SCHEDULE_BY_NODE에 NODE_ID별로 따로 정의 가능
SCHEDULE_DEFAULT = {
    "weekdays": [0, 1, 2, 3, 4],         # 월~금만
    "periods": [
        # (시작, 끝, 라벨)
        ("08:50", "09:40", "1교시"),
        ("09:50", "10:40", "2교시"),
        ("10:50", "11:40", "3교시"),
        ("11:50", "12:40", "4교시"),
        # 점심 시간 (12:40~13:30) — 비수업
        ("13:30", "14:20", "5교시"),
        ("14:30", "15:20", "6교시"),
        ("15:30", "16:20", "7교시"),
    ],
}

# 학급별로 시간표를 다르게 두고 싶을 때 (선택):
# SCHEDULE_BY_NODE = {
#     "1-1": {"weekdays": [0,1,2,3,4], "periods": [...]},
#     "2-3": {...},
# }
SCHEDULE_BY_NODE = {}


# ---------- 에너지 낭비 감지 임계값 ----------
# 비수업 시간에 다음 조건이면 '낭비 의심' 표시:
#   - 조명: light(상대 밝기) >= LIGHT_ON_THRESHOLD
#   - 에어컨: 온도 <= AIRCON_TEMP_THRESHOLD (여름 냉방 의심)
#   - 난방: 온도 >= HEATER_TEMP_THRESHOLD (겨울 난방 의심)
# 학교·계절별로 조정 가능. 분석팀이 실측 데이터로 보정.
LIGHT_ON_THRESHOLD = 40        # %
AIRCON_TEMP_THRESHOLD = 24     # °C 미만 (여름 적용)
HEATER_TEMP_THRESHOLD = 23     # °C 초과 (겨울 적용)

# 계절 자동 판단: 5~9월=여름(에어컨), 11~3월=겨울(난방), 4·10월=둘 다 확인
SUMMER_MONTHS = {5, 6, 7, 8, 9}
WINTER_MONTHS = {11, 12, 1, 2, 3}


# ---------- API ----------
def get_schedule(node_id=None):
    """노드 ID에 맞는 시간표를 반환. 학급별 시간표가 없으면 DEFAULT."""
    if node_id and node_id in SCHEDULE_BY_NODE:
        return SCHEDULE_BY_NODE[node_id]
    return SCHEDULE_DEFAULT


def current_period(dt, schedule=None):
    """dt(datetime KST)가 어느 교시인지 반환.
    수업 중이면 라벨 ('3교시'), 아니면 None."""
    if schedule is None:
        schedule = SCHEDULE_DEFAULT
    if dt.weekday() not in schedule["weekdays"]:
        return None
    hm = dt.strftime("%H:%M")
    for start, end, label in schedule["periods"]:
        if start <= hm < end:
            return label
    return None


def is_class_time(dt, schedule=None):
    """수업 시간인가?"""
    return current_period(dt, schedule) is not None


def detect_waste(latest, current_dt, node_id=None):
    """비수업 시간 에너지 낭비 의심 감지.
    Returns: list of (icon, label) 튜플.
    예: [("💡", "조명 ON"), ("❄️", "에어컨 ON")]"""
    schedule = get_schedule(node_id)
    if is_class_time(current_dt, schedule):
        return []          # 수업 중이라 정상
    # 주말은 너무 시끄러우니 알림 약화
    is_weekend = current_dt.weekday() not in schedule["weekdays"]

    out = []
    light = latest.get("light")
    if light is not None and light >= LIGHT_ON_THRESHOLD:
        out.append(("💡", "조명 ON" if not is_weekend else "조명(주말)"))

    temp = latest.get("temperature")
    month = current_dt.month
    if temp is not None:
        if month in SUMMER_MONTHS and temp <= AIRCON_TEMP_THRESHOLD:
            out.append(("❄️", "에어컨 ON" if not is_weekend else "에어컨(주말)"))
        elif month in WINTER_MONTHS and temp >= HEATER_TEMP_THRESHOLD:
            out.append(("🔥", "난방 ON" if not is_weekend else "난방(주말)"))

    return out


def schedule_as_table(schedule=None):
    """시간표를 표로 그릴 수 있는 형태로 반환 (사이드바 표시용)."""
    if schedule is None:
        schedule = SCHEDULE_DEFAULT
    rows = []
    for start, end, label in schedule["periods"]:
        rows.append({"교시": label, "시간": f"{start} ~ {end}"})
    return rows
