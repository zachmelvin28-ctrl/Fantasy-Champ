from itertools import combinations
import json
import os
import ssl
import time
import urllib.request
from flask import (
    Flask,
    jsonify,
    redirect,
    render_template_string,
    request,
    session,
)
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.secret_key = "dynasty_trade_calc_secret_key_2026"

# Apply ProxyFix middleware for correct handling behind proxies (e.g., Vercel, Nginx, Heroku)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# Use /tmp directory on Vercel to avoid read-only file system errors
PLAYER_CACHE_FILE = (
    os.path.join("/tmp", "sleeper_players.json")
    if os.environ.get("VERCEL")
    else "sleeper_players.json"
)
VALUES_CACHE_FILE = (
    os.path.join("/tmp", "fantasycalc_cache.json")
    if os.environ.get("VERCEL")
    else "fantasycalc_cache.json"
)
CACHE_EXPIRATION_SECONDS = 86400  # 24 Hours

THEMES = {
    "dark": {
        "name": "Classic Dark",
        "bg": "#121212",
        "container": "#1e1e1e",
        "panel": "#262626",
        "text": "#e0e0e0",
        "subtext": "#aaa",
        "primary": "#007bff",
        "primary_hover": "#0056b3",
        "border": "#333",
        "input_bg": "#333",
        "card_bg": "#1e1e1e",
    },
    "light": {
        "name": "Clean Light",
        "bg": "#f0f2f5",
        "container": "#ffffff",
        "panel": "#f8f9fa",
        "text": "#212529",
        "subtext": "#6c757d",
        "primary": "#0066cc",
        "primary_hover": "#004080",
        "border": "#ced4da",
        "input_bg": "#ffffff",
        "card_bg": "#ffffff",
    },
    "cyberpunk": {
        "name": "Cyberpunk Neon",
        "bg": "#0f051d",
        "container": "#1a0933",
        "panel": "#260d4d",
        "text": "#00ffcc",
        "subtext": "#ff007f",
        "primary": "#ff007f",
        "primary_hover": "#cc0064",
        "border": "#ff007f44",
        "input_bg": "#120424",
        "card_bg": "#16062b",
    },
    "emerald": {
        "name": "Emerald Forest",
        "bg": "#0b1a12",
        "container": "#132e20",
        "panel": "#1b3b2b",
        "text": "#e0f2f1",
        "subtext": "#81c784",
        "primary": "#2e7d32",
        "primary_hover": "#1b5e20",
        "border": "#2e7d3244",
        "input_bg": "#0d2117",
        "card_bg": "#132e20",
    },
}

NFL_TEAMS = {
    "ARI": {"name": "Arizona Cardinals", "primary": "#97233F", "secondary": "#000000"},
    "ATL": {"name": "Atlanta Falcons", "primary": "#A71930", "secondary": "#000000"},
    "BAL": {"name": "Baltimore Ravens", "primary": "#241773", "secondary": "#000000"},
    "BUF": {"name": "Buffalo Bills", "primary": "#00338D", "secondary": "#C60C30"},
    "CAR": {"name": "Carolina Panthers", "primary": "#0085CA", "secondary": "#101820"},
    "CHI": {"name": "Chicago Bears", "primary": "#0B162A", "secondary": "#C83803"},
    "CIN": {"name": "Cincinnati Bengals", "primary": "#FB4F14", "secondary": "#000000"},
    "CLE": {"name": "Cleveland Browns", "primary": "#311D00", "secondary": "#FF3C00"},
    "DAL": {"name": "Dallas Cowboys", "primary": "#003594", "secondary": "#041E42"},
    "DEN": {"name": "Denver Broncos", "primary": "#FB4F14", "secondary": "#002244"},
    "DET": {"name": "Detroit Lions", "primary": "#0076B6", "secondary": "#B0B7BC"},
    "GB": {"name": "Green Bay Packers", "primary": "#203731", "secondary": "#FFB612"},
    "HOU": {"name": "Houston Texans", "primary": "#03202F", "secondary": "#A71930"},
    "IND": {"name": "Indianapolis Colts", "primary": "#002C5F", "secondary": "#A2AAAD"},
    "JAX": {"name": "Jacksonville Jaguars", "primary": "#006778", "secondary": "#D7A22A"},
    "KC": {"name": "Kansas City Chiefs", "primary": "#E31837", "secondary": "#FFB81C"},
    "LV": {"name": "Las Vegas Raiders", "primary": "#000000", "secondary": "#A5ACAF"},
    "LAC": {"name": "Los Angeles Chargers", "primary": "#0080C6", "secondary": "#FFC20E"},
    "LAR": {"name": "Los Angeles Rams", "primary": "#003594", "secondary": "#FFA300"},
    "MIA": {"name": "Miami Dolphins", "primary": "#008E97", "secondary": "#FC4C02"},
    "MIN": {"name": "Minnesota Vikings", "primary": "#4F2683", "secondary": "#FFC62F"},
    "NE": {"name": "New England Patriots", "primary": "#002244", "secondary": "#C60C30"},
    "NO": {"name": "New Orleans Saints", "primary": "#D3BC8D", "secondary": "#101820"},
    "NYG": {"name": "New York Giants", "primary": "#0B2265", "secondary": "#A71930"},
    "NYJ": {"name": "New York Jets", "primary": "#125740", "secondary": "#000000"},
    "PHI": {"name": "Philadelphia Eagles", "primary": "#004C54", "secondary": "#A5ACAF"},
    "PIT": {"name": "Pittsburgh Steelers", "primary": "#FFB612", "secondary": "#101820"},
    "SF": {"name": "San Francisco 49ers", "primary": "#AA0000", "secondary": "#B3995D"},
    "SEA": {"name": "Seattle Seahawks", "primary": "#002244", "secondary": "#69BE28"},
    "TB": {"name": "Tampa Bay Buccaneers", "primary": "#D50A0A", "secondary": "#0A0A08"},
    "TEN": {"name": "Tennessee Titans", "primary": "#0C2340", "secondary": "#4B92DB"},
    "WAS": {"name": "Washington Commanders", "primary": "#5A1414", "secondary": "#FFB612"},
}


def get_shared_styles(t):
  return f"""
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; padding: 10px; background: {t['bg']}; color: {t['text']}; margin: 0; transition: background 0.3s, color 0.3s; -webkit-tap-highlight-color: transparent; }}
    .container {{ max-width: 700px; margin: 0 auto; background: {t['container']}; padding: 15px; border-radius: 12px; border: 1px solid {t['border']}; box-sizing: border-box; }}
    @media (max-width: 480px) {{ .container {{ padding: 10px; border-radius: 8px; }} body {{ padding: 4px; }} }}
    h2 {{ text-align: center; color: {t['text']}; margin-top: 0; font-size: 1.4em; }}
    .theme-bar {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; gap: 8px; font-size: 0.85em; flex-wrap: wrap; }}
    .theme-bar select {{ background: {t['input_bg']}; color: {t['text']}; border: 1px solid {t['border']}; padding: 6px; border-radius: 4px; max-width: 100%; }}
    .nav-tabs {{ display: flex; gap: 6px; margin-bottom: 15px; background: {t['panel']}; padding: 6px; border-radius: 8px; border: 1px solid {t['border']}; overflow-x: auto; -webkit-overflow-scrolling: touch; }}
    .nav-btn {{ flex: 0 0 auto; text-align: center; padding: 8px 12px; background: {t['input_bg']}; color: {t['subtext']}; text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 0.85em; white-space: nowrap; }}
    .nav-btn.active {{ background: {t['primary']}; color: white; }}
    .sync-box {{ background: {t['panel']}; border: 1px solid {t['primary']}; padding: 12px; border-radius: 8px; margin-bottom: 15px; }}
    .sync-inputs {{ display: flex; gap: 8px; margin-top: 6px; flex-wrap: wrap; }}
    input[type="text"], input[type="number"], select {{ background: {t['input_bg']}; color: {t['text']}; border: 1px solid {t['border']}; padding: 10px; border-radius: 6px; font-size: 16px; box-sizing: border-box; }}
    input[type="text"] {{ flex: 2; min-width: 140px; }}
    button {{ width: 100%; padding: 12px; background: {t['primary']}; color: white; border: none; border-radius: 6px; font-weight: bold; font-size: 16px; margin-top: 10px; cursor: pointer; }}
    button:hover {{ background: {t['primary_hover']}; }}
    .sync-msg {{ font-size: 0.85em; color: {t['primary']}; margin-top: 6px; font-weight: bold; }}
    .rank-card {{ background: {t['panel']}; border: 1px solid {t['border']}; padding: 12px 15px; border-radius: 8px; margin-bottom: 12px; }}
    .rank-header {{ display: flex; justify-content: space-between; align-items: center; font-size: 1.1em; font-weight: bold; color: {t['primary']}; margin-bottom: 6px; flex-wrap: wrap; gap: 6px; }}
    .badge {{ padding: 3px 8px; border-radius: 4px; font-size: 0.75em; text-transform: uppercase; font-weight: bold; }}
    .badge-contender {{ background: #1b3320; color: #81c784; border: 1px solid #2e7d32; }}
    .badge-playoff {{ background: #00363a; color: #4dd0e1; border: 1px solid #00acc1; }}
    .badge-rebuild {{ background: #3e2723; color: #ffb74d; border: 1px solid #ef6c00; }}
    .breakdown-grid {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 6px; text-align: center; margin-top: 8px; background: {t['input_bg']}; padding: 8px; border-radius: 6px; font-size: 0.8em; }}
    .breakdown-item span {{ display: block; color: {t['subtext']}; font-size: 0.7em; }}
"""


def render_theme_form(current_theme, current_team=""):
  options = ""
  for key, data in THEMES.items():
    selected = "selected" if key == current_theme else ""
    options += f'<option value="{key}" {selected}>{data["name"]}</option>'

  team_options = '<option value="">Select Favorite Team</option>'
  for code, tdata in NFL_TEAMS.items():
    selected = "selected" if code == current_team else ""
    team_options += f'<option value="{code}" {selected}>{tdata["name"]}</option>'

  return f"""
    <div class="theme-bar">
        <form method="POST" action="/set-preference" style="margin:0; display:flex; align-items:center; gap:8px; flex-wrap:wrap; width:100%;">
            <div style="display:flex; align-items:center; gap:4px; flex:1; min-width:140px;">
                <label>🎨 Theme:</label>
                <select name="theme_choice" onchange="this.form.submit()" style="width:150px; padding:4px;">
                    {options}
                </select>
            </div>
            <div style="display:flex; align-items:center; gap:4px; flex:1; min-width:140px;">
                <label>🛡️ Team:</label>
                <select name="favorite_team" onchange="this.form.submit()" style="width:150px; padding:4px;">
                    {team_options}
                </select>
            </div>
        </form>
    </div>
    """


