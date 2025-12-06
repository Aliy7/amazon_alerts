
from fastapi import FastAPI, Form, Request
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
    verify_password, 
    create_session,
    get_session,
    touch_session,
    delete_session,
    get_user_by_id

)

SESSION_COOKIE_NAME = "session_id"


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
def index(request: Request):
    # who is logged in (if anyone)
    user = get_current_user(request)

    locations = get_locations()
    options = []

    # 1) Area groups first
    for label, towns in AREA_GROUPS.items():
        towns_label = ", ".join(towns)
        options.append(
            f'<option value="{label}">{label} – {towns_label}</option>'
        )

    # 2) Individual locations from DB
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

    body = f"""
      <div class="card">
        <h1>Amazon Job Alerts</h1>
        <p class="muted">
          Create an account with email + password and choose up to three preferred areas.
          Start typing, e.g. "Birmingham", "Coventry", "Swansea".
        </p>

        <form action="/subscribe" method="post">
          <label>
            Email
            <input type="email" name="email" required />
          </label>

          <label>
            Password
            <input type="password" name="password" required />
          </label>

          <label>
            Confirm password
            <input type="password" name="password2" required />
          </label>

          <label>
            Preferred location 1
            <input list="locations" name="preferred_location1"
                   placeholder="e.g. Birmingham / Midlands" />
          </label>

          <label>
            Preferred location 2 (optional)
            <input list="locations" name="preferred_location2"
                   placeholder="e.g. South Wales" />
          </label>

          <label>
            Preferred location 3 (optional)
            <input list="locations" name="preferred_location3"
                   placeholder="e.g. Glasgow / Edinburgh" />
          </label>

          <datalist id="locations">
            {options_html}
          </datalist>

          <label>
            Job type
            <select name="job_type">
              <option value="Any">Any</option>
              <option value="Full Time">Full Time</option>
              <option value="Part Time">Part Time</option>
              <option value="Fixed-term">Fixed-term</option>
            </select>
          </label>

          <button type="submit">Start alerts</button>
        </form>

        <p class="muted" style="margin-top:1.5rem;">
          Admin views:
          <a href="/subscriptions">subscriptions</a> ·
          <a href="/jobs">jobs</a>
        </p>
      </div>
    """

    return render_page("Amazon Job Alerts", body, user)



def render_page(title: str, body: str, user: dict | None = None) -> HTMLResponse:
    """
    Shared layout: dark background, nav bar, and optional 'signed in as' line.
    """
    if user:
        auth_links = """
          <a href="/dashboard">📋 My alerts</a>
          <a href="/logout">🚪 Logout</a>
        """
        signed_in_text = f'Signed in as <strong>{user.get("email")}</strong>'
    else:
        auth_links = """
          <a href="/login">🔑 Login</a>
        """
        signed_in_text = "Not signed in"

    html = f"""
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="utf-8" />
        <title>{title}</title>
        <style>
          :root {{
            color-scheme: dark;
          }}
          * {{
            box-sizing: border-box;
          }}
          body {{
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            margin: 0;
            padding: 0;
            background: #020617;
            color: #e5e7eb;
          }}
          .page {{
            max-width: 960px;
            margin: 0 auto;
            padding: 1.5rem 1rem 3rem;
          }}
          header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.5rem;
          }}
          header h1 {{
            font-size: 1.4rem;
            margin: 0;
          }}
          nav a {{
            margin-right: 0.75rem;
            text-decoration: none;
            color: #e5e7eb;
            font-size: 0.9rem;
          }}
          nav a:hover {{
            color: #38bdf8;
          }}
          .signed-in {{
            font-size: 0.8rem;
            color: #9ca3af;
            margin-top: 0.25rem;
          }}
          main {{
            margin-top: 1rem;
          }}
          a {{
            color: #38bdf8;
          }}
          .card {{
            background: #020617;
            border-radius: 0.75rem;
            border: 1px solid #1f2937;
            padding: 1rem 1.25rem;
            box-shadow: 0 10px 30px rgba(15, 23, 42, 0.5);
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
          .muted {{
            color: #9ca3af;
            font-size: 0.85rem;
          }}
          .stats {{
            display: flex;
            gap: 0.75rem;
            margin-bottom: 1rem;
            flex-wrap: wrap;
          }}
          .stat {{
            flex: 0 0 140px;
            padding: 0.6rem 0.8rem;
            border-radius: 0.75rem;
            border: 1px solid #1f2937;
            background: #020617;
          }}
          .stat .label {{
            font-size: 0.75rem;
            color: #9ca3af;
          }}
          .stat .value {{
            font-size: 1.2rem;
            font-weight: 600;
          }}
        </style>
      </head>
      <body>
        <div class="page">
          <header>
            <div>
              <h1>{title}</h1>
              <div class="signed-in">{signed_in_text}</div>
            </div>
            <nav>
              <a href="/">🏠 Home</a>
              <a href="/jobs">📦 Jobs</a>
              <a href="/subscriptions">📧 Subscriptions</a>
              {auth_links}
            </nav>
          </header>
          <main>
            {body}
          </main>
        </div>
      </body>
    </html>
    """
    return HTMLResponse(content=html)
