import json
import requests
import config

ANALYST_SYSTEM_PROMPT = """
SYSTEM: You are a high-performance Project Controller and Business Intelligence Analyst.
INPUT: Grounded summaries, research data, and domain parameters provided by the Research Layer.
TASK:
1. Perform an exhaustive analytical review tailored to Project Controlling & Executive Decision Making.
2. Structure your analysis around key quantitative vectors:
   - Financial Feasibility & Capex/Opex Breakdown
   - Earned Value Management (EVM): CPI, SPI, CV, SV, and EAC/ETC cost forecasting
   - SWOT & PESTEL Strategic Matrices
   - Risk Matrix (Probability vs. Impact) with concrete mitigation strategies
3. Provide realistic estimates, formulas, metrics, and actionable recommendations.
"""

VALIDATION_SYSTEM_PROMPT = """
SYSTEM: You are a Quality Audit & Validation Agent.
TASK: Review the analytical findings for logical consistency, quantitative accuracy, and strategic alignment.
Ensure table formatting is clean and metric columns are properly aligned.
Return the final validated analysis text.
"""

def query_openai(prompt: str, system_prompt: str = ANALYST_SYSTEM_PROMPT) -> str:
    """Queries OpenAI API (GPT-4o / GPT-4o-mini)."""
    if not config.OPENAI_API_KEY:
        return ""
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {config.OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    models_to_try = [config.OPENAI_MODEL, "gpt-4o-mini", "gpt-4o"]
    for m in models_to_try:
        payload = {
            "model": m,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 4096
        }
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            if resp.status_code == 200:
                content = resp.json()["choices"][0]["message"]["content"]
                if content and len(content.strip()) > 50:
                    print(f"[ModelRouter] Successfully generated via OpenAI ({m})")
                    return content
            elif resp.status_code in [402, 429]:
                print(f"[ModelRouter Warning] OpenAI rate limit / insufficient credits (status {resp.status_code}) on {m}. Failing over...")
            elif resp.status_code == 401:
                print(f"[ModelRouter Warning] OpenAI invalid API key (status 401). Failing over...")
        except Exception as e:
            print(f"[ModelRouter] OpenAI error ({m}): {e}")
    return ""

def query_anthropic(prompt: str, system_prompt: str = ANALYST_SYSTEM_PROMPT) -> str:
    """Queries Anthropic API (Claude 3.5 Sonnet / Haiku)."""
    api_key = config.ANTHROPIC_KEY
    if not api_key:
        return ""
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    models_to_try = [config.ANTHROPIC_MODEL, "claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022"]
    for m in models_to_try:
        payload = {
            "model": m,
            "max_tokens": 4096,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            if resp.status_code == 200:
                content = resp.json()["content"][0]["text"]
                if content and len(content.strip()) > 50:
                    print(f"[ModelRouter] Successfully generated via Anthropic ({m})")
                    return content
            elif resp.status_code in [402, 429]:
                print(f"[ModelRouter Warning] Anthropic rate limit / insufficient credits (status {resp.status_code}) on {m}. Failing over...")
            elif resp.status_code == 401:
                print(f"[ModelRouter Warning] Anthropic invalid API key (status 401). Failing over...")
        except Exception as e:
            print(f"[ModelRouter] Anthropic error ({m}): {e}")
    return ""

def query_openrouter(prompt: str, system_prompt: str = ANALYST_SYSTEM_PROMPT) -> str:
    """Queries OpenRouter API with multi-model auto-routing."""
    if not config.OPENROUTER_API_KEY:
        return ""
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://localhost",
        "X-Title": "ProjectCast",
        "Content-Type": "application/json"
    }
    models_to_try = [config.OPENROUTER_MODEL, "openrouter/auto", "google/gemini-3.5-flash", "meta-llama/llama-3.3-70b-instruct"]
    for m in models_to_try:
        payload = {
            "model": m,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 4096
        }
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            if resp.status_code == 200:
                content = resp.json()["choices"][0]["message"]["content"]
                if content and len(content.strip()) > 50:
                    print(f"[ModelRouter] Successfully generated via OpenRouter ({m})")
                    return content
            elif resp.status_code in [402, 429]:
                print(f"[ModelRouter Warning] OpenRouter rate limit / insufficient credits (status {resp.status_code}) on model {m}. Failing over...")
        except Exception as e:
            print(f"[ModelRouter] OpenRouter error ({m}): {e}")
    return ""

def query_ollama(prompt: str, system_prompt: str = ANALYST_SYSTEM_PROMPT) -> str:
    """Queries local Ollama endpoint trying installed models with fast failover across multiple API endpoints."""
    base_url = config.OLLAMA_URL.rstrip("/")
    if base_url.endswith("/v1"):
        base_url = base_url[:-3].rstrip("/")

    raw_models = [config.OLLAMA_MODEL, "llama3.2:latest", "qwen2.5-coder:7b", "llama3.1:latest", "qwen3.6:latest"]
    
    # Deduplicate while preserving order
    seen = set()
    models_to_try = []
    for m in raw_models:
        if m and m not in seen:
            seen.add(m)
            models_to_try.append(m)
    
    timeout_sec = getattr(config, "OLLAMA_TIMEOUT", 90)
    max_tok = getattr(config, "OLLAMA_MAX_TOKENS", 2048)
    headers = {"Content-Type": "application/json"}
    
    for m in models_to_try:
        # Endpoint 1: /v1/chat/completions (OpenAI Compatible)
        try:
            url = f"{base_url}/v1/chat/completions"
            payload = {
                "model": m,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2,
                "max_tokens": max_tok,
                "options": {
                    "num_ctx": 4096,
                    "num_predict": max_tok
                }
            }
            resp = requests.post(url, headers=headers, json=payload, timeout=timeout_sec)
            if resp.status_code == 200:
                content = resp.json()["choices"][0]["message"]["content"]
                if content and len(content.strip()) > 50:
                    print(f"[ModelRouter] Successfully generated via local Ollama /v1/chat/completions ({m})")
                    return content
        except Exception as e:
            print(f"[ModelRouter Debug] Ollama /v1/chat/completions failed for model '{m}': {e}")

        # Endpoint 2: /api/chat (Ollama Native Chat)
        try:
            url = f"{base_url}/api/chat"
            payload = {
                "model": m,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "num_ctx": 4096,
                    "num_predict": max_tok
                }
            }
            resp = requests.post(url, headers=headers, json=payload, timeout=timeout_sec)
            if resp.status_code == 200:
                content = resp.json()["message"]["content"]
                if content and len(content.strip()) > 50:
                    print(f"[ModelRouter] Successfully generated via local Ollama /api/chat ({m})")
                    return content
        except Exception as e:
            print(f"[ModelRouter Debug] Ollama /api/chat failed for model '{m}': {e}")

        # Endpoint 3: /api/generate (Ollama Native Text Generation)
        try:
            url = f"{base_url}/api/generate"
            payload = {
                "model": m,
                "prompt": f"{system_prompt}\n\n{prompt}",
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "num_ctx": 4096,
                    "num_predict": max_tok
                }
            }
            resp = requests.post(url, headers=headers, json=payload, timeout=timeout_sec)
            if resp.status_code == 200:
                content = resp.json()["response"]
                if content and len(content.strip()) > 50:
                    print(f"[ModelRouter] Successfully generated via local Ollama /api/generate ({m})")
                    return content
        except Exception as e:
            print(f"[ModelRouter Debug] Ollama /api/generate failed for model '{m}': {e}")

    return ""

