import os
import re
import requests
import duckdb
import config

class DuckDBRAGEngine:
    """Local-first DuckDB analytical RAG index for semantically chunking and retrieving grounded research passages."""
    
    def __init__(self):
        self.conn = duckdb.connect(':memory:')
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS rag_passages (
                id INTEGER PRIMARY KEY,
                title VARCHAR,
                url VARCHAR,
                passage VARCHAR
            )
        """)
        self.counter = 0

    def index_document(self, document_data: dict):
        raw_text = document_data.get("raw_text", "")
        sources = document_data.get("sources", [])
        default_title = document_data.get("title", "Ingested Research Document")
        default_url = sources[0].get("url", "#") if sources and isinstance(sources[0], dict) else "#"

        # Semantic passage chunking by paragraphs or bullet blocks
        raw_chunks = [c.strip() for c in re.split(r'\n{2,}|\n(?=[#-]\s)', raw_text) if len(c.strip()) > 30]
        
        for chunk in raw_chunks:
            self.counter += 1
            self.conn.execute(
                "INSERT INTO rag_passages VALUES (?, ?, ?, ?)",
                (self.counter, default_title, default_url, chunk)
            )

    def search_passages(self, topic: str, limit: int = 5) -> str:
        if self.counter == 0:
            return ""

        # Key analytical domain terms for project controlling
        query_terms = [topic, "Capex", "Opex", "cost", "schedule", "EVM", "CPI", "SPI", "EAC", "ETC", "risk", "mitigation", "wind", "MW", "GW", "NOK", "EUR"]
        
        like_conditions = []
        params = []
        for term in query_terms:
            like_conditions.append("LOWER(passage) LIKE ?")
            params.append(f"%{term.lower()}%")
        
        sql = f"""
            SELECT title, url, passage 
            FROM rag_passages 
            WHERE {' OR '.join(like_conditions)} 
            LIMIT ?
        """
        params.append(limit)
        
        try:
            rows = self.conn.execute(sql, params).fetchall()
            if not rows:
                rows = self.conn.execute("SELECT title, url, passage FROM rag_passages LIMIT ?", (limit,)).fetchall()
                
            formatted_passages = []
            for r in rows:
                formatted_passages.append(f"- **Passage from [{r[0]}]({r[1]})**:\n  \"{r[2]}\"")
                
            return "\n\n### Grounded RAG Passages (Local DuckDB Analytical Engine)\n" + "\n\n".join(formatted_passages)
        except Exception as e:
            print(f"[DuckDB RAG] Query error: {e}")
            return ""

# Module-level RAG engine singleton
_RAG_ENGINE = DuckDBRAGEngine()

class NotebookLMSync:
    def __init__(self, project_id: str = None, api_endpoint: str = None):
        self.project_id = project_id or config.YAML_CONFIG.get("models", {}).get("notebook_lm", {}).get("project_id", "agentic-research-base")
        self.api_endpoint = api_endpoint or config.YAML_CONFIG.get("models", {}).get("notebook_lm", {}).get("api_endpoint", "https://api.notebooklm.google/v1")
        self.developer_key = os.getenv("NOTEBOOKLM_DEVELOPER_KEY", "")

    def upload_document(self, document_data: dict) -> bool:
        """Syncs document payload into NotebookLM workspace & local DuckDB RAG corpus."""
        _RAG_ENGINE.index_document(document_data)
        
        if self.developer_key:
            try:
                headers = {"Authorization": f"Bearer {self.developer_key}", "Content-Type": "application/json"}
                resp = requests.post(f"{self.api_endpoint}/projects/{self.project_id}/documents", headers=headers, json=document_data, timeout=5)
                return resp.status_code in [200, 201]
            except Exception as e:
                print(f"[NotebookLM] Upload error: {e}")
        return True

    def query_notebook(self, topic: str) -> str:
        """Queries NotebookLM or local DuckDB RAG engine for grounded passage retrieval."""
        if self.developer_key:
            try:
                headers = {"Authorization": f"Bearer {self.developer_key}", "Content-Type": "application/json"}
                payload = {"query": f"Summarize key insights, cost parameters, and risks for: {topic}"}
                resp = requests.post(f"{self.api_endpoint}/projects/{self.project_id}/query", headers=headers, json=payload, timeout=5)
                if resp.status_code == 200:
                    return resp.json().get("answer", "")
            except Exception as e:
                print(f"[NotebookLM] Grounded query error: {e}")

        # Local DuckDB RAG passage retrieval
        return _RAG_ENGINE.search_passages(topic)

def sync_to_notebook(data: dict) -> bool:
    sync_obj = NotebookLMSync()
    return sync_obj.upload_document(data)

def query_grounded_context(topic: str) -> str:
    sync_obj = NotebookLMSync()
    return sync_obj.query_notebook(topic)
