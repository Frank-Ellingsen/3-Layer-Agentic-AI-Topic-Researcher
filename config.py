import os
import yaml
from dotenv import load_dotenv

# Load any .env file in the workspace
load_dotenv()

CONFIG_YAML_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml")

def load_yaml_config():
    """Loads settings from config.yaml if present."""
    if os.path.exists(CONFIG_YAML_PATH):
        try:
            with open(CONFIG_YAML_PATH, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            pass
    return {}

YAML_CONFIG = load_yaml_config()

# Provider Keys & Models
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", YAML_CONFIG.get("models", {}).get("openai", {}).get("model_name", "gpt-4o-mini"))

ANTHROPIC_KEY = os.getenv("ANTHROPIC_KEY") or os.getenv("ANTHROPIC_API_KEY") or ""
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", YAML_CONFIG.get("models", {}).get("anthropic", {}).get("model_name", "claude-3-5-sonnet-20241022"))

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", YAML_CONFIG.get("models", {}).get("openrouter", {}).get("model_name", "openrouter/auto"))

HF_API_KEY = os.getenv("HF_API_KEY") or os.getenv("HF_TOKEN") or ""
HF_MODEL = os.getenv("HF_MODEL", YAML_CONFIG.get("models", {}).get("huggingface", {}).get("model_name", "meta-llama/Llama-3.2-3B-Instruct"))

OLLAMA_URL = os.getenv("OLLAMA_URL", YAML_CONFIG.get("models", {}).get("ollama", {}).get("base_url", "http://localhost:11434/v1"))
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", YAML_CONFIG.get("models", {}).get("ollama", {}).get("model_name", "llama3.1:latest"))
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", YAML_CONFIG.get("models", {}).get("ollama", {}).get("timeout", 300)))
OLLAMA_MAX_TOKENS = int(os.getenv("OLLAMA_MAX_TOKENS", YAML_CONFIG.get("models", {}).get("ollama", {}).get("max_tokens", 2048)))

LM_STUDIO_URL = YAML_CONFIG.get("models", {}).get("lm_studio", {}).get("base_url", "http://localhost:1234/v1")
LOCAL_LLM_URL = os.getenv("LOCAL_LLM_URL", OLLAMA_URL)
LOCAL_LLM_MODEL = os.getenv("LOCAL_LLM_MODEL", OLLAMA_MODEL)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""
GEMINI_MODEL = os.getenv("GEMINI_MODEL", YAML_CONFIG.get("models", {}).get("gemini", {}).get("model_name", "gemini-3.5-flash"))

# Watchdog & Storage Paths
WATCH_DIRECTORY = YAML_CONFIG.get("scheduler", {}).get("watch_directory", "./input_folder_z/raw_docs")
DB_PATH = YAML_CONFIG.get("destinations", {}).get("database", {}).get("path", "./database/workflow_logs.db")
LEGACY_DB_PATH = YAML_CONFIG.get("destinations", {}).get("database", {}).get("legacy_path", "./research_history.db")
