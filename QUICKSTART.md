# Quick Start Guide - LinkedIn EasyApply Bot (Playwright)

## Installation (5 minutes)

### Step 1: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Install Playwright Chromium Browser
```bash
playwright install chromium
```

### Step 3: Configure Credentials
1. Copy `.env.example` to `.env`:
   ```bash
   copy .env.example .env
   ```

2. Edit `.env` and add your credentials:
   ```ini
   CANDIDATE_001_PASSWORD=your_password_here
   LINKEDIN_USERNAME=your_email@example.com
   LINKEDIN_PASSWORD=your_password
   PHONE_NUMBER=1234567890
   ```

### Step 4: Configure Job Search & Candidate Profile
Copy `config/candidates.example.yaml` to `config/candidates.yaml`:
```bash
copy config\candidates.example.yaml config\candidates.yaml
```
Edit `config/candidates.yaml`:
```yaml
candidates:
  - id: candidate_001
    name: "Your Name"
    enabled: true
    credentials:
      email: "your_email@example.com"
      phone: "1234567890"
    uploads:
      Resume: ./assets/candidates/candidate_001/resume.pdf
    search:
      positions:
        - "Software Engineer"
        - "Python Developer"
      locations:
        - "Remote"
    preferences:
      max_applications_per_run: 5
      cooldown_seconds: 5
      dry_run: true  # Keep true for testing!
```

### Step 5: Add Your Resume
Place your resume in the configured assets path:
- `assets/candidates/candidate_001/resume.pdf`

---

## Validate Setup

Run the validation script to verify all local components are ready:
```bash
python validate.py
```

---

## First Run (Dry Run Mode)

**IMPORTANT**: Always test in dry run mode first!

```bash
python main.py
```

### What to Expect:
1. Browser will open automatically
2. Bot will log into LinkedIn
3. Bot will search for jobs
4. Bot will click "Easy Apply" buttons
5. Bot will fill out forms using profile data
6. **Bot will NOT submit** (dry run mode)
7. You'll see a local session summary at the end

---

## Checking Results

All applications are saved locally in `data/bot_data.duckdb` and `data/bot.log`.
```bash
python view_stats.py
python check_submissions.py
```

Happy job hunting! 🚀
