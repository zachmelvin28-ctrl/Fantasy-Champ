@app.route('/favicon.ico')
@app.route('/favicon.png')
def favicon():
    return '', 204


from itertools import combinations
import json
import os
import ssl
import time
import urllib.request
from flask import Flask, jsonify, render_template_string, request, session

app = Flask(__name__)
app.secret_key = "dynasty_trade_calc_secret_key_2026"

PLAYER_CACHE_FILE = "sleeper_players.json"
VALUES_CACHE_FILE = "fantasycalc_cache.json"
CACHE_EXPIRATION_SECONDS = 86400  # 24 Hours

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
        "DJ Giddens (RB)": 1200,
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
        "Puka Nacua (WR)": 7600,
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
        "Tory Horton (WR)": 1100,
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
    {
        "id": 1,
        "name": "Jeremiyah Love",
        "pos": "RB",
        "team": "Arizona Cardinals",
        "rank": 1,
    },
    {
        "id": 2,
        "name": "Carnell Tate",
        "pos": "WR",
        "team": "Tennessee Titans",
        "rank": 2,
    },
    {
        "id": 3,
        "name": "Jordyn Tyson",
        "pos": "WR",
        "team": "New Orleans Saints",
        "rank": 3,
    },
    {
        "id": 4,
        "name": "Makai Lemon",
        "pos": "WR",
        "team": "Philadelphia Eagles",
        "rank": 4,
    },
    {
        "id": 5,
        "name": "Jadarian Price",
        "pos": "RB",
        "team": "Seattle Seahawks",
        "rank": 5,
    },
    {
        "id": 6,
        "name": "KC Concepcion",
        "pos": "WR",
        "team": "Cleveland Browns",
        "rank": 6,
    },
    {
        "id": 7,
        "name": "Fernando Mendoza",
        "pos": "QB",
        "team": "Las Vegas Raiders",
        "rank": 7,
    },
    {
        "id": 8,
        "name": "Kenyon Sadiq",
        "pos": "TE",
        "team": "New York Jets",
        "rank": 8,
    },
    {
        "id": 9,
        "name": "Omar Cooper Jr.",
        "pos": "WR",
        "team": "New York Jets",
        "rank": 9,
    },
    {
        "id": 10,
        "name": "Denzel Boston",
        "pos": "WR",
        "team": "Cleveland Browns",
        "rank": 10,
    },
]

SHARED_STYLES = """
    body { font-family: -apple-system, sans-serif; padding: 15px; background: #121212; color: #e0e0e0; margin: 0; }
    .container { max-width: 650px; margin: 0 auto; background: #1e1e1e; padding: 20px; border-radius: 12px; }
    h2 { text-align: center; color: #fff; margin-top: 0; }
    .nav-tabs { display: flex; gap: 8px; margin-bottom: 20px; background: #181818; padding: 6px; border-radius: 8px; border: 1px solid #333; overflow-x: auto; }
    .nav-btn { flex: 1; text-align: center; padding: 10px; background: #262626; color: #bbb; text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 0.9em; white-space: nowrap; }
    .nav-btn.active { background: #007bff; color: white; }
    .sync-box { background: #222d38; border: 1px solid #1e88e5; padding: 12px; border-radius: 8px; margin-bottom: 15px; }
    .sync-inputs { display: flex; gap: 8px; margin-top: 6px; }
    input[type="text"], input[type="number"], select { background: #333; color: #fff; border: 1px solid #555; padding: 8px; border-radius: 4px; }
    input[type="text"] { flex: 2; }
    button { width: 100%; padding: 14px; background: #007bff; color: white; border: none; border-radius: 6px; font-weight: bold; font-size: 16px; margin-top: 10px; cursor: pointer; }
    .sync-msg { font-size: 0.85em; color: #29b6f6; margin-top: 6px; font-weight: bold; }
    .rank-card { background: #262626; border: 1px solid #3a3a3a; padding: 12px 15px; border-radius: 8px; margin-bottom: 12px; }
    .rank-header { display: flex; justify-content: space-between; align-items: center; font-size: 1.1em; font-weight: bold; color: #64b5f6; margin-bottom: 6px; }
    .badge { padding: 3px 8px; border-radius: 4px; font-size: 0.75em; text-transform: uppercase; font-weight: bold; }
    .badge-contender { background: #1b3320; color: #81c784; border: 1px solid #2e7d32; }
    .badge-playoff { background: #00363a; color: #4dd0e1; border: 1px solid #00acc1; }
    .badge-rebuild { background: #3e2723; color: #ffb74d; border: 1px solid #ef6c00; }
    .breakdown-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 6px; text-align: center; margin-top: 8px; background: #1a1a1a; padding: 8px; border-radius: 6px; font-size: 0.85em; }
    .breakdown-item span { display: block; color: #aaa; font-size: 0.75em; }
"""

