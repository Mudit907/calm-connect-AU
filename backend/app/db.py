"""
SQLite storage layer for CalmConnect.

Replaces the flat-CSV interaction log from v1/v2 with a real queryable
store, specifically because the trend view needs "all rows for this
session_id, ordered by time" — a query a CSV can technically answer but
shouldn't have to. This is the natural point where a database earns its
place: not because CSV was wrong before, but because a new requirement
(per-session history) makes it the wrong tool now.

No accounts, no auth, no personally identifying information. A session_id
is a random client-generated token with no link to a real identity. If a
person clears their browser storage, their history is gone — that's a
deliberate, stated privacy property, not a bug (see backend/README.md).
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "calmconnect.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    timestamp_utc TEXT NOT NULL,
    age INTEGER NOT NULL,
    text TEXT NOT NULL,
    category TEXT NOT NULL,
    category_confidence REAL NOT NULL,
    escalation_flag INTEGER NOT NULL,
    escalation_probability REAL NOT NULL,
    season TEXT NOT NULL,
    top_recommendation TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_session_id ON interactions(session_id);
CREATE INDEX IF NOT EXISTS idx_timestamp ON interactions(timestamp_utc);
"""


@contextmanager
def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_connection() as conn:
        conn.executescript(SCHEMA)


def log_interaction(session_id: str, age: int, text: str, result) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO interactions
                (session_id, timestamp_utc, age, text, category,
                 category_confidence, escalation_flag, escalation_probability,
                 season, top_recommendation)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                datetime.now(timezone.utc).isoformat(),
                age,
                text,
                result.category,
                result.category_confidence,
                int(result.escalation_flag),
                result.escalation_probability,
                result.season,
                result.ranked[0]["id"],
            ),
        )


def get_session_history(session_id: str, limit: int = 90) -> list[dict]:
    """Returns up to `limit` most recent interactions for a session,
    oldest first (chronological order, suited to plotting a trend line)."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT timestamp_utc, category, category_confidence,
                   escalation_flag, escalation_probability, season, top_recommendation
            FROM interactions
            WHERE session_id = ?
            ORDER BY timestamp_utc DESC
            LIMIT ?
            """,
            (session_id, limit),
        ).fetchall()
    return [dict(r) for r in reversed(rows)]
