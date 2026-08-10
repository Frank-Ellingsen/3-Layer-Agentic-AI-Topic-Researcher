import os
import sqlite3
from datetime import datetime
import config

DB_PATH = config.LEGACY_DB_PATH

def init_db():
    """Initializes the SQLite database tables for research history."""
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS researches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        topic TEXT NOT NULL,
        analysis_focus TEXT NOT NULL,
        report_format TEXT NOT NULL,
        raw_research TEXT,
        analysis TEXT,
        report_content TEXT,
        report_path TEXT
    )
    """)
    
    conn.commit()
    conn.close()

def save_research(topic: str, analysis_focus: str, report_format: str, raw_research: str = None, analysis: str = None, report_content: str = None, report_path: str = None) -> int:
    """Saves a new research record or updates it."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    timestamp = datetime.now().isoformat()
    
    cursor.execute("""
    INSERT INTO researches (timestamp, topic, analysis_focus, report_format, raw_research, analysis, report_content, report_path)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (timestamp, topic, analysis_focus, report_format, raw_research, analysis, report_content, report_path))
    
    row_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return row_id

def update_research(row_id: int, raw_research: str = None, analysis: str = None, report_content: str = None, report_path: str = None):
    """Updates an existing research record with raw research, analysis, and report contents."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    updates = []
    params = []
    if raw_research is not None:
        updates.append("raw_research = ?")
        params.append(raw_research)
    if analysis is not None:
        updates.append("analysis = ?")
        params.append(analysis)
    if report_content is not None:
        updates.append("report_content = ?")
        params.append(report_content)
    if report_path is not None:
        updates.append("report_path = ?")
        params.append(report_path)
        
    if updates:
        params.append(row_id)
        query = f"UPDATE researches SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, tuple(params))
        conn.commit()
    
    conn.close()
