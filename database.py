
import sqlite3, hashlib
import bcrypt

from pathlib import Path
from typing import List, Dict
from datetime import datetime

database_path = Path(__file__).with_name("jobs.db")

# --- Canonical Amazon UK locations (real sites from public lists) ---
# You can add/remove rows here later if you want.
DEFAULT_LOCATIONS = [
    # Major cities / areas (to make typing "Birmingham", "Manchester", etc. work)
    {"code": None, "name": "Birmingham", "region": "West Midlands"},
    {"code": None, "name": "Manchester", "region": "Greater Manchester"},
    {"code": None, "name": "Leeds", "region": "West Yorkshire"},
    {"code": None, "name": "London", "region": "Greater London"},
    {"code": None, "name": "Cardiff", "region": "Wales"},
    {"code": None, "name": "Swansea", "region": "Wales"},
    {"code": None, "name": "Bristol", "region": "South West"},
    {"code": None, "name": "Newport", "region": "Wales"},
    {"code": None, "name": "Glasgow", "region": "Scotland"},
    {"code": None, "name": "Edinburgh", "region": "Scotland"},
    {"code": None, "name": "Belfast", "region": "Northern Ireland"},

    # England – Midlands & North (actual FC / DS towns)
    {"code": "BHX1", "name": "Rugeley", "region": "Staffordshire"},
    {"code": "BHX2", "name": "Coalville", "region": "Leicestershire"},
    {"code": "BHX3", "name": "Daventry", "region": "Northamptonshire"},
    {"code": "BHX4", "name": "Coventry", "region": "West Midlands"},
    {"code": "BHX5", "name": "Rugby", "region": "Warwickshire"},
    {"code": "BHX8", "name": "Redditch", "region": "Worcestershire"},
    {"code": "MAN2", "name": "Warrington", "region": "Cheshire"},
    {"code": "MAN3", "name": "Bolton", "region": "Greater Manchester"},
    {"code": "MAN4", "name": "Chesterfield", "region": "Derbyshire"},
    {"code": "LBA1", "name": "Doncaster", "region": "South Yorkshire"},
    {"code": "LBA2", "name": "Doncaster (LBA2)", "region": "South Yorkshire"},
    {"code": "LBA3", "name": "Doncaster (LBA3)", "region": "South Yorkshire"},
    {"code": "LBA4", "name": "Doncaster (LBA4)", "region": "South Yorkshire"},
    {"code": "DXS1", "name": "Sheffield", "region": "South Yorkshire"},
    {"code": "NCL2", "name": "Billingham", "region": "County Durham"},
    {"code": "MME1", "name": "Darlington", "region": "County Durham"},
    {"code": "DPN1", "name": "Carlisle", "region": "Cumbria"},

    # England – South & East
    {"code": "LCY2", "name": "Tilbury", "region": "Essex"},
    {"code": "LCY3", "name": "Dartford", "region": "Kent"},
    {"code": "LCY8", "name": "Rochester", "region": "Kent"},
    {"code": "DME4", "name": "Aylesford", "region": "Kent"},
    {"code": "LTN1", "name": "Milton Keynes (Ridgmont)", "region": "Buckinghamshire"},
    {"code": "ALT1", "name": "Milton Keynes (Northfield)", "region": "Buckinghamshire"},
    {"code": "LTN7", "name": "Bedford", "region": "Bedfordshire"},

    # England – South West
    {"code": "BRS1", "name": "Bristol (BRS1)", "region": "South West"},
    {"code": "BRS2", "name": "Swindon", "region": "South West"},

    # Wales (FC / DS towns)
    {"code": "DCF1", "name": "Newport (DCF1)", "region": "Wales"},
    {"code": "CWL1", "name": "Port Talbot", "region": "Wales"},

    # Scotland
    {"code": "EDI4", "name": "Dunfermline", "region": "Scotland"},
    {"code": "DEH1", "name": "Edinburgh (DEH1)", "region": "Scotland"},
    {"code": "HEH1", "name": "Edinburgh (HEH1)", "region": "Scotland"},
    {"code": "DXG1", "name": "Glasgow (DXG1)", "region": "Scotland"},
    {"code": "DXG2", "name": "Glasgow (DXG2)", "region": "Scotland"},
    {"code": "DDD1", "name": "Dundee", "region": "Scotland"},
    {"code": "SEH1", "name": "Bathgate", "region": "Scotland"},

    # Northern Ireland – delivery stations
    {"code": None, "name": "Portadown", "region": "Northern Ireland"},
]


