import os
import sqlite3

from app_config import DB_PATH


def get_connection():
    return sqlite3.connect(DB_PATH)


def ensure_database():
    os.makedirs("data", exist_ok=True)

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS books (
            epc TEXT PRIMARY KEY,
            title TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS book_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            epc TEXT NOT NULL,
            rssi INTEGER,
            ant INTEGER,
            detected_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS book_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            epc TEXT NOT NULL,
            title TEXT,
            event_type TEXT NOT NULL,
            event_at TEXT NOT NULL,
            duration_sec INTEGER
        )
    """)

    conn.commit()
    conn.close()