DEFAULT_PLAYERS = {
    "Quarterbacks": {
        "Josh Allen (QB)": 8400,
        "Patrick Mahomes (QB)": 8500,
        "Lamar Jackson (QB)": 8200,
        "C.J. Stroud (QB)": 8000,
        "Jayden Daniels (QB)": 7800,
        "Caleb Williams (QB)": 7500,
        "Jalen Hurts (QB)": 7700,
        "Joe Burrow (QB)": 7400,
        "Anthony Richardson (QB)": 7000,
        "Kyler Murray (QB)": 6800,
        "Jordan Love (QB)": 6700,
        "Brock Purdy (QB)": 6600,
        "Dak Prescott (QB)": 6500,
        "Trevor Lawrence (QB)": 6400,
        "Jared Goff (QB)": 6300,
        "Drake Maye (QB)": 6200,
        "Tua Tagovailoa (QB)": 6100,
        "Bo Nix (QB)": 5800,
        "Bryce Young (QB)": 5400,
        "Will Levis (QB)": 4800,
        "Deshaun Watson (QB)": 4500,
        "Geno Smith (QB)": 4200,
        "Kirk Cousins (QB)": 4000,
        "Aaron Rodgers (QB)": 3800,
        "Michael Penix Jr. (QB)": 4500,
        "J.J. McCarthy (QB)": 5000,
    },
    "Running Backs": {
        "Bijan Robinson (RB)": 8900,
        "Breece Hall (RB)": 8800,
        "Jahmyr Gibbs (RB)": 8800,
        "De'Von Achane (RB)": 8100,
        "Ashton Jeanty (RB)": 7900,
        "Saquon Barkley (RB)": 7500,
        "Kyren Williams (RB)": 7300,
        "Jonathan Taylor (RB)": 7200,
        "Derrick Henry (RB)": 6900,
        "Christian McCaffrey (RB)": 6800,
        "Kenneth Walker III (RB)": 6700,
        "Josh Jacobs (RB)": 6600,
        "Travis Etienne (RB)": 6400,
        "James Cook (RB)": 6300,
        "Alvin Kamara (RB)": 6200,
        "Isiah Pacheco (RB)": 6000,
        "Joe Mixon (RB)": 5900,
        "David Montgomery (RB)": 5800,
        "Aaron Jones (RB)": 5500,
        "Rachaad White (RB)": 5400,
        "Jonathon Brooks (RB)": 5300,
        "Trey Benson (RB)": 4800,
        "James Conner (RB)": 4700,
        "Blake Corum (RB)": 4200,
        "Jaylen Wright (RB)": 3900,
        "MarShawn Lloyd (RB)": 3500,
        "Quinshon Judkins (RB)": 4500,
        "TreVeyon Henderson (RB)": 4200,
    },
    "Wide Receivers": {
        "Ja'Marr Chase (WR)": 9500,
        "Justin Jefferson (WR)": 9400,
        "CeeDee Lamb (WR)": 9300,
        "Amon-Ra St. Brown (WR)": 8600,
        "Marvin Harrison Jr. (WR)": 8200,
        "Malik Nabers (WR)": 8100,
        "Garrett Wilson (WR)": 7800,
        "AJ Brown (WR)": 7700,
        "Puka Nacua (WR)": 9500,
        "Nico Collins (WR)": 7400,
        "Drake London (WR)": 7300,
        "Tyreek Hill (WR)": 7100,
        "Chris Olave (WR)": 7000,
        "Zay Flowers (WR)": 7000,
        "Brandon Aiyuk (WR)": 6900,
        "George Pickens (WR)": 6900,
        "Jaylen Waddle (WR)": 6800,
        "Rome Odunze (WR)": 6800,
        "Devonta Smith (WR)": 6700,
        "DK Metcalf (WR)": 6700,
        "Brian Thomas Jr. (WR)": 6600,
        "DJ Moore (WR)": 6600,
        "Xavier Worthy (WR)": 6500,
        "Michael Pittman Jr. (WR)": 6500,
        "Jaxon Smith-Njigba (WR)": 6400,
        "Rashee Rice (WR)": 6400,
        "Tee Higgins (WR)": 6200,
        "Jordan Addison (WR)": 6100,
        "Jayden Reed (WR)": 6000,
        "Ladd McConkey (WR)": 5900,
        "Keon Coleman (WR)": 5200,
        "Xavier Legette (WR)": 4800,
        "Ja'Lynn Polk (WR)": 4400,
        "Adonai Mitchell (WR)": 4300,
        "Luther Burden III (WR)": 5000,
        "Tetairoa McMillan (WR)": 4800,
    },
    "Tight Ends": {
        "Brock Bowers (TE)": 7800,
        "Trey McBride (TE)": 7200,
        "Sam LaPorta (TE)": 7000,
        "Dalton Kincaid (TE)": 6200,
        "Kyle Pitts (TE)": 5800,
        "TJ Hockenson (TE)": 5600,
        "George Kittle (TE)": 5500,
        "Mark Andrews (TE)": 5400,
        "Evan Engram (TE)": 5300,
        "David Njoku (TE)": 5200,
        "Jake Ferguson (TE)": 5100,
        "Dallas Goedert (TE)": 4700,
        "Luke Musgrave (TE)": 4200,
        "Tucker Kraft (TE)": 4100,
        "Ben Sinnott (TE)": 3900,
        "Ja'Tavion Sanders (TE)": 3500,
    },
    "Draft Picks": {
        "2027 Early 1st Pick": 6000,
        "2027 Mid 1st Pick": 4800,
        "2027 Late 1st Pick": 3800,
        "2027 2nd Round Pick": 2200,
        "2027 3rd Round Pick": 1000,
        "2028 Early 1st Pick": 5500,
        "2028 Mid 1st Pick": 4400,
        "2028 Late 1st Pick": 3500,
        "2028 2nd Round Pick": 2000,
        "2028 3rd Round Pick": 900,
    },
}

ROOKIE_PROSPECTS = [
    {"id": 1, "name": "Jeremiyah Love", "pos": "RB", "team": "Arizona Cardinals", "rank": 1, "val": 7900, "adp": 1.2, "projected_points": 240},
    {"id": 2, "name": "Carnell Tate", "pos": "WR", "team": "Tennessee Titans", "rank": 2, "val": 7600, "adp": 2.1, "projected_points": 225},
    {"id": 3, "name": "Jordyn Tyson", "pos": "WR", "team": "New Orleans Saints", "rank": 3, "val": 7300, "adp": 3.0, "projected_points": 210},
    {"id": 4, "name": "Makai Lemon", "pos": "WR", "team": "Philadelphia Eagles", "rank": 4, "val": 7000, "adp": 4.2, "projected_points": 195},
    {"id": 5, "name": "Jadarian Price", "pos": "RB", "team": "Seattle Seahawks", "rank": 5, "val": 6800, "adp": 5.1, "projected_points": 190},
    {"id": 6, "name": "KC Concepcion", "pos": "WR", "team": "Cleveland Browns", "rank": 6, "val": 6500, "adp": 6.4, "projected_points": 180},
    {"id": 7, "name": "Fernando Mendoza", "pos": "QB", "team": "Las Vegas Raiders", "rank": 7, "val": 6200, "adp": 7.0, "projected_points": 260},
    {"id": 8, "name": "Kenyon Sadiq", "pos": "TE", "team": "New York Jets", "rank": 8, "val": 5800, "adp": 8.5, "projected_points": 150},
    {"id": 9, "name": "Omar Cooper Jr.", "pos": "WR", "team": "New York Jets", "rank": 9, "val": 5500, "adp": 9.2, "projected_points": 140},
    {"id": 10, "name": "Denzel Boston", "pos": "WR", "team": "Cleveland Browns", "rank": 10, "val": 5200, "adp": 10.1, "projected_points": 135},
]

