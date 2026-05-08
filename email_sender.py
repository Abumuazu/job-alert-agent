"""
Email sender — builds and dispatches HTML emails via Gmail SMTP.
Handles two email types:
  1. Job alert  — fires whenever new jobs are found (up to every 15 min)
  2. Daily digest — cold email targets + recruiter DMs, sent once at 7am UTC
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timezone

from config import SENDER_EMAIL, GMAIL_APP_PASSWORD, ALERT_EMAIL


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _time_ago(posted_at_str: str) -> str:
    try:
        from dateutil import parser
        posted = parser.parse(posted_at_str)
        if posted.tzinfo is None:
            posted = posted.replace(tzinfo=timezone.utc)
        diff    = datetime.now(timezone.utc) - posted
        minutes = int(diff.total_seconds() / 60)
        if minutes < 1:
            return "just now"
        if minutes < 60:
            return f"{minutes}m ago"
        return f"{minutes // 60}h ago"
    except Exception:
        return "recently"


def _send(subject: str, html: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = SENDER_EMAIL
    msg["To"]      = ALERT_EMAIL
    msg.attach(MIMEText(html, "html"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER_EMAIL, GMAIL_APP_PASSWORD)
        server.sendmail(SENDER_EMAIL, ALERT_EMAIL, msg.as_string())


# ─────────────────────────────────────────────────────────────────────────────
# Job alert
# ─────────────────────────────────────────────────────────────────────────────

def send_job_alert(jobs: list) -> None:
    if not jobs:
        return
    jobs = sorted(jobs, key=lambda j: j.get("score", 0), reverse=True)
    subject = f"🔥 {len(jobs)} new React Native job{'s' if len(jobs) > 1 else ''} — posted just now"
    html    = _build_job_alert_html(jobs)
    _send(subject, html)
    print(f"[Email] Job alert sent — {len(jobs)} job(s)")


def _build_job_alert_html(jobs: list) -> str:
    rows = ""
    for job in jobs:
        score      = job.get("score", 0)
        score_color = "#16a34a" if score >= 75 else "#d97706" if score >= 55 else "#6b7280"
        time_ago   = _time_ago(job.get("posted_at", ""))
        salary_str = f" &nbsp;·&nbsp; {job['salary_text']}" if job.get("salary_text") else ""

        rows += f"""
        <div style="border:1px solid #fbbf24;border-radius:10px;padding:18px;margin-bottom:14px;background:#fffbeb;">
          <table width="100%" cellpadding="0" cellspacing="0">
            <tr>
              <td style="vertical-align:top;">
                <p style="margin:0;font-size:15px;font-weight:700;color:#111;">{job['title']}</p>
                <p style="margin:5px 0 0;font-size:13px;color:#555;">{job['company']}{salary_str}</p>
              </td>
              <td style="vertical-align:top;text-align:right;white-space:nowrap;padding-left:12px;">
                <span style="background:{score_color};color:white;font-size:11px;font-weight:700;
                             padding:3px 9px;border-radius:20px;">{score}% match</span>
              </td>
            </tr>
          </table>
          <p style="margin:10px 0 12px;font-size:12px;color:#b45309;font-weight:600;">
            ⏰ Posted {time_ago} &nbsp;·&nbsp; via {job['source']}
          </p>
          <a href="{job['url']}"
             style="display:inline-block;background:#111;color:#fff;text-decoration:none;
                    padding:9px 18px;border-radius:7px;font-size:13px;font-weight:600;">
            Apply now →
          </a>
        </div>
        """

    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f3f4f6;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
  <div style="max-width:600px;margin:24px auto;background:#fff;border-radius:14px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.08);">

    <div style="background:#0f172a;padding:22px 26px;">
      <p style="margin:0;color:#fbbf24;font-size:11px;font-weight:700;letter-spacing:1.2px;text-transform:uppercase;">
        React Native Job Alert
      </p>
      <h1 style="margin:6px 0 0;color:#fff;font-size:21px;font-weight:700;line-height:1.3;">
        {len(jobs)} new job{'s' if len(jobs) > 1 else ''} — you're among the first to see {'these' if len(jobs) > 1 else 'this'}
      </h1>
    </div>

    <div style="padding:22px 26px 8px;">
      <p style="margin:0 0 18px;font-size:13px;color:#6b7280;line-height:1.6;">
        These were posted in the last 20 minutes. Most applicants won't see them for another hour or more.
        <strong style="color:#111;">Apply now to be in the first wave.</strong>
      </p>
      {rows}
    </div>

    <div style="padding:16px 26px;background:#f9fafb;border-top:1px solid #e5e7eb;">
      <p style="margin:0;font-size:12px;color:#9ca3af;">
        Job Alert Agent &nbsp;·&nbsp; Runs every 15 min &nbsp;·&nbsp; Sending to {ALERT_EMAIL}
      </p>
    </div>
  </div>
</body></html>"""


