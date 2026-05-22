from flask import Flask, render_template_string

app = Flask(__name__)

# ✅ SAFE ASCII ART (fixed quotes)
SQUID_ART = r'''
        _.-""""-._
      .'  _     _ '.
     /   (_)   (_)  \
    |  ,           , |
    |  \`.       .`/ |
     \  '.`'---'`.' /
      '.  `'---'`  .'
        '-._____.-'
'''

# Simple game state
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
            color: #7fd0ff;
        }
        button {
            padding: 10px;
            margin: 5px;
        }
    </style>
</head>
<body>

<h1>{{ name }}</h1>

<pre>{{ art }}</pre>

<p>Hunger: {{ hunger }}</p>
<p>Happiness: {{ happiness }}</p>

/feed
    <button>Feed</button>
</form>

/play
    <button>Play</button>
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
