
# import asyncio
# import re
# import smtplib
# from email.mime.text import MIMEText
# from playwright.async_api import async_playwright

# # -------- CONFIG --------
# CHECK_INTERVAL = 40  # seconds
# SEARCH_URL = "https://www.jobsatamazon.co.uk/app#/jobSearch"

# EMAIL_FROM = "wezyali@gmail.com"
# EMAIL_TO = "aliblizzard2@gmail.com"
# SMTP_SERVER = "smtp.gmail.com"
# SMTP_PORT = 587
# EMAIL_USER = "wezyali@gmail.com"
# EMAIL_PASS = "xstarmmghjatvxck"  # Gmail app password
# # ------------------------


# def send_email(message: str) -> None:
#     msg = MIMEText(message)
#     msg["Subject"] = "Amazon Job Alert!"
#     msg["From"] = EMAIL_FROM
#     msg["To"] = EMAIL_TO

#     with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
#         server.starttls()
#         server.login(EMAIL_USER, EMAIL_PASS)
#         server.sendmail(EMAIL_FROM, [EMAIL_TO], msg.as_string())
#     print("✅ Email sent.")


# async def get_all_text(page) -> str:
#     """Return combined innerText from all frames."""
#     chunks = []
#     for frame in page.frames:
#         try:
#             text = await frame.evaluate(
#                 "() => document.body ? document.body.innerText : ''"
#             )
#             if text:
#                 chunks.append(text)
#         except Exception:
#             continue
#     return "\n".join(chunks)


# def parse_jobs_from_text(text: str) -> list[dict]:
#     """
#     Parse job blocks into structured dicts:
#     {title, type, duration, pay, location}
#     """
#     lines = [l.strip() for l in text.splitlines() if l.strip()]
#     jobs: list[dict] = []

#     # First, make sure we actually have jobs at all
#     joined = "\n".join(lines)
#     m = re.search(r"(\d+)\s+job(?:s)?\s+found", joined, re.IGNORECASE)
#     if not m:
#         return []

#     for i, line in enumerate(lines):
#         if "Type:" not in line:
#             continue

#         # Title is usually just above "Type:"
#         title = lines[i - 1] if i > 0 else "Unknown role"

#         job_type = ""
#         duration = ""
#         pay = ""
#         location = ""

#         # Extract "Type:" from this line
#         parts = line.split("Type:", 1)
#         if len(parts) > 1:
#             job_type = parts[1].strip()

#         # Look ahead a few lines for duration, pay, location
#         for k in range(i + 1, min(i + 8, len(lines))):
#             l = lines[k]

#             if "Duration:" in l:
#                 duration = l.split("Duration:", 1)[1].strip()
#                 continue
#             if "Pay rate:" in l:
#                 pay = l.split("Pay rate:", 1)[1].strip()
#                 continue

#             # Heuristic for location: line after pay, or any line that looks like "Town, Region"
#             if not location and ("," in l or "United Kingdom" in l or "UK" in l):
#                 location = l.strip()

#         jobs.append(
#             {
#                 "title": title,
#                 "type": job_type,
#                 "duration": duration,
#                 "pay": pay,
#                 "location": location,
#                 "url": None,  # to fill later
#             }
#         )

#     # Deduplicate by (title, location)
#     unique = {}
#     for j in jobs:
#         key = (j["title"], j["location"])
#         if key not in unique:
#             unique[key] = j

#     return list(unique.values())


# async def find_job_url(page, title: str) -> str | None:
#     """
#     Try to find a clickable link for the job title in the DOM.
#     If found, return href. Otherwise, return None.
#     """
#     try:
#         # Use Playwright's text locator (can pierce into many structures)
#         locator = page.locator(f"text={title}")
#         count = await locator.count()
#         if count == 0:
#             return None

#         # Take the first match
#         first = locator.nth(0)
#         handle = await first.element_handle()
#         if not handle:
#             return None

#         href = await handle.evaluate(
#             "node => (node.closest('a') && node.closest('a').href) || ''"
#         )
#         href = (href or "").strip()
#         if href:
#             return href
#     except Exception:
#         pass

#     return None


# async def check_jobs():
#     print("Opening browser...")
#     async with async_playwright() as p:
#         browser = await p.chromium.launch(headless=False)

#         context = await browser.new_context(permissions=[])
#         page = await context.new_page()

#         print("Loading page...")
#         await page.goto(SEARCH_URL, wait_until="domcontentloaded")

