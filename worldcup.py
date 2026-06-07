import requests
import pandas as pd

URL = "https://raw.githubusercontent.com/openfootball/worldcup.json/master/2026/worldcup.json"

resp = requests.get(URL)
resp.raise_for_status()
data = resp.json()

matches = pd.DataFrame(data["matches"])

print(f"Tournament: {data['name']}")
print(f"Total matches: {len(matches)}\n")
print(matches[["date", "team1", "team2", "group"]].head(20).to_string(index=False))
