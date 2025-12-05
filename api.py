
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from database import (
    init_db,
    add_subscription,
    get_locations,
    get_active_subscriptions,
    get_all_jobs,
    deactivate_subscription, 
    get_stats, 
    create_user,
    get_user_by_email,
    get_subscriptions_for_email,
    verify_password

)

# ----- AREA GROUPS (regions -> list of towns/warehouses) -----
AREA_GROUPS = {
    # Midlands – around Birmingham / Coventry / Stoke
    "Birmingham / Midlands": [
        "Birmingham",
        "Rugeley",
        "Coalville",
        "Daventry",
        "Coventry",
        "Rugby",
        "Hinckley",
        "Redditch",
        "Stoke-on-Trent",
        "Wednesbury",
        "Mansfield",
        "Eastwood",
        "Kegworth",
        "Northampton",
        "Banbury",
        "Burton-on-Trent",
    ],

    # North West England
    "Manchester / North West": [
        "Manchester",
        "Warrington",
        "Bolton",
        "Haydock",
        "Rochdale",
        "Carlisle",
        "Stoke-on-Trent",
    ],

    # Yorkshire & Humber
    "Leeds / Yorkshire": [
        "Leeds",
        "Doncaster",
        "Wakefield",
        "Sheffield",
        "Hull",
        "North Ferriby",
    ],

    # North East England
    "Newcastle / North East": [
        "Newcastle upon Tyne",
        "Gateshead",
        "Durham",
        "Sunderland",
        "Darlington",
        "Billingham",
    ],

    # London – inner
    "London (inner)": [
        "London",
        "Barking",
        "Croydon",
        "Enfield",
        "Bexley",
        "Neasden",
        "Orpington",
    ],

    # London commuter belt / South East
    "London commuter belt / South East": [
        "Tilbury",
        "Dartford",
        "Rochester",
        "Aylesford",
        "Harlow",
        "Grays",
        "Weybridge",
    ],

    # East of England
    "East of England": [
        "Bedford",
        "Milton Keynes",
        "Ridgmont",
        "Dunstable",
        "Peterborough",
        "Norwich",
        "Ipswich",
        "Cambridge",
    ],

    # South West
    "South West": [
        "Bristol",
        "Swindon",
        "Exeter",
        "Plymouth",
    ],

    # Wales – mostly South Wales belt
    "South Wales": [
        "Cardiff",
        "Newport",
        "Port Talbot",
        "Swansea",
        "Garden City",
    ],

    # Scotland – Central belt + Dundee
    "Glasgow / Edinburgh": [
        "Glasgow",
        "Edinburgh",
        "Dunfermline",
        "Bathgate",
        "Dundee",
    ],

    # Northern Ireland
    "Northern Ireland": [
        "Belfast",
        "Portadown",
    ],
}

app = FastAPI()


@app.on_event("startup")
def on_startup():
    # ensures jobs, locations, subscriptions tables exist & locations are seeded
    init_db()


