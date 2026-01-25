# 🩻 Project X-Ray: Automated Codebase Auditor

**Project X-Ray** is a lightweight, single-file static analysis tool designed to instantly visualize, audit, and summarize any software project. 

It combines **Static Code Analysis** (Regex/Heuristic) with **Generative AI** (Google Gemini) to produce a comprehensive HTML dashboard containing architecture diagrams, risk assessments, and impact analysis.

---

## 🚀 Key Features

* **🔍 Instant Architecture Visualization:** Automatically generates a dependency graph (using Mermaid.js) by parsing imports across multiple languages (Python, TS/JS, Java, Go, etc.).
* **🛡️ Security & Risk Scanning:** Detects hardcoded secrets, passwords, and bad practices (e.g., `Thread.sleep`, `console.log`) using regex pattern matching.
* **🧠 AI-Powered Summaries:** Uses Google Gemini 1.5 Flash to read file metadata and generate a human-readable "Executive Summary" of the project.
* **🕸️ Impact Analysis:** Identifies "Critical Hubs"—files that are heavily relied upon by the rest of the system, helping developers avoid breaking changes.
* **📊 Zero-Config Dashboard:** Outputs a single, self-contained `qa_report_final.html` file that works offline.

## 🛠️ Prerequisites

* **Python 3.8+**
* **Google Gemini API Key** (Optional, but recommended for AI summaries)

## 📦 Installation

No complex dependencies. Just install `requests` if you haven't already:

In Github, go to actions, there is workflow, provide github repository url and it will run the all scan and produce a html page with all findings.


```bash

⚡ Usage
1. Scan a Local Project
Run the script pointing to your project directory:

Bash

python xray.py "C:/Users/Dev/MyProject"
2. Scan a GitHub Repo (Ephemeral Mode)
The tool can clone, scan, and auto-delete a remote repo without cluttering your disk:

Bash

python xray.py "[https://github.com/username/repo-name](https://github.com/username/repo-name)"
3. Setting the API Key
You can hardcode the key in the script or set it as an environment variable:

Bash

# Windows
set GEMINI_API_KEY=your_key_here
# Mac/Linux
export GEMINI_API_KEY=your_key_here