#         # ===== Handle cookie banner =====
#         try:
#             await page.wait_for_timeout(3000)
#             for frame in page.frames:
#                 buttons = await frame.query_selector_all("button")
#                 for btn in buttons:
#                     try:
#                         text = (await btn.inner_text()).strip().lower()
#                         if any(
#                             k in text
#                             for k in [
#                                 "continue",
#                                 "reject",
#                                 "accept",
#                                 "save preferences",
#                                 "accept all",
#                             ]
#                         ):
#                             await btn.click()
#                             print(f"Clicked cookie banner button: {text}")
#                             break
#                     except Exception:
#                         continue
#         except Exception as e:
#             print(f"Cookie banner handling error: {e}")

#         # ===== Handle sticky alerts =====
#         try:
#             await page.wait_for_timeout(1000)
#             sticky_btns = await page.query_selector_all("button")
#             for btn in sticky_btns:
#                 try:
#                     text = (await btn.inner_text()).strip().lower()
#                     if "close sticky alerts" in text:
#                         await btn.click(force=True)
#                         print("Closed sticky alerts popup.")
#                         break
#                 except Exception:
#                     continue
#         except Exception as e:
#             print(f"Sticky alert handling error: {e}")

#         # ===== Remove job alerts / step modal via JS =====
#         try:
#             await page.wait_for_timeout(2000)
#             await page.evaluate(
#                 """
#                 const modals = document.querySelectorAll(
#                     'div[style*="position: fixed"], div[class*="modal"], div[role="dialog"]'
#                 );
#                 modals.forEach(m => m.remove());
#                 """
#             )
#             print("Removed job alert / step modal via JavaScript.")
#         except Exception as e:
#             print(f"Failed to remove job alert modal: {e}")

#         # Let React fully render results
#         await page.wait_for_timeout(4000)

#         # Optional: scroll once
#         await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
#         await page.wait_for_timeout(1500)

#         # ===== Read *all* visible text and parse jobs =====
#         full_text = await get_all_text(page)

#         # Debug sample (you can comment this out later)
#         print("---- PAGE TEXT SAMPLE ----")
#         print(full_text[:800])
#         print("---- END SAMPLE ----")

#         jobs = parse_jobs_from_text(full_text)
#         print(f"Parsed {len(jobs)} job(s) from text.")

#         # ===== Try to find URLs for each job =====
#         for job in jobs:
#             url = await find_job_url(page, job["title"])
#             job["url"] = url or SEARCH_URL

#         await browser.close()
#         return jobs


# async def main():
#     while True:
#         print("🔎 Checking for jobs...")
#         jobs = await check_jobs()

#         if jobs:
#             print(f"📩 Jobs available: {len(jobs)}. Sending email...")

#             email_lines = []
#             for idx, job in enumerate(jobs, start=1):
#                 email_lines.append(f"Job {idx}")
#                 email_lines.append(f"Title: {job['title']}")
#                 if job["type"]:
#                     email_lines.append(f"Type: {job['type']}")
#                 if job["duration"]:
#                     email_lines.append(f"Duration: {job['duration']}")
#                 if job["pay"]:
#                     email_lines.append(f"Pay: {job['pay']}")
#                 if job["location"]:
#                     email_lines.append(f"Location: {job['location']}")

#                 # Brief profile line
#                 summary_parts = [
#                     job["type"],
#                     job["duration"],
#                     job["pay"],
#                     job["location"],
#                 ]
#                 summary = ", ".join(p for p in summary_parts if p)
#                 if summary:
#                     email_lines.append(f"Profile: {job['title']} – {summary}")

#                 # URL
#                 email_lines.append(f"URL: {job['url']}")
#                 email_lines.append("")  # blank line between jobs

#             send_email("\n".join(email_lines))
#             break

#         print("⏳ No jobs. Waiting before next check...")
#         await asyncio.sleep(CHECK_INTERVAL)


# if __name__ == "__main__":
#     asyncio.run(main())
# import asyncio
# from email.mime.text import MIMEText
# import smtplib
# from amazon_engine import fetch_jobs 
# from database import init_db, get_new_jobs


# # -------- CONFIG --------
# EMAIL_FROM = "wezyali@gmail.com"
# EMAIL_TO = "aliblizzard2@gmail.com"
# SMTP_SERVER = "smtp.gmail.com"
# SMTP_PORT = 587
# EMAIL_USER = "wezyali@gmail.com"
# EMAIL_PASS = "xstarmmghjatvxck"  # Gmail app password
# # # ------------------------

# # ------------------------


# def send_email(message: str) -> None:
#     msg = MIMEText(message)
#     msg["Subject"] = "Amazon Job Alert!"
#     msg["From"] = EMAIL_FROM
#     msg["To"] = EMAIL_TO

