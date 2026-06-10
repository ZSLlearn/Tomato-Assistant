import sqlite3
import config


def get_db():
    conn = sqlite3.connect(config.DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn=None):
    own_conn = conn is None
    if own_conn:
        conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS system_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS finance_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('income','expense')),
            icon TEXT DEFAULT '',
            is_deleted INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS finance_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('income','expense')),
            amount REAL NOT NULL CHECK(amount > 0),
            date TEXT NOT NULL,
            note TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            is_deleted INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS health_weight (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            weight REAL NOT NULL CHECK(weight > 0),
            date TEXT NOT NULL,
            note TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS health_exercise (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            duration INTEGER NOT NULL CHECK(duration > 0),
            calories REAL DEFAULT 0 CHECK(calories >= 0),
            date TEXT NOT NULL,
            note TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS health_water (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount INTEGER NOT NULL CHECK(amount > 0),
            date TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS health_sleep (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            quality INTEGER DEFAULT 3 CHECK(quality BETWEEN 1 AND 5),
            date TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS schedule_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            start_time TEXT NOT NULL,
            end_time TEXT DEFAULT '',
            category TEXT DEFAULT '个人' CHECK(category IN ('工作','个人','紧急')),
            priority INTEGER DEFAULT 2 CHECK(priority BETWEEN 1 AND 3),
            is_completed INTEGER DEFAULT 0,
            is_deleted INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS memo_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT DEFAULT '',
            category TEXT DEFAULT '',
            tags TEXT DEFAULT '',
            is_pinned INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS ai_conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT DEFAULT '新对话',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS ai_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('user','assistant','system')),
            content TEXT NOT NULL,
            tool_called TEXT,
            tool_result TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (conversation_id) REFERENCES ai_conversations(id)
        );
    """)
    conn.commit()
    if own_conn:
        conn.close()
