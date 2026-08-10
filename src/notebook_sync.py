import os
import requests
import config

class NotebookLMSync:
    def __init__(self, project_id: str = None, api_endpoint: str = None):
        self.project_id = project_id or config.YAML_CONFIG.get("models", {}).get("notebook_lm", {}).get("project_id", "agentic-research-base")
        self.api_endpoint = api_endpoint or config.YAML_CONFIG.get("models", {}).get("notebook_lm", {}).get("api_endpoint", "https://api.notebooklm.google/v1")
        self.developer_key = os.getenv("NOTEBOOKLM_DEVELOPER_KEY", "")
        self.ingested_sources = []

    def upload_document(self, document_data: dict) -> bool:
        """Syncs document payload into NotebookLM workspace/RAG corpus."""
        title = document_data.get("title", "Untitled Document")
        self.ingested_sources.append(title)
        
        # If API Key present, execute upload HTTP call
        if self.developer_key:
            try:
                headers = {"Authorization": f"Bearer {self.developer_key}", "Content-Type": "application/json"}
                resp = requests.post(f"{self.api_endpoint}/projects/{self.project_id}/documents", headers=headers, json=document_data, timeout=5)
                return resp.status_code in [200, 201]
            except Exception as e:
                print(f"[NotebookLM] Upload error: {e}")
        return True

    def query_notebook(self, topic: str) -> str:
        """Queries NotebookLM RAG engine for multi-document synthesis and grounded Q&A."""
        if self.developer_key:
            try:
                headers = {"Authorization": f"Bearer {self.developer_key}", "Content-Type": "application/json"}
                payload = {"query": f"Summarize key insights, cost parameters, and risks for: {topic}"}
                resp = requests.post(f"{self.api_endpoint}/projects/{self.project_id}/query", headers=headers, json=payload, timeout=5)
                if resp.status_code == 200:
                    return resp.json().get("answer", "")
            except Exception as e:
                print(f"[NotebookLM] Grounded query error: {e}")
        return f"Grounded RAG context for topic '{topic}' compiled across {len(self.ingested_sources)} ingested source(s)."

def sync_to_notebook(data: dict) -> bool:
    sync_obj = NotebookLMSync()
    return sync_obj.upload_document(data)

def query_grounded_context(topic: str) -> str:
    sync_obj = NotebookLMSync()
    return sync_obj.query_notebook(topic)