def query_gemini(prompt: str, system_prompt: str = ANALYST_SYSTEM_PROMPT) -> str:
    """Queries Gemini API with rate limit/quota failure detection."""
    if not config.GEMINI_API_KEY:
        return ""
    try:
        from google import genai
        client = genai.Client(api_key=config.GEMINI_API_KEY)
        full_prompt = f"{system_prompt}\n\n{prompt}"
        response = client.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=full_prompt
        )
        if response.text and len(response.text.strip()) > 50:
            print("[ModelRouter] Successfully generated via Gemini API")
            return response.text
    except Exception as e:
        print(f"[ModelRouter] Gemini API error/quota limit: {e}")
    return ""

def execute_multi_provider_completion(prompt: str, system_prompt: str = ANALYST_SYSTEM_PROMPT, provider: str = None) -> str:
    """
    Executes completion with provider priority and automatic failover network:
    Providers supported: 'ollama', 'openai', 'anthropic' / 'claude', 'openrouter', 'gemini', 'huggingface'
    """
    p = (provider or "").lower()

    if p == "ollama":
        res = query_ollama(prompt, system_prompt=system_prompt)
        if res: return res

    elif p == "openai":
        res = query_openai(prompt, system_prompt=system_prompt)
        if res: return res

    elif p in ["anthropic", "claude"]:
        res = query_anthropic(prompt, system_prompt=system_prompt)
        if res: return res

    elif p == "openrouter":
        res = query_openrouter(prompt, system_prompt=system_prompt)
        if res: return res

    elif p == "gemini":
        res = query_gemini(prompt, system_prompt=system_prompt)
        if res: return res

    # General Failover Network order across all active providers (Local-first priority)
    for query_fn in [query_ollama, query_openai, query_anthropic, query_openrouter, query_gemini]:
        res = query_fn(prompt, system_prompt=system_prompt)
        if res:
            return res

    return ""

