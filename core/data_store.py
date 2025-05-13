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

def get_activity_summary(limit=10, date=None):
    """
    检索活动摘要记录，支持按日期过滤。
    
    参数:
        limit (int): 返回记录的最大数量
        date (str, 可选): 按指定日期过滤数据，格式'YYYY-MM-DD'
    
    返回:
        list: 活动记录列表
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 构建SQL查询
    query = '''
        SELECT datetime(timestamp, '+8 hours') as timestamp,
               app_name, window_title, duration_seconds, activity_type
        FROM activity_log
    '''
    
    params = []
    
    # 如果指定了日期，添加日期筛选条件
    if date:
        # 日期在数据库中是UTC时间，但我们需要按北京时间(+8小时)过滤
        # 首先获取指定日期的开始时间和结束时间(北京时间)
        date_start = f"{date} 00:00:00"
        date_end = f"{date} 23:59:59"
        
        # 然后转换回UTC时间进行查询(-8小时)
        query += '''
            WHERE date(datetime(timestamp, '+8 hours')) = date(?)
        '''
        params.append(date)
    
    # 添加排序和限制
    query += '''
        ORDER BY timestamp DESC
        LIMIT ?
    '''
    params.append(limit)
    
    # 执行查询
    cursor.execute(query, params)
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