#     with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
#         server.starttls()
#         server.login(EMAIL_USER, EMAIL_PASS)
#         server.sendmail(EMAIL_FROM, [EMAIL_TO], msg.as_string())
#     print("✅ Email sent.")


# async def main():
#     init_db()
#     while True:
#         print("🔎 Checking for jobs...")
#         jobs = await fetch_jobs(headless=False)
#         new_jobs = get_new_jobs(jobs)
#         print(f"[main] Fetched {len(jobs)} job(s), {len(new_jobs)} new.")

#         if new_jobs:
#             print(f"📩 Jobs available: {len(jobs)}. Sending email...")

#             email_lines: list[str] = []
#             for idx, job in enumerate(jobs, start=1):
#                 email_lines.append(f"Job {idx}")
#                 email_lines.append(f"Title: {job['title']}")
#                 if job.get("type"):
#                     email_lines.append(f"Type: {job['type']}")
#                 if job.get("duration"):
#                     email_lines.append(f"Duration: {job['duration']}")
#                 if job.get("pay"):
#                     email_lines.append(f"Pay: {job['pay']}")
#                 if job.get("location"):
#                     email_lines.append(f"Location: {job['location']}")

#                 summary_parts = [
#                     job.get("type") or "",
#                     job.get("duration") or "",
#                     job.get("pay") or "",
#                     job.get("location") or "",
#                 ]
#                 summary = ", ".join(p for p in summary_parts if p)
#                 if summary:
#                     email_lines.append(f"Profile: {job['title']} – {summary}")

#                 email_lines.append(f"URL: {job.get('url')}")
#                 email_lines.append("")

#             send_email("\n".join(email_lines))
#             break

#         print("⏳ No jobs. Waiting before next check...")
#         CHECK_INTERVAL = 40
#         await asyncio.sleep(CHECK_INTERVAL)


# if __name__ == "__main__":
#     asyncio.run(main())

import asyncio
from email.mime.text import MIMEText
import smtplib
from typing import Dict, List

from amazon_engine import fetch_jobs
from database import (
    init_db,
    get_new_jobs,
    get_active_subscriptions,
)
from api import AREA_GROUPS  # we only use the constant, importing this is safe

# -------- CONFIG --------
CHECK_INTERVAL = 40  # seconds between checks
TEST_MODE = True     # <- set to True to test with fake jobs instead of Amazon

EMAIL_FROM = "wezyali@gmail.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_USER = "wezyali@gmail.com"
EMAIL_PASS = "xstarmmghjatvxck"  # Gmail app password
# ------------------------


def send_email(to_email: str, message: str) -> None:
    """Send an email to a single recipient."""
    msg = MIMEText(message)
    msg["Subject"] = "Amazon Job Alert!"
    msg["From"] = EMAIL_FROM
    msg["To"] = to_email

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_FROM, [to_email], msg.as_string())
    print(f"✅ Email sent to {to_email}")


def expand_preferred_locations(raw_pref: str) -> List[str]:
    """
    Turn things like:
      - "Birmingham"
      - "Birmingham / Midlands"
      - "Birmingham / Midlands; South Wales"
    into a list of location tokens in lowercase, e.g.:
      ['birmingham', 'rugeley', 'coventry', 'cardiff', 'newport', ...]
    """
    if not raw_pref:
        return []

    tokens: List[str] = []

    # split up to 3 preferences "loc1; loc2; loc3"
    parts = [p.strip() for p in raw_pref.split(";") if p.strip()]

    for part in parts:
        part_stripped = part.strip()
        part_lower = part_stripped.lower()

        # 1) Exact match to an area group label
        if part_stripped in AREA_GROUPS:
            print(f"[debug] Expanding exact area group: {part_stripped} -> {AREA_GROUPS[part_stripped]}")
            tokens.extend(AREA_GROUPS[part_stripped])
            continue

        # 2) Fuzzy match: user typed "Birmingham" but label is "Birmingham / Midlands"
        matched_group = None
        for label, towns in AREA_GROUPS.items():
            if part_lower in label.lower():  # e.g. "birmingham" in "birmingham / midlands"
                matched_group = label
                break

        if matched_group:
            print(f"[debug] Expanding fuzzy area group: {part_stripped} -> {matched_group} -> {AREA_GROUPS[matched_group]}")
            tokens.extend(AREA_GROUPS[matched_group])
        else:
            # 3) Fallback: treat it as a direct location token
            print(f"[debug] Using raw location token: {part_stripped}")
            tokens.append(part_stripped)

    # normalise + dedupe
    tokens = [t.lower() for t in tokens]
    tokens = list(dict.fromkeys(tokens))
    print(f"[debug] Final tokens for '{raw_pref}': {tokens}")
    return tokens