@app.get("/jobs", response_class=HTMLResponse)
def list_jobs(request: Request):
    user = get_current_user(request)
    jobs = get_all_jobs(limit=100)

    rows_html = ""
    for j in jobs:
        url = j.get("url") or "#"
        rows_html += f"""
        <tr>
          <td>{j.get('id')}</td>
          <td>{j.get('title') or ''}</td>
          <td>{j.get('location') or ''}</td>
          <td>{j.get('type') or ''}</td>
          <td>{j.get('duration') or ''}</td>
          <td>{j.get('pay') or ''}</td>
          <td>{j.get('first_seen_at') or ''}</td>
          <td><a href="{url}" target="_blank">View</a></td>
        </tr>
        """

    if not jobs:
        rows_html = '<tr><td colspan="8">No jobs stored yet.</td></tr>'

    body = f"""
    <div class="card">
      <h2>Stored jobs</h2>
      <p class="muted">
        Showing the most recent {len(jobs)} jobs currently in the database.
      </p>
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Title</th>
            <th>Location</th>
            <th>Type</th>
            <th>Duration</th>
            <th>Pay</th>
            <th>First seen</th>
            <th>Link</th>
          </tr>
        </thead>
        <tbody>
          {rows_html}
        </tbody>
      </table>
    </div>
    """

    return render_page("Stored Jobs – Amazon Job Alerts", body, user=user)

@app.post("/subscribe")
def subscribe(
    email: str = Form(...),
    password: str = Form(...),
    password2: str = Form(...),
    preferred_location1: str = Form(""),
    preferred_location2: str = Form(""),
    preferred_location3: str = Form(""),
    job_type: str = Form("Any"),
):
    # 1) password confirmation
    if password != password2:
        return HTMLResponse(
            content="""
            <html>
              <head><title>Error</title></head>
              <body>
                <h1>Passwords do not match ❌</h1>
                <p><a href="/">Go back</a></p>
              </body>
            </html>
            """,
            status_code=400,
        )

    # 2) create or reuse user
    user = get_user_by_email(email)
    if user is None:
        # new account
        user_id = create_user(email, password)
    else:
        # existing account – make sure password is correct
        if not verify_password(password, user["password_hash"]):
            return HTMLResponse(
                content="""
                <html>
                  <head><title>Error</title></head>
                  <body>
                    <h1>Account already exists ❌</h1>
                    <p>The email is already registered, but the password is wrong.</p>
                    <p>Please either use the correct password on the form, or log in via
                    <a href="/login">the login page</a>.</p>
                    <p><a href="/">Back to form</a></p>
                  </body>
                </html>
                """,
                status_code=401,
            )
        user_id = user["id"]

    # 3) combine locations
    locs = [
        preferred_location1.strip(),
        preferred_location2.strip(),
        preferred_location3.strip(),
    ]
    locs = [l for l in locs if l]
    combined_locations = "; ".join(locs)

    # 4) store subscription
    add_subscription(email, combined_locations, job_type)

    # 5) create session + cookie
    session_token = create_session(user_id)

    resp = RedirectResponse(url="/dashboard", status_code=303)
    resp.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_token,
        httponly=True,
        max_age=1800,   # 30 minutes
        samesite="lax",
    )
    return resp


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
        

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    subs = get_subscriptions_for_email(user["email"])
    stats = get_stats()

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
        rows_html = '<tr><td colspan="4">No alerts yet. Create one on the home page.</td></tr>'

    body = f"""
    <div class="stats">
      <div class="stat">
        <div class="label">Your alerts</div>
        <div class="value">{len(subs)}</div>
      </div>
      <div class="stat">
        <div class="label">All active subscriptions</div>
        <div class="value">{stats.get("active_subscriptions", 0)}</div>
      </div>
      <div class="stat">
        <div class="label">Jobs stored</div>
        <div class="value">{stats.get("jobs", 0)}</div>
      </div>
    </div>

    <div class="card">
      <p class="muted">These are the alerts currently attached to your account.</p>
      <table>
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
    </div>
    """

    return render_page("My Amazon Alerts", body, user=user)

def get_current_user(request: Request) -> dict | None:
    """
    Read session_id cookie and return the user dict (or None).
    Also refreshes the 30-minute inactivity timeout.
    """
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        return None

    session = get_session(token)
    if not session:
        return None

    user = get_user_by_id(session["user_id"])
    if not user:
        # Session points to missing user; clean it up
        delete_session(token)
        return None

    # refresh inactivity timeout
    touch_session(token)
    return user

@app.get("/login", response_class=HTMLResponse)
def login_form():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8" />
      <title>Login – Amazon Job Alerts</title>
    </head>
    <body>
      <h1>Login</h1>
      <form method="post" action="/login">
        <label>Email</label><br />
        <input type="email" name="email" required /><br /><br />

        <label>Password</label><br />
        <input type="password" name="password" required /><br /><br />

        <button type="submit">Login</button>
      </form>

      <p><a href="/">⬅ Back to subscription form</a></p>
    </body>
    </html>
    """
    return HTMLResponse(content=html)
@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    user = get_current_user(request)
    body = """
    <div class="card">
      <p class="muted">Log in to view or manage your alerts.</p>
      <form method="post" action="/login">
        <label>Email</label>
        <input type="email" name="email" required />

        <label>Password</label>
        <input type="password" name="password" required />

        <button type="submit">Login</button>
      </form>
    </div>
    """
    return render_page("Login – Amazon Job Alerts", body, user=user)
