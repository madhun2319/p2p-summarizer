# 🧬 BioPulse AI — P2P Structural Biology Summarizer Engine

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![NVIDIA NIM](https://img.shields.io/badge/NVIDIA%20NIM-Llama--3.1--70B-green.svg)](https://build.nvidia.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Automated structural biology intelligence engine that ingests, triages, and visualizes newly released RCSB PDB structures and PubMed research papers using NVIDIA NIM Llama 3.1 8B & 70B.**

---

## 🚀 Key Features

* 🔍 **RCSB PDB & PubMed Ingestion**: Automatically fetches all protein structures deposited or released in the last 7 days.
* 🧪 **Llama 3.1 8B Triage Agent**: Evaluates abstracts for clinical impact, druggability, and novelty (scoring 1-10) to filter out noise.
* 🎨 **Visual ASCII Interaction Diagrams**: Generates custom ASCII art diagrams showing domain interactions, kinase autoinhibition, and binding state changes.
* 📰 **"Proteins of the Week" Newsletter**: Auto-compiles Top 5 high-impact protein highlights into publication-grade Markdown & PDF issues.
* ☁️ **100% Serverless Cloud Execution**: Pre-configured GitHub Actions workflow runs every Monday at 08:00 AM UTC in the cloud.

---

## 🏗️ Architecture

```
[RCSB PDB & PubMed APIs] ──> [ingest.py (Llama 3.1 8B Triage)] ──> [triaged_pdbs.json]
                                                                          │
                                                                          ▼
[newsletter_YYYY_MM_DD.md] <── [newsletter.py (Llama 3.1 70B Summarizer)] ┘
```

---

## ⚡ Quickstart

### 1. Prerequisites
Install dependencies using [`uv`](https://github.com/astral-sh/uv) (fast Python package manager):
```bash
uv pip install openai
```

### 2. Set API Key
Add your NVIDIA NIM API key to `.env`:
```env
NVIDIA_API_KEY="nvapi-your-key-here"
```

### 3. Run Single PDB Summarizer
```bash
uv run --env-file .env --with openai summarize.py 7BYR
```

### 4. Run Automated Ingestion & Triage (Last 7 Days)
```bash
uv run --env-file .env --with openai ingest.py
```

### 5. Build Newsletter Digest (Top 5)
```bash
uv run --env-file .env --with openai newsletter.py
```

---

## 📄 Executive & Business Blueprints

* 💰 **[Monetization Blueprint](BIOPULSE_MONETIZATION_BLUEPRINT.md)**: 3-tier SaaS recurring revenue model ($49/mo newsletter, $499/mo API, $1,499/mo enterprise Slack bot).
* 📣 **[Go-To-Market Playbook](GTM_MARKETING_PLAYBOOK.md)**: Zero-ad-spend acquisition strategy for Life Science VCs, Drug Discovery leads, and Equity Analysts.
* 📄 **[Executive PDF Report](BioPulse_AI_Executive_Blueprint.pdf)**: Rendered executive blueprint summary.

---

## 🤖 Automation & Cloud Execution

* **VS Code Auto-Task**: Configured in `.vscode/tasks.json` to auto-execute on workspace open.
* **Windows Task Scheduler**: Run `powershell -File setup_windows_cron.ps1` to schedule weekly execution.
* **GitHub Actions Cloud Cron**: Managed automatically by `.github/workflows/weekly_pipeline.yml`.

---

## 📜 License
MIT License. Free for research, personal, and commercial use.
