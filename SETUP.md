# Job Alert Agent — Setup Guide

Everything runs on GitHub Actions for free — no server, no laptop needed.
Follow these steps exactly and you'll be live in under 15 minutes.

---

## Step 1 — Create the GitHub repository

1. Go to https://github.com/new
2. Name it: `job-alert-agent`
3. Set visibility to **Private** (your email credentials will be stored here)
4. Leave everything else as default — do NOT add a README or .gitignore
5. Click **Create repository**

---

## Step 2 — Upload all the files

On the empty repo page, click **"uploading an existing file"** (the link in the centre).

Drag and drop the entire `job-alert-agent` folder contents:

```
config.py
main.py
daily_digest.py
scorer.py
dedup.py
email_sender.py
cold_targets.py
requirements.txt
seen_jobs.json
scrapers/
  __init__.py
  remoteok.py
  remotive.py
  weworkremotely.py
  linkedin.py
.github/
  workflows/
    scrape.yml
    daily_digest.yml
```

> **Important:** GitHub's drag-and-drop uploader handles folders.
> Just drag the whole lot in at once.

Click **Commit changes**.

---

## Step 3 — Get your Gmail App Password

The agent sends emails through your Gmail account. You need an **App Password**
(a special 16-character code Gmail generates — it is NOT your normal password).

1. Go to https://myaccount.google.com/security
2. Make sure **2-Step Verification** is ON (required for App Passwords)
3. Search for "App Passwords" in the search bar at the top
4. Click **App Passwords**
5. Under "Select app" choose **Mail**
6. Under "Select device" choose **Other** → type: `Job Alert Agent`
7. Click **Generate**
8. **Copy the 16-character code shown** (you won't see it again)

> Use your **kakupepe09@gmail.com** account for the sender.
> Alerts will be delivered to **abumuazu09@gmail.com**.

---

## Step 4 — Add GitHub Secrets

1. In your GitHub repo, go to **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret** and add these two:

| Secret name        | Value                                      |
|--------------------|--------------------------------------------|
| `GMAIL_SENDER`     | `kakupepe09@gmail.com`                     |
| `GMAIL_APP_PASSWORD` | *(the 16-character code from Step 3)*    |

---

## Step 5 — Enable GitHub Actions

1. In your repo, click the **Actions** tab
2. If you see a message "Workflows aren't being run on this forked repository",
   click **I understand my workflows, go ahead and enable them**
3. You should see two workflows listed:
   - **Job Scraper — Every 15 Minutes**
   - **Daily Digest — 7am UTC**

---

## Step 6 — Test it manually

Run each workflow once to confirm everything is working:

1. Click **Job Scraper — Every 15 Minutes** in the Actions tab
2. Click **Run workflow** → **Run workflow** (green button)
3. Watch the run — it should complete in ~60 seconds
4. Check **abumuazu09@gmail.com** — if any React Native jobs posted in the
   last 20 minutes were found, you'll have an email

Do the same for the **Daily Digest** workflow to test your cold targets email.

---

## You're live

Once set up, the agent runs automatically:
- **Every 15 minutes** — checking for new React Native remote jobs
- **Every morning at 7am UTC** — sending your daily cold email + recruiter DM list

No laptop needed. It runs even when your computer is off.

---

## Customising the agent

| What to change              | Where                          |
|-----------------------------|--------------------------------|
| Keywords to search          | `config.py` → `KEYWORDS`       |
| Minimum salary              | `config.py` → `SALARY_MIN`     |
| Minimum match score         | `config.py` → `SCORE_THRESHOLD`|
| Cold email company list     | `cold_targets.py` → `SEED_COMPANIES` |
| Recruiter DM list           | `cold_targets.py` → `RECRUITERS` |
| Alert email address         | `config.py` → `ALERT_EMAIL`   |

After any change, commit the file in GitHub and the next run picks it up automatically.

---

## Troubleshooting

**No email received after manual run:**
- Check the Actions run log for errors (red X means it failed)
- Confirm your App Password is correct — regenerate in Google if unsure
- Check your spam folder

**"Authentication failed" error in logs:**
- Your App Password is wrong or expired — generate a new one in Step 3 and update the secret

**Workflow not running on schedule:**
- GitHub Actions cron can be delayed up to 15 minutes on free accounts under load
- This is normal — your window is still well within the first hour of a posting
