from flask import Flask, render_template_string

app = Flask(__name__)

# ✅ FIXED ASCII ART (no syntax errors)
SQUID_ART = r"""
        _.-""""-._
      .'  _     _ '.
     /   (_)   (_)  \
    |  ,           , |
    |  \`.       .`/ |
     \  '.`'---'`.' /
      '.  `'---'`  .'
        '-._____.-'
"""

# Simple game state (basic starter)
pet = {
    "name": "Squishy",
    "hunger": 50,
    "happiness": 50
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Squid Virtual Pet</title>
    <style>
        body {
            font-family: Arial;
            text-align: center;
            background: #0b1e2d;
            color: white;
        }
        pre {
            font-size: 16px;
            color: #7fd0ff;
        }
        .stats {
            margin: 20px;
        }
        button {
            padding: 10px 20px;
            margin: 10px;
            font-size: 16px;
        }
    </style>
</head>
<body>

<h1>🐙 {{ name }}</h1>

<pre>{{ art }}</pre>

<div class="stats">
    <p>Hunger: {{ hunger }}</p>
    <p>Happiness: {{ happiness }}</p>
</div>

<form method="post" action="/feed">
    <button type="submit">Feed</button>
</form>

<form method="post" action="/play">
    <button type="submit">Play</button>
</form>

</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(
        HTML_TEMPLATE,
        name=pet["name"],
        art=SQUID_ART,
        hunger=pet["hunger"],
        happiness=pet["happiness"]
    )

@app.route("/feed", methods=["POST"])
def feed():
    pet["hunger"] = max(0, pet["hunger"] - 10)
    return home()

@app.route("/play", methods=["POST"])
def play():
    pet["happiness"] = min(100, pet["happiness"] + 10)
    return home()

if __name__ == "__main__":
    app.run(debug=True)
