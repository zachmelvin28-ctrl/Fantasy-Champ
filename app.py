from flask import Flask, jsonify, render_template_string, request, session
import json
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Default player database including Cam Newton
DEFAULT_PLAYERS = {
    "Cam Newton": {"position": "QB", "value": 1500, "team": "FA", "age": 37}
}

@app.route("/")
def home():
    return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Dynasty Trade Calculator</title>
            <style>
                body { font-family: Arial, sans-serif; background: #121212; color: #e0e0e0; padding: 20px; }
                .container { max-width: 600px; margin: auto; background: #1e1e1e; padding: 20px; border-radius: 8px; }
                input, select, button { width: 100%; padding: 10px; margin: 10px 0; background: #2d2d2d; border: 1px solid #444; color: #fff; border-radius: 4px; }
                button { background: #ff5722; cursor: pointer; font-weight: bold; }
                button:hover { background: #e64a19; }
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Dynasty Trade Calculator</h2>
                <p>Example Evaluated Player: <strong>Cam Newton</strong> (QB)</p>
                <form method="POST" action="/evaluate">
                    <label>Player Name:</label>
                    <input type="text" name="player" value="Cam Newton">
                    <button type="submit">Evaluate Trade</button>
                </form>
            </div>
        </body>
        </html>
    """)

@app.route("/evaluate", methods=["POST"])
def evaluate():
    player_name = request.form.get("player", "Cam Newton")
    player_data = DEFAULT_PLAYERS.get(player_name, {"position": "Unknown", "value": 0})
    return jsonify({
        "player": player_name,
        "details": player_data,
        "status": "Success"
    })

if __name__ == "__main__":
    app.run(debug=True)