CALCULATOR_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Dynasty Trade Calculator</title>
    <style>
        {{ shared_styles }}
        .toggle-group { display: flex; justify-content: space-around; background: #2a2a2a; padding: 10px; border-radius: 8px; margin-bottom: 15px; }
        .toggle-group label { cursor: pointer; font-weight: bold; }
        .team-section { background: #262626; padding: 15px; border-radius: 8px; margin-bottom: 20px; border: 1px solid #333; }
        .team-title { font-size: 1.1em; color: #007bff; margin-bottom: 10px; font-weight: bold; }
        .roster-box { background: #1a2733; border: 1px solid #29b6f6; padding: 10px; border-radius: 6px; margin-bottom: 12px; }
        .search-box { width: 100%; box-sizing: border-box; margin-bottom: 12px; padding: 8px; background: #181818; color: #fff; border: 1px solid #444; border-radius: 6px; }
        details { background: #1e1e1e; margin-bottom: 8px; border-radius: 6px; padding: 8px; border: 1px solid #3a3a3a; }
        summary { font-weight: bold; cursor: pointer; color: #64b5f6; }
        .checkbox-grid { display: grid; grid-template-columns: 1fr; gap: 6px; margin-top: 8px; }
        .checkbox-item { display: flex; align-items: center; background: #2a2a2a; padding: 8px; border-radius: 4px; font-size: 0.95em; }
        .checkbox-item input { margin-right: 10px; transform: scale(1.2); }
        .custom-entry { margin-top: 12px; padding-top: 10px; border-top: 1px dashed #444; }
        .custom-inputs { display: flex; gap: 8px; margin-top: 6px; }
        input[type="number"] { flex: 1; }
        .btn-copy { background: #28a745; margin-top: 12px; }
        .btn-clear { background: #d9534f; margin-top: 10px; }
        .btn-suggest { background: #673ab7; margin-top: 10px; }
        .btn-smart { background: #00acc1; margin-top: 10px; }
        .btn-smart-more { background: #00796b; margin-top: 6px; }
        .result { margin-top: 20px; padding: 15px; border-radius: 8px; text-align: center; background: #2a2a2a; border: 1px solid #007bff; }
        .note { font-size: 0.9em; color: #ffca28; margin-top: 8px; }
        .suggestion { font-size: 0.95em; color: #81c784; margin-top: 10px; background: #1b3320; padding: 10px; border-radius: 6px; }
        .counter-msg { font-size: 0.95em; color: #b388ff; margin-top: 10px; background: #2a1b3d; border: 1px solid #7c4dff; padding: 10px; border-radius: 6px; }
        .smart-container { text-align: left; margin-top: 12px; }
        .smart-card { font-size: 0.95em; color: #4dd0e1; margin-top: 8px; background: #00363a; border: 1px solid #00acc1; padding: 10px; border-radius: 6px; }
        .pick-adjuster { background: #242424; padding: 8px; border-radius: 6px; margin-bottom: 15px; display: flex; justify-content: space-between; align-items: center; }
        .smart-options { background: #222d38; border: 1px solid #00acc1; padding: 12px; border-radius: 8px; margin-bottom: 15px; }
    </style>
</head>
<body>
<div class="container">
    <h2>🏈 Dynasty Suite</h2>
    
    <div class="nav-tabs">
        <a href="/" class="nav-btn active">⚖️ Trade Calculator</a>
        <a href="/analysis" class="nav-btn">📊 Team Rankings</a>
        <a href="/rookie-draft" class="nav-btn">📋 Rookie Mock</a>
        <a href="/league-feed" class="nav-btn">⚡ League Feed</a>
        <a href="/hall-of-fame" class="nav-btn">🏆 Hall of Fame</a>
        <a href="/trends" class="nav-btn">📈 Trends</a>
    </div>
    
    <form method="POST" id="calcForm">
        <input type="hidden" name="smart_page" id="smart_page" value="{{ smart_page }}">

        <div class="sync-box">
            <small><b>⚡ Sleeper App Sync:</b></small>
            <div class="sync-inputs">
                <input type="text" name="sleeper_input" id="sleeper_input" placeholder="Sleeper Username or League ID" value="{{ sleeper_input }}">
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
                    <button type="submit" name="action" value="select_league" style="background: #1e88e5; padding: 8px; margin-top: 6px; font-size: 0.9em;">Sync Selected League</button>
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
            <select name="pick_modifier" style="width: auto; padding: 4px;" onchange="document.getElementById('calcForm').submit()">
                <option value="1.0" {% if pick_modifier == 1.0 %}selected{% endif %}>Standard (100%)</option>
                <option value="1.15" {% if pick_modifier == 1.15 %}selected{% endif %}>Draft SZN Hype (+15%)</option>
                <option value="0.85" {% if pick_modifier == 0.85 %}selected{% endif %}>In-Season Contender (-15%)</option>
            </select>
        </div>

        {% if league_owners %}
            <div style="background: #242424; padding: 10px; border-radius: 8px; margin-bottom: 15px;">
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
            <small style="color: #4dd0e1;"><b>🧠 Smart Trade Finder Options (1-for-1s & Packages):</b></small>
            <div style="display: flex; gap: 10px; margin-top: 8px; flex-wrap: wrap;">
                <div style="flex: 1; min-width: 180px;">
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
                <div style="flex: 1; min-width: 180px;">
                    <small>Specific Player Target (Optional):</small>
                    <input type="text" name="target_player_filter" placeholder="e.g. Breece Hall" value="{{ target_player_filter }}" style="width: 100%; box-sizing: border-box; margin-top: 4px;">
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
                <small><b>📋 {{ current_owner }}'s Sleeper Roster (Players & Traded Picks):</b></small>
                <div class="checkbox-grid" style="margin-top: 6px;">
                    {% for name, val in owner_rosters[current_owner].items() %}
                        <div class="checkbox-item" data-name="{{ name|lower }}">
                            <label>
                                <input type="checkbox" name="{{ team_key }}" value="{{ name }}" {% if name in selected_assets[team_key] %}checked{% endif %}>
                                {{ name }} ({{ val }})
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
                            <label>
                                <input type="checkbox" name="{{ team_key }}" value="{{ name }}" {% if name in selected_assets[team_key] %}checked{% endif %}>
                                {{ name }} ({{ display_val }})
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
        <button type="submit" name="action" value="smart_suggestion" class="btn-smart">🧠 Smart Trade Suggestions (1-for-1s & Packages)</button>
        <button type="submit" name="action" value="clear_trade" class="btn-clear">🧹 Clear Trade Selections</button>
    </form>

    {% if result %}
        <div class="result">
            <p><b>Team A Total:</b> {{ result.team_a_total }} pts</p>
            <p><b>Team B Total:</b> {{ result.team_b_total }} pts</p>

            {% if result.stud_msg %}
                <div class="note">{{ result.stud_msg }}</div>
            {% endif %}

            {% if result.counter_msg %}
                <div class="counter-msg">{{ result.counter_msg }}</div>
            {% endif %}

            {% if result.smart_suggestions %}
                <div class="smart-container">
                    <small><b>🧠 Top League-Wide Trade Suggestions for {{ selected_owner_a }} (Focus: {{ smart_strategy_label }}) :</b></small>
                    {% for s in result.smart_suggestions %}
                        <div class="smart-card">
                            <b>vs. {{ s.partner }}</b><br>
                            Give: <b>{{ s.gives }}</b> ({{ s.gives_val }} pts) ➔ Get: <b>{{ s.gets }}</b> ({{ s.gets_val }} pts)<br>
                            <small style="color: #b2ebf2;">Value Diff: {{ s.diff }} pts</small>
                        </div>
                    {% endfor %}
                </div>
            {% endif %}

            <hr style="border-color: #444;">
            <h3>{{ result.message }}</h3>

            {% if result.balancer_msg %}
                <div class="suggestion">{{ result.balancer_msg }}</div>
            {% endif %}

            <button type="button" class="btn-copy" onclick="copyTradeSummary()">📋 Copy Trade Summary</button>
        </div>

        <div id="summary-text" style="display:none;">🏈 DYNASTY TRADE SUMMARY
Team A Total: {{ result.team_a_total }} pts
Team B Total: {{ result.team_b_total }} pts
{% if result.stud_msg %}{{ result.stud_msg }}
{% endif %}{% if result.counter_msg %}{{ result.counter_msg }}
{% endif %}Result: {{ result.message }}
{% if result.balancer_msg %}{{ result.balancer_msg }}{% endif %}
        </div>
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
    <h2>📊 Team Power Rankings & Analysis</h2>
    
    <div class="nav-tabs">
        <a href="/" class="nav-btn">⚖️ Trade Calculator</a>
        <a href="/analysis" class="nav-btn active">📊 Team Rankings</a>
        <a href="/rookie-draft" class="nav-btn">📋 Rookie Mock</a>
        <a href="/league-feed" class="nav-btn">⚡ League Feed</a>
        <a href="/hall-of-fame" class="nav-btn">🏆 Hall of Fame</a>
        <a href="/trends" class="nav-btn">📈 Trends</a>
    </div>

    <form method="POST" action="/analysis">
        <div class="sync-box">
            <small><b>⚡ Sync League for Analysis:</b></small>
            <div class="sync-inputs">
                <input type="text" name="sleeper_input" placeholder="Sleeper Username or League ID" value="{{ sleeper_input }}">
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
                    <button type="submit" name="action" value="select_league" style="background: #1e88e5; padding: 8px; margin-top: 6px; font-size: 0.9em;">Load Power Rankings</button>
                </div>
            {% endif %}

            {% if sleeper_msg %}
                <div class="sync-msg">{{ sleeper_msg }}</div>
            {% endif %}
        </div>
    </form>

    {% if power_rankings %}
        <div style="margin-top: 15px;">
            <p style="color: #aaa; font-size: 0.9em; text-align: center;">League-wide valuation rankings based on total player assets and traded draft capital.</p>
            
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
                            <span style="color: #fff; margin-left: 8px;">{{ "{:,}".format(team.total_val | int) }} pts</span>
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
        <div style="text-align: center; padding: 30px; color: #777;">
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
    <title>Rookie Mock Draft Board</title>
    <style>
        {{ shared_styles }}
        .draft-container { display: grid; grid-template-columns: 1fr 1.5fr; gap: 15px; margin-top: 15px; }
        @media (max-width: 768px) { .draft-container { grid-template-columns: 1fr; } }
        .panel { background: #262626; padding: 15px; border-radius: 8px; border: 1px solid #3a3a3a; }
        .filters { display: flex; gap: 5px; margin-bottom: 12px; }
        .filter-btn { background: #333; color: #fff; border: none; padding: 6px 10px; border-radius: 4px; cursor: pointer; font-size: 0.85em; font-weight: bold; }
        .filter-btn.active { background: #007bff; color: #fff; }
        .player-list { max-height: 450px; overflow-y: auto; }
        .player-card { background: #1e1e1e; padding: 10px; margin-bottom: 8px; border-radius: 6px; display: flex; justify-content: space-between; align-items: center; border: 1px solid #333; }
        .player-card:hover { border-color: #007bff; }
        .draft-grid { display: flex; flex-direction: column; gap: 8px; max-height: 480px; overflow-y: auto; }
        .pick-slot { background: #1e1e1e; padding: 10px 12px; border-radius: 6px; display: flex; justify-content: space-between; align-items: center; border-left: 4px solid #007bff; border: 1px solid #333; font-size: 0.9em; }
        button.draft-btn { background: #007bff; color: #fff; border: none; padding: 6px 12px; border-radius: 4px; font-weight: bold; cursor: pointer; width: auto; font-size: 0.85em; margin-top: 0; }
        button.draft-btn:hover { background: #0056b3; }
        .sync-badge { background: #1e88e5; color: white; padding: 4px 8px; border-radius: 4px; font-size: 0.8em; margin-bottom: 10px; display: inline-block; font-weight: bold; }
    </style>
</head>
<body>
<div class="container" style="max-width: 850px;">
    <h2>📋 Rookie Mock Draft Board</h2>
    <div class="nav-tabs">
        <a href="/" class="nav-btn">⚖️ Trade Calculator</a>
        <a href="/analysis" class="nav-btn">📊 Team Rankings</a>
        <a href="/rookie-draft" class="nav-btn active">📋 Rookie Mock</a>
        <a href="/league-feed" class="nav-btn">⚡ League Feed</a>
        <a href="/hall-of-fame" class="nav-btn">🏆 Hall of Fame</a>
        <a href="/trends" class="nav-btn">📈 Trends</a>
    </div>

    <form method="POST" action="/rookie-draft">
        <div class="sync-box">
            <small><b>⚡ Sleeper App Sync:</b></small>
            <div class="sync-inputs">
                <input type="text" name="sleeper_input" placeholder="Sleeper Username or League ID" value="{{ sleeper_input }}">
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
                    <button type="submit" name="action" value="select_league" style="background: #1e88e5; padding: 8px; margin-top: 6px; font-size: 0.9em;">Sync Selected League</button>
                </div>
            {% endif %}

            {% if sleeper_msg %}
                <div class="sync-msg">{{ sleeper_msg }}</div>
            {% endif %}
        </div>
    </form>

    <div id="syncStatus"></div>

    <div class="draft-container">
        <!-- Available Players Panel -->
        <div class="panel">
            <h3 style="margin-top:0; color:#64b5f6; font-size: 1.1em;">Available Prospects</h3>
            <div class="filters">
                <button class="filter-btn active" onclick="filterPos('ALL', event)">ALL</button>
                <button class="filter-btn" onclick="filterPos('QB', event)">QB</button>
                <button class="filter-btn" onclick="filterPos('RB', event)">RB</button>
                <button class="filter-btn" onclick="filterPos('WR', event)">WR</button>
                <button class="filter-btn" onclick="filterPos('TE', event)">TE</button>
            </div>
            <div class="player-list" id="playerList"></div>
        </div>

        <!-- Draft Board Grid Panel -->
        <div class="panel">
            <h3 style="margin-top:0; color:#64b5f6; font-size: 1.1em;" id="boardTitle">Round 1 Draft Board</h3>
            <div class="draft-grid" id="draftGrid"></div>
        </div>
    </div>
</div>

<script>
    let rookies = [];
    let currentFilter = 'ALL';
    let totalPicks = 10;
    let draftState = {};
    let leagueDraftInfo = null;

    async function loadRookies() {
        try {
            const [rookRes, draftRes] = await Promise.all([
                fetch('/api/rookies'),
                fetch('/api/league-draft-info')
            ]);
            rookies = await rookRes.json();
            const draftData = await draftRes.json();
            
            if (draftData.success) {
                leagueDraftInfo = draftData;
                totalPicks = draftData.teams || 10;
                document.getElementById('syncStatus').innerHTML = `<div class="sync-badge">⚡ Synced with Sleeper League Draft Order (${totalPicks} Teams)</div>`;
            } else {
                document.getElementById('syncStatus').innerHTML = `<div style="color: #aaa; font-size: 0.85em; margin-bottom: 10px;">💡 Tip: Sync a league above or on the Trade Calculator to load your league's exact draft order & managers.</div>`;
            }

            renderPlayers();
            renderGrid();
        } catch(e) {
            console.error("Failed to load rookies or league draft info", e);
            renderPlayers();
            renderGrid();
        }
    }

    function filterPos(pos, event) {
        currentFilter = pos;
        document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
        event.target.classList.add('active');
        renderPlayers();
    }

    function renderPlayers() {
        const listEl = document.getElementById('playerList');
        listEl.innerHTML = '';
        
        const filtered = rookies.filter(p => !Object.values(draftState).includes(p.id) && (currentFilter === 'ALL' || p.pos === currentFilter));
        
        if (filtered.length === 0) {
            listEl.innerHTML = '<p style="color: #777; text-align:center; font-size:0.9em;">No prospects available.</p>';
            return;
        }

        filtered.forEach(player => {
            const card = document.createElement('div');
            card.className = 'player-card';
            card.innerHTML = `<span><strong>${player.rank}. ${player.name}</strong><br><small style="color:#aaa;">${player.pos} - ${player.team}</small></span>
                              <button class="draft-btn" onclick="draftPlayer(${player.id})">Draft</button>`;
            listEl.appendChild(card);
        });
    }

    function renderGrid() {
        const gridEl = document.getElementById('draftGrid');
        gridEl.innerHTML = '';

        for (let i = 1; i <= totalPicks; i++) {
            const slot = document.createElement('div');
            slot.className = 'pick-slot';
            const draftedPlayerId = draftState[i];
            const draftedPlayer = rookies.find(p => p.id === draftedPlayerId);

            let ownerName = '';
            if (leagueDraftInfo && leagueDraftInfo.slot_to_owner) {
                ownerName = leagueDraftInfo.slot_to_owner[i] || leagueDraftInfo.slot_to_owner[String(i)] || '';
            }

            const pickLabel = `Pick 1.${i < 10 ? '0' + i : i}` + (ownerName ? ` <small style="color:#29b6f6;">(${ownerName})</small>` : '');

            slot.innerHTML = `<span><strong>${pickLabel}</strong></span>
                              <span>${draftedPlayer ? '<strong>' + draftedPlayer.name + '</strong> <small style="color:#64b5f6;">(' + draftedPlayer.pos + ')</small>' : '<em style="color:#777;">Available</em>'}</span>`;
            gridEl.appendChild(slot);
        }
    }

    function draftPlayer(playerId) {
        for (let i = 1; i <= totalPicks; i++) {
            if (!draftState[i]) {
                draftState[i] = playerId;
                break;
            }
        }
        renderPlayers();
        renderGrid();
    }

    loadRookies();
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
    <h2>⚡ Live League Feed</h2>
    <div class="nav-tabs">
        <a href="/" class="nav-btn">⚖️ Trade Calculator</a>
        <a href="/analysis" class="nav-btn">📊 Team Rankings</a>
        <a href="/rookie-draft" class="nav-btn">📋 Rookie Mock</a>
        <a href="/league-feed" class="nav-btn active">⚡ League Feed</a>
        <a href="/hall-of-fame" class="nav-btn">🏆 Hall of Fame</a>
        <a href="/trends" class="nav-btn">📈 Trends</a>
    </div>
    <div style="background: #262626; padding: 15px; border-radius: 8px;">
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
                    <div style="background: #1a1a1a; padding: 10px; border-radius: 6px; margin-bottom: 8px;">
                        <p style="color: #64b5f6; font-weight: bold; margin: 0;">Type: {{ tx.type }}</p>
                    </div>
                {% endfor %}
            </div>
        {% else %}
            <p style="color: #888; font-size: 0.9em; margin-top: 10px;">Enter a valid Sleeper League ID above to pull real-time transactions.</p>
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
    <h2>🏆 League Hall of Fame</h2>
    <div class="nav-tabs">
        <a href="/" class="nav-btn">⚖️ Trade Calculator</a>
        <a href="/analysis" class="nav-btn">📊 Team Rankings</a>
        <a href="/rookie-draft" class="nav-btn">📋 Rookie Mock</a>
        <a href="/league-feed" class="nav-btn">⚡ League Feed</a>
        <a href="/hall-of-fame" class="nav-btn active">🏆 Hall of Fame</a>
        <a href="/trends" class="nav-btn">📈 Trends</a>
    </div>
    <div style="background: #262626; padding: 15px; border-radius: 8px;">
        <div style="background: #1a1a1a; padding: 12px; border-radius: 6px; margin-bottom: 10px;">
            <p style="color: #ffca28; font-weight: bold; margin: 0;">🏆 2025 Champion: TheMedulla Oblangatas</p>
            <p style="color: #aaa; font-size: 0.85em; margin: 4px 0 0 0;">Manager: Zach | Runner-Up: Gridiron Gurus</p>
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
    <h2>📈 Player Market Value Trends</h2>
    <div class="nav-tabs">
        <a href="/" class="nav-btn">⚖️ Trade Calculator</a>
        <a href="/analysis" class="nav-btn">📊 Team Rankings</a>
        <a href="/rookie-draft" class="nav-btn">📋 Rookie Mock</a>
        <a href="/league-feed" class="nav-btn">⚡ League Feed</a>
        <a href="/hall-of-fame" class="nav-btn">🏆 Hall of Fame</a>
        <a href="/trends" class="nav-btn active">📈 Trends</a>
    </div>
    <div style="background: #262626; padding: 15px; border-radius: 8px; height: 350px;">
        <canvas id="trendChart"></canvas>
    </div>
</div>
<script>
const rawData = {{ trends | safe }};
const labels = ['June 2026', 'July 2026', 'August 2026'];
const datasets = Object.keys(rawData).map((player, idx) => {
    const colors = ['#3b82f6', '#6366f1', '#10b981'];
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


def fetch_live_fantasycalc_values(is_superflex=False):
  num_qbs = 2 if is_superflex else 1
  cache_key = f"sf_{num_qbs}"

  if os.path.exists(VALUES_CACHE_FILE):
    try:
      with open(VALUES_CACHE_FILE, "r") as f:
        cache_data = json.load(f)
        if cache_key in cache_data:
          cached_time = cache_data[cache_key].get("timestamp", 0)
          if time.time() - cached_time < CACHE_EXPIRATION_SECONDS:
            return cache_data[cache_key].get("players")
    except Exception:
      pass

  url = f"https://api.fantasycalc.com/values/current?isDynasty=true&numQbs={num_qbs}&numTeams=12&ppr=1"
  data = fetch_sleeper_api(url)

  if isinstance(data, list) and len(data) > 0:
    live_players = {
        "Quarterbacks": {},
        "Running Backs": {},
        "Wide Receivers": {},
        "Tight Ends": {},
        "Draft Picks": dict(DEFAULT_PLAYERS["Draft Picks"]),
    }
    pos_map = {
        "QB": "Quarterbacks",
        "RB": "Running Backs",
        "WR": "Wide Receivers",
        "TE": "Tight Ends",
    }

    for item in data:
      pinfo = item.get("player", {})
      fname = pinfo.get("name")
      pos = pinfo.get("position")
      val = item.get("value", 800)

      if fname and pos in pos_map:
        formatted_name = f"{fname} ({pos})"
        live_players[pos_map[pos]][formatted_name] = int(val)

    try:
      cache_data = {}
      if os.path.exists(VALUES_CACHE_FILE):
        with open(VALUES_CACHE_FILE, "r") as f:
          cache_data = json.load(f)
      cache_data[cache_key] = {"timestamp": time.time(), "players": live_players}
      with open(VALUES_CACHE_FILE, "w") as f:
        json.dump(cache_data, f)
    except Exception:
      pass

    return live_players

  return DEFAULT_PLAYERS


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

      active_players = fetch_live_fantasycalc_values(is_superflex=is_league_sf)

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
            pname = player_map.get(str(pid))
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


@app.errorhandler(Exception)
def handle_exception(e):
  return (
      f"""
    <div style="font-family: sans-serif; padding: 20px; color: #fff; background: #121212;">
        <h3>⚠️ App Exception Handler</h3>
        <p style="color: #ff5252;">{str(e)}</p>
        <a href="/" style="color: #64b5f6;">Return to Calculator</a>
    </div>
    """,
      500,
  )


@app.route("/", methods=["GET", "POST"])
def home():
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
      league_owners = session.get("league_owners", {})

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
  ]:
    flat_players = {}
    for pos, p_dict in active_players.items():
      for name, val in p_dict.items():
        is_pick = "Pick" in name
        flat_players[name] = int(val * pick_modifier) if is_pick else val

    selected_assets["team_a"] = request.form.getlist("team_a")
    selected_assets["team_b"] = request.form.getlist("team_b")
    all_selected = set(selected_assets["team_a"] + selected_assets["team_b"])

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
            "⚠️ Please select your team (Team A) from the dropdown above to"
            " generate league-wide smart trades."
        )
      else:
        roster_a = owner_rosters.get(selected_owner_a, {})
        if not roster_a:
          counter_msg = (
              "⚠️ Roster data not found for your team. Try re-fetching your"
              " Sleeper league."
          )
        else:
          all_candidates = []
          for other_owner, roster_b in owner_rosters.items():
            if other_owner == selected_owner_a:
              continue

            items_a = list(roster_a.items())
            items_b = list(roster_b.items())

            packages_a = []
            for r_size in range(1, 3):
              for combo in combinations(items_a, r_size):
                p_names = " + ".join([x[0] for x in combo])
                p_val = sum(x[1] for x in combo)
                packages_a.append((p_names, p_val, combo))

            packages_b = []
            for r_size in range(1, 3):
              for combo in combinations(items_b, r_size):
                p_names = " + ".join([x[0] for x in combo])
                p_val = sum(x[1] for x in combo)
                packages_b.append((p_names, p_val, combo))

            for gives_str, gives_val, gives_combo in packages_a:
              for gets_str, gets_val, gets_combo in packages_b:
                diff = abs(gets_val - gives_val)
                if diff > 2000:
                  continue

                is_gives_all_picks = all(
                    "Pick" in x[0] or "Round" in x[0] for x in gives_combo
                )
                is_gets_all_picks = all(
                    "Pick" in x[0] or "Round" in x[0] for x in gets_combo
                )
                if is_gives_all_picks and is_gets_all_picks:
                  continue

                # Strategy-specific filtering rules
                if smart_strategy == "balanced" and diff > 1000:
                  continue
                elif (
                    smart_strategy == "rb_focus"
                    and "(RB)" not in gets_str
                    and gets_val < 5000
                ):
                  continue
                elif (
                    smart_strategy == "improve_rbs"
                    and "(RB)" not in gets_str
                    and gets_val <= gives_val
                ):
                  continue
                elif (
                    smart_strategy == "rb_depth" and "(RB)" not in gets_str
                ):
                  continue
                elif (
                    smart_strategy == "wr_focus" and "(WR)" not in gets_str
                ):
                  continue
                elif (
                    smart_strategy == "improve_wrs"
                    and "(WR)" not in gets_str
                    and gets_val <= gives_val
                ):
                  continue
                elif (
                    smart_strategy == "qb_focus" and "(QB)" not in gets_str
                ):
                  continue
                elif (
                    smart_strategy == "te_focus" and "(TE)" not in gets_str
                ):
                  continue
                elif smart_strategy == "tier_up" and gets_val <= gives_val:
                  continue
                elif (
                    smart_strategy == "win_now"
                    and gets_val < 6000
                    and "Pick" in gets_str
                ):
                  continue
                elif (
                    smart_strategy == "youth_rebuild"
                    and "Pick" not in gets_str
                    and gets_val > 7500
                ):
                  continue
                elif (
                    smart_strategy == "pick_hoard" and "Pick" not in gets_str
                ):
                  continue

                if (
                    target_player_filter
                    and target_player_filter not in gets_str.lower()
                    and target_player_filter not in gives_str.lower()
                ):
                  continue

                all_candidates.append({
                    "partner": other_owner,
                    "gives": gives_str,
                    "gives_val": gives_val,
                    "gets": gets_str,
                    "gets_val": gets_val,
                    "diff": diff,
                })

          all_candidates.sort(key=lambda x: x["diff"])

          filtered_candidates = []
          partner_counts = {}
          seen_core_trades = set()

          for cand in all_candidates:
            partner = cand["partner"]
            if partner_counts.get(partner, 0) >= 1:
              continue

            core_sig = (
                partner,
                cand["gives"].split(" (")[0],
                cand["gets"].split(" (")[0],
            )
            if core_sig in seen_core_trades:
              continue

            seen_core_trades.add(core_sig)
            partner_counts[partner] = partner_counts.get(partner, 0) + 1
            filtered_candidates.append(cand)

          all_candidates = filtered_candidates
          page_size = 4
          if all_candidates:
            start_idx = (smart_page * page_size) % len(all_candidates)
            smart_suggestions = all_candidates[start_idx : start_idx + page_size]

    raw_a = (
        sum(flat_players.get(item, 800) for item in selected_assets["team_a"])
        + a_custom_num
    )
    raw_b = (
        sum(flat_players.get(item, 800) for item in selected_assets["team_b"])
        + b_custom_num
    )
    count_a = len(selected_assets["team_a"]) + (
        1 if a_cname and a_custom_num > 0 else 0
    )
    count_b = len(selected_assets["team_b"]) + (
        1 if b_cname and b_custom_num > 0 else 0
    )

    temp_a_tot, temp_b_tot = raw_a, raw_b
    if count_a > 0 and count_b > 0 and count_a != count_b:
      if count_a < count_b:
        temp_a_tot = int(raw_a * 1.10)
      else:
        temp_b_tot = int(raw_b * 1.10)

    if action == "suggest_trade" and temp_a_tot != temp_b_tot:
      losing_team = "team_b" if temp_a_tot > temp_b_tot else "team_a"
      winning_tot = temp_a_tot if losing_team == "team_b" else temp_b_tot
      losing_tot = temp_b_tot if losing_team == "team_b" else temp_a_tot
      diff = abs(winning_tot - losing_tot)

      losing_owner = (
          selected_owner_b if losing_team == "team_b" else selected_owner_a
      )
      pool = (
          owner_rosters.get(losing_owner, flat_players)
          if losing_owner
          else flat_players
      )
      available_pool = {
          k: v for k, v in pool.items() if k not in all_selected
      }

      if available_pool:
        best_asset = min(
            available_pool.keys(), key=lambda k: abs(available_pool[k] - diff)
        )
        selected_assets[losing_team].append(best_asset)
        counter_msg = f"💡 Counter-Offer Added: Automatically added {best_asset} ({available_pool[best_asset]:,} pts)."

      raw_a = (
          sum(flat_players.get(item, 800) for item in selected_assets["team_a"])
          + a_custom_num
      )
      raw_b = (
          sum(flat_players.get(item, 800) for item in selected_assets["team_b"])
          + b_custom_num
      )

    stud_msg = ""
    team_a_total = raw_a
    team_b_total = raw_b

    if count_a > 0 and count_b > 0 and count_a != count_b:
      if count_a < count_b:
        team_a_total = int(raw_a * 1.10)
        stud_msg = f"⚡ Stud Premium (+10%) applied to Team A ({count_a} vs {count_b} pieces)."
      else:
        team_b_total = int(raw_b * 1.10)
        stud_msg = f"⚡ Stud Premium (+10%) applied to Team B ({count_b} vs {count_a} pieces)."

    diff = abs(team_a_total - team_b_total)
    total_val = max(team_a_total + team_b_total, 1)
    diff_pct = (diff / total_val) * 100

    balancer_msg = ""
    if diff > 0 and (team_a_total > 0 or team_b_total > 0):
      losing_team = "team_b" if team_a_total > team_b_total else "team_a"
      losing_owner = (
          selected_owner_b if losing_team == "team_b" else selected_owner_a
      )
      balancer_pool = (
          owner_rosters.get(losing_owner, flat_players)
          if losing_owner
          else flat_players
      )
      balancer_pool = {
          k: v for k, v in balancer_pool.items() if k not in all_selected
      }
      if balancer_pool:
        closest_asset = min(
            balancer_pool.keys(), key=lambda k: abs(balancer_pool[k] - diff)
        )
        balancer_msg = f"💡 Trade Balancer: Add ~{diff:,} pts (Closest match: {closest_asset} @ {balancer_pool[closest_asset]:,} pts)."

    if team_a_total == 0 and team_b_total == 0:
      msg = "Select or enter assets on both sides."
    elif diff_pct <= 5.0:
      msg = f"⚖️ Fair Trade! Difference: {diff:,} pts ({diff_pct:.1f}%)."
    elif team_a_total > team_b_total:
      msg = f"🏆 Team A wins by {diff:,} pts ({diff_pct:.1f}% margin)."
    else:
      msg = f"🏆 Team B wins by {diff:,} pts ({diff_pct:.1f}% margin)."

    result = {
        "team_a_total": team_a_total,
        "team_b_total": team_b_total,
        "message": msg,
        "stud_msg": stud_msg,
        "balancer_msg": balancer_msg,
        "counter_msg": counter_msg,
        "smart_suggestions": smart_suggestions,
    }

  strategy_labels = {
      "balanced": "Balanced Value Match",
      "rb_focus": "Target Star RBs",
      "improve_rbs": "Improve Running Backs",
      "rb_depth": "Add RB Depth",
      "wr_focus": "Improve WR Depth",
      "improve_wrs": "Improve Wide Receivers",
      "tier_up": "Tier Up / Target Studs",
      "win_now": "Win-Now / Veteran Push",
      "pick_hoard": "Draft Pick Accumulation",
      "qb_focus": "Elite QB Hunter",
      "te_focus": "Tight End Upgrade",
      "youth_rebuild": "Youth & Upside / Rebuild",
  }

  return render_template_string(
      CALCULATOR_TEMPLATE,
      shared_styles=SHARED_STYLES,
      player_groups=active_players,
      result=result,
      league_format=league_format,
      selected_assets=selected_assets,
      custom_assets=custom_assets,
      sleeper_input=sleeper_input,
      sleeper_msg=sleeper_msg,
      user_leagues=user_leagues,
      league_owners=league_owners,
      owner_rosters=owner_rosters,
      selected_league_id=selected_league_id,
      selected_owner_a=selected_owner_a,
      selected_owner_b=selected_owner_b,
      pick_modifier=pick_modifier,
      smart_strategy=smart_strategy,
      smart_strategy_label=strategy_labels.get(smart_strategy, "Balanced Value Match"),
      target_player_filter=target_player_filter,
      smart_page=smart_page,
  )


@app.route("/analysis", methods=["GET", "POST"])
def analysis():
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
        selected_league_id
        and selected_league_id != session.get("selected_league_id")
    ):
      sleeper_msg = process_sleeper_sync(sleeper_input, selected_league_id)
      owner_rosters = session.get("owner_rosters", {})

  if owner_rosters:
    for name, roster in owner_rosters.items():
      qb_val = sum(v for k, v in roster.items() if "(QB)" in k)
      rb_val = sum(v for k, v in roster.items() if "(RB)" in k)
      wr_val = sum(v for k, v in roster.items() if "(WR)" in k)
      te_val = sum(v for k, v in roster.items() if "(TE)" in k)
      pick_val = sum(
          v for k, v in roster.items() if "Pick" in k or "Round" in k
      )
      total_val = sum(roster.values())

      power_rankings.append({
          "name": name,
          "total_val": total_val,
          "qb_val": qb_val,
          "rb_val": rb_val,
          "wr_val": wr_val,
          "te_val": te_val,
          "pick_val": pick_val,
      })

    power_rankings.sort(key=lambda x: x["total_val"], reverse=True)

    total_teams = len(power_rankings)
    for idx, team in enumerate(power_rankings):
      pick_ratio = team["pick_val"] / max(team["total_val"], 1)

      if idx < max(3, int(total_teams * 0.33)) and pick_ratio < 0.45:
        archetype = "Contender"
      elif pick_ratio > 0.35 or idx >= int(total_teams * 0.65):
        archetype = "Rebuilder"
      else:
        archetype = "Playoff Threat"

      team["archetype"] = archetype

  return render_template_string(
      ANALYSIS_TEMPLATE,
      shared_styles=SHARED_STYLES,
      sleeper_input=sleeper_input,
      selected_league_id=selected_league_id,
      user_leagues=user_leagues,
      sleeper_msg=sleeper_msg,
      power_rankings=power_rankings,
  )


@app.route("/rookie-draft", methods=["GET", "POST"])
def rookie_draft():
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
        selected_league_id
        and selected_league_id != session.get("selected_league_id")
    ):
      sleeper_msg = process_sleeper_sync(sleeper_input, selected_league_id)

  return render_template_string(
      ROOKIE_DRAFT_TEMPLATE,
      shared_styles=SHARED_STYLES,
      sleeper_input=sleeper_input,
      selected_league_id=selected_league_id,
      user_leagues=user_leagues,
      sleeper_msg=sleeper_msg,
  )


@app.route("/api/rookies", methods=["GET"])
def get_rookies():
  return jsonify(ROOKIE_PROSPECTS)


@app.route("/api/league-draft-info", methods=["GET"])
def league_draft_info():
  league_id = session.get("selected_league_id")
  if not league_id:
    return jsonify({"success": False, "message": "No league selected"})

  drafts = fetch_sleeper_api(
      f"https://api.sleeper.app/v1/league/{league_id}/drafts"
  )
  if not drafts or not isinstance(drafts, list):
    return jsonify({"success": False, "message": "No draft found for league"})

  draft = next((d for d in drafts if d.get("status") == "pre"), drafts[0])
  draft_order = draft.get("draft_order", {})
  settings = draft.get("settings", {})
  rounds = settings.get("rounds", 4)
  teams = settings.get("teams", 10)

  users_data = (
      fetch_sleeper_api(
          f"https://api.sleeper.app/v1/league/{league_id}/users"
      )
      or []
  )
  user_id_to_name = {
      u["user_id"]: u.get("display_name", "Unknown")
      for u in users_data
      if "user_id" in u
  }

  slot_to_owner = {}
  if isinstance(draft_order, dict):
    for uid, slot in draft_order.items():
      owner_name = user_id_to_name.get(uid, f"Team {slot}")
      slot_to_owner[int(slot)] = owner_name

  return jsonify({
      "success": True,
      "rounds": rounds,
      "teams": teams,
      "slot_to_owner": slot_to_owner,
  })


@app.route("/league-feed")
def league_feed():
  league_id = request.args.get("league_id", "")
  transactions = []
  if league_id:
    try:
      res = fetch_sleeper_api(
          f"https://api.sleeper.app/v1/league/{league_id}/transactions/1"
      )
      if isinstance(res, list):
        transactions = res
    except Exception:
      pass
  return render_template_string(
      LEAGUE_FEED_TEMPLATE,
      shared_styles=SHARED_STYLES,
      league_id=league_id,
      transactions=transactions,
  )


@app.route("/hall-of-fame")
def hall_of_fame():
  return render_template_string(HOF_TEMPLATE, shared_styles=SHARED_STYLES)


@app.route("/trends")
def trends():
  trend_data = {
      "Patrick Mahomes": [
          {"date": "2026-06-01", "value": 8200},
          {"date": "2026-07-01", "value": 8400},
          {"date": "2026-08-01", "value": 8500},
      ],
      "Caleb Williams": [
          {"date": "2026-06-01", "value": 7000},
          {"date": "2026-07-01", "value": 7300},
          {"date": "2026-08-01", "value": 7500},
      ],
      "Breece Hall": [
          {"date": "2026-06-01", "value": 8600},
          {"date": "2026-07-01", "value": 8700},
          {"date": "2026-08-01", "value": 8800},
      ],
  }
  return render_template_string(
      TRENDS_TEMPLATE,
      shared_styles=SHARED_STYLES,
      trends=json.dumps(trend_data),
  )


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5000, debug=False, threaded=False, use_reloader=False)
