# from fastapi import FastAPI, Form
# from fastapi.responses import HTMLResponse

# from database import init_db, add_subscription, get_locations

# app = FastAPI()

# AREA_GROUPS = {
#     # --- Midlands / Birmingham orbit ---
#     "Birmingham area": [
#         "Birmingham",
#         "Rugeley",
#         "Coalville",
#         "Lutterworth",
#         "Rugby",
#         "Coventry",
#         "Redditch",
#         "Wednesbury",
#         "Droitwich",
#         "Stoke-on-Trent",
#         "Derby",
#         "Nottingham",
#         "Mansfield",
#         "Eastwood",
#         "Wellingborough",
#     ],

#     # --- North West / Manchester orbit ---
#     "Manchester / North West": [
#         "Manchester",
#         "Altrincham",
#         "Heywood",
#         "Warrington",
#         "Bolton",
#         "Chesterfield",
#         "St Helens",
#         "Haydock",
#         "Widnes",
#         "Runcorn",
#         "Liverpool",
#         "Leyland",
#         "Carlisle",
#     ],

#     # --- Yorkshire & Humber cluster ---
#     "Yorkshire & Humber": [
#         "Doncaster",
#         "Leeds",
#         "Sheffield",
#         "Rotherham",
#         "Barnsley",
#     ],

#     # --- North East England cluster ---
#     "North East England": [
#         "Sunderland",
#         "Gateshead",
#         "Durham",
#         "Darlington",
#         "Newcastle upon Tyne",
#         "Teesside",
#         "Middlesbrough",
#     ],

#     # --- London / South East belt ---
#     "London & South East": [
#         "London",
#         "Croydon",
#         "Enfield",
#         "Tilbury",
#         "Dartford",
#         "Rochester",
#         "Banbury",
#         "Fareham",
#         "Welwyn Garden City",
#         "Bury St Edmunds",
#         "Norwich",
#         "Peterborough",
#     ],

#     # --- Milton Keynes / Bedford belt (M1 corridor) ---
#     "Milton Keynes & Bedford": [
#         "Milton Keynes",
#         "Ridgmont",
#         "Dunstable",
#         "Bedford",
#         "Wootton",
#     ],

#     # --- South West England cluster ---
#     "South West England": [
#         "Bristol",
#         "Severn Beach",
#         "Avonmouth",
#         "Swindon",
#         "Exeter",
#     ],

#     # --- South Wales & North Wales FCs/DSs ---
#     "South Wales": [
#         "Cardiff",
#         "Newport",
#         "Port Talbot",
#         "Swansea",
#     ],
#     "North Wales / Deeside": [
#         "Garden City",
#         "Deeside",
#     ],

#     # --- Central Scotland / Central Belt ---
#     "Central Scotland": [
#         "Glasgow",
#         "Gourock",
#         "Edinburgh",
#         "Bathgate",
#         "Dunfermline",
#         "Dundee",
#     ],

#     # --- Northern Ireland ---
#     "Northern Ireland": [
#         "Belfast",
#         "Portadown",
#     ],
# }


# @app.on_event("startup")
# def on_startup():
#     init_db()


# @app.get("/", response_class=HTMLResponse)
# def index():
#     locations = get_locations()

#     options = []
#     for loc in locations:
#         label = loc["name"]
#         code = loc.get("code")
#         region = loc.get("region") or ""
#         extra = []
#         if code:
#             extra.append(code)
#         if region:
#             extra.append(region)
#         if extra:
#             label = f"{label} ({', '.join(extra)})"
#         # value is just the location name; label adds context
#         options.append(f'<option value="{loc["name"]}">{label}</option>')

#     options_html = "\n".join(options)

#     return f"""
#     <html>
#       <head>
#         <title>Amazon Job Alerts</title>
#         <style>
#           body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 2rem auto; }}
#           label {{ display: block; margin-top: 1rem; }}
#           input, select {{ width: 100%; padding: 0.5rem; margin-top: 0.25rem; }}
#           button {{ margin-top: 1.5rem; padding: 0.75rem 1.5rem; }}
#         </style>
#       </head>
#       <body>
#         <h1>Amazon Job Alerts</h1>
#         <p>Choose up to three preferred areas. Start typing, e.g. "Birmingham", "Coventry", "Swansea".</p>

#         <form action="/subscribe" method="post">
#           <label>
#             Email:
#             <input type="email" name="email" required />
#           </label>

#           <label>
#             Preferred location 1:
#             <input list="locations" name="preferred_location1"
#                    placeholder="e.g. Birmingham" />
#           </label>

#           <label>
#             Preferred location 2 (optional):
#             <input list="locations" name="preferred_location2"
#                    placeholder="e.g. Coventry" />
#           </label>

#           <label>
#             Preferred location 3 (optional):
#             <input list="locations" name="preferred_location3"
#                    placeholder="e.g. Swansea" />
#           </label>

#           <datalist id="locations">
#             {options_html}
#           </datalist>

#           <label>
#             Job type:
#             <select name="job_type">
#               <option value="Any">Any</option>
#               <option value="Full Time">Full Time</option>
#               <option value="Part Time">Part Time</option>
#               <option value="Fixed-term">Fixed-term</option>
#             </select>
#           </label>

#           <button type="submit">Start alerts</button>
#         </form>
#       </body>
#     </html>
#     """
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse

from database import init_db, add_subscription, get_locations

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
    <html>
      <head>
        <title>Amazon Job Alerts</title>
        <style>
          body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 2rem auto; }}
          label {{ display: block; margin-top: 1rem; }}
          input, select {{ width: 100%; padding: 0.5rem; margin-top: 0.25rem; }}
          button {{ margin-top: 1.5rem; padding: 0.75rem 1.5rem; }}
        </style>
      </head>
      <body>
        <h1>Amazon Job Alerts</h1>
        <p>Choose up to three preferred areas. Start typing, e.g. "Birmingham", "Coventry", "Swansea".</p>

        <form action="/subscribe" method="post">
          <label>
            Email:
            <input type="email" name="email" required />
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
      </body>
    </html>
    """


@app.post("/subscribe", response_class=HTMLResponse)
def subscribe(
    email: str = Form(...),
    preferred_location1: str = Form(""),
    preferred_location2: str = Form(""),
    preferred_location3: str = Form(""),
    job_type: str = Form("Any"),
):
    # Combine up to three preferences into one string stored in DB
    locs = [
        preferred_location1.strip(),
        preferred_location2.strip(),
        preferred_location3.strip(),
    ]
    locs = [l for l in locs if l]
    combined_locations = "; ".join(locs)  # e.g. "Birmingham / Midlands; South Wales"

    add_subscription(email, combined_locations, job_type)

    return f"""
    <html>
      <head>
        <title>Subscribed</title>
      </head>
      <body>
        <h1>You're subscribed ✅</h1>
        <p>Email: <strong>{email}</strong></p>
        <p>Preferred locations: <strong>{combined_locations or "Any"}</strong></p>
        <p>Job type: <strong>{job_type}</strong></p>
        <p>You will start receiving alerts when matching jobs are found.</p>
        <p><a href="/">Back to form</a></p>
      </body>
    </html>
    """