# ─────────────────────────────────────────────────────────────────────────────
# Daily digest
# ─────────────────────────────────────────────────────────────────────────────

def send_daily_digest(cold_targets: list, recruiters: list) -> None:
    today   = datetime.now().strftime("%A, %B %-d")
    subject = f"📨 Daily digest — {today} · Cold targets + recruiter DMs"
    html    = _build_digest_html(cold_targets, recruiters, today)
    _send(subject, html)
    print("[Email] Daily digest sent")


def _build_digest_html(cold_targets: list, recruiters: list, today: str) -> str:
    target_rows = ""
    for i, t in enumerate(cold_targets[:5], 1):
        link_html = (
            f'<br><a href="{t["url"]}" style="font-size:12px;color:#1d4ed8;text-decoration:none;">'
            f'→ {t["url"]}</a>'
        ) if t.get("url") else ""

        target_rows += f"""
        <div style="border:1px solid #bfdbfe;border-radius:10px;padding:14px;margin-bottom:10px;background:#eff6ff;">
          <table cellpadding="0" cellspacing="0" width="100%"><tr>
            <td style="vertical-align:top;width:28px;">
              <span style="display:inline-block;background:#1d4ed8;color:#fff;font-size:11px;font-weight:700;
                           padding:2px 7px;border-radius:20px;">{i}</span>
            </td>
            <td style="vertical-align:top;padding-left:10px;">
              <p style="margin:0;font-size:14px;font-weight:700;color:#111;">{t['name']}</p>
              <p style="margin:4px 0 0;font-size:12px;color:#374151;">{t['reason']}{link_html}</p>
            </td>
          </tr></table>
        </div>
        """

    recruiter_rows = ""
    for i, r in enumerate(recruiters[:3], 1):
        link_html = (
            f'<br><a href="{r["linkedin"]}" style="font-size:12px;color:#059669;text-decoration:none;">'
            f'→ View on LinkedIn / DM here</a>'
        ) if r.get("linkedin") else ""

        recruiter_rows += f"""
        <div style="border:1px solid #a7f3d0;border-radius:10px;padding:14px;margin-bottom:10px;background:#ecfdf5;">
          <table cellpadding="0" cellspacing="0" width="100%"><tr>
            <td style="vertical-align:top;width:28px;">
              <span style="display:inline-block;background:#059669;color:#fff;font-size:11px;font-weight:700;
                           padding:2px 7px;border-radius:20px;">{i}</span>
            </td>
            <td style="vertical-align:top;padding-left:10px;">
              <p style="margin:0;font-size:14px;font-weight:700;color:#111;">
                {r['name']} <span style="font-weight:400;color:#6b7280;">· {r['title']}</span>
              </p>
              <p style="margin:4px 0 0;font-size:12px;color:#374151;">{r['note']}{link_html}</p>
            </td>
          </tr></table>
        </div>
        """

    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f3f4f6;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
  <div style="max-width:600px;margin:24px auto;background:#fff;border-radius:14px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.08);">

    <div style="background:#0f172a;padding:22px 26px;">
      <p style="margin:0;color:#86efac;font-size:11px;font-weight:700;letter-spacing:1.2px;text-transform:uppercase;">
        Daily Digest · {today}
      </p>
      <h1 style="margin:6px 0 0;color:#fff;font-size:21px;font-weight:700;line-height:1.3;">
        Your outreach targets for today
      </h1>
    </div>

    <div style="padding:22px 26px 8px;">
      <h2 style="margin:0 0 6px;font-size:13px;font-weight:700;color:#111;text-transform:uppercase;letter-spacing:.6px;">
        📨 Top 5 Companies — Cold Email Your Portfolio
      </h2>
      <p style="margin:0 0 14px;font-size:13px;color:#6b7280;">
        These are actively growing, recently funded, or known to hire React Native talent remotely.
        Send a short email with your portfolio link today — before the role is posted publicly.
      </p>
      {target_rows}
    </div>

    <div style="padding:0 26px 22px;">
      <h2 style="margin:0 0 6px;font-size:13px;font-weight:700;color:#111;text-transform:uppercase;letter-spacing:.6px;">
        💬 Top 3 Recruiters — DM on LinkedIn Today
      </h2>
      <p style="margin:0 0 14px;font-size:13px;color:#6b7280;">
        These recruiters actively place React Native engineers in remote roles.
        Send them a short DM with your portfolio — one message could fast-track a placement.
      </p>
      {recruiter_rows}
    </div>

    <div style="padding:16px 26px;background:#f9fafb;border-top:1px solid #e5e7eb;">
      <p style="margin:0;font-size:12px;color:#9ca3af;">
        Daily digest &nbsp;·&nbsp; Sent at 7am UTC &nbsp;·&nbsp; {ALERT_EMAIL}
      </p>
    </div>
  </div>
</body></html>"""
