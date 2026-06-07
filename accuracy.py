import requests
import pandas as pd

URL = "https://raw.githubusercontent.com/openfootball/worldcup.json/master/2026/worldcup.json"

predictions = pd.read_csv("predictions.csv")
data = requests.get(URL).json()
matches = pd.DataFrame(data["matches"])

def actual_result(row):
    score = row.get("score")
    if not isinstance(score, dict):
        return None
    ft = score.get("ft")
    if not ft or len(ft) < 2:
        return None
    g1, g2 = ft[0], ft[1]
    if g1 > g2:
        return row["team1"]
    elif g2 > g1:
        return row["team2"]
    return "Draw"

played = []
for _, m in matches.iterrows():
    res = actual_result(m)
    if res is not None:
        played.append({"date": m["date"], "team1": m["team1"],
                       "team2": m["team2"], "actual": res})

actuals = pd.DataFrame(played)

if actuals.empty:
    print("No completed matches yet — run this once the tournament starts.")
else:
    merged = predictions.merge(actuals, on=["date", "team1", "team2"])
    merged["correct"] = merged["prediction"] == merged["actual"]
    total = len(merged)
    correct = int(merged["correct"].sum())
    print(f"Matches scored:      {total}")
    print(f"Correct predictions: {correct}")
    print(f"Accuracy:            {correct / total * 100:.1f}%\n")
    merged.to_csv("results_tracked.csv", index=False)
    print(merged[["date", "team1", "team2", "prediction", "actual", "correct"]].to_string(index=False))