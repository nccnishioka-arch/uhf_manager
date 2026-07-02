import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path("data/uhf_manager.db")


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db():
    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS books (
                epc TEXT PRIMARY KEY,
                title TEXT,
                author TEXT,
                category TEXT,
                shelf_no TEXT
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS book_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                detected_at TEXT NOT NULL,
                epc TEXT NOT NULL,
                rssi INTEGER,
                ant INTEGER
            )
        """)

        conn.commit()


def save_event(epc, rssi=None, ant=None):
    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO book_events (
                detected_at,
                epc,
                rssi,
                ant
            ) VALUES (?, ?, ?, ?)
        """, (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            epc,
            rssi,
            ant,
        ))

        conn.commit()


def get_event_count():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM book_events")
        return cur.fetchone()[0]


def get_ranking(limit=20):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                epc,
                COUNT(*) AS cnt,
                AVG(rssi) AS avg_rssi,
                MAX(detected_at) AS last_detected_at
            FROM book_events
            GROUP BY epc
            ORDER BY cnt DESC
            LIMIT ?
        """, (limit,))
        return cur.fetchall()
