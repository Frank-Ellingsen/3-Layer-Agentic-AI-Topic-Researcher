# ProjectCast 🚀
> **A 3-Layer Agentic AI Engine for Project Controlling, EVM Forecasting & Decision Intelligence**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688.svg?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Style: Edward Tufte Data-Ink](https://img.shields.io/badge/Design-Tufte_Data--Ink-000000.svg)](https://www.edwardtufte.com/)

**ProjectCast** is an enterprise-grade, automated 3-Layer Agentic AI system engineered for **Project Controllers**, **Financial Analysts**, and **Engineering Project Managers**. It automates the entire research & intelligence lifecycle—from multi-source web and local document ingestion to deep analytical reasoning, EVM forecasting (CPI/SPI, EAC/ETC), DuckDB RAG passage retrieval, self-correction validation, and multi-format executive report publishing (PDF, HTML, Markdown).

---

## 🌟 Key Features

* **🤖 3-Layer Agentic Architecture:**
  * **Layer 1 (Research Agent):** Ingests web feeds, local PDFs/CSVs, and syncs grounded RAG corpora via NotebookLM.
  * **Layer 2 (Analyst Agent):** Executes deep reasoning, Earned Value Management (EVM) variance calculations, and self-correction verification.
  * **Layer 3 (Report Agent):** Compiles executive briefings in HTML, PDF, and Markdown.
* **🛡️ Resilient Multi-Provider Failover Router:**
  * Auto-routes and fails over across **OpenAI (GPT-4o)**, **Anthropic (Claude 3.5 Sonnet)**, **OpenRouter**, **Google Gemini**, **Local Ollama**, and **Hugging Face**.
  * Handles 402/429 rate limits and token credit exhaustion gracefully without breaking pipeline execution.
* **📊 Edward Tufte Data-Ink Ratio Compliance:**
  * PDF and Web pages feature zero vertical gridlines, left-aligned text, right-aligned numeric columns, and muted slate styling with active risk callouts (`.risk-amber`, `.risk-red`).
* **🌐 Modern Web Dashboard & Action Bar:**
  * Interactive dark-mode glassmorphism interface powered by FastAPI with live Markdown rendering and instant one-click downloads for PDF, MD, and HTML.
* **📂 Automated Folder Watchdog:**
  * Background filesystem watcher (`main.py --watch`) monitoring `./input_folder_z/raw_docs/` for automatic pipeline triggering upon document drop.

---

## 🏗️ System Architecture

```
                                  +---------------------------------------+
                                  |    Trigger (Web UI / CLI / Watchdog)  |
                                  +---------------------------------------+
                                                      |
                                                      v
  ===================================================================================================
  LAYER 1: RESEARCH AGENT (Ingestion & Search Grounding)
  ---------------------------------------------------------------------------------------------------
  * Web Search Grounding (Gemini / Multi-Provider)
  * Local File Ingestion (PDF / CSV / TXT / MD)
  * Grounded Corpus Synchronization (NotebookLM RAG)
  ===================================================================================================
                                                      |
                                                      v
  ===================================================================================================
  LAYER 2: ANALYST AGENT (Deep Reasoning & Self-Correction)
  ---------------------------------------------------------------------------------------------------
  * EVM Variance Analysis (CPI, SPI, CV, SV, EAC / ETC Forecasting)
  * Strategic Matrices (SWOT, PESTEL, Risk Matrix, Bottleneck Analysis)
  * Self-Correction Quality Audit Loop (Factual Assertions Verification)
  ===================================================================================================
                                                      |
                                                      v
  ===================================================================================================
  LAYER 3: REPORT AGENT & STORAGE ENGINE (Output Compilation)
  ---------------------------------------------------------------------------------------------------
  * Tufte Data-Ink HTML Web Page Generator (Default)
  * Executive Presentation Header Banner Generator (16:9 Visual Asset)
  * PDF Compiler (xhtml2pdf + Tufte CSS Layouts) & Markdown Vault Archiving
  * Dual SQLite Database Persistence (Research History & Telemetry Execution Logs)
  ===================================================================================================
```

---

## 📂 Repository Directory Structure

```
ProjectCast/
├── agent.py                 # Interactive Rich Terminal CLI Application
├── server.py                # FastAPI Web API Server (Port 8000)
├── main.py                  # Pipeline Execution Engine & Watchdog (--watch)
├── pdf_generator.py         # Tufte Data-Ink PDF & HTML Compiler
├── database.py              # SQLite Research History Database Manager
├── config.py                # Environment Variables & YAML Config Ingestor
├── config.yaml              # Application Configuration Settings
├── requirements.txt         # Complete Python Package Dependencies
├── .env.example             # Template for API Keys & Model Settings
├── .gitignore               # Clean Git Exclusion Rules
├── Architecture and....md   # Architectural Whitepaper & System Specifications
├── src/                     # Core Modular Engine
│   ├── scraper.py           # Ingestion & Search Grounding Module
│   ├── local_lm.py          # Multi-Provider Failover Model Router
│   ├── notebook_sync.py     # Grounded RAG Corpus Connector
│   ├── report_agent.py      # Executive Report & Banner Injection Agent
│   ├── storage_sync.py      # Telemetry DB, Notion & Drive Connectors
│   └── image_generator.py   # Dynamic 16:9 Presentation Header Image Generator
├── web/                     # Web Dashboard UI
│   ├── index.html           # Dark-Mode Glassmorphism Dashboard
│   ├── styles.css           # Modern CSS Tokens & Micro-Animations
│   └── app.js               # Async REST Client & Live Preview Engine
├── outputs/                 # Output Vault (Git-tracked structure)
│   ├── pdf/                 # Compiled PDF Reports (.pdf)
│   ├── html/                # Rendered HTML Web Pages (.html)
│   ├── markdown/            # Clean Raw Markdown Files (.md)
│   └── assets/              # Generated Executive Header Banners (.jpg)
├── database/                # Telemetry Database
│   └── workflow_logs.db     # Execution Audit Trail & Performance Telemetry
└── input_folder_z/          # Folder Watchdog Directory
    └── raw_docs/            # Monitored Ingestion Folder
```

---

## 🚀 Quickstart Guide

### 1. Prerequisites
* **Python 3.10+** installed.
* **Local Ollama** installed and running (`http://localhost:11434`) with model `llama3.1:latest` (Default AI Provider).

### 2. Installation
Clone the repository and install the dependencies:

```bash
git clone https://github.com/your-username/projectcast.git
cd projectcast
pip install -r requirements.txt
```

### 3. Environment Configuration
Copy the environment template and insert optional cloud API keys (if using cloud providers instead of local Ollama):

```bash
cp .env.example .env
```

Edit `.env`:
```env
OLLAMA_URL=http://localhost:11434/v1
OLLAMA_MODEL=llama3.1:latest
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-...
OPENROUTER_API_KEY=sk-or-v1-...
GEMINI_API_KEY=AIzaSy...
```

---

## 🖥️ Usage Modes

### Mode 1: Web Dashboard (Recommended)
Launch the FastAPI web server:

```bash
python server.py
```
Open your browser at `http://localhost:8000`. Enter a research topic, select an analytical framework, choose a model provider, and click **Launch Agentic Research**. Download generated reports directly as **PDF**, **MD**, or **HTML**.

### Mode 2: Interactive Terminal CLI
Run the rich terminal CLI interface:

```bash
python agent.py
```
Follow the interactive prompts to choose from **9 analytical frameworks** and set your preferred output format.

### Mode 3: Automated Folder Watchdog
Start monitoring `./input_folder_z/raw_docs/` for incoming documents:

```bash
python main.py --watch
```
Drop any `.txt`, `.md`, or `.csv` file into `./input_folder_z/raw_docs/` to automatically trigger the 3-Layer pipeline.

---

## 📊 Analytical Frameworks Supported

1. **Comprehensive Multi-Dimensional Analysis** *(Default)*
2. **Cost-Benefit & Financial Feasibility** *(EVM / Capex / Opex)*
3. **SWOT Strategic Analysis**
4. **Risk Matrix & Mitigation Tracking** *(Probability vs. Impact)*
5. **PESTEL Analysis** *(Political, Economic, Social, Tech, Environmental, Legal)*
6. **Bottleneck & Operational Efficiency**
7. **Project Controlling & Earned Value (EV) Analysis** *(CPI / SPI / CV / SV / EAC / ETC)*
8. **Custom Analytical Focus**

---

## 🎨 Edward Tufte Data-Ink Principles Applied

* **Clean Tables:** Horizontal lines only for header borders (`border-top: 1pt solid`, `border-bottom: 1.5pt solid`). No vertical gridlines.
* **Strict Alignment:** Text columns left-aligned; numeric columns right-aligned with vertical decimal place alignment (`style="text-align:right;"`).
* **Visual Palette:** High-legibility typography with muted slate accents. Highlights (`.risk-amber`, `.risk-red`) are restricted exclusively to active variances and risk callouts.

---

## 📜 License
Distributed under the **MIT License**. See `LICENSE` for details.