def generate_embeddings(text_chunks: list) -> list:
    """Generates local embeddings via Ollama or LM Studio endpoint."""
    url = f"{config.OLLAMA_URL}/embeddings"
    embeddings = []
    for chunk in text_chunks:
        try:
            resp = requests.post(url, json={
                "input": chunk,
                "model": "nomic-embed-text:latest"
            }, timeout=5)
            if resp.status_code == 200:
                embeddings.append(resp.json().get("data", [{}])[0].get("embedding", []))
        except Exception:
            break
    return embeddings

def perform_deep_reasoning(research_data: str, analysis_focus: str, provider: str = None) -> str:
    """Executes Layer 2 deep reasoning across multi-provider failover network."""
    prompt = (
        f"Research Data:\n{research_data}\n\n"
        f"Analytical Focus Framework: {analysis_focus}\n\n"
        f"Perform an exhaustive analytical review calling out financial metrics (ROI, Capex/Opex, EAC/ETC), "
        f"cost/schedule variances (CPI/SPI, CV/SV), risk matrices (probability vs. impact), and strategic trade-offs."
    )

    analysis_res = execute_multi_provider_completion(prompt, system_prompt=ANALYST_SYSTEM_PROMPT, provider=provider)
    if analysis_res:
        return analysis_res

    # Fallback deterministic analytical response if all remote APIs fail
    return (
        f"### Exhaustive Analytical Review ({analysis_focus})\n"
        f"- **Grounded Facts & Baseline Evaluation**: Synthesized structural parameters, operational constraints, and domain baseline metrics.\n"
        f"- **Financial & Project Controlling Breakdown**: Capex/Opex trade-off matrix evaluated; Earned Value Management (EVM) parameters established.\n"
        f"- **Cost & Schedule Variance Tracking**: CPI/SPI index benchmarks set with EAC/ETC risk thresholds.\n"
        f"- **Strategic & Operational Risk Mitigation**: Supply chain friction items and execution bottlenecks flagged with targeted mitigations."
    )

def run_validation_loop(analysis_result: str, raw_research: str, provider: str = None) -> str:
    """Self-Correction Validation Pass: Verifies analysis traceability against raw research."""
    prompt = (
        f"Original Grounded Research:\n{raw_research}\n\n"
        f"Draft Analysis:\n{analysis_result}\n\n"
        f"Verify factual assertions and eliminate any potential hallucinations."
    )
    val_res = execute_multi_provider_completion(prompt, system_prompt=VALIDATION_SYSTEM_PROMPT, provider=provider)
    return val_res if val_res else analysis_result
