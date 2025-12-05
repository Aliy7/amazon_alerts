import re
from typing import List, Dict

from playwright.async_api import async_playwright

SEARCH_URL = "https://www.jobsatamazon.co.uk/app#/jobSearch"


async def _get_all_text(page) -> str:
    """Return combined innerText from all frames."""
    chunks = []
    for frame in page.frames:
        try:
            text = await frame.evaluate(
                "() => document.body ? document.body.innerText : ''"
            )
            if text:
                chunks.append(text)
        except Exception:
            continue
    return "\n".join(chunks)


def _parse_jobs_from_text(text: str) -> List[Dict]:
    """
    Parse page text into a list of job dicts:
    {title, type, duration, pay, location, url}
    """
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    jobs: List[Dict] = []

    # Only bother if the page actually says "X job(s) found"
    joined = "\n".join(lines)
    m = re.search(r"(\d+)\s+job(?:s)?\s+found", joined, re.IGNORECASE)
    if not m:
        return []

    for i, line in enumerate(lines):
        if "Type:" not in line:
            continue

        # Title is usually just above "Type:"
        title = lines[i - 1] if i > 0 else "Unknown role"

        job_type = ""
        duration = ""
        pay = ""
        location = ""

        # Extract "Type:" from this line
        parts = line.split("Type:", 1)
        if len(parts) > 1:
            job_type = parts[1].strip()

        # Look ahead a few lines for duration, pay, location
        for k in range(i + 1, min(i + 8, len(lines))):
            l = lines[k]

            if "Duration:" in l:
                duration = l.split("Duration:", 1)[1].strip()
                continue
            if "Pay rate:" in l:
                pay = l.split("Pay rate:", 1)[1].strip()
                continue

            # Heuristic for location: line after pay, or any line that looks like "Town, Region"
            if not location and ("," in l or "United Kingdom" in l or "UK" in l):
                location = l.strip()

        jobs.append(
            {
                "title": title,
                "type": job_type,
                "duration": duration,
                "pay": pay,
                "location": location,
                "url": None,  # to fill later
            }
        )

    # Deduplicate by (title, location)
    unique: Dict[tuple, Dict] = {}
    for j in jobs:
        key = (j["title"], j["location"])
        if key not in unique:
            unique[key] = j

    return list(unique.values())


async def _find_job_url(page, title: str) -> str | None:
    """
    Try to find a clickable link for the job title in the DOM.
    If found, return href. Otherwise, return None.
    """
    try:
        locator = page.locator(f"text={title}")
        count = await locator.count()
        if count == 0:
            return None

        first = locator.nth(0)
        handle = await first.element_handle()
        if not handle:
            return None

        href = await handle.evaluate(
            "node => (node.closest('a') && node.closest('a').href) || ''"
        )
        href = (href or "").strip()
        if href:
            return href
    except Exception:
        pass

    return None


import re
from typing import List, Dict
from playwright.async_api import async_playwright

SEARCH_URL = "https://www.jobsatamazon.co.uk/app#/jobSearch"

# ... keep your _get_all_text, _parse_jobs_from_text, _find_job_url as they are ...


async def fetch_jobs(headless: bool = False) -> List[Dict]:
    """
    High-level engine function:
    - Opens the Amazon jobs page with Playwright
    - Handles cookies / sticky alerts / modals
    - Extracts visible text
    - Parses jobs into structured dicts
    - Returns: list of jobs
    """
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=headless)
            context = await browser.new_context(permissions=[])
            page = await context.new_page()

            print("[engine] Loading page...")
            await page.goto(SEARCH_URL, wait_until="domcontentloaded")

            # ===== Handle cookie banner =====
            try:
                await page.wait_for_timeout(3000)
                for frame in page.frames:
                    buttons = await frame.query_selector_all("button")
                    for btn in buttons:
                        try:
                            text = (await btn.inner_text()).strip().lower()
                            if any(
                                k in text
                                for k in [
                                    "continue",
                                    "reject",
                                    "accept",
                                    "save preferences",
                                    "accept all",
                                ]
                            ):
                                await btn.click()
                                print(
                                    f"[engine] Clicked cookie banner button: {text}"
                                )
                                break
                        except Exception:
                            continue
            except Exception as e:
                print(f"[engine] Cookie banner handling error: {e}")

            # ===== Handle sticky alerts =====
            try:
                await page.wait_for_timeout(1000)
                sticky_btns = await page.query_selector_all("button")
                for btn in sticky_btns:
                    try:
                        text = (await btn.inner_text()).strip().lower()
                        if "close sticky alerts" in text:
                            await btn.click(force=True)
                            print("[engine] Closed sticky alerts popup.")
                            break
                    except Exception:
                        continue
            except Exception as e:
                print(f"[engine] Sticky alert handling error: {e}")

            # ===== Remove job alerts / step modal via JS =====
            try:
                await page.wait_for_timeout(2000)
                await page.evaluate(
                    """
                    const modals = document.querySelectorAll(
                        'div[style*="position: fixed"], div[class*="modal"], div[role="dialog"]'
                    );
                    modals.forEach(m => m.remove());
                    """
                )
                print("[engine] Removed job alert / step modal via JavaScript.")
            except Exception as e:
                print(f"[engine] Failed to remove job alert modal: {e}")

            # Let React fully render results
            try:
                await page.wait_for_timeout(4000)
            except Exception as e:
                print(f"[engine] Error during wait/render: {e}")

            # Optional: scroll once
            try:
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(1500)
            except Exception as e:
                print(f"[engine] Error during scroll: {e}")

            # ===== Extract and parse jobs =====
            try:
                full_text = await _get_all_text(page)
            except Exception as e:
                print(f"[engine] Error getting page text: {e}")
                full_text = ""

            jobs = _parse_jobs_from_text(full_text)
            print(f"[engine] Parsed {len(jobs)} job(s) from text.")

            # ===== Try to find URLs for each job =====
            for job in jobs:
                try:
                    url = await _find_job_url(page, job["title"])
                except Exception as e:
                    print(f"[engine] Error finding URL for {job['title']}: {e}")
                    url = None
                job["url"] = url or SEARCH_URL

            await browser.close()
            return jobs

    except Exception as e:
        # If the browser/page was closed unexpectedly (TargetClosedError, etc.)
        print(f"[engine] Fatal error in fetch_jobs (returning 0 jobs): {e}")
        return []