@app.get("/", response_class=HTMLResponse)
def index():
    # Use locations + AREA_GROUPS exactly as before
    locations = get_locations()

    options = []

    # 1) Area groups first (e.g. "Birmingham / Midlands – ...")
    for label, towns in AREA_GROUPS.items():
        towns_label = ", ".join(towns)
        options.append(
            f'<option value="{label}">{label} – {towns_label}</option>'
        )

    # 2) Individual locations from DB (Rugeley, Coventry, etc.)
    for loc in locations:
        label = loc["name"]
        code = loc.get("code")
        region = loc.get("region") or ""
        extra = []
        if code:
            extra.append(code)
        if region:
            extra.append(region)
        if extra:
            label = f"{label} ({', '.join(extra)})"

        options.append(f'<option value="{loc["name"]}">{label}</option>')

    options_html = "\n".join(options)

    return f"""
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="utf-8" />
        <title>Amazon Job Alerts</title>
        <style>
          body {{
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            max-width: 700px;
            margin: 2rem auto;
            padding: 1rem;
            background: #020617;
            color: #e5e7eb;
          }}
          h1 {{
            margin-bottom: 0.5rem;
          }}
          p.lead {{
            margin-bottom: 1.5rem;
            color: #9ca3af;
          }}
          label {{
            display: block;
            margin-top: 1rem;
            font-size: 0.95rem;
          }}
          input, select {{
            width: 100%;
            padding: 0.5rem;
            margin-top: 0.25rem;
            border-radius: 0.375rem;
            border: 1px solid #4b5563;
            background: #020617;
            color: #e5e7eb;
          }}
          button {{
            margin-top: 1.5rem;
            padding: 0.75rem 1.5rem;
            border-radius: 0.5rem;
            border: none;
            background: #22c55e;
            color: #022c22;
            font-weight: 600;
            cursor: pointer;
          }}
          button:hover {{
            background: #16a34a;
          }}
          a {{
            color: #38bdf8;
          }}
          .nav-links {{
            margin-top: 1.5rem;
            font-size: 0.9rem;
          }}
        </style>
      </head>
      <body>
        <h1>Amazon Job Alerts</h1>
        <p class="lead">
          Create an account with email + password and choose up to three preferred areas.
          Start typing, e.g. "Birmingham", "Coventry", "Swansea".
        </p>

        <form action="/subscribe" method="post">
          <label>
            Email:
            <input type="email" name="email" required />
          </label>

          <label>
            Password:
            <input type="password" name="password" required />
          </label>

          <label>
            Confirm password:
            <input type="password" name="password2" required />
          </label>

          <label>
            Preferred location 1:
            <input list="locations" name="preferred_location1"
                   placeholder="e.g. Birmingham / Midlands" />
          </label>

          <label>
            Preferred location 2 (optional):
            <input list="locations" name="preferred_location2"
                   placeholder="e.g. South Wales" />
          </label>

          <label>
            Preferred location 3 (optional):
            <input list="locations" name="preferred_location3"
                   placeholder="e.g. Glasgow / Edinburgh" />
          </label>

          <datalist id="locations">
            {options_html}
          </datalist>

          <label>
            Job type:
            <select name="job_type">
              <option value="Any">Any</option>
              <option value="Full Time">Full Time</option>
              <option value="Part Time">Part Time</option>
              <option value="Fixed-term">Fixed-term</option>
            </select>
          </label>

          <button type="submit">Start alerts</button>
        </form>

        <div class="nav-links">
          <p><a href="/subscriptions">📧 View subscriptions</a></p>
          <p><a href="/jobs">📦 View stored jobs</a></p>
        </div>
      </body>
    </html>
    """

@app.post("/subscribe", response_class=HTMLResponse)
def subscribe(
    email: str = Form(...),
    password: str = Form(...),
    password2: str = Form(...),
    preferred_location1: str = Form(""),
    preferred_location2: str = Form(""),
    preferred_location3: str = Form(""),
    job_type: str = Form("Any"),
):
    # 1) basic password check
    if password != password2:
        return """
        <html>
          <head><title>Error</title></head>
          <body>
            <h1>Passwords do not match ❌</h1>
            <p><a href="/">Go back</a></p>
          </body>
        </html>
        """

    # 2) Upsert user in users table
    existing = get_user_by_email(email)
    if existing is None:
        # user does not exist yet → create
        try:
            create_user(email, password)
        except Exception as e:
            # e.g. race / duplicate, just show simple message
            return f"""
            <html>
              <head><title>Error</title></head>
              <body>
                <h1>Could not create user ❌</h1>
                <p>{str(e)}</p>
                <p><a href="/">Go back</a></p>
              </body>
            </html>
            """

    # 3) Combine up to three preferences into one string stored in DB
    locs = [
        preferred_location1.strip(),
        preferred_location2.strip(),
        preferred_location3.strip(),
    ]
    locs = [l for l in locs if l]
    combined_locations = "; ".join(locs)  # e.g. "Birmingham / Midlands; South Wales"

    # 4) Store subscription (same as before)
    add_subscription(email, combined_locations, job_type)

    return f"""
    <html>
      <head>
        <title>Subscribed</title>
      </head>
      <body>
        <h1>You're subscribed ✅</h1>
        <p>Email (and account): <strong>{email}</strong></p>
        <p>Preferred locations: <strong>{combined_locations or "Any"}</strong></p>
        <p>Job type: <strong>{job_type}</strong></p>
        <p>You will start receiving alerts when matching jobs are found.</p>
        <p><a href="/">Back to form</a></p>
        <p><a href="/subscriptions">View all subscriptions</a></p>
      </body>
    </html>
    """