def init_db() -> None:
    """Create the jobs, locations and subscriptions tables if they don't exist."""
    conn = sqlite3.connect(database_path)
    cur = conn.cursor()

    # Jobs table (as before)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            type TEXT,
            duration TEXT,
            pay TEXT,
            location TEXT,
            url TEXT,
            first_seen_at TEXT,
            UNIQUE(title, location, url)
        )
        """
    )

    # NEW: canonical locations table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS locations(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT,
            name TEXT NOT NULL,
            region TEXT,
            country TEXT DEFAULT 'United Kingdom',
            active INTEGER DEFAULT 1,
            UNIQUE(name, region, code)
        )
        """
    )

    # Subscriptions table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS subscriptions(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            preferred_location TEXT,
            job_type TEXT,
            created_at TEXT,
            active INTEGER DEFAULT 1
        )
        """
    )
    #user table 
    cur.execute(
    """
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        created_at TEXT
    )
    """
    

    )

    conn.commit()
    conn.close()

    # Seed locations after tables exist
    seed_default_locations()


def seed_default_locations() -> None:
    """Insert DEFAULT_LOCATIONS into the locations table (idempotent)."""
    conn = sqlite3.connect(database_path)
    cur = conn.cursor()

    for loc in DEFAULT_LOCATIONS:
        cur.execute(
            """
            INSERT OR IGNORE INTO locations (code, name, region, country, active)
            VALUES (?, ?, ?, 'United Kingdom', 1)
            """,
            (loc.get("code"), loc["name"], loc.get("region")),
        )

    conn.commit()
    conn.close()


def get_locations() -> List[Dict]:
    """Return all active locations as a list of dicts."""
    conn = sqlite3.connect(database_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, code, name, region
        FROM locations
        WHERE active = 1
        ORDER BY name
        """
    )

    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# 🔧 REPLACE your existing get_new_jobs with THIS VERSION
def get_new_jobs(jobs: List[Dict]) -> List[Dict]:
    """
    Insert jobs into the DB and return only the ones that are NEW.

    "New" means we haven't seen a job with the same (title, location, url) before.
    """
    if not jobs:
        print("[db] get_new_jobs: no jobs passed in.")
        return []

    conn = sqlite3.connect(database_path)
    cur = conn.cursor()

    # Count BEFORE inserting
    cur.execute("SELECT COUNT(*) FROM jobs")
    before_count = cur.fetchone()[0]

    new_jobs: List[Dict] = []
    now = datetime.utcnow().isoformat(timespec="seconds")

    for job in jobs:
        title = job.get("title") or ""
        location = job.get("location") or ""
        url = job.get("url") or ""

        try:
            cur.execute(
                """
                INSERT INTO jobs (title, type, duration, pay, location, url, first_seen_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    title,
                    job.get("type"),
                    job.get("duration"),
                    job.get("pay"),
                    location,
                    url,
                    now,
                ),
            )
            # If insert succeeds, this is a new job
            new_jobs.append(job)
        except sqlite3.IntegrityError:
            # UNIQUE constraint hit -> we've seen this job before
            continue

    conn.commit()

    # Count AFTER inserting
    cur.execute("SELECT COUNT(*) FROM jobs")
    after_count = cur.fetchone()[0]
    conn.close()

    print(
        f"[db] get_new_jobs: before={before_count}, inserted={len(new_jobs)}, "
        f"after={after_count}, db={database_path.resolve()}"
    )

    return new_jobs


def add_subscription(email: str, preferred_location: str, job_type: str) -> None:
    """Add a new active subscription."""
    conn = sqlite3.connect(database_path)
    cur = conn.cursor()
    now = datetime.utcnow().isoformat(timespec="seconds")

    cur.execute(
        """
        INSERT INTO subscriptions (email, preferred_location, job_type, created_at, active)
        VALUES (?, ?, ?, ?, 1)
        """,
        (email, preferred_location, job_type, now),
    )

    conn.commit()
    conn.close()


def get_active_subscriptions() -> List[Dict]:
    """Return all active subscriptions as a list of dicts."""
    conn = sqlite3.connect(database_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, email, preferred_location, job_type
        FROM subscriptions
        WHERE active = 1
        """
    )

    rows = cur.fetchall()
    conn.close()

    return [dict(row) for row in rows]