def job_matches_subscription(job: Dict, sub: Dict) -> bool:
    """
    Decide if a job should be sent to this subscriber based on:
    - preferred_location (area groups and/or individual locations)
    - job_type (Any, Full Time, Part Time, Fixed-term)
    """
    loc_pref_raw = sub.get("preferred_location") or ""
    job_type_pref = (sub.get("job_type") or "").strip().lower()

    job_location = (job.get("location") or "").lower()
    job_type_str = f"{job.get('type') or ''} {job.get('duration') or ''}".lower()

    # LOCATION MATCH
    tokens = expand_preferred_locations(loc_pref_raw)
    if tokens:
        if not any(tok in job_location for tok in tokens):
            return False

    # JOB TYPE MATCH
    if job_type_pref and job_type_pref != "any":
        if job_type_pref not in job_type_str:
            return False

    return True


async def run_once() -> int:
    """
    Do one full check:
    - fetch jobs (real or fake)
    - keep only new jobs (when not in TEST_MODE)
    - match new jobs to subscriptions
    - send emails
    Returns number of emails sent.
    """
    print("🔎 Checking for jobs...")

    if TEST_MODE:
    # ----- FAKE JOBS FOR TESTING -----
        jobs = [
            {
                "title": "Warehouse Operative",
                "type": "Full Time",
                "duration": "Fixed-term",
                "pay": "From £14.30",
                "location": "Coventry, United Kingdom",
                "url": "https://example.com/job1",
            },
            {
                "title": "Warehouse Operative",
                "type": "Full Time",
                "duration": "Fixed-term",
                "pay": "From £14.30",
                "location": "Swansea, Wales",
                "url": "https://example.com/job2",
            },
            {
                "title": "Warehouse Operative",
                "type": "Full Time",
                "duration": "Fixed-term",
                "pay": "From £15.00",
                "location": "London, United Kingdom",
                "url": "https://example.com/job3",
            },
        ]
        new_jobs = jobs  # in test mode, treat all as new
        print(
            f"[worker] TEST_MODE: using {len(jobs)} fake jobs, "
            f"{len(new_jobs)} new inserted into DB."
        )  

    else:
        # ----- REAL AMAZON SCRAPE -----
        jobs = await fetch_jobs(headless=False)
        new_jobs = get_new_jobs(jobs)
        print(f"[worker] Fetched {len(jobs)} job(s), {len(new_jobs)} new.")

    if not new_jobs:
        print("[worker] No new jobs this cycle.")
        return 0

    # Load all active subscriptions
    subs = get_active_subscriptions()
    if not subs:
        print("[worker] No active subscriptions. Nothing to send.")
        return 0

    # For each subscriber, collect the jobs that match their preferences
    alerts_for_email: Dict[str, List[Dict]] = {}

    for job in new_jobs:
        for sub in subs:
            if job_matches_subscription(job, sub):
                email = sub["email"]
                alerts_for_email.setdefault(email, []).append(job)

    # Build and send emails
    sent_count = 0
    for email, jobs_for_email in alerts_for_email.items():
        if not jobs_for_email:
            continue

        lines: List[str] = []
        lines.append(f"{len(jobs_for_email)} new job(s) found for your preferences.\n")

        for idx, job in enumerate(jobs_for_email, start=1):
            lines.append(f"Job {idx}")
            lines.append(f"Title: {job.get('title')}")
            if job.get("type"):
                lines.append(f"Type: {job['type']}")
            if job.get("duration"):
                lines.append(f"Duration: {job['duration']}")
            if job.get("pay"):
                lines.append(f"Pay: {job['pay']}")
            if job.get("location"):
                lines.append(f"Location: {job['location']}")

            summary_parts = [
                job.get("type") or "",
                job.get("duration") or "",
                job.get("pay") or "",
                job.get("location") or "",
            ]
            summary = ", ".join(p for p in summary_parts if p)
            if summary:
                lines.append(f"Profile: {job.get('title')} – {summary}")

            lines.append(f"URL: {job.get('url')}")
            lines.append("")

        body = "\n".join(lines)
        send_email(email, body)
        sent_count += 1

    print(f"[worker] Sent {sent_count} email(s) this cycle.")
    return sent_count


async def main():
    init_db()

    while True:
        try:
            emails_sent = await run_once()
        except Exception as e:
            print(f"Error during run: {e}")
            emails_sent = 0

        if TEST_MODE:
            # In test mode just run once
            break

        print(f"⏳ Sleeping {CHECK_INTERVAL} seconds...\n")
        await asyncio.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())
