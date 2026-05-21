import sqlite3
from datetime import datetime

DB_PATH = "public_monitor.db"

def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = connect()
    cur = conn.cursor()

    cur.execute('''
    CREATE TABLE IF NOT EXISTS channels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        link TEXT NOT NULL UNIQUE,
        username TEXT NOT NULL,
        title TEXT,
        is_active INTEGER DEFAULT 1,
        created_at TEXT NOT NULL
    )
    ''')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS keywords (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        keyword TEXT NOT NULL UNIQUE,
        category TEXT,
        created_at TEXT NOT NULL
    )
    ''')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        channel_link TEXT NOT NULL,
        channel_username TEXT NOT NULL,
        message_id TEXT NOT NULL,
        message_url TEXT,
        message_text TEXT NOT NULL,
        matched_keyword TEXT NOT NULL,
        repetition_count INTEGER NOT NULL,
        message_time TEXT,
        created_at TEXT NOT NULL,
        UNIQUE(channel_username, message_id, matched_keyword)
    )
    ''')

    conn.commit()
    conn.close()

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def add_channel(link, username, title=None):
    conn = connect()
    conn.execute(
        "INSERT OR IGNORE INTO channels(link, username, title, created_at) VALUES (?, ?, ?, ?)",
        (link, username, title or username, now())
    )
    conn.commit()
    conn.close()

def add_keyword(keyword, category=None):
    conn = connect()
    conn.execute(
        "INSERT OR IGNORE INTO keywords(keyword, category, created_at) VALUES (?, ?, ?)",
        (keyword.lower().strip(), category, now())
    )
    conn.commit()
    conn.close()

def get_channels():
    conn = connect()
    rows = conn.execute("SELECT * FROM channels ORDER BY id DESC").fetchall()
    conn.close()
    return rows

def get_keywords():
    conn = connect()
    rows = conn.execute("SELECT * FROM keywords ORDER BY id DESC").fetchall()
    conn.close()
    return rows

def save_result(channel_link, username, message_id, message_url, text, keyword, count, message_time):
    conn = connect()
    conn.execute('''
    INSERT OR IGNORE INTO results
    (channel_link, channel_username, message_id, message_url, message_text, matched_keyword, repetition_count, message_time, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (channel_link, username, message_id, message_url, text, keyword, count, message_time, now()))
    conn.commit()
    conn.close()

def get_results(q=None, keyword=None):
    conn = connect()
    sql = "SELECT * FROM results WHERE 1=1"
    params = []

    if q:
        sql += " AND message_text LIKE ?"
        params.append(f"%{q}%")

    if keyword:
        sql += " AND matched_keyword = ?"
        params.append(keyword)

    sql += " ORDER BY id DESC LIMIT 500"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return rows

def stats():
    conn = connect()
    total_results = conn.execute("SELECT COUNT(*) FROM results").fetchone()[0]
    total_channels = conn.execute("SELECT COUNT(*) FROM channels").fetchone()[0]
    total_keywords = conn.execute("SELECT COUNT(*) FROM keywords").fetchone()[0]
    conn.close()
    return {
        "total_results": total_results,
        "total_channels": total_channels,
        "total_keywords": total_keywords
    }
