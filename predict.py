import requests
import pandas as pd

URL = "https://raw.githubusercontent.com/openfootball/worldcup.json/master/2026/worldcup.json"

# --- YOUR TEAM STRENGTH RATINGS ---
# Starting estimates based on FIFA ranking tiers. EDIT THESE — plug in current
# FIFA ranking points or your own numbers. This is YOUR model's logic to defend.
STRENGTH = {
    "Argentina": 93, "France": 92, "Spain": 91, "England": 90, "Brazil": 90,
    "Portugal": 89, "Netherlands": 88, "Belgium": 86, "Italy": 86, "Germany": 86,
    "Croatia": 84, "Uruguay": 84, "Colombia": 83, "Morocco": 83, "Switzerland": 82,
    "USA": 81, "Mexico": 81, "Japan": 81, "Senegal": 80, "Denmark": 80,
    "Norway": 79, "Ecuador": 79, "Austria": 79, "Turkey": 78, "South Korea": 78,
    "Australia": 77, "Canada": 77, "Nigeria": 77, "Serbia": 77, "Sweden": 76,
    "Egypt": 76, "Poland": 76, "Ivory Coast": 75,
}
DEFAULT_STRENGTH = 70  # any team not listed gets this

def rating(team):
    return STRENGTH.get(team, DEFAULT_STRENGTH)

def predict(t1, t2):
    diff = rating(t1) - rating(t2)
    p1 = 1 / (1 + 10 ** (-diff / 15))          # win chance for team1
    draw = max(0.27 * (1 - abs(diff) / 40), 0.10)  # draws likelier when close
    probs = {t1: p1 * (1 - draw), "Draw": draw, t2: (1 - p1) * (1 - draw)}
    predicted = max(probs, key=probs.get)
    return predicted, round(probs[predicted] * 100)

data = requests.get(URL).json()
matches = pd.DataFrame(data["matches"])

# group stage only
group_matches = matches[matches["group"].astype(str).str.startswith("Group")].copy()

rows = []
for _, m in group_matches.iterrows():
    pred, conf = predict(m["team1"], m["team2"])
    rows.append({
        "date": m["date"], "group": m["group"],
        "team1": m["team1"], "team2": m["team2"],
        "prediction": pred, "confidence_%": conf
    })

predictions = pd.DataFrame(rows)
predictions.to_csv("predictions.csv", index=False)

print(f"Generated {len(predictions)} predictions — saved to predictions.csv\n")
print(predictions.head(20).to_string(index=False))