@app.get("/jobs", response_class=HTMLResponse)
def list_jobs():
    # Show most recent 100 jobs; adjust if you want more/less
    jobs = get_all_jobs(limit=100)

    rows_html = ""
    for j in jobs:
        url = j.get("url") or "#"
        rows_html += f"""
        <tr>
          <td>{j.get('id')}</td>
          <td>{j.get('title')}</td>
          <td>{j.get('location') or ''}</td>
          <td>{j.get('type') or ''}</td>
          <td>{j.get('duration') or ''}</td>
          <td>{j.get('pay') or ''}</td>
          <td><a href="{url}" target="_blank">View</a></td>
          <td>{j.get('first_seen_at') or ''}</td>
        </tr>
        """

    if not jobs:
        rows_html = '<tr><td colspan="8">No jobs stored yet.</td></tr>'

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Stored Jobs</title>
        <meta charset="utf-8" />
        <style>
          body {{
              font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
              max-width: 1100px;
              margin: 2rem auto;
              padding: 1rem;
              background: #0f172a;
              color: #e5e7eb;
          }}
          h1 {{
              margin-bottom: 1rem;
          }}
          table {{
              width: 100%;
              border-collapse: collapse;
              margin-top: 1rem;
              background: #020617;
              font-size: 0.9rem;
          }}
          th, td {{
              border: 1px solid #1f2937;
              padding: 0.4rem 0.6rem;
              vertical-align: top;
          }}
          th {{
              background: #111827;
              text-align: left;
              white-space: nowrap;
          }}
          tr:nth-child(even) td {{
              background: #020617;
          }}
          a {{
              color: #38bdf8;
          }}
          .nav {{
              margin-bottom: 0.75rem;
              font-size: 0.9rem;
          }}
          .nav a {{
              margin-right: 0.75rem;
          }}
        </style>
    </head>
    <body>
        <h1>Stored Jobs</h1>
        <div class="nav">
          <a href="/">⬅ Subscription form</a>
          <a href="/subscriptions">📧 Subscriptions</a>
          <a href="/jobs">📦 Jobs</a>
        </div>

        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Title</th>
              <th>Location</th>
              <th>Type</th>
              <th>Duration</th>
              <th>Pay</th>
              <th>Link</th>
              <th>First seen</th>
            </tr>
          </thead>
          <tbody>
            {rows_html}
          </tbody>
        </table>
    </body>
    </html>
    """

    return HTMLResponse(content=html)



@app.get("/subscriptions", response_class=HTMLResponse)
def list_subscriptions():
    subs = get_active_subscriptions()

    rows_html = ""
    for s in subs:
        rows_html += f"""
        <tr>
          <td>{s.get('id')}</td>
          <td>{s.get('email')}</td>
          <td>{s.get('preferred_location') or ''}</td>
          <td>{s.get('job_type') or ''}</td>
          <td>
            <a href="/subscriptions/{s.get('id')}/deactivate"
               onclick="return confirm('Deactivate this subscription?');">
               Deactivate
            </a>
          </td>
        </tr>
        """

    if not subs:
        rows_html = '<tr><td colspan="5">No active subscriptions.</td></tr>'

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Subscriptions</title>
        <meta charset="utf-8" />
        <style>
          body {{
              font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
              max-width: 900px;
              margin: 2rem auto;
              padding: 1rem;
              background: #020617;
              color: #e5e7eb;
          }}
          h1 {{
              margin-bottom: 1rem;
          }}
          table {{
              width: 100%;
              border-collapse: collapse;
              margin-top: 1rem;
              background: #020617;
              font-size: 0.9rem;
          }}
          th, td {{
              border: 1px solid #1f2937;
              padding: 0.4rem 0.6rem;
              vertical-align: top;
          }}
          th {{
              background: #111827;
              text-align: left;
          }}
          tr:nth-child(even) td {{
              background: #020617;
          }}
          a {{
              color: #38bdf8;
          }}
          .nav {{
              margin-bottom: 0.75rem;
              font-size: 0.9rem;
          }}
          .nav a {{
              margin-right: 0.75rem;
          }}
        </style>
    </head>
    <body>
        <h1>Active Subscriptions</h1>
        <div class="nav">
          <a href="/">⬅ Subscription form</a>
          <a href="/subscriptions">📧 Subscriptions</a>
          <a href="/jobs">📦 Jobs</a>
        </div>

        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Email</th>
              <th>Preferred locations</th>
              <th>Job type</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {rows_html}
          </tbody>
        </table>
    </body>
    </html>
    """

    return HTMLResponse(content=html)