def get_stats() -> Dict:
    """
    Return simple stats about the database:
      - total jobs
      - active subscriptions
      - active locations
    """
    conn = sqlite3.connect(database_path)
    cur = conn.cursor()

    # Jobs count
    cur.execute("SELECT COUNT(*) FROM jobs")
    jobs_count = cur.fetchone()[0]

    # Active subscriptions
    cur.execute("SELECT COUNT(*) FROM subscriptions WHERE active = 1")
    subs_count = cur.fetchone()[0]

    # Active locations
    cur.execute("SELECT COUNT(*) FROM locations WHERE active = 1")
    locs_count = cur.fetchone()[0]

    conn.close()

    return {
        "jobs": jobs_count,
        "active_subscriptions": subs_count,
        "active_locations": locs_count,
    }

def get_all_jobs(limit: int | None = None) -> List[Dict]:
    """
    Return all stored jobs as a list of dicts, newest first.
    Optional `limit` to cap how many rows we fetch.
    """
    conn = sqlite3.connect(database_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    sql = """
        SELECT id, title, type, duration, pay, location, url, first_seen_at
        FROM jobs
        ORDER BY datetime(first_seen_at) DESC, id DESC
    """
    if limit is not None:
        sql += " LIMIT ?"
        cur.execute(sql, (limit,))
    else:
        cur.execute(sql)

    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def deactivate_subscription(sub_id: int) -> None:
    """
    Mark a subscription as inactive (unsubscribe).
    """
    conn = sqlite3.connect(database_path)
    cur = conn.cursor()

    cur.execute(
        "UPDATE subscriptions SET active = 0 WHERE id = ?",
        (sub_id,),
    )

    conn.commit()
    conn.close()

# --- Simple password hashing (OK for this small tool; can swap to bcrypt later) ---

def hash_password(raw_password: str) -> str:
    """
    Hash a password using SHA256 + a static salt.

    For a personal side project this is fine.
    If you ever expose this to the public internet at scale,
    switch to bcrypt / argon2.
    """
    hashed = bcrypt.hashpw(raw_password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8") #store as text


def verify_password(raw_password: str, stored_hash: str) -> bool:
    return bcrypt.checkpw(raw_password.encode("utf-8"), stored_hash.encode("utf-8"))

def hash_password(raw_password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(raw_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")  # store as text
        

def verify_password(raw_password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(
            raw_password.encode("utf-8"),
            password_hash.encode("utf-8"),
        )
    except Exception:
        return False

def create_user(email: str, raw_password: str) -> int:
    conn = sqlite3.connect(database_path)
    cur = conn.cursor()
    now = datetime.utcnow().isoformat(timespec="seconds")

    password_hash = hash_password(raw_password)

    cur.execute(
        """
        INSERT INTO users (email, password_hash, created_at)
        VALUES (?, ?, ?)
        """,
        (email.strip().lower(), password_hash, now),
    )

    user_id = cur.lastrowid
    conn.commit()
    conn.close()
    return user_id


def get_user_by_email(email: str) -> Dict | None:
    conn = sqlite3.connect(database_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, email, password_hash, created_at
        FROM users
        WHERE email = ?
        """,
        (email.strip().lower(),),
    )
    row = cur.fetchone()
    conn.close()

    return dict(row) if row else None

from typing import List, Dict, Optional

def get_subscriptions_for_email(email: str) -> List[Dict]:
    """Return all subscriptions for a given email."""
    conn = sqlite3.connect(database_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, email, preferred_location, job_type, created_at
        FROM subscriptions
        WHERE email = ?
        ORDER BY created_at DESC
        """,
        (email.strip().lower(),),
    )

    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]
