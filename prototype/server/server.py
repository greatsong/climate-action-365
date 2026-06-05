"""
교실 환경 모니터링 수집 서버 (FastAPI + SQLite).

엔드포인트:
- POST /reading  : Pico가 측정값을 전송
- GET  /readings : 대시보드가 측정값 조회 (node_id·기간 필터)
- GET  /nodes    : 등록된 노드 목록 + 최근 측정 시각

DB 스키마는 Phase 2(CO2) / Phase 3(미세먼지) 확장 시 컬럼만 추가하면 됨.
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

DB_PATH = "data.db"

app = FastAPI(title="Climate Action 365 — Collector")


# ---------- DB ----------

SCHEMA = """
CREATE TABLE IF NOT EXISTS readings (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id     TEXT    NOT NULL,
    ts          INTEGER NOT NULL,        -- Pico 내부 시간 (참고용)
    received_at TEXT    NOT NULL,        -- 서버 수신 시각 (ISO8601 UTC)
    temperature REAL,                    -- °C
    humidity    REAL,                    -- %RH
    light       REAL,                    -- Grove Light Sensor 상대 밝기 (0~100%)
    lux         REAL,                    -- (예약) 향후 BH1750 등 lux 절대값 도입 시 사용
    -- Phase 2/3 확장 예약 컬럼
    co2_ppm     REAL,
    pm25        REAL,
    pm10        REAL
);

CREATE INDEX IF NOT EXISTS idx_readings_node_time
    ON readings(node_id, received_at DESC);
"""


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


@app.on_event("startup")
def init_db():
    with get_db() as conn:
        conn.executescript(SCHEMA)


# ---------- Models ----------

class Reading(BaseModel):
    node_id: str
    ts: Optional[int] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    light: Optional[float] = None        # 0~100% 상대 밝기 (현재 Phase 1)
    lux: Optional[float] = None          # 예약 (향후 BH1750 lux 절대값)
    # Phase 2/3 예약
    co2_ppm: Optional[float] = None
    pm25: Optional[float] = None
    pm10: Optional[float] = None


# ---------- Endpoints ----------

@app.post("/reading")
def post_reading(r: Reading):
    received = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        conn.execute(
            """INSERT INTO readings
               (node_id, ts, received_at, temperature, humidity, light, lux,
                co2_ppm, pm25, pm10)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (r.node_id, r.ts or 0, received,
             r.temperature, r.humidity, r.light, r.lux,
             r.co2_ppm, r.pm25, r.pm10),
        )
    return {"ok": True, "received_at": received}


@app.get("/readings")
def get_readings(
    node_id: Optional[str] = None,
    limit: int = Query(default=500, le=100000),
    since_minutes: Optional[int] = Query(default=None),
):
    sql = "SELECT * FROM readings"
    where = []
    params = []
    if node_id:
        where.append("node_id = ?")
        params.append(node_id)
    if since_minutes:
        cutoff = datetime.now(timezone.utc).timestamp() - since_minutes * 60
        cutoff_iso = datetime.fromtimestamp(cutoff, tz=timezone.utc).isoformat()
        where.append("received_at >= ?")
        params.append(cutoff_iso)
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY received_at DESC LIMIT ?"
    params.append(limit)

    with get_db() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(row) for row in rows]


@app.get("/nodes")
def get_nodes():
    """등록된 노드 목록 + 최근 수신 시각 + 최신 측정값."""
    sql = """
    SELECT node_id,
           MAX(received_at) AS last_seen,
           COUNT(*)         AS reading_count
    FROM readings
    GROUP BY node_id
    ORDER BY node_id
    """
    with get_db() as conn:
        rows = conn.execute(sql).fetchall()
        result = []
        for row in rows:
            latest = conn.execute(
                "SELECT * FROM readings WHERE node_id=? ORDER BY received_at DESC LIMIT 1",
                (row["node_id"],),
            ).fetchone()
            result.append({
                "node_id": row["node_id"],
                "last_seen": row["last_seen"],
                "reading_count": row["reading_count"],
                "latest": dict(latest) if latest else None,
            })
    return result


@app.get("/health")
def health():
    return {"ok": True}
