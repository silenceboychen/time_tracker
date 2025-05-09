import sqlite3
import os
from datetime import datetime

# Determine the absolute path for the data directory relative to this file
# core/data_store.py -> project_root/data/
PROJECT_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(PROJECT_ROOT_DIR, 'data')
DB_NAME = 'time_tracker.db'
DB_PATH = os.path.join(DB_DIR, DB_NAME)

def init_db():
    """Initializes the database and creates tables if they don't exist."""
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR)
        print(f"Created directory: {DB_DIR}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Table for activity logs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            app_name TEXT,
            window_title TEXT,
            duration_seconds INTEGER,
            activity_type TEXT  -- e.g., 'coding', 'browsing', 'idle'
        )
    ''')
    # Table for application categories (future use)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS app_categories (
            app_name TEXT PRIMARY KEY,
            category TEXT
        )
    ''')
    conn.commit()
    conn.close()
    print(f"Database initialized/checked at {DB_PATH}")

def log_activity(app_name, window_title, duration_seconds, activity_type="general"):
    """Logs an activity to the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO activity_log (app_name, window_title, duration_seconds, activity_type)
        VALUES (?, ?, ?, ?)
    ''', (app_name, window_title, duration_seconds, activity_type))
    conn.commit()
    conn.close()

def get_activity_summary(limit=10):
    """Retrieves a summary of recent activities."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT timestamp, app_name, window_title, duration_seconds, activity_type
        FROM activity_log
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows

if __name__ == '__main__': # For basic testing of this module
    print(f"DB path: {DB_PATH}")
    init_db()
    log_activity("TestApp", "Test Window - data_store", 60, "testing")
    summary = get_activity_summary(5)
    print("\nRecent test activities:")
    for row in summary:
        print(row) 