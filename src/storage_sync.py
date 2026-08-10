import os
import sqlite3
import requests
from datetime import datetime
import config

def init_telemetry_db():
    """Initializes SQLite database with schema specified in build spec."""
    db_path = config.DB_PATH
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS execution_logs (
        run_id TEXT PRIMARY KEY,
        timestamp TEXT NOT NULL,
        topic TEXT NOT NULL,
        analysis_type TEXT,
        status TEXT NOT NULL,
        runtime_ms INTEGER,
        source_count INTEGER,
        insights_extracted TEXT,
        report_paths TEXT,
        error_message TEXT
    );
    """)
    conn.commit()
    conn.close()

def log_telemetry(run_id: str, topic: str, analysis_type: str, status: str, runtime_ms: int = 0, source_count: int = 1, insights_extracted: str = "", report_paths: str = "", error_message: str = ""):
    """Logs execution telemetry into SQLite telemetry database."""
    init_telemetry_db()
    conn = sqlite3.connect(config.DB_PATH)
    cursor = conn.cursor()
    timestamp = datetime.now().isoformat()
    cursor.execute("""
    INSERT OR REPLACE INTO execution_logs (run_id, timestamp, topic, analysis_type, status, runtime_ms, source_count, insights_extracted, report_paths, error_message)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (run_id, timestamp, topic, analysis_type, status, runtime_ms, source_count, insights_extracted, report_paths, error_message))
    conn.commit()
    conn.close()

def sync_to_notion(payload: dict, report_path: str = "") -> bool:
    """Notion Database API connector stub."""
    token = os.getenv("NOTION_INTEGRATION_TOKEN", "")
    database_id = config.YAML_CONFIG.get("destinations", {}).get("notion", {}).get("database_id", "")
    if not token or not database_id:
        return False
    try:
        url = "https://api.notion.com/v1/pages"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        body = {
            "parent": {"database_id": database_id},
            "properties": {
                "Title": {"title": [{"text": {"content": payload.get("topic", "Research Report")}}]},
                "Date": {"date": {"start": datetime.now().isoformat()}},
                "Report Path": {"rich_text": [{"text": {"content": report_path}}]}
            }
        }
        resp = requests.post(url, headers=headers, json=body, timeout=5)
        return resp.status_code == 200
    except Exception as e:
        print(f"[StorageSync] Notion sync error: {e}")
        return False

def backup_to_drive(file_path: str) -> bool:
    """Google Drive upload API connector stub."""
    credentials_json = os.getenv("GOOGLE_DRIVE_CREDENTIALS_JSON", "")
    if not credentials_json or not os.path.exists(file_path):
        return False
    # API upload implementation stub
    return True
