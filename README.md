# LinkedIn EasyApply Bot (Playwright Edition) - Standalone Local Bot

A robust, stealthy, and modular bot to automate LinkedIn Easy Apply applications using Playwright. This is a **100% standalone local application** with zero external platform dependencies, zero remote telemetry, and complete local data persistence.

---

## 🏛️ Local Architecture

```text
LOCAL MACHINE
|
| python main.py
v
Standalone Playwright Bot
|
+-- Local configuration (config/candidates.yaml or config.yaml)
+-- Local credentials (.env)
+-- Local browser profiles (./profiles/<candidate_id>/)
+-- Local resume / cover letters (./assets/)
+-- Local job search & application workflow
+-- Local learned answers (saved to candidates.yaml & DuckDB)
+-- Local DuckDB database (data/bot_data.duckdb)
+-- Local logging (data/bot.log & stdout)
+-- Local session metrics
|
X-- NO EXTERNAL API / TELEMETRY DEPENDENCIES
```

---

## 🚀 Key Features

### 🛡️ Anti-Detection & Stealth
* **Playwright Native Engine**: Modern browser automation with stealth scripts.
* **Variable Fingerprinting**: Randomizes WebGL, Canvas, user agent, and viewport fingerprints.
* **Natural Human-like Behavior**: Bezier curve mouse movement, human-like scrolling, and randomized typing pauses.
* **Local Profile Persistence**: Saves browser session cookies and state locally in `./profiles/<candidate_id>/`.

### 🧠 Smart Form Filling & Human-in-the-Loop
* **Automated Keyword Matching**: Automatically answers known questions from candidate profile fields.
* **Interactive Human-in-Loop**: When an unknown question appears, the bot pauses and highlights the field for human input.
* **Local Answer Learning**: Remembers your answers and saves them locally for future runs.

### 💾 100% Local Data & Security
* **Local DuckDB**: Stores job details, statuses, run metrics, and QA pairs in `data/bot_data.duckdb`.
* **Local Logging**: Structured logs stored locally in `data/bot.log`.
* **Secure Environment**: Passwords and secrets stay in `.env` (git-ignored) and are sanitized from logs.

---

## 🛠️ Standalone Local Setup

### 1. Prerequisites
* Python 3.10+
* Playwright browser (Chromium)

### 2. Install Dependencies
```bash
pip install -r requirements.txt
playwright install chromium
```

### 3. Configure Local Credentials
Copy `.env.example` to `.env` and set your credentials:
```bash
copy .env.example .env
```

Example `.env`:
```ini
# Multi-profile candidate credentials
CANDIDATE_001_PASSWORD=your_password_here

# Single profile / fallback credentials
LINKEDIN_USERNAME=your_email@example.com
LINKEDIN_PASSWORD=your_password
PHONE_NUMBER=1234567890
```

### 4. Configure Candidate Profiles
Copy `config/candidates.example.yaml` to `config/candidates.yaml`:
```bash
copy config\candidates.example.yaml config\candidates.yaml
```
Edit `config/candidates.yaml` to configure target job positions, locations, experience levels, resume paths, and profile answers.

### 5. Add Resume & Cover Letter
Place your PDF files into the configured path (e.g., `assets/candidates/candidate_001/resume.pdf`).

---

## 🔍 Validation

Verify that your local environment is properly configured and free of external telemetry:
```bash
python validate.py
```

---

## ▶️ Execution

### Run the Bot
```bash
python main.py
```

### Dry-Run Mode
Keep `dry_run: true` in your configuration to test searching and form-filling without submitting applications. When ready to submit live applications, set `dry_run: false`.

### Local Analytics & Stats
View your local application history and metrics stored in DuckDB:
```bash
# View summary statistics
python view_stats.py

# Check submissions per candidate
python check_submissions.py
```

---

## 📂 Project Structure
```text
.
├── main.py                     # Main application entry point
├── validate.py                 # Local independence & environment validator
├── view_stats.py               # Local application analytics (DuckDB)
├── check_submissions.py        # Local candidate submission counter
├── test_smart_filler.py        # Profile matching test utility
├── config/
│   ├── candidates.example.yaml # Example multi-candidate configuration
│   └── candidates.yaml         # Your local candidate profiles (git-ignored)
├── config.example.yaml         # Example legacy configuration
├── .env.example                # Example environment secrets template
├── bot/
│   ├── core/                   # Browser, Session, Metrics, Guard, Proxy
│   ├── discovery/              # Search, Scroll, Job Identity
│   ├── application/            # Workflow, Smart Form Filler
│   ├── persistence/            # Local DuckDB Store
│   └── utils/                  # Human Interaction, Logger, Selectors, Stealth
├── data/                       # Local DuckDB (bot_data.duckdb) & Local Log (bot.log)
├── profiles/                   # Local Playwright persistent browser profiles
└── assets/                     # Resumes and cover letters
```

---

## ⚠️ Disclaimer
This bot is for educational and personal productivity purposes. Always adhere to website terms of service and best practices for job applications.
