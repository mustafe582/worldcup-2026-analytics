import requests
import pandas as pd

url = "https://fantasy.premierleague.com/api/bootstrap-static/"
response = requests.get(url)
data = response.json()

players = pd.DataFrame(data['elements'])

players = players[['first_name', 'second_name', 'team', 'now_cost', 'total_points', 'minutes']]
players['cost_millions'] = players['now_cost'] / 10
players['points_per_million'] = players['total_points'] / players['cost_millions']

top_value = players[players['minutes'] > 900].sort_values('points_per_million', ascending=False).head(20)

print(top_value[['first_name', 'second_name', 'cost_millions', 'total_points', 'points_per_million']].to_string())