@app.get("/subscriptions/{sub_id}/deactivate")
def deactivate_subscription_route(sub_id: int):
    deactivate_subscription(sub_id)
    # Redirect back to the subscriptions list
    return RedirectResponse(url="/subscriptions", status_code=303)

@app.get("/health")
def health():
    """
    Basic health check for the app.

    Returns JSON with:
      - status: "ok" if DB is reachable
      - stats: counts of jobs, subscriptions, locations
    """
    try:
        stats = get_stats()
        return {
            "status": "ok",
            "stats": stats,
        }
    except Exception as e:
        # If something is wrong (e.g. DB missing), return an error payload
        return {
            "status": "error",
            "detail": str(e),
        }
        


@app.get("/my-alerts", response_class=HTMLResponse)
def my_alerts_form():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8" />
      <title>My Amazon Alerts – Login</title>
    </head>
    <body>
      <h1>My Amazon Alerts</h1>
      <form method="post" action="/my-alerts">
        <label>Email</label><br />
        <input type="email" name="email" required /><br /><br />

        <label>Password</label><br />
        <input type="password" name="password" required /><br /><br />

        <button type="submit">View my alerts</button>
      </form>

      <p><a href="/">⬅ Back to subscription form</a></p>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.post("/my-alerts", response_class=HTMLResponse)
def my_alerts(email: str = Form(...), password: str = Form(...)):
    user = get_user_by_email(email)
    if not user or not verify_password(password, user["password_hash"]):
        return HTMLResponse(
            content="""
            <html><body>
              <h1>My Amazon Alerts</h1>
              <p style="color:red;">Invalid email or password.</p>
              <p><a href="/my-alerts">Try again</a></p>
            </body></html>
            """,
            status_code=401,
        )

    subs = get_subscriptions_for_email(email)

    rows_html = ""
    for s in subs:
        rows_html += f"""
        <tr>
          <td>{s.get('id')}</td>
          <td>{s.get('preferred_location') or ''}</td>
          <td>{s.get('job_type') or ''}</td>
          <td>{s.get('created_at') or ''}</td>
        </tr>
        """

    if not rows_html:
        rows_html = '<tr><td colspan="4">No alerts yet.</td></tr>'

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8" />
      <title>My Amazon Alerts</title>
    </head>
    <body>
      <h1>My Amazon Alerts</h1>
      <p>Logged in as: <strong>{email}</strong></p>
      <p><a href="/">⬅ Back to subscription form</a></p>

      <table border="1" cellspacing="0" cellpadding="4">
        <thead>
          <tr>
            <th>ID</th>
            <th>Preferred locations</th>
            <th>Job type</th>
            <th>Created</th>
          </tr>
        </thead>
        <tbody>
          {rows_html}
        </tbody>
      </table>
    </body>
    </html>
    """

    return HTMLResponse(content=html)
