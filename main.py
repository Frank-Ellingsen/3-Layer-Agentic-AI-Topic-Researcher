import os
import sys
import time
import uuid
import time
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Modular src imports
import config
import database
from src import scraper, local_lm, notebook_sync, report_agent, storage_sync

class RawDocWatchdogHandler(FileSystemEventHandler):
    """Monitors input_folder_z/raw_docs for incoming documents."""
    def on_created(self, event):
        if event.is_directory:
            return
        file_path = event.src_path
        print(f"\n[Watchdog] New document detected: {file_path}")
        topic = os.path.splitext(os.path.basename(file_path))[0].replace("_", " ")
        payload = {
            "run_id": str(uuid.uuid4()),
            "topic": topic,
            "analysis_type": "Automated Watchdog Analysis",
            "analysis_focus": "Automated Document Ingestion & Strategic Evaluation",
            "file_path": file_path,
            "format_code": "all"
        }
        execute_pipeline(payload)

def execute_pipeline(payload: dict) -> dict:
    """Executes the end-to-end 3-Layer Agentic AI pipeline."""
    start_time = time.time()
    run_id = payload.get("run_id") or str(uuid.uuid4())
    topic = payload["topic"]
    analysis_type = payload.get("analysis_type", "Comprehensive Multi-Dimensional Analysis")
    analysis_focus = payload.get("analysis_focus", f"{analysis_type}: Integrated analysis combining Financial, Risk, SWOT, and Operational perspectives")
    format_code = payload.get("format_code", "all")
    provider = payload.get("provider")
    file_path = payload.get("file_path")

    print(f"\n=======================================================")
    print(f"Executing Agentic AI Pipeline [Run ID: {run_id}]")
    print(f"Topic: {topic} | Framework: {analysis_type} | Provider: {provider or 'Auto Failover'}")
    print(f"=======================================================")

    try:
        # Step 1: Ingestion & Research Phase
        print("[Step 1/5] Ingesting & Researching Sources...")
        if file_path and os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            abs_p = os.path.abspath(file_path).replace("\\", "/")
            doc_data = {
                "title": os.path.basename(file_path),
                "source": file_path,
                "raw_text": content,
                "sources": [{"title": os.path.basename(file_path), "url": f"file:///{abs_p}"}],
                "timestamp": datetime.now().isoformat()
            }
        else:
            doc_data = scraper.execute_web_research(topic, provider=provider)

        # Grounded RAG Sync
        notebook_sync.sync_to_notebook(doc_data)
        raw_research = doc_data["raw_text"]

        # Step 2: Deep Local Reasoning & Analysis
        print("[Step 2/5] Executing Deep Analytical Reasoning...")
        grounded_context = notebook_sync.query_grounded_context(topic)
        combined_research = f"{raw_research}\n\n{grounded_context}"
        
        raw_analysis = local_lm.perform_deep_reasoning(combined_research, analysis_focus, provider=provider)
        
        print("[Step 3/5] Executing Self-Correction Validation Loop...")
        validated_analysis = local_lm.run_validation_loop(raw_analysis, combined_research, provider=provider)

        # Step 3: Report Compilation
        print("[Step 4/5] Compiling Executive Tufte-Style Report...")
        report_markdown = report_agent.generate_markdown_report(
            validated_analysis, analysis_focus, topic, analysis_type, provider=provider, sources=doc_data.get("sources")
        )

        # DB Logging (Legacy DB & Telemetry DB)
        db_id = database.save_research(topic, analysis_focus, format_code, raw_research=combined_research, analysis=validated_analysis, report_content=report_markdown)

        # Step 4: Multi-Destination Archiving
        print("[Step 5/5] Archiving Outputs across Multi-Destination Storage...")
        output_files = report_agent.compile_outputs(report_markdown, topic, analysis_type, db_id, format_code=format_code)
        
        report_paths_str = ", ".join(output_files.values())
        database.update_research(db_id, report_path=report_paths_str)

        storage_sync.sync_to_notion(payload, report_path=report_paths_str)
        if "pdf" in output_files:
            storage_sync.backup_to_drive(output_files["pdf"])

        runtime_ms = int((time.time() - start_time) * 1000)
        storage_sync.log_telemetry(
            run_id=run_id,
            topic=topic,
            analysis_type=analysis_type,
            status="SUCCESS",
            runtime_ms=runtime_ms,
            source_count=1,
            insights_extracted=validated_analysis[:500],
            report_paths=report_paths_str
        )

        print("\n[Pipeline Complete] Successfully generated files:")
        for fmt, p in output_files.items():
            print(f"  - ({fmt.upper()}): {p}")

        return {
            "status": "SUCCESS",
            "run_id": run_id,
            "db_id": db_id,
            "output_files": output_files,
            "runtime_ms": runtime_ms
        }

    except Exception as e:
        runtime_ms = int((time.time() - start_time) * 1000)
        storage_sync.log_telemetry(
            run_id=run_id,
            topic=topic,
            analysis_type=analysis_type,
            status="FAILED",
            runtime_ms=runtime_ms,
            error_message=str(e)
        )
        print(f"[Pipeline Failed] Error: {e}")
        raise e

def start_watchdog(watch_dir: str = None):
    """Starts background filesystem watchdog monitoring watch_dir."""
    target_dir = watch_dir or config.WATCH_DIRECTORY
    raw_docs_dir = os.path.join(target_dir)
    os.makedirs(raw_docs_dir, exist_ok=True)

    event_handler = RawDocWatchdogHandler()
    observer = Observer()
    observer.schedule(event_handler, path=raw_docs_dir, recursive=False)
    observer.start()
    print(f"\n[Watchdog Started] Monitoring folder: {os.path.abspath(raw_docs_dir)}")
    print("Press Ctrl+C to stop.\n")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--watch":
        start_watchdog()
    elif len(sys.argv) > 1:
        topic_arg = " ".join(sys.argv[1:])
        execute_pipeline({"topic": topic_arg})
    else:
        print("Usage:")
        print("  python main.py --watch               (Starts Watchdog mode)")
        print("  python main.py \"<Topic to Research>\" (Executes single automated pipeline)")
