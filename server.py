import os
import sys
import uuid
import time
from typing import Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Local imports
import config
import database
from main import execute_pipeline
from src import storage_sync

load_dotenv()

app = FastAPI(title="ProjectCast API — Project Controlling & Decision Intelligence", version="2.0.0")

# Serve static output assets and web app UI
os.makedirs("outputs", exist_ok=True)
os.makedirs("web", exist_ok=True)

app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")
app.mount("/static", StaticFiles(directory="web"), name="static")

class ResearchRequest(BaseModel):
    topic: str
    analysis_type: Optional[str] = "Comprehensive Multi-Dimensional Analysis"
    analysis_focus: Optional[str] = None
    provider: Optional[str] = "ollama" # ollama, openai, anthropic, openrouter, gemini, huggingface
    openai_key: Optional[str] = None
    anthropic_key: Optional[str] = None
    openrouter_key: Optional[str] = None
    gemini_key: Optional[str] = None
    hf_key: Optional[str] = None
    ollama_url: Optional[str] = None
    format_code: Optional[str] = "html"

class ConfigUpdateRequest(BaseModel):
    openai_key: Optional[str] = None
    anthropic_key: Optional[str] = None
    openrouter_key: Optional[str] = None
    gemini_key: Optional[str] = None
    hf_key: Optional[str] = None
    ollama_url: Optional[str] = None

import asyncio

@app.get("/")
def read_root():
    if os.path.exists("web/index.html"):
        return FileResponse("web/index.html")
    return FileResponse("index.html")

@app.get("/api/config")
def get_system_config():
    return {
        "providers": {
            "openai": {"active": bool(config.OPENAI_API_KEY), "model": config.OPENAI_MODEL},
            "anthropic": {"active": bool(config.ANTHROPIC_KEY), "model": config.ANTHROPIC_MODEL},
            "openrouter": {"active": bool(config.OPENROUTER_API_KEY), "model": config.OPENROUTER_MODEL},
            "ollama": {"active": True, "url": config.OLLAMA_URL, "model": config.OLLAMA_MODEL},
            "gemini": {"active": bool(config.GEMINI_API_KEY), "model": config.GEMINI_MODEL},
            "huggingface": {"active": bool(config.HF_API_KEY), "model": config.HF_MODEL}
        },
        "watch_directory": config.WATCH_DIRECTORY
    }

@app.post("/api/config")
def update_system_config(req: ConfigUpdateRequest):
    env_path = ".env"
    env_vars = {}
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    k, v = line.strip().split("=", 1)
                    env_vars[k] = v
                    
    if req.openai_key is not None:
        env_vars["OPENAI_API_KEY"] = req.openai_key
        config.OPENAI_API_KEY = req.openai_key
        os.environ["OPENAI_API_KEY"] = req.openai_key

    if req.anthropic_key is not None:
        env_vars["ANTHROPIC_API_KEY"] = req.anthropic_key
        config.ANTHROPIC_KEY = req.anthropic_key
        os.environ["ANTHROPIC_API_KEY"] = req.anthropic_key
        os.environ["ANTHROPIC_KEY"] = req.anthropic_key

    if req.openrouter_key is not None:
        env_vars["OPENROUTER_API_KEY"] = req.openrouter_key
        config.OPENROUTER_API_KEY = req.openrouter_key
        os.environ["OPENROUTER_API_KEY"] = req.openrouter_key

    if req.gemini_key is not None:
        env_vars["GEMINI_API_KEY"] = req.gemini_key
        config.GEMINI_API_KEY = req.gemini_key
        os.environ["GEMINI_API_KEY"] = req.gemini_key

    if req.hf_key is not None:
        env_vars["HF_API_KEY"] = req.hf_key
        config.HF_API_KEY = req.hf_key
        os.environ["HF_API_KEY"] = req.hf_key

    if req.ollama_url is not None:
        env_vars["OLLAMA_URL"] = req.ollama_url
        config.OLLAMA_URL = req.ollama_url
        os.environ["OLLAMA_URL"] = req.ollama_url

    with open(env_path, "w", encoding="utf-8") as f:
        for k, v in env_vars.items():
            f.write(f"{k}={v}\n")

    return {"status": "SUCCESS", "message": "API Keys and Configuration updated successfully"}

@app.post("/api/research")
async def run_research_api(req: ResearchRequest):
    # Update temporary keys if supplied in request
    if req.openai_key:
        config.OPENAI_API_KEY = req.openai_key
        os.environ["OPENAI_API_KEY"] = req.openai_key
    if req.anthropic_key:
        config.ANTHROPIC_KEY = req.anthropic_key
        os.environ["ANTHROPIC_API_KEY"] = req.anthropic_key
        os.environ["ANTHROPIC_KEY"] = req.anthropic_key
    if req.openrouter_key:
        config.OPENROUTER_API_KEY = req.openrouter_key
        os.environ["OPENROUTER_API_KEY"] = req.openrouter_key
    if req.gemini_key:
        config.GEMINI_API_KEY = req.gemini_key
        os.environ["GEMINI_API_KEY"] = req.gemini_key
    if req.hf_key:
        config.HF_API_KEY = req.hf_key
        os.environ["HF_API_KEY"] = req.hf_key
    if req.ollama_url:
        config.OLLAMA_URL = req.ollama_url
        os.environ["OLLAMA_URL"] = req.ollama_url

    if not req.topic.strip():
        raise HTTPException(status_code=400, detail="Topic cannot be empty")

    analysis_focus = req.analysis_focus
    if not analysis_focus:
        analysis_focus = f"{req.analysis_type}: Integrated analysis combining Financial, Risk, SWOT, and Operational perspectives"

    payload = {
        "run_id": str(uuid.uuid4()),
        "topic": req.topic,
        "analysis_type": req.analysis_type,
        "analysis_focus": analysis_focus,
        "provider": req.provider,
        "format_code": req.format_code or "all"
    }

    try:
        result = await asyncio.to_thread(execute_pipeline, payload)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reports")
def get_reports_history():
    database.init_db()
    import sqlite3
    conn = sqlite3.connect(database.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, timestamp, topic, analysis_focus, report_format, report_path FROM researches ORDER BY id DESC LIMIT 50")
    rows = cursor.fetchall()
    conn.close()

    reports = []
    for r in rows:
        paths = [p.strip() for p in (r[5] or "").split(",") if p.strip()]
        reports.append({
            "id": r[0],
            "timestamp": r[1],
            "topic": r[2],
            "analysis_focus": r[3],
            "format": r[4],
            "paths": paths
        })
    return {"reports": reports}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