CALCULATOR_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Dynasty Suite</title>
    <style>
        {{ shared_styles }}
        .toggle-group { display: flex; justify-content: space-around; background: {{ t['panel'] }}; padding: 10px; border-radius: 8px; margin-bottom: 15px; border: 1px solid {{ t['border'] }}; }
        .toggle-group label { cursor: pointer; font-weight: bold; font-size: 0.9em; }
        .team-section { background: {{ t['panel'] }}; padding: 12px; border-radius: 8px; margin-bottom: 15px; border: 1px solid {{ t['border'] }}; }
        .team-title { font-size: 1.05em; color: {{ t['primary'] }}; margin-bottom: 8px; font-weight: bold; }
        .roster-box { background: {{ t['card_bg'] }}; border: 1px solid {{ t['primary'] }}; padding: 10px; border-radius: 6px; margin-bottom: 12px; }
        .search-box { width: 100%; box-sizing: border-box; margin-bottom: 10px; padding: 10px; background: {{ t['input_bg'] }}; color: {{ t['text'] }}; border: 1px solid {{ t['border'] }}; border-radius: 6px; font-size: 16px; }
        details { background: {{ t['card_bg'] }}; margin-bottom: 8px; border-radius: 6px; padding: 8px; border: 1px solid {{ t['border'] }}; }
        summary { font-weight: bold; cursor: pointer; color: {{ t['primary'] }}; font-size: 0.95em; }
        .checkbox-grid { display: grid; grid-template-columns: 1fr; gap: 6px; margin-top: 8px; }
        .checkbox-item { display: flex; align-items: center; background: {{ t['panel'] }}; padding: 10px; border-radius: 6px; font-size: 0.95em; border: 1px solid {{ t['border'] }}; }
        .checkbox-item input { margin-right: 10px; transform: scale(1.3); }
        .custom-entry { margin-top: 10px; padding-top: 10px; border-top: 1px dashed {{ t['border'] }}; }
        .custom-inputs { display: flex; gap: 8px; margin-top: 6px; flex-wrap: wrap; }
        input[type="number"] { flex: 1; min-width: 100px; }
        .btn-copy { background: #28a745; margin-top: 12px; }
        .btn-clear { background: #d9534f; margin-top: 10px; }
        .btn-suggest { background: #673ab7; margin-top: 10px; }
        .btn-smart { background: #00acc1; margin-top: 10px; }
        .btn-smart-more { background: #00796b; margin-top: 6px; }
        .result { margin-top: 20px; padding: 12px; border-radius: 8px; text-align: center; background: {{ t['panel'] }}; border: 1px solid {{ t['primary'] }}; }
        .note { font-size: 0.9em; color: #ffca28; margin-top: 8px; }
        .suggestion { font-size: 0.95em; color: #81c784; margin-top: 10px; background: #1b3320; padding: 10px; border-radius: 6px; }
        .counter-msg { font-size: 0.95em; color: #b388ff; margin-top: 10px; background: #2a1b3d; border: 1px solid #7c4dff; padding: 10px; border-radius: 6px; }
        .smart-container { text-align: left; margin-top: 12px; }
        .smart-card { font-size: 0.9em; color: {{ t['text'] }}; margin-top: 8px; background: {{ t['card_bg'] }}; border: 1px solid {{ t['primary'] }}; padding: 10px; border-radius: 6px; }
        .pick-adjuster { background: {{ t['panel'] }}; padding: 10px; border-radius: 6px; margin-bottom: 15px; display: flex; justify-content: space-between; align-items: center; border: 1px solid {{ t['border'] }}; flex-wrap: wrap; gap: 8px; }
        .smart-options { background: {{ t['panel'] }}; border: 1px solid {{ t['primary'] }}; padding: 12px; border-radius: 8px; margin-bottom: 15px; }
    </style>
</head>
<body>
<div class="container">
    {{ theme_form | safe }}
    <h2>🏈 Dynasty Suite</h2>
    
    <div class="nav-tabs">
        <a href="/" class="nav-btn active">⚖️ Trade Calculator</a>
        <a href="/analysis" class="nav-btn">📊 Team Rankings</a>
        <a href="/rookie-draft" class="nav-btn">📋 Live Draft Board</a>
        <a href="/league-feed" class="nav-btn">⚡ League Feed</a>
        <a href="/hall-of-fame" class="nav-btn">🏆 Hall of Fame</a>
        <a href="/trends" class="nav-btn">📈 Trends</a>
        <a href="/draft-analyzer" class="nav-btn">🎯 Draft Analyzer</a>
    </div>
    
    <form method="POST" id="calcForm">
        <input type="hidden" name="smart_page" id="smart_page" value="{{ smart_page }}">

        <div class="sync-box">
            <small><b>⚡ Sleeper App Sync:</b></small>
            <div class="sync-inputs">
                <input type="text" name="sleeper_input" id="sleeper_input" placeholder="Username or League ID" value="{{ sleeper_input }}">
                <button type="submit" name="action" value="sync" style="width: auto; margin-top:0; padding: 8px 12px;">Fetch Leagues</button>
            </div>

            {% if user_leagues %}
                <div style="margin-top: 10px;">
                    <small><b>Select League:</b></small>
                    <select name="sleeper_league_id" style="width: 100%; margin-top: 4px;">
                        {% for lg in user_leagues %}
                            <option value="{{ lg.id }}" {% if selected_league_id == lg.id %}selected{% endif %}>{{ lg.name }} ({{ lg.season }})</option>
                        {% endfor %}
                    </select>
                    <button type="submit" name="action" value="select_league" style="background: {{ t['primary'] }}; padding: 8px; margin-top: 6px; font-size: 0.9em;">Sync Selected League</button>
                </div>
            {% endif %}

            {% if sleeper_msg %}
                <div class="sync-msg">{{ sleeper_msg }}</div>
            {% endif %}
        </div>

        <div class="toggle-group">
            <label><input type="radio" name="league_format" value="1QB" onchange="document.getElementById('calcForm').submit()" {% if league_format != 'Superflex' %}checked{% endif %}> 1QB PPR</label>
            <label><input type="radio" name="league_format" value="Superflex" onchange="document.getElementById('calcForm').submit()" {% if league_format == 'Superflex' %}checked{% endif %}> Superflex PPR</label>
        </div>

        <div class="pick-adjuster">
            <small><b>📈 Dynamic Pick Valuation:</b></small>
            <select name="pick_modifier" style="width: auto; padding: 6px;" onchange="document.getElementById('calcForm').submit()">
                <option value="1.0" {% if pick_modifier == 1.0 %}selected{% endif %}>Standard (100%)</option>
                <option value="1.15" {% if pick_modifier == 1.15 %}selected{% endif %}>Draft SZN Hype (+15%)</option>
                <option value="0.85" {% if pick_modifier == 0.85 %}selected{% endif %}>In-Season Contender (-15%)</option>
            </select>
        </div>

        {% if league_owners %}
            <div style="background: {{ t['panel'] }}; padding: 10px; border-radius: 8px; margin-bottom: 15px; border: 1px solid {{ t['border'] }};">
                <small><b>👥 Select Your Team (Team A):</b></small>
                <div style="margin-top: 6px;">
                    <select name="owner_a" style="width: 100%;" onchange="document.getElementById('calcForm').submit()">
                        <option value="">Select Your Team</option>
                        {% for owner in league_owners %}
                            <option value="{{ owner }}" {% if selected_owner_a == owner %}selected{% endif %}>{{ owner }}</option>
                        {% endfor %}
                    </select>
                </div>
            </div>
        {% endif %}

        <div class="smart-options">
            <small style="color: {{ t['primary'] }};"><b>🧠 Smart Trade Finder Options:</b></small>
            <div style="display: flex; gap: 10px; margin-top: 8px; flex-wrap: wrap;">
                <div style="flex: 1; min-width: 160px;">
                    <small>Strategy Focus:</small>
                    <select name="smart_strategy" style="width: 100%; margin-top: 4px;">
                        <option value="balanced" {% if smart_strategy == 'balanced' %}selected{% endif %}>Balanced Value Match</option>
                        <option value="rb_focus" {% if smart_strategy == 'rb_focus' %}selected{% endif %}>Target Star RBs 🏈</option>
                        <option value="improve_rbs" {% if smart_strategy == 'improve_rbs' %}selected{% endif %}>Improve Running Backs 🏃‍♂️</option>
                        <option value="rb_depth" {% if smart_strategy == 'rb_depth' %}selected{% endif %}>Add RB Depth 🔋</option>
                        <option value="wr_focus" {% if smart_strategy == 'wr_focus' %}selected{% endif %}>Improve WR Depth 🎯</option>
                        <option value="improve_wrs" {% if smart_strategy == 'improve_wrs' %}selected{% endif %}>Improve Wide Receivers ✨</option>
                        <option value="tier_up" {% if smart_strategy == 'tier_up' %}selected{% endif %}>Tier Up / Target Studs 📈</option>
                        <option value="win_now" {% if smart_strategy == 'win_now' %}selected{% endif %}>Win-Now / Veteran Push 💍</option>
                        <option value="pick_hoard" {% if smart_strategy == 'pick_hoard' %}selected{% endif %}>Draft Pick Accumulation 🎫</option>
                        <option value="qb_focus" {% if smart_strategy == 'qb_focus' %}selected{% endif %}>Elite QB Hunter 🚀</option>
                        <option value="te_focus" {% if smart_strategy == 'te_focus' %}selected{% endif %}>Tight End Upgrade 🛡️</option>
                        <option value="youth_rebuild" {% if smart_strategy == 'youth_rebuild' %}selected{% endif %}>Youth & Upside / Rebuild 🌱</option>
                    </select>
                </div>
                <div style="flex: 1; min-width: 160px;">
                    <small>Specific Player Target (Optional):</small>
                    <input type="text" name="target_player_filter" placeholder="e.g. Bijan" value="{{ target_player_filter }}" style="width: 100%; box-sizing: border-box; margin-top: 4px;">
                </div>
            </div>
            <button type="submit" name="action" value="smart_more" class="btn-smart-more">🔄 Suggest More Trade Options</button>
        </div>

        {% for team_key, team_label in [('team_a', 'Team A Gives (Your Side)'), ('team_b', 'Team B Receives (Target Side)')] %}
        {% set current_owner = selected_owner_a if team_key == 'team_a' else selected_owner_b %}
        <div class="team-section" id="{{ team_key }}_section">
            <div class="team-title">
                {{ team_label }} 
                {% if current_owner %}({{ current_owner }}){% endif %}
            </div>

            {% if league_owners and team_key == 'team_b' %}
                <div style="margin-bottom: 12px;">
                    <small><b>Select Target Team (Team B):</b></small>
                    <select name="owner_b" style="width: 100%; margin-top: 4px;" onchange="document.getElementById('calcForm').submit()">
                        <option value="">Select Target Team (Optional)</option>
                        {% for owner in league_owners %}
                            <option value="{{ owner }}" {% if selected_owner_b == owner %}selected{% endif %}>{{ owner }}</option>
                        {% endfor %}
                    </select>
                </div>
            {% endif %}

            {% if current_owner and owner_rosters.get(current_owner) %}
            <div class="roster-box">
                <small><b>📋 {{ current_owner }}'s Sleeper Roster:</b></small>
                <div class="checkbox-grid" style="margin-top: 6px;">
                    {% for name, val in owner_rosters[current_owner].items() %}
                        <div class="checkbox-item" data-name="{{ name|lower }}">
                            <label style="display:flex; align-items:center; width:100%; cursor:pointer;">
                                <input type="checkbox" name="{{ team_key }}" value="{{ name }}" {% if name in selected_assets[team_key] %}checked{% endif %}>
                                <span>{{ name }} ({{ val }})</span>
                            </label>
                        </div>
                    {% endfor %}
                </div>
            </div>
            {% endif %}
            
            <input type="text" class="search-box" placeholder="🔍 Search full database or picks..." onkeyup="filterAssets('{{ team_key }}', this.value)">

            {% for pos, players in player_groups.items() %}
            <details id="{{ team_key }}_{{ pos }}_details">
                <summary>{{ pos }}</summary>
                <div class="checkbox-grid">
                    {% for name, base_val in players.items() %}
                        {% set is_pick = 'Pick' in name %}
                        {% set display_val = (base_val * pick_modifier)|int if is_pick else base_val %}
                        <div class="checkbox-item" data-name="{{ name|lower }}">
                            <label style="display:flex; align-items:center; width:100%; cursor:pointer;">
                                <input type="checkbox" name="{{ team_key }}" value="{{ name }}" {% if name in selected_assets[team_key] %}checked{% endif %}>
                                <span>{{ name }} ({{ display_val }})</span>
                            </label>
                        </div>
                    {% endfor %}
                </div>
            </details>
            {% endfor %}

            <div class="custom-entry">
                <small><b>Add Custom Player/Pick:</b></small>
                <div class="custom-inputs">
                    <input type="text" name="{{ team_key }}_custom_name" placeholder="Asset Name" value="{{ custom_assets[team_key]['name'] }}">
                    <input type="number" name="{{ team_key }}_custom_val" placeholder="Value" value="{{ custom_assets[team_key]['val'] }}">
                </div>
            </div>
        </div>
        {% endfor %}

        <button type="submit" name="action" value="analyze">Analyze Trade</button>
        <button type="submit" name="action" value="suggest_trade" class="btn-suggest">💡 Suggest Counter-Offer (Auto-Balance)</button>
        <button type="submit" name="action" value="smart_suggestion" class="btn-smart">🧠 Smart Trade Suggestions</button>
        <button type="submit" name="action" value="clear_trade" class="btn-clear">🧹 Clear Trade Selections</button>
    </form>

    {% if result %}
        <div class="result">
            <div style="display: flex; justify-content: space-around; margin-bottom: 15px; text-align: left; gap: 10px; flex-wrap: wrap;">
                <div style="flex: 1; min-width: 220px;">
                    <b style="color: {{ t['primary'] }};">{{ selected_owner_a or 'Team A' }} Gives:</b>
                    <ul style="margin: 5px 0; padding-left: 15px; font-size: 0.9em;">
                        {% for item in result.team_a_items %}
                            <li>{{ item.name }} ({{ "{:,}".format(item.val) }} pts)</li>
                        {% endfor %}
                    </ul>
                    <p style="margin: 5px 0;"><b>Total:</b> {{ "{:,}".format(result.team_a_total) }} pts</p>
                </div>
                <div style="flex: 1; min-width: 220px; border-left: 1px solid {{ t['border'] }}; padding-left: 10px;">
                    <b style="color: {{ t['primary'] }};">{{ selected_owner_b or 'Team B' }} Gives:</b>
                    <ul style="margin: 5px 0; padding-left: 15px; font-size: 0.9em;">
                        {% for item in result.team_b_items %}
                            <li>{{ item.name }} ({{ "{:,}".format(item.val) }} pts)</li>
                        {% endfor %}
                    </ul>
                    <p style="margin: 5px 0;"><b>Total:</b> {{ "{:,}".format(result.team_b_total) }} pts</p>
                </div>
            </div>

            {% if result.stud_msg %}
                <div class="note">{{ result.stud_msg }}</div>
            {% endif %}

            {% if result.counter_msg %}
                <div class="counter-msg">{{ result.counter_msg }}</div>
            {% endif %}

            {% if result.smart_suggestions %}
                <div class="smart-container">
                    <small><b>🧠 Top Trade Suggestions for {{ selected_owner_a }} (Focus: {{ smart_strategy_label }}) :</b></small>
                    {% for s in result.smart_suggestions %}
                        <div class="smart-card">
                            <b>vs. {{ s.partner }}</b><br>
                            Give: <b>{{ s.gives }}</b> ({{ s.gives_val }} pts) ➔ Get: <b>{{ s.gets }}</b> ({{ s.gets_val }} pts)<br>
                            <small style="color: {{ t['primary'] }};">Value Diff: {{ s.diff }} pts</small>
                        </div>
                    {% endfor %}
                </div>
            {% endif %}

            <hr style="border-color: {{ t['border'] }};">
            <h3>{{ result.message }}</h3>

            {% if result.balancer_msg %}
                <div class="suggestion">{{ result.balancer_msg }}</div>
            {% endif %}

            <button type="button" class="btn-copy" onclick="copyTradeSummary()">📋 Copy Trade Summary</button>
        </div>

        <div id="summary-text" style="display:none;">{{ result.itemized_summary_text }}</div>
    {% endif %}
</div>

<script>
document.addEventListener("DOMContentLoaded", () => {
    const sleeperInput = document.getElementById('sleeper_input');
    if (sleeperInput) {
        const savedUser = localStorage.getItem('sleeper_username');
        if (!sleeperInput.value && savedUser) {
            sleeperInput.value = savedUser;
        }
        document.getElementById('calcForm').addEventListener('submit', () => {
            if (sleeperInput.value) {
                localStorage.setItem('sleeper_username', sleeperInput.value);
            }
        });
    }
});

function filterAssets(teamKey, query) {
    const q = query.toLowerCase().trim();
    const section = document.getElementById(teamKey + '_section');
    const items = section.querySelectorAll('.checkbox-item');
    const details = section.querySelectorAll('details');

    items.forEach(item => {
        const name = item.getAttribute('data-name');
        if (name.includes(q)) {
            item.style.display = 'flex';
        } else {
            item.style.display = 'none';
        }
    });

    details.forEach(det => {
        if (q.length > 0) {
            const hasMatches = Array.from(det.querySelectorAll('.checkbox-item')).some(i => i.style.display !== 'none');
            det.open = hasMatches;
        } else {
            det.open = false;
        }
    });
}

function copyTradeSummary() {
    const textData = document.getElementById('summary-text').innerText;
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(textData).then(() => {
            alert('Trade summary copied to clipboard!');
        }).catch(err => {
            fallbackCopy(textData);
        });
    } else {
        fallbackCopy(textData);
    }
}

function fallbackCopy(text) {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    document.body.appendChild(textarea);
    textarea.select();
    try {
        document.execCommand('copy');
        alert('Trade summary copied to clipboard!');
    } catch (err) {
        alert('Failed to copy summary.');
    }
    document.body.removeChild(textarea);
}
</script>
</body>
</html>
"""

ANALYSIS_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Team Power Rankings & Analysis</title>
    <style>
        {{ shared_styles }}
    </style>
</head>
<body>
<div class="container">
    {{ theme_form | safe }}
    <h2>📊 Team Power Rankings & Analysis</h2>
    
    <div class="nav-tabs">
        <a href="/" class="nav-btn">⚖️ Trade Calculator</a>
        <a href="/analysis" class="nav-btn active">📊 Team Rankings</a>
        <a href="/rookie-draft" class="nav-btn">📋 Live Draft Board</a>
        <a href="/league-feed" class="nav-btn">⚡ League Feed</a>
        <a href="/hall-of-fame" class="nav-btn">🏆 Hall of Fame</a>
        <a href="/trends" class="nav-btn">📈 Trends</a>
        <a href="/draft-analyzer" class="nav-btn">🎯 Draft Analyzer</a>
    </div>

    <form method="POST" action="/analysis">
        <div class="sync-box">
            <small><b>⚡ Sync League for Analysis:</b></small>
            <div class="sync-inputs">
                <input type="text" name="sleeper_input" placeholder="Username or League ID" value="{{ sleeper_input }}">
                <button type="submit" name="action" value="sync" style="width: auto; margin-top:0; padding: 8px 12px;">Fetch</button>
            </div>

            {% if user_leagues %}
                <div style="margin-top: 10px;">
                    <small><b>Select League:</b></small>
                    <select name="sleeper_league_id" style="width: 100%; margin-top: 4px;">
                        {% for lg in user_leagues %}
                            <option value="{{ lg.id }}" {% if selected_league_id == lg.id %}selected{% endif %}>{{ lg.name }} ({{ lg.season }})</option>
                        {% endfor %}
                    </select>
                    <button type="submit" name="action" value="select_league" style="background: {{ t['primary'] }}; padding: 8px; margin-top: 6px; font-size: 0.9em;">Load Power Rankings</button>
                </div>
            {% endif %}

            {% if sleeper_msg %}
                <div class="sync-msg">{{ sleeper_msg }}</div>
            {% endif %}
        </div>
    </form>

    {% if power_rankings %}
        <div style="margin-top: 15px;">
            <p style="color: {{ t['subtext'] }}; font-size: 0.9em; text-align: center;">League-wide valuation rankings based on total player assets and traded draft capital.</p>
            
            {% for team in power_rankings %}
                <div class="rank-card">
                    <div class="rank-header">
                        <span>#{{ loop.index }} - {{ team.name }}</span>
                        <div>
                            {% if team.archetype == 'Contender' %}
                                <span class="badge badge-contender">💍 Contender</span>
                            {% elif team.archetype == 'Playoff Threat' %}
                                <span class="badge badge-playoff">🚀 Playoff Threat</span>
                            {% else %}
                                <span class="badge badge-rebuild">🌱 Rebuilder</span>
                            {% endif %}
                            <span style="color: {{ t['text'] }}; margin-left: 8px;">{{ "{:,}".format(team.total_val | int) }} pts</span>
                        </div>
                    </div>
                    <div class="breakdown-grid">
                        <div class="breakdown-item"><span>QB</span>{{ "{:,}".format(team.qb_val | int) }}</div>
                        <div class="breakdown-item"><span>RB</span>{{ "{:,}".format(team.rb_val | int) }}</div>
                        <div class="breakdown-item"><span>WR</span>{{ "{:,}".format(team.wr_val | int) }}</div>
                        <div class="breakdown-item"><span>TE</span>{{ "{:,}".format(team.te_val | int) }}</div>
                        <div class="breakdown-item"><span>Picks</span>{{ "{:,}".format(team.pick_val | int) }}</div>
                    </div>
                </div>
            {% endfor %}
        </div>
    {% else %}
        <div style="text-align: center; padding: 30px; color: {{ t['subtext'] }};">
            <p>No league data loaded. Enter your Sleeper username or League ID above to generate power rankings and team breakdowns.</p>
        </div>
    {% endif %}
</div>
</body>
</html>
"""

ROOKIE_DRAFT_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Live Draft Board</title>
    <style>
        {{ shared_styles }}
        .draft-container {{ display: grid; grid-template-columns: 1fr 1.5fr; gap: 15px; margin-top: 15px; }}
        @media (max-width: 768px) {{ .draft-container {{ grid-template-columns: 1fr; }} }}
        .panel {{ background: {{ t['panel'] }}; padding: 12px; border-radius: 8px; border: 1px solid {{ t['border'] }}; }}
        .filters {{ display: flex; gap: 6px; margin-bottom: 12px; align-items: center; flex-wrap: wrap; }}
        .filter-btn {{ background: {{ t['input_bg'] }}; color: {{ t['text'] }}; border: 1px solid {{ t['border'] }}; padding: 6px 10px; border-radius: 6px; cursor: pointer; font-size: 0.85em; font-weight: bold; }}
        .filter-btn.active {{ background: {{ t['primary'] }}; color: #fff; }}
        .player-list {{ max-height: 420px; overflow-y: auto; -webkit-overflow-scrolling: touch; }}
        .player-card {{ background: {{ t['card_bg'] }}; padding: 10px; margin-bottom: 8px; border-radius: 6px; display: flex; justify-content: space-between; align-items: center; border: 1px solid {{ t['border'] }}; gap: 8px; }}
        .player-card:hover {{ border-color: {{ t['primary'] }}; }}
        .draft-grid {{ display: flex; flex-direction: column; gap: 8px; max-height: 450px; overflow-y: auto; -webkit-overflow-scrolling: touch; }}
        .pick-slot {{ background: {{ t['card_bg'] }}; padding: 10px 12px; border-radius: 6px; display: flex; justify-content: space-between; align-items: center; border-left: 4px solid {{ t['primary'] }}; border: 1px solid {{ t['border'] }}; font-size: 0.9em; gap: 8px; }}
        button.draft-btn {{ background: {{ t['primary'] }}; color: #fff; border: none; padding: 6px 12px; border-radius: 6px; font-weight: bold; cursor: pointer; width: auto; font-size: 0.85em; margin-top: 0; }}
        button.draft-btn:hover {{ background: {{ t['primary_hover'] }}; }}
        .sync-badge {{ background: {{ t['primary'] }}; color: white; padding: 6px 10px; border-radius: 6px; font-size: 0.8em; margin-bottom: 10px; display: inline-block; font-weight: bold; }}
        .live-controls {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; font-size: 0.9em; flex-wrap: wrap; gap: 8px; }}
        .draft-mode-bar {{ display: flex; gap: 12px; margin-bottom: 12px; align-items: center; background: {{ t['card_bg'] }}; padding: 10px; border-radius: 6px; border: 1px solid {{ t['border'] }}; flex-wrap: wrap; font-size: 0.9em; }}
        .draft-mode-bar label {{ cursor: pointer; font-weight: bold; display: flex; align-items: center; gap: 4px; }}
    </style>
</head>
<body>
<div class="container" style="max-width: 900px;">
    {{ theme_form | safe }}
    <h2>📋 Live Sleeper Draft Board</h2>
    <div class="nav-tabs">
        <a href="/" class="nav-btn">⚖️ Trade Calculator</a>
        <a href="/analysis" class="nav-btn">📊 Team Rankings</a>
        <a href="/rookie-draft" class="nav-btn active">📋 Live Draft Board</a>
        <a href="/league-feed" class="nav-btn">⚡ League Feed</a>
        <a href="/hall-of-fame" class="nav-btn">🏆 Hall of Fame</a>
        <a href="/trends" class="nav-btn">📈 Trends</a>
        <a href="/draft-analyzer" class="nav-btn">🎯 Draft Analyzer</a>
    </div>

    <form method="POST" action="/rookie-draft">
        <div class="sync-box">
            <small><b>⚡ Sleeper App Sync:</b></small>
            <div class="sync-inputs">
                <input type="text" name="sleeper_input" placeholder="Username or League ID" value="{{ sleeper_input }}">
                <button type="submit" name="action" value="sync" style="width: auto; margin-top:0; padding: 8px 12px;">Fetch</button>
            </div>

            {% if user_leagues %}
                <div style="margin-top: 10px;">
                    <small><b>Select League:</b></small>
                    <select name="sleeper_league_id" style="width: 100%; margin-top: 4px;">
                        {% for lg in user_leagues %}
                            <option value="{{ lg.id }}" {% if selected_league_id == lg.id %}selected{% endif %}>{{ lg.name }} ({{ lg.season }})</option>
                        {% endfor %}
                    </select>
                    <button type="submit" name="action" value="select_league" style="background: {{ t['primary'] }}; padding: 8px; margin-top: 6px; font-size: 0.9em;">Sync Selected League</button>
                </div>
            {% endif %}

            {% if sleeper_msg %}
                <div class="sync-msg">{{ sleeper_msg }}</div>
            {% endif %}
        </div>
    </form>

    <div id="syncStatus"></div>

    <div class="draft-mode-bar">
        <div>
            <small style="display:block; color:{{ t['subtext'] }}; margin-bottom:4px;">Draft Type:</small>
            <div style="display:flex; gap:10px; flex-wrap:wrap;">
                <label><input type="radio" name="draft_mode" value="rookie" checked onchange="switchDraftMode('rookie')"> Rookie Draft</label>
                <label><input type="radio" name="draft_mode" value="startup" onchange="switchDraftMode('startup')"> Startup Draft</label>
                <label><input type="radio" name="draft_mode" value="regular" onchange="switchDraftMode('regular')"> Regular / Vet Draft</label>
            </div>
        </div>
        <div style="margin-left:auto;">
            <small style="display:block; color:{{ t['subtext'] }}; margin-bottom:4px;">Scoring / Format:</small>
            <div style="display:flex; gap:10px;">
                <label><input type="radio" name="draft_format" value="1QB" checked onchange="switchFormat('1QB')"> 1QB PPR</label>
                <label><input type="radio" name="draft_format" value="Superflex" onchange="switchFormat('Superflex')"> Superflex PPR</label>
            </div>
        </div>
    </div>

    <div class="live-controls">
        <span id="liveStatusText" style="color: {{ t['subtext'] }}; font-size: 0.85em;">🟢 Live Draft Polling: Active</span>
        <button onclick="loadLiveDraftData()" style="width: auto; margin-top: 0; padding: 6px 12px; font-size: 0.85em;">🔄 Force Refresh</button>
    </div>

    <div class="draft-container">
        <div class="panel">
            <h3 style="margin-top:0; color:{{ t['primary'] }}; font-size: 1.05em;" id="poolTitle">Available Prospects</h3>
            <div class="filters">
                <button class="filter-btn active" onclick="filterPos('ALL', event)">ALL</button>
                <button class="filter-btn" onclick="filterPos('QB', event)">QB</button>
                <button class="filter-btn" onclick="filterPos('RB', event)">RB</button>
                <button class="filter-btn" onclick="filterPos('WR', event)">WR</button>
                <button class="filter-btn" onclick="filterPos('TE', event)">TE</button>
                <select id="sortSelect" onchange="changeSort(this.value)" style="margin-left: auto; background: {{ t['input_bg'] }}; color: {{ t['text'] }}; border: 1px solid {{ t['border'] }}; padding: 6px; border-radius: 6px; font-size: 0.85em;">
                    <option value="value">Sort: Dynasty Value</option>
                    <option value="adp">Sort: ADP</option>
                    <option value="points">Sort: Projected Pts</option>
                    <option value="name">Sort: Name (A-Z)</option>
                </select>
            </div>
            <div class="player-list" id="playerList"></div>
        </div>

        <div class="panel">
            <h3 style="margin-top:0; color:{{ t['primary'] }}; font-size: 1.05em;" id="boardTitle">Live Draft Board (Rounds 1+)</h3>
            <div class="draft-grid" id="draftGrid"></div>
        </div>
    </div>
</div>

<script>
    let rookieList = [];
    let startupList = [];
    let regularList = [];
    let currentDraftMode = 'rookie';
    let currentFormat = '1QB';
    let currentFilter = 'ALL';
    let currentSort = 'value';
    let totalPicks = 12;
    let draftState = {};
    let leagueDraftInfo = null;
    let pollInterval = null;

    async function loadLiveDraftData() {
        try {
            const [rookRes, startRes, regRes, draftRes] = await Promise.all([
                fetch('/api/rookies'),
                fetch(`/api/all-players?format=${currentFormat}&type=startup`),
                fetch(`/api/all-players?format=${currentFormat}&type=regular`),
                fetch('/api/league-draft-info')
            ]);
            rookieList = await rookRes.json();
            startupList = await startRes.json();
            regularList = await regRes.json();
            const draftData = await draftRes.json();
            
            if (draftData.success) {
                leagueDraftInfo = draftData;
                totalPicks = draftData.total_picks || (draftData.teams * 4) || 48;
                if (draftData.draft_id) {
                    document.getElementById('syncStatus').innerHTML = `<div class="sync-badge">⚡ Live Sleeper Draft Connected (Draft ID: ${draftData.draft_id})</div>`;
                } else {
                    document.getElementById('syncStatus').innerHTML = `<div class="sync-badge">⚡ Synced with Sleeper League (${draftData.teams} Teams)</div>`;
                }

                if (draftData.picks) {
                    draftState = {};
                    draftData.picks.forEach(p => {
                        draftState[p.pick_no] = p.player_id;
                    });
                }
            } else {
                document.getElementById('syncStatus').innerHTML = `<div style="color: {{ t['subtext'] }}; font-size: 0.85em; margin-bottom: 10px;">💡 Tip: Sync a league above or on the Trade Calculator to load your league's exact draft order & managers.</div>`;
            }

            renderPlayers();
            renderGrid();
        } catch(e) {
            console.error("Failed to load live draft data", e);
            renderPlayers();
            renderGrid();
        }
    }

    function switchDraftMode(mode) {
        currentDraftMode = mode;
        const titles = {
            'rookie': 'Available Prospects (Rookie Draft)',
            'startup': 'Available Players (Startup Draft)',
            'regular': 'Available Players (Regular/Vet Draft)'
        };
        document.getElementById('poolTitle').innerText = titles[mode] || 'Available Players';
        renderPlayers();
    }

    function switchFormat(fmt) {
        currentFormat = fmt;
        loadLiveDraftData();
    }

    function filterPos(pos, event) {
        currentFilter = pos;
        document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
        event.target.classList.add('active');
        renderPlayers();
    }

    function changeSort(sortVal) {
        currentSort = sortVal;
        renderPlayers();
    }

    function renderPlayers() {
        const listEl = document.getElementById('playerList');
        listEl.innerHTML = '';
        
        let activeList = rookieList;
        if (currentDraftMode === 'startup') activeList = startupList;
        else if (currentDraftMode === 'regular') activeList = regularList;

        const draftedValues = Object.values(draftState);
        
        const filtered = activeList.filter(player => {
            if (currentFilter !== 'ALL' && player.pos !== currentFilter) return false;
            
            const isDrafted = draftedValues.some(d => {
                if (!d) return false;
                const dStr = String(d).trim().toLowerCase();
                const pName = player.name.trim().toLowerCase();
                const pCleanName = pName.replace(/\\s*\\([a-z]+\\)\\s*$/, '');
                const dCleanName = dStr.replace(/\\s*\\([a-z]+\\)\\s*$/, '');
                return dStr === pName || dStr === pCleanName || dStr === String(player.id).toLowerCase() || pCleanName === dCleanName;
            });
            
            return !isDrafted;
        });

        filtered.sort((a, b) => {
            if (currentSort === 'adp') {
                return (a.adp || 999) - (b.adp || 999);
            } else if (currentSort === 'points') {
                return (b.projected_points || 0) - (a.projected_points || 0);
            } else if (currentSort === 'name') {
                return a.name.localeCompare(b.name);
            } else {
                return (b.val || 0) - (a.val || 0);
            }
        });
        
        if (filtered.length === 0) {
            listEl.innerHTML = '<p style="color: {{ t[\'subtext\'] }}; text-align:center; font-size:0.9em;">No players available.</p>';
            return;
        }

        filtered.forEach(player => {
            const card = document.createElement('div');
            card.className = 'player-card';
            const ptsText = player.projected_points ? ` | ${player.projected_points} proj pts` : '';
            const adpText = player.adp ? ` | ADP: ${player.adp}` : '';
            const subtitle = currentDraftMode === 'rookie' ? `${player.pos} - ${player.team}` : `${player.pos} - ${player.team || 'NFL'} (${player.val || 0} pts${ptsText}${adpText})`;
            card.innerHTML = `<span><strong>#${player.rank || ''} ${player.name}</strong><br><small style="color:{{ t['subtext'] }};">${subtitle}</small></span>
                              <button class="draft-btn" onclick="draftPlayer('${player.name}')">Draft</button>`;
            listEl.appendChild(card);
        });
    }

    function renderGrid() {
        const gridEl = document.getElementById('draftGrid');
        gridEl.innerHTML = '';

        let activeList = rookieList;
        if (currentDraftMode === 'startup') activeList = startupList;
        else if (currentDraftMode === 'regular') activeList = regularList;

        const displayCount = Math.max(totalPicks, 24);
        for (let i = 1; i <= displayCount; i++) {
            const slot = document.createElement('div');
            slot.className = 'pick-slot';
            const draftedPlayerId = draftState[i];
            const draftedPlayer = activeList.find(p => p.id == draftedPlayerId || p.name === draftedPlayerId || p.name.toLowerCase().includes(String(draftedPlayerId).toLowerCase()));

            let ownerName = '';
            if (leagueDraftInfo && leagueDraftInfo.slot_to_owner) {
                ownerName = leagueDraftInfo.slot_to_owner[i] || leagueDraftInfo.slot_to_owner[String(i)] || '';
            }

            const roundNum = Math.ceil(i / (leagueDraftInfo?.teams || 12));
            const pickInRound = ((i - 1) % (leagueDraftInfo?.teams || 12)) + 1;
            const pickLabel = `Pick ${roundNum}.${pickInRound < 10 ? '0' + pickInRound : pickInRound}` + (ownerName ? ` <small style="color:{{ t['primary'] }};">(${ownerName})</small>` : '');

            slot.innerHTML = `<span><strong>${pickLabel}</strong></span>
                              <span>${draftedPlayer ? '<strong>' + draftedPlayer.name + '</strong> <small style="color:{{ t['primary'] }};">(' + draftedPlayer.pos + ')</small>' : (draftedPlayerId ? '<strong>' + draftedPlayerId + '</strong>' : '<em style="color:{{ t[\'subtext\'] }};">Available</em>')}</span>`;
            gridEl.appendChild(slot);
        }
    }

    async function draftPlayer(playerName) {
        for (let i = 1; i <= 100; i++) {
            if (!draftState[i]) {
                draftState[i] = playerName;
                break;
            }
        }
        renderPlayers();
        renderGrid();
    }

    loadLiveDraftData();
    pollInterval = setInterval(loadLiveDraftData, 8000);
</script>
</body>
</html>
"""

LEAGUE_FEED_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>League Feed</title>
    <style>{{ shared_styles }}</style>
</head>
<body>
<div class="container">
    {{ theme_form | safe }}
    <h2>⚡ Live League Feed</h2>
    <div class="nav-tabs">
        <a href="/" class="nav-btn">⚖️ Trade Calculator</a>
        <a href="/analysis" class="nav-btn">📊 Team Rankings</a>
        <a href="/rookie-draft" class="nav-btn">📋 Live Draft Board</a>
        <a href="/league-feed" class="nav-btn active">⚡ League Feed</a>
        <a href="/hall-of-fame" class="nav-btn">🏆 Hall of Fame</a>
        <a href="/trends" class="nav-btn">📈 Trends</a>
        <a href="/draft-analyzer" class="nav-btn">🎯 Draft Analyzer</a>
    </div>
    <div style="background: {{ t['panel'] }}; padding: 15px; border-radius: 8px; border: 1px solid {{ t['border'] }};">
        <form method="GET" action="/league-feed">
            <small><b>Connect Sleeper League Feed:</b></small>
            <div class="sync-inputs" style="margin-top: 6px;">
                <input type="text" name="league_id" value="{{ league_id }}" placeholder="Enter Sleeper League ID...">
                <button type="submit" style="width: auto; margin-top:0; padding: 8px 12px;">Load</button>
            </div>
        </form>
        {% if transactions %}
            <div style="margin-top: 15px;">
                {% for tx in transactions %}
                    <div style="background: {{ t['card_bg'] }}; padding: 10px; border-radius: 6px; margin-bottom: 8px; border: 1px solid {{ t['border'] }};">
                        <p style="color: {{ t['primary'] }}; font-weight: bold; margin: 0;">Type: {{ tx.type }} (Week {{ tx.week }})</p>
                    </div>
                {% endfor %}
            </div>
        {% else %}
            <p style="color: {{ t['subtext'] }}; font-size: 0.9em; margin-top: 10px;">Enter a valid Sleeper League ID above to pull real-time transactions.</p>
        {% endif %}
    </div>
</div>
</body>
</html>
"""

HOF_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Hall of Fame</title>
    <style>{{ shared_styles }}</style>
</head>
<body>
<div class="container">
    {{ theme_form | safe }}
    <h2>🏆 League Hall of Fame</h2>
    <div class="nav-tabs">
        <a href="/" class="nav-btn">⚖️ Trade Calculator</a>
        <a href="/analysis" class="nav-btn">📊 Team Rankings</a>
        <a href="/rookie-draft" class="nav-btn">📋 Live Draft Board</a>
        <a href="/league-feed" class="nav-btn">⚡ League Feed</a>
        <a href="/hall-of-fame" class="nav-btn active">🏆 Hall of Fame</a>
        <a href="/trends" class="nav-btn">📈 Trends</a>
        <a href="/draft-analyzer" class="nav-btn">🎯 Draft Analyzer</a>
    </div>
    <div style="background: {{ t['panel'] }}; padding: 15px; border-radius: 8px; border: 1px solid {{ t['border'] }};">
        <div style="background: {{ t['card_bg'] }}; padding: 12px; border-radius: 6px; margin-bottom: 10px; border: 1px solid {{ t['border'] }};">
            <p style="color: #ffca28; font-weight: bold; margin: 0;">🏆 Champion: TheMedulla Oblangatas</p>
            <p style="color: {{ t['subtext'] }}; font-size: 0.85em; margin: 4px 0 0 0;">Manager: Zach</p>
        </div>
    </div>
</div>
</body>
</html>
"""

TRENDS_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Value Trends</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>{{ shared_styles }}</style>
</head>
<body>
<div class="container">
    {{ theme_form | safe }}
    <h2>📈 Player Market Value Trends</h2>
    <div class="nav-tabs">
        <a href="/" class="nav-btn">⚖️ Trade Calculator</a>
        <a href="/analysis" class="nav-btn">📊 Team Rankings</a>
        <a href="/rookie-draft" class="nav-btn">📋 Live Draft Board</a>
        <a href="/league-feed" class="nav-btn">⚡ League Feed</a>
        <a href="/hall-of-fame" class="nav-btn">🏆 Hall of Fame</a>
        <a href="/trends" class="nav-btn active">📈 Trends</a>
        <a href="/draft-analyzer" class="nav-btn">🎯 Draft Analyzer</a>
    </div>
    <div style="background: {{ t['panel'] }}; padding: 15px; border-radius: 8px; height: 350px; border: 1px solid {{ t['border'] }};">
        <canvas id="trendChart"></canvas>
    </div>
</div>
<script>
const rawData = {{ trends | safe }};
const labels = ['June 2026', 'July 2026', 'August 2026'];
const datasets = Object.keys(rawData).map((player, idx) => {
    const colors = ['#3b82f6', '#6366f1', '#10b981', '#f59e0b'];
    return {
        label: player,
        data: rawData[player].map(item => item.value),
        borderColor: colors[idx % colors.length],
        tension: 0.3
    };
});
new Chart(document.getElementById('trendChart').getContext('2d'), {
    type: 'line',
    data: { labels: labels, datasets: datasets },
    options: { responsive: true, maintainAspectRatio: false }
});
</script>
</body>
</html>
"""

DRAFT_ANALYZER_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Draft Analyzer</title>
    <style>
        {{ shared_styles }}
        .draft-summary-card { background: {{ t['panel'] }}; border: 1px solid {{ t['border'] }}; padding: 15px; border-radius: 8px; margin-bottom: 15px; }
        .pick-row { background: {{ t['card_bg'] }}; padding: 10px; border-radius: 6px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; border: 1px solid {{ t['border'] }}; font-size: 0.9em; gap: 8px; }
        .badge-grade { padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 0.85em; text-transform: uppercase; }
        .grade-s { background: #1b3320; color: #81c784; border: 1px solid #2e7d32; }
        .grade-a { background: #00363a; color: #4dd0e1; border: 1px solid #00acc1; }
        .grade-b { background: #3e2723; color: #ffb74d; border: 1px solid #ef6c00; }
        .grade-c { background: #2a1b3d; color: #b388ff; border: 1px solid #7c4dff; }
        .grade-d { background: #4a1515; color: #ff8a8a; border: 1px solid #d32f2f; }
    </style>
</head>
<body>
<div class="container" style="max-width: 800px;">
    {{ theme_form | safe }}
    <h2>🎯 Dynasty Draft Analyzer</h2>
    <div class="nav-tabs">
        <a href="/" class="nav-btn">⚖️ Trade Calculator</a>
        <a href="/analysis" class="nav-btn">📊 Team Rankings</a>
        <a href="/rookie-draft" class="nav-btn">📋 Live Draft Board</a>
        <a href="/league-feed" class="nav-btn">⚡ League Feed</a>
        <a href="/hall-of-fame" class="nav-btn">🏆 Hall of Fame</a>
        <a href="/trends" class="nav-btn">📈 Trends</a>
        <a href="/draft-analyzer" class="nav-btn active">🎯 Draft Analyzer</a>
    </div>

    <form method="POST" action="/draft-analyzer">
        <div class="sync-box">
            <small><b>⚡ Sync League for Draft Analysis:</b></small>
            <div class="sync-inputs">
                <input type="text" name="sleeper_input" placeholder="Username or League ID" value="{{ sleeper_input }}">
                <button type="submit" name="action" value="sync" style="width: auto; margin-top:0; padding: 8px 12px;">Fetch Leagues</button>
            </div>

            {% if user_leagues %}
                <div style="margin-top: 10px;">
                    <small><b>Select League:</b></small>
                    <select name="sleeper_league_id" style="width: 100%; margin-top: 4px;">
                        {% for lg in user_leagues %}
                            <option value="{{ lg.id }}" {% if selected_league_id == lg.id %}selected{% endif %}>{{ lg.name }} ({{ lg.season }})</option>
                        {% endfor %}
                    </select>
                    <button type="submit" name="action" value="analyze_draft" style="background: {{ t['primary'] }}; padding: 8px; margin-top: 6px; font-size: 0.9em;">Analyze Draft Board</button>
                </div>
            {% endif %}

            {% if sleeper_msg %}
                <div class="sync-msg">{{ sleeper_msg }}</div>
            {% endif %}
        </div>
    </form>

    {% if draft_results %}
        <div style="margin-top: 20px;">
            <h3 style="color: {{ t['primary'] }};">🏆 Team Draft Value & Grades</h3>
            {% for team_name, data in draft_results.team_grades.items() %}
                <div class="draft-summary-card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; flex-wrap:wrap; gap:6px;">
                        <b style="font-size: 1.1em; color: {{ t['primary'] }};">{{ team_name }}</b>
                        <div>
                            <span class="badge-grade {% if data.grade == 'S' %}grade-s{% elif data.grade == 'A' %}grade-a{% elif data.grade == 'B' %}grade-b{% elif data.grade == 'C' %}grade-c{% else %}grade-d{% endif %}">Grade: {{ data.grade }}</span>
                            <span style="margin-left: 8px; font-weight: bold;">{{ "{:,}".format(data.total_value) }} pts</span>
                        </div>
                    </div>
                    <small style="color: {{ t['subtext'] }};">Picks made: {{ data.picks_count }}</small>
                    <div style="margin-top: 8px;">
                        {% for pick in data.picks %}
                            <div class="pick-row">
                                <span>Rd {{ pick.round }}, Pick {{ pick.pick_no }} (Overall {{ pick.overall }})<br><strong>{{ pick.player_name }}</strong></span>
                                <span style="text-align: right;">{{ "{:,}".format(pick.value) }} pts<br><small style="color: {{ t['primary'] }};">Expected: ~{{ "{:,}".format(pick.expected_value) }} pts</small></span>
                            </div>
                        {% endfor %}
                    </div>
                </div>
            {% endfor %}
        </div>
    {% else %}
        <div style="text-align: center; padding: 30px; color: {{ t['subtext'] }};">
            <p>Select your league above and click "Analyze Draft Board" to evaluate rookie drafts, pick values, and manager draft grades.</p>
        </div>
    {% endif %}
</div>
</body>
</html>
"""


def get_current_theme_data():
  theme_key = session.get("theme", "dark")
  if theme_key not in THEMES:
    theme_key = "dark"

  t = dict(THEMES[theme_key])

  fav_team = session.get("favorite_team")
  if fav_team and fav_team in NFL_TEAMS:
    team_info = NFL_TEAMS[fav_team]
    t["primary"] = team_info["primary"]
    sec_color = team_info["secondary"]
    t["primary_hover"] = (
        sec_color
        if sec_color and sec_color != "#000000"
        else team_info["primary"]
    )

  return theme_key, t


def fetch_sleeper_api(url):
  try:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=5, context=ctx) as resp:
      return json.loads(resp.read().decode("utf-8"))
  except Exception:
    return None


def get_fantasycalc_player_data(is_superflex=False):
  num_qbs = 2 if is_superflex else 1
  cache_key = f"sf_{num_qbs}"

  if os.path.exists(VALUES_CACHE_FILE):
    try:
      with open(VALUES_CACHE_FILE, "r") as f:
        cache_data = json.load(f)
        if cache_key in cache_data:
          cached_time = cache_data[cache_key].get("timestamp", 0)
          if time.time() - cached_time < CACHE_EXPIRATION_SECONDS:
            return (
                cache_data[cache_key].get("players"),
                cache_data[cache_key].get("id_map", {}),
            )
    except Exception:
      pass

  url = f"https://api.fantasycalc.com/values/current?isDynasty=true&numQbs={num_qbs}&numTeams=12&ppr=1"
  data = fetch_sleeper_api(url)

  live_players = {
      "Quarterbacks": {},
      "Running Backs": {},
      "Wide Receivers": {},
      "Tight Ends": {},
      "Draft Picks": dict(DEFAULT_PLAYERS["Draft Picks"]),
  }
  id_map = {}

  if isinstance(data, list) and len(data) > 0:
    pos_map = {
        "QB": "Quarterbacks",
        "RB": "Running Backs",
        "WR": "Wide Receivers",
        "TE": "Tight Ends",
    }

    for item in data:
      pinfo = item.get("player", {})
      pid = str(pinfo.get("id", ""))
      fname = pinfo.get("name")
      pos = pinfo.get("position")
      val = item.get("value", 800)

      if fname and pos in pos_map:
        formatted_name = f"{fname} ({pos})"
        val_int = int(val)
        live_players[pos_map[pos]][formatted_name] = val_int
        if pid:
          id_map[pid] = {"name": formatted_name, "val": val_int}

    try:
      cache_data = {}
      if os.path.exists(VALUES_CACHE_FILE):
        with open(VALUES_CACHE_FILE, "r") as f:
          cache_data = json.load(f)
      cache_data[cache_key] = {
          "timestamp": time.time(),
          "players": live_players,
          "id_map": id_map,
      }
      with open(VALUES_CACHE_FILE, "w") as f:
        json.dump(cache_data, f)
    except Exception:
      pass

    return live_players, id_map

  return DEFAULT_PLAYERS, {}


def fetch_live_fantasycalc_values(is_superflex=False):
  players, _ = get_fantasycalc_player_data(is_superflex)
  return players


def get_sleeper_player_map():
  if os.path.exists(PLAYER_CACHE_FILE):
    try:
      with open(PLAYER_CACHE_FILE, "r") as f:
        return json.load(f)
    except Exception:
      pass

  data = fetch_sleeper_api("https://api.sleeper.app/v1/players/nfl")
  if isinstance(data, dict):
    player_map = {}
    for pid, pinfo in data.items():
      fname = pinfo.get("first_name", "")
      lname = pinfo.get("last_name", "")
      pos = pinfo.get("position", "")
      if fname and lname and pos in ["QB", "RB", "WR", "TE"]:
        player_map[str(pid)] = f"{fname} {lname} ({pos})"
    try:
      with open(PLAYER_CACHE_FILE, "w") as f:
        json.dump(player_map, f)
    except Exception:
      pass
    return player_map
  return {}


def process_sleeper_sync(sleeper_input, selected_league_id):
  user_leagues = session.get("user_leagues", [])
  target_league = None
  owner_rosters = {}
  league_owners = []

  sleeper_input = str(sleeper_input) if sleeper_input else ""
  selected_league_id = str(selected_league_id) if selected_league_id else ""

  try:
    if sleeper_input and not sleeper_input.isdigit() and not selected_league_id:
      user_data = fetch_sleeper_api(
          f"https://api.sleeper.app/v1/user/{sleeper_input}"
      )
      if not user_data or not isinstance(user_data, dict):
        return (
            f"Error: Could not find Sleeper user '{sleeper_input}'. Please check"
            " your username."
        )

      uid = user_data.get("user_id")
      if not uid:
        return f"Error: Invalid user data returned for '{sleeper_input}'."

      leagues_2026 = (
          fetch_sleeper_api(
              f"https://api.sleeper.app/v1/user/{uid}/leagues/nfl/2026"
          )
          or []
      )
      leagues_2025 = (
          fetch_sleeper_api(
              f"https://api.sleeper.app/v1/user/{uid}/leagues/nfl/2025"
          )
          or []
      )
      all_leagues = (
          leagues_2026 if isinstance(leagues_2026, list) else []
      ) + (leagues_2025 if isinstance(leagues_2025, list) else [])

      if all_leagues:
        user_leagues = [
            {
                "id": l["league_id"],
                "name": l.get("name", "Unnamed League"),
                "season": l.get("season", ""),
            }
            for l in all_leagues
            if "league_id" in l
        ]
        session["user_leagues"] = user_leagues
        return (
            f"Found {len(user_leagues)} leagues for {sleeper_input}. Please"
            " select your league below and click Sync Selected League."
        )
      else:
        return (
            f"No 2025 or 2026 NFL leagues found for username '{sleeper_input}'."
        )

    if selected_league_id:
      target_league = fetch_sleeper_api(
          f"https://api.sleeper.app/v1/league/{selected_league_id}"
      )
    elif sleeper_input.isdigit():
      selected_league_id = sleeper_input
      target_league = fetch_sleeper_api(
          f"https://api.sleeper.app/v1/league/{selected_league_id}"
      )

    if not target_league:
      return (
          f"Error: Could not fetch league details for ID '{selected_league_id}'."
          " Please verify the League ID."
      )

    if isinstance(target_league, dict) and "roster_positions" in target_league:
      roster_pos = target_league.get("roster_positions", [])
      is_league_sf = "SUPER_FLEX" in roster_pos or roster_pos.count("QB") > 1
      league_format = "Superflex" if is_league_sf else "1QB"
      lname = target_league.get("name", "Sleeper League")
      selected_league_id = target_league.get("league_id", "")

      session["selected_league_id"] = selected_league_id
      session["sleeper_input"] = sleeper_input
      session["league_format"] = league_format

      active_players, fc_id_map = get_fantasycalc_player_data(
          is_superflex=is_league_sf
      )

      users_data = (
          fetch_sleeper_api(
              f"https://api.sleeper.app/v1/league/{selected_league_id}/users"
          )
          or []
      )
      rosters_data = (
          fetch_sleeper_api(
              f"https://api.sleeper.app/v1/league/{selected_league_id}/rosters"
          )
          or []
      )
      traded_picks_data = (
          fetch_sleeper_api(
              f"https://api.sleeper.app/v1/league/{selected_league_id}/traded_picks"
          )
          or []
      )

      current_season = int(target_league.get("season", 2026))
      num_rounds = target_league.get("settings", {}).get("draft_rounds", 4)

      player_map = get_sleeper_player_map()
      user_id_to_name = {
          u["user_id"]: u.get("display_name", "Unknown")
          for u in users_data
          if "user_id" in u
      }
      league_owners = sorted(list(user_id_to_name.values()))

      roster_id_to_name = {}
      for r in rosters_data:
        r_id = r.get("roster_id")
        oid = r.get("owner_id")
        oname = user_id_to_name.get(oid)
        if r_id and oname:
          roster_id_to_name[r_id] = oname

      future_seasons = [
          str(current_season),
          str(current_season + 1),
          str(current_season + 2),
      ]
      pick_ownership = {}
      for r in rosters_data:
        r_id = r.get("roster_id")
        if r_id:
          for season in future_seasons:
            for rd in range(1, num_rounds + 1):
              pick_ownership[(season, rd, r_id)] = r_id

      if isinstance(traded_picks_data, list):
        for trade in traded_picks_data:
          season = str(trade.get("season"))
          rd = int(trade.get("round", 1))
          orig_owner = trade.get("roster_id")
          new_owner = trade.get("owner_id")
          if (season, rd, orig_owner) in pick_ownership:
            pick_ownership[(season, rd, orig_owner)] = new_owner

      flat_lookup = {}
      for pos, p_dict in active_players.items():
        for name, val in p_dict.items():
          flat_lookup[name] = val

      round_default_values = {1: 4800, 2: 2200, 3: 1000, 4: 500}

      for r in rosters_data:
        oid = r.get("owner_id")
        oname = user_id_to_name.get(oid)
        if not oname:
          continue
        roster_dict = {}
        if "players" in r and isinstance(r["players"], list):
          for pid in r["players"]:
            pid_str = str(pid)
            if pid_str in fc_id_map:
              pdata = fc_id_map[pid_str]
              roster_dict[pdata["name"]] = pdata["val"]
            else:
              pname = player_map.get(pid_str)
              if pname:
                val = flat_lookup.get(pname, 800)
                roster_dict[pname] = val
        owner_rosters[oname] = roster_dict

      pick_modifier = float(session.get("pick_modifier", 1.0))
      for (season, rd, orig_owner), current_owner_id in pick_ownership.items():
        current_owner_name = roster_id_to_name.get(current_owner_id)
        if current_owner_name and current_owner_name in owner_rosters:
          orig_owner_name = roster_id_to_name.get(
              orig_owner, f"Team {orig_owner}"
          )

          if rd == 1:
            pick_name = f"{season} Mid 1st Pick ({orig_owner_name})"
          elif rd == 2:
            pick_name = f"{season} 2nd Round Pick ({orig_owner_name})"
          elif rd == 3:
            pick_name = f"{season} 3rd Round Pick ({orig_owner_name})"
          else:
            pick_name = f"{season} {rd}th Round Pick ({orig_owner_name})"

          pick_val = int(round_default_values.get(rd, 500) * pick_modifier)
          owner_rosters[current_owner_name][pick_name] = pick_val

      session["owner_rosters"] = owner_rosters
      session["league_owners"] = league_owners
      return (
          f"Synced with '{lname}'! Rosters & traded picks loaded for"
          f" {len(owner_rosters)} managers."
      )
    else:
      return "Error: Invalid league data structure returned from Sleeper API."
  except Exception as err:
    return f"Roster fetch error: {str(err)}"


# ==========================================
# LIVE DRAFT TOOLS API & ROUTE HANDLERS
# ==========================================

@app.route("/api/rookies")
def api_rookies():
  return jsonify(ROOKIE_PROSPECTS)


@app.route("/api/all-players")
def api_all_players():
  format_arg = request.args.get("format", "1QB")
  draft_type = request.args.get("type", "startup")
  is_sf = format_arg == "Superflex"
  num_qbs = 2 if is_sf else 1
  url = f"https://api.fantasycalc.com/values/current?isDynasty=true&numQbs={num_qbs}&numTeams=12&ppr=1"
  data = fetch_sleeper_api(url)
  
  all_players_list = []
  if isinstance(data, list) and len(data) > 0:
    for idx, item in enumerate(data, start=1):
      pinfo = item.get("player", {})
      fname = pinfo.get("name")
      pos = pinfo.get("position")
      if not fname or pos not in ["QB", "RB", "WR", "TE"]:
        continue
      val = int(item.get("value", 800))
      
      if draft_type == "regular" and val > 7000:
        val = int(val * 0.95)

      adp = float(item.get("adp", item.get("overallRank", idx)))
      redraft_val = float(item.get("redraftValue", val * 0.4))
      projected_pts = int(redraft_val * 3.5 if redraft_val else val * 0.35)
      formatted_name = f"{fname} ({pos})"
      
      all_players_list.append({
          "id": idx,
          "name": formatted_name,
          "pos": pos,
          "team": pinfo.get("team", "NFL"),
          "val": val,
          "rank": idx,
          "adp": adp,
          "projected_points": projected_pts
      })
  
  if not all_players_list:
    rank_ctr = 1
    for pos_group, p_dict in DEFAULT_PLAYERS.items():
      if pos_group == "Draft Picks":
        continue
      pos_code = pos_group[:-1] if pos_group.endswith('s') else pos_group
      if "Quarter" in pos_group: pos_code = "QB"
      elif "Running" in pos_group: pos_code = "RB"
      elif "Wide" in pos_group: pos_code = "WR"
      elif "Tight" in pos_group: pos_code = "TE"
      for name, val in p_dict.items():
        all_players_list.append({
            "id": rank_ctr,
            "name": name,
            "pos": pos_code,
            "team": "NFL",
            "val": val,
            "rank": rank_ctr,
            "adp": rank_ctr,
            "projected_points": int(val * 0.35)
        })
        rank_ctr += 1

  all_players_list.sort(key=lambda x: x["val"], reverse=True)
  for i, p in enumerate(all_players_list, start=1):
    p["rank"] = i
    p["id"] = i

  return jsonify(all_players_list)


@app.route("/api/league-draft-info")
def api_league_draft_info():
  league_id = session.get("selected_league_id")
  if not league_id:
    return jsonify({"success": False, "message": "No league selected"})

  drafts = fetch_sleeper_api(f"https://api.sleeper.app/v1/league/{league_id}/drafts")
  if not drafts or not isinstance(drafts, list):
    target_league = fetch_sleeper_api(f"https://api.sleeper.app/v1/league/{league_id}")
    teams = target_league.get("total_rosters", 12) if target_league else 12
    return jsonify({"success": True, "teams": teams, "picks": []})

  draft = drafts[0]
  draft_id = draft.get("draft_id")
  teams = draft.get("settings", {}).get("teams", 12)
  rounds = draft.get("settings", {}).get("rounds", 4)
  total_picks = teams * rounds

  picks_data = fetch_sleeper_api(f"https://api.sleeper.app/v1/draft/{draft_id}/picks") or []
  users_data = fetch_sleeper_api(f"https://api.sleeper.app/v1/league/{league_id}/users") or []
  rosters_data = fetch_sleeper_api(f"https://api.sleeper.app/v1/league/{league_id}/rosters") or []

  user_id_to_name = {u["user_id"]: u.get("display_name", "Unknown") for u in users_data if "user_id" in u}
  roster_id_to_owner = {}
  for r in rosters_data:
    r_id = r.get("roster_id")
    oid = r.get("owner_id")
    if r_id and oid in user_id_to_name:
      roster_id_to_owner[r_id] = user_id_to_name[oid]

  slot_to_owner = {}
  draft_order = draft.get("draft_order", {})
  inv_draft_order = {str(slot): r_id for r_id, slot in draft_order.items()}

  for pick_no in range(1, total_picks + 1):
    round_num = ((pick_no - 1) // teams) + 1
    pick_in_round = ((pick_no - 1) % teams) + 1

    if round_num % 2 == 1:
      pos_in_round = pick_in_round
    else:
      pos_in_round = teams - pick_in_round + 1

    roster_id = inv_draft_order.get(str(pos_in_round))
    if roster_id and roster_id in roster_id_to_owner:
      slot_to_owner[pick_no] = roster_id_to_owner[roster_id]

  formatted_picks = []
  if isinstance(picks_data, list):
    player_map = get_sleeper_player_map()
    for p in picks_data:
      pick_no = p.get("pick_no")
      player_id = p.get("player_id")
      metadata = p.get("metadata", {})
      player_name = metadata.get("first_name", "") + " " + metadata.get("last_name", "")
      if not player_name.strip():
        player_name = player_map.get(str(player_id), player_id)

      formatted_picks.append({
          "pick_no": pick_no,
          "player_id": player_name or player_id,
      })

  return jsonify({
      "success": True,
      "draft_id": draft_id,
      "teams": teams,
      "rounds": rounds,
      "total_picks": total_picks,
      "slot_to_owner": slot_to_owner,
      "picks": formatted_picks,
  })


@app.route("/rookie-draft", methods=["GET", "POST"])
def rookie_draft():
  theme_key, t = get_current_theme_data()
  current_team = session.get("favorite_team", "")
  theme_form = render_theme_form(theme_key, current_team)
  shared_styles = get_shared_styles(t)

  sleeper_input = session.get("sleeper_input", "")
  selected_league_id = session.get("selected_league_id", "")
  user_leagues = session.get("user_leagues", [])
  sleeper_msg = ""

  if request.method == "POST":
    action = request.form.get("action")
    sleeper_input = request.form.get("sleeper_input", "").strip()
    form_league_id = request.form.get("sleeper_league_id", "").strip()
    if form_league_id:
      selected_league_id = form_league_id

    if action in ["sync", "select_league"] or (
        selected_league_id and selected_league_id != session.get("selected_league_id")
    ):
      sleeper_msg = process_sleeper_sync(sleeper_input, selected_league_id)

  return render_template_string(
      ROOKIE_DRAFT_TEMPLATE,
      t=t,
      theme_form=theme_form,
      shared_styles=shared_styles,
      sleeper_input=sleeper_input,
      selected_league_id=selected_league_id,
      user_leagues=user_leagues,
      sleeper_msg=sleeper_msg,
  )


@app.route("/analysis", methods=["GET", "POST"])
def analysis_route():
  theme_key, t = get_current_theme_data()
  current_team = session.get("favorite_team", "")
  theme_form = render_theme_form(theme_key, current_team)
  shared_styles = get_shared_styles(t)

  sleeper_input = session.get("sleeper_input", "")
  selected_league_id = session.get("selected_league_id", "")
  user_leagues = session.get("user_leagues", [])
  owner_rosters = session.get("owner_rosters", {})
  sleeper_msg = ""
  power_rankings = []

  if request.method == "POST":
    action = request.form.get("action")
    sleeper_input = request.form.get("sleeper_input", "").strip()
    form_league_id = request.form.get("sleeper_league_id", "").strip()
    if form_league_id:
      selected_league_id = form_league_id

    if action in ["sync", "select_league"] or (
        selected_league_id and selected_league_id != session.get("selected_league_id")
    ):
      sleeper_msg = process_sleeper_sync(sleeper_input, selected_league_id)
      owner_rosters = session.get("owner_rosters", {})

  if owner_rosters:
    for name, roster in owner_rosters.items():
      qb_val = sum(val for p_name, val in roster.items() if "(QB)" in p_name)
      rb_val = sum(val for p_name, val in roster.items() if "(RB)" in p_name)
      wr_val = sum(val for p_name, val in roster.items() if "(WR)" in p_name)
      te_val = sum(val for p_name, val in roster.items() if "(TE)" in p_name)
      pick_val = sum(val for p_name, val in roster.items() if "Pick" in p_name or "Round" in p_name)
      total_val = sum(roster.values())

      archetype = "Contender" if total_val > 50000 else ("Playoff Threat" if total_val > 38000 else "Rebuilder")
      power_rankings.append({
          "name": name,
          "total_val": total_val,
          "qb_val": qb_val,
          "rb_val": rb_val,
          "wr_val": wr_val,
          "te_val": te_val,
          "pick_val": pick_val,
          "archetype": archetype
      })
    power_rankings.sort(key=lambda x: x["total_val"], reverse=True)

  return render_template_string(
      ANALYSIS_TEMPLATE,
      t=t,
      theme_form=theme_form,
      shared_styles=shared_styles,
      sleeper_input=sleeper_input,
      selected_league_id=selected_league_id,
      user_leagues=user_leagues,
      sleeper_msg=sleeper_msg,
      power_rankings=power_rankings
  )


@app.route("/league-feed")
def league_feed():
  theme_key, t = get_current_theme_data()
  current_team = session.get("favorite_team", "")
  theme_form = render_theme_form(theme_key, current_team)
  shared_styles = get_shared_styles(t)
  league_id = request.args.get("league_id", session.get("selected_league_id", ""))
  transactions = []
  if league_id:
    tx_data = fetch_sleeper_api(f"https://api.sleeper.app/v1/league/{league_id}/transactions/1")
    if isinstance(tx_data, list):
      for tx in tx_data:
        transactions.append({
            "type": tx.get("type", "Transaction").title(),
            "week": tx.get("week", 1)
        })
  return render_template_string(
      LEAGUE_FEED_TEMPLATE,
      t=t,
      theme_form=theme_form,
      shared_styles=shared_styles,
      league_id=league_id,
      transactions=transactions
  )


@app.route("/hall-of-fame")
def hall_of_fame():
  theme_key, t = get_current_theme_data()
  current_team = session.get("favorite_team", "")
  theme_form = render_theme_form(theme_key, current_team)
  shared_styles = get_shared_styles(t)
  return render_template_string(HOF_TEMPLATE, t=t, theme_form=theme_form, shared_styles=shared_styles)


@app.route("/trends")
def trends():
  theme_key, t = get_current_theme_data()
  current_team = session.get("favorite_team", "")
  theme_form = render_theme_form(theme_key, current_team)
  shared_styles = get_shared_styles(t)
  sample_trends = {
      "Ja'Marr Chase (WR)": [{"value": 9100}, {"value": 9300}, {"value": 9500}],
      "Bijan Robinson (RB)": [{"value": 8500}, {"value": 8700}, {"value": 8900}],
      "Josh Allen (QB)": [{"value": 8200}, {"value": 8300}, {"value": 8400}],
      "Brock Bowers (TE)": [{"value": 7200}, {"value": 7500}, {"value": 7800}]
  }
  return render_template_string(
      TRENDS_TEMPLATE,
      t=t,
      theme_form=theme_form,
      shared_styles=shared_styles,
      trends=json.dumps(sample_trends)
  )


@app.route("/draft-analyzer", methods=["GET", "POST"])
def draft_analyzer():
  theme_key, t = get_current_theme_data()
  current_team = session.get("favorite_team", "")
  theme_form = render_theme_form(theme_key, current_team)
  shared_styles = get_shared_styles(t)

  sleeper_input = session.get("sleeper_input", "")
  selected_league_id = session.get("selected_league_id", "")
  user_leagues = session.get("user_leagues", [])
  sleeper_msg = ""
  draft_results = None

  if request.method == "POST":
    action = request.form.get("action")
    sleeper_input = request.form.get("sleeper_input", "").strip()
    form_league_id = request.form.get("sleeper_league_id", "").strip()
    if form_league_id:
      selected_league_id = form_league_id

    if action in ["sync", "select_league"] or (
        selected_league_id and selected_league_id != session.get("selected_league_id")
    ):
      sleeper_msg = process_sleeper_sync(sleeper_input, selected_league_id)

    if action == "analyze_draft" and selected_league_id:
      draft_results = {"team_grades": {}}
      drafts = fetch_sleeper_api(f"https://api.sleeper.app/v1/league/{selected_league_id}/drafts")
      if drafts and isinstance(drafts, list):
        draft_id = drafts[0].get("draft_id")
        picks = fetch_sleeper_api(f"https://api.sleeper.app/v1/draft/{draft_id}/picks") or []
        users_data = fetch_sleeper_api(f"https://api.sleeper.app/v1/league/{selected_league_id}/users") or []
        rosters_data = fetch_sleeper_api(f"https://api.sleeper.app/v1/league/{selected_league_id}/rosters") or []
        user_id_to_name = {u["user_id"]: u.get("display_name", "Unknown") for u in users_data}
        roster_to_owner = {r.get("roster_id"): user_id_to_name.get(r.get("owner_id"), "Team") for r in rosters_data}

        team_picks_map = {}
        for p in picks:
          owner_id = p.get("roster_id")
          owner_name = roster_to_owner.get(owner_id, "Team")
          if owner_name not in team_picks_map:
            team_picks_map[owner_name] = []
          
          metadata = p.get("metadata", {})
          p_name = f"{metadata.get('first_name', '')} {metadata.get('last_name', '')}".strip() or "Prospect"
          pick_no = p.get("pick_no", 1)
          round_no = p.get("round", 1)
          overall = pick_no
          val = max(1000, 6000 - (overall * 100))
          expected = val - 200

          team_picks_map[owner_name].append({
              "round": round_no,
              "pick_no": ((pick_no - 1) % 12) + 1,
              "overall": overall,
              "player_name": p_name,
              "value": val,
              "expected_value": expected
          })

        team_grades = {}
        for t_name, t_picks in team_picks_map.items():
          tot_val = sum(tp["value"] for tp in t_picks)
          grade = "S" if tot_val > 15000 else ("A" if tot_val > 12000 else ("B" if tot_val > 9000 else "C"))
          team_grades[t_name] = {
              "total_value": tot_val,
              "grade": grade,
              "picks_count": len(t_picks),
              "picks": t_picks
          }
        draft_results["team_grades"] = team_grades

  return render_template_string(
      DRAFT_ANALYZER_TEMPLATE,
      t=t,
      theme_form=theme_form,
      shared_styles=shared_styles,
      sleeper_input=sleeper_input,
      selected_league_id=selected_league_id,
      user_leagues=user_leagues,
      sleeper_msg=sleeper_msg,
      draft_results=draft_results
  )


@app.errorhandler(Exception)
def handle_exception(e):
  theme_key, t = get_current_theme_data()
  return (
      f"""
    <div style="font-family: sans-serif; padding: 20px; color: {t['text']}; background: {t['bg']};">
        <h3>⚠️ App Exception Handler</h3>
        <p style="color: #ff5252;">{str(e)}</p>
        <a href="/" style="color: {t['primary']};">Return to Calculator</a>
    </div>
    """,
      500,
  )


@app.route("/set-theme", methods=["POST"])
def set_theme():
  choice = request.form.get("theme_choice", "dark")
  if choice in THEMES:
    session["theme"] = choice
  return redirect(request.referrer or "/")


@app.route("/set-preference", methods=["POST"])
def set_preference():
  choice = request.form.get("theme_choice")
  if choice in THEMES:
    session["theme"] = choice
  fav_team = request.form.get("favorite_team")
  if fav_team in NFL_TEAMS or fav_team == "":
    session["favorite_team"] = fav_team
  return redirect(request.referrer or "/")


@app.route("/", methods=["GET", "POST"])
def home():
  theme_key, t = get_current_theme_data()
  current_team = session.get("favorite_team", "")
  theme_form = render_theme_form(theme_key, current_team)
  shared_styles = get_shared_styles(t)

  result = None
  league_format = session.get("league_format", "1QB")
  sleeper_input = session.get("sleeper_input", "")
  selected_league_id = session.get("selected_league_id", "")
  selected_owner_a = session.get("selected_owner_a", "")
  selected_owner_b = session.get("selected_owner_b", "")
  pick_modifier = session.get("pick_modifier", 1.0)
  smart_strategy = session.get("smart_strategy", "balanced")
  target_player_filter = session.get("target_player_filter", "")
  smart_page = session.get("smart_page", 0)
  sleeper_msg = ""

  user_leagues = session.get("user_leagues", [])
  league_owners = session.get("league_owners", [])
  owner_rosters = session.get("owner_rosters", {})

  selected_assets = {"team_a": [], "team_b": []}
  custom_assets = {
      "team_a": {"name": "", "val": ""},
      "team_b": {"name": "", "val": ""},
  }

  if request.method == "POST":
    action = request.form.get("action", "analyze")
    league_format = request.form.get("league_format", "1QB")
    sleeper_input = request.form.get("sleeper_input", "").strip()
    form_league_id = request.form.get("sleeper_league_id", "").strip()

    if form_league_id:
      selected_league_id = form_league_id

    selected_owner_a = request.form.get("owner_a", "")
    selected_owner_b = request.form.get("owner_b", "")
    smart_strategy = request.form.get("smart_strategy", "balanced")
    target_player_filter = (
        request.form.get("target_player_filter", "").strip().lower()
    )

    session["selected_owner_a"] = selected_owner_a
    session["selected_owner_b"] = selected_owner_b
    session["league_format"] = league_format
    session["smart_strategy"] = smart_strategy
    session["target_player_filter"] = target_player_filter

    try:
      smart_page = int(request.form.get("smart_page", "0"))
    except ValueError:
      smart_page = 0

    if action == "smart_suggestion":
      smart_page = 0
    elif action == "smart_more":
      smart_page += 1
    session["smart_page"] = smart_page

    try:
      pick_modifier = float(request.form.get("pick_modifier", "1.0"))
      session["pick_modifier"] = pick_modifier
    except ValueError:
      pick_modifier = 1.0

    if action in ["sync", "select_league"] or (
        selected_league_id
        and (
            selected_league_id != session.get("selected_league_id")
            or not owner_rosters
        )
    ):
      sleeper_msg = process_sleeper_sync(sleeper_input, selected_league_id)
      owner_rosters = session.get("owner_rosters", {})
      league_owners = session.get("league_owners", [])

    if action == "clear_trade":
      selected_assets = {"team_a": [], "team_b": []}
      custom_assets = {
          "team_a": {"name": "", "val": ""},
          "team_b": {"name": "", "val": ""},
      }

  is_sf = league_format == "Superflex"
  active_players = fetch_live_fantasycalc_values(is_superflex=is_sf)

  if request.method == "POST" and request.form.get("action") not in [
      "sync",
      "select_league",
      "clear_trade",
  ]:
    flat_players = {}
    for pos, p_dict in active_players.items():
      for name, val in p_dict.items():
        is_pick = "Pick" in name
        flat_players[name] = int(val * pick_modifier) if is_pick else val

    selected_assets["team_a"] = request.form.getlist("team_a")
    selected_assets["team_b"] = request.form.getlist("team_b")

    a_cname = request.form.get("team_a_custom_name", "").strip()
    a_cval = request.form.get("team_a_custom_val", "")
    b_cname = request.form.get("team_b_custom_name", "").strip()
    b_cval = request.form.get("team_b_custom_val", "")

    custom_assets["team_a"] = {"name": a_cname, "val": a_cval}
    custom_assets["team_b"] = {"name": b_cname, "val": b_cval}

    a_custom_num = int(a_cval) if a_cval.isdigit() else 0
    b_custom_num = int(b_cval) if b_cval.isdigit() else 0

    counter_msg = ""
    smart_suggestions = []
    action = request.form.get("action", "analyze")

    if action in ["smart_suggestion", "smart_more"]:
      if not selected_owner_a:
        counter_msg = (
            "⚠️ Please select your team (Team A) from the dropdown above to use the Smart Trade Finder."
        )
      else:
        user_roster = owner_rosters.get(selected_owner_a, {})
        candidates = []
        for partner_name, partner_roster in owner_rosters.items():
          if partner_name != selected_owner_a:
            for give_item, give_val in user_roster.items():
              for get_item, get_val in partner_roster.items():
                if target_player_filter and target_player_filter not in get_item.lower():
                  continue
                diff_val = abs(give_val - get_val)
                if diff_val < 2000:
                  candidates.append({
                      "partner": partner_name,
                      "gives": give_item,
                      "gives_val": give_val,
                      "gets": get_item,
                      "gets_val": get_val,
                      "diff": diff_val
                  })
        candidates.sort(key=lambda x: x["diff"])
        chunk_size = 3
        start_idx = (smart_page * chunk_size) % max(1, len(candidates))
        smart_suggestions = candidates[start_idx:start_idx + chunk_size]

    a_items = []
    a_total = 0
    for name in selected_assets["team_a"]:
      val = flat_players.get(name, 800)
      a_items.append({"name": name, "val": val})
      a_total += val
    if a_cname:
      a_items.append({"name": a_cname, "val": a_custom_num})
      a_total += a_custom_num

    b_items = []
    b_total = 0
    for name in selected_assets["team_b"]:
      val = flat_players.get(name, 800)
      b_items.append({"name": name, "val": val})
      b_total += val
    if b_cname:
      b_items.append({"name": b_cname, "val": b_custom_num})
      b_total += b_custom_num

    diff = a_total - b_total
    if abs(diff) < 300:
      msg = "⚖️ Fair Trade! Both sides are balanced."
      balancer_msg = ""
    elif diff > 0:
      msg = f"📉 Team A wins by {abs(diff):,} pts (Overpay by Team A)"
      balancer_msg = f"Tip: Team B should add an asset worth around {abs(diff):,} pts to balance this trade."
    else:
      msg = f"📈 Team B wins by {abs(diff):,} pts (Overpay by Team B)"
      balancer_msg = f"Tip: Team A should add an asset worth around {abs(diff):,} pts to balance this trade."

    stud_msg = ""
    if any("Mahomes" in item["name"] or "Allen" in item["name"] or "Chase" in item["name"] for item in a_items + b_items):
      msg += " 🔥 Elite Stud Involved!"

    itemized_summary_text = f"Dynasty Trade Breakdown:\n{selected_owner_a or 'Team A'} Gives:\n"
    for item in a_items:
      itemized_summary_text += f"- {item['name']} ({item['val']:,} pts)\n"
    itemized_summary_text += f"Total: {a_total:,} pts\n\n{selected_owner_b or 'Team B'} Gives:\n"
    for item in b_items:
      itemized_summary_text += f"- {item['name']} ({item['val']:,} pts)\n"
    itemized_summary_text += f"Total: {b_total:,} pts\n\nAssessment: {msg}"

    result = {
        "team_a_items": a_items,
        "team_a_total": a_total,
        "team_b_items": b_items,
        "team_b_total": b_total,
        "message": msg,
        "balancer_msg": balancer_msg,
        "stud_msg": stud_msg,
        "counter_msg": counter_msg,
        "smart_suggestions": smart_suggestions,
        "itemized_summary_text": itemized_summary_text
    }

  player_groups = active_players
  return render_template_string(
      CALCULATOR_TEMPLATE,
      t=t,
      theme_form=theme_form,
      shared_styles=shared_styles,
      league_format=league_format,
      player_groups=player_groups,
      user_leagues=user_leagues,
      league_owners=league_owners,
      owner_rosters=owner_rosters,
      selected_league_id=selected_league_id,
      selected_owner_a=selected_owner_a,
      selected_owner_b=selected_owner_b,
      sleeper_input=sleeper_input,
      pick_modifier=pick_modifier,
      smart_strategy=smart_strategy,
      smart_strategy_label=smart_strategy.replace('_', ' ').title(),
      target_player_filter=target_player_filter,
      smart_page=smart_page,
      selected_assets=selected_assets,
      custom_assets=custom_assets,
      result=result,
      sleeper_msg=sleeper_msg
  )


if __name__ == "__main__":
  app.run(debug=True, port=5000)
