import requests
import pandas as pd
import streamlit as st

st.set_page_config(page_title="World Cup 2026 · Prediction Model", page_icon="⚽", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
html, body, [class*="css"] { font-family: 'Sora', sans-serif; }
.stApp { background: #0a0a0b; }
#MainMenu, header, footer { visibility: hidden; }
.block-container { padding-top: 2.5rem; max-width: 1120px; }
.hero-label { font-family: 'JetBrains Mono', monospace; font-size: 12px; letter-spacing: 0.25em; color: #6b7280; text-transform: uppercase; }
.hero-title { font-size: 46px; font-weight: 700; color: #fafafa; line-height: 1.04; margin: 10px 0 8px; letter-spacing: -0.02em; }
.hero-sub { font-size: 15px; color: #9ca3af; font-weight: 300; max-width: 640px; }
.metrics { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin: 36px 0; }
.metric { background: #111113; border: 1px solid #1f1f23; border-radius: 16px; padding: 22px; }
.metric-label { font-family: 'JetBrains Mono', monospace; font-size: 11px; letter-spacing: 0.12em; color: #6b7280; text-transform: uppercase; margin-bottom: 12px; }
.metric-value { font-size: 34px; font-weight: 700; color: #fafafa; letter-spacing: -0.02em; }
.metric-accent { color: #c8ff00; }
.groups { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
.group { background: #111113; border: 1px solid #1f1f23; border-radius: 16px; padding: 22px; }
.group-head { font-family: 'JetBrains Mono', monospace; font-size: 12px; letter-spacing: 0.15em; color: #c8ff00; margin-bottom: 18px; }
.match { margin-bottom: 16px; }
.match-teams { font-size: 13px; color: #e5e7eb; margin-bottom: 6px; }
.match-pred { font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #9ca3af; margin-bottom: 7px; }
.bar { height: 4px; background: #1f1f23; border-radius: 3px; overflow: hidden; }
.bar-fill { height: 100%; background: #c8ff00; }
.bar-draw { height: 100%; background: #4b5563; }
.section-label { font-family: 'JetBrains Mono', monospace; font-size: 12px; letter-spacing: 0.15em; color: #6b7280; text-transform: uppercase; margin: 44px 0 16px; }
</style>
""", unsafe_allow_html=True)

URL = "https://raw.githubusercontent.com/openfootball/worldcup.json/master/2026/worldcup.json"

@st.cache_data(ttl=1800)
def get_actuals():
    try:
        data = requests.get(URL).json()
        played = []
        for m in data["matches"]:
            s = m.get("score", {})
            ft = s.get("ft") if isinstance(s, dict) else None
            if ft and len(ft) == 2:
                r = m["team1"] if ft[0] > ft[1] else m["team2"] if ft[1] > ft[0] else "Draw"
                played.append({"date": m["date"], "team1": m["team1"], "team2": m["team2"], "actual": r})
        return pd.DataFrame(played)
    except:
        return pd.DataFrame()

try:
    preds = pd.read_csv("predictions.csv")
except FileNotFoundError:
    st.error("Run predict.py first to generate predictions.csv")
    st.stop()

actuals = get_actuals()
if not actuals.empty:
    merged = preds.merge(actuals, on=["date", "team1", "team2"])
    merged["correct"] = merged["prediction"] == merged["actual"]
    played, correct = len(merged), int(merged["correct"].sum())
    accuracy = f"{correct/played*100:.0f}%" if played else "—"
else:
    played, correct, accuracy = 0, 0, "—"

st.markdown("""
<div class="hero-label">World Cup 2026 · Prediction Model</div>
<div class="hero-title">Can data out-predict<br>the pundits?</div>
<div class="hero-sub">A strength-based model forecasting all 72 group-stage matches — locked before kickoff, tracked live against every result.</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="metrics">
  <div class="metric"><div class="metric-label">Predictions</div><div class="metric-value">72</div></div>
  <div class="metric"><div class="metric-label">Played</div><div class="metric-value">{played}</div></div>
  <div class="metric"><div class="metric-label">Correct</div><div class="metric-value">{correct}</div></div>
  <div class="metric"><div class="metric-label">Accuracy</div><div class="metric-value metric-accent">{accuracy}</div></div>
</div>
""", unsafe_allow_html=True)

html = '<div class="groups">'
for grp in sorted(preds["group"].unique()):
    gp = preds[preds["group"] == grp].sort_values("date")
    html += f'<div class="group"><div class="group-head">{grp.upper()}</div>'
    for _, row in gp.iterrows():
        conf = int(row["confidence_%"])
        fill = "bar-draw" if row["prediction"] == "Draw" else "bar-fill"
        html += f'<div class="match"><div class="match-teams">{row["team1"]} v {row["team2"]}</div><div class="match-pred">{row["prediction"]} · {conf}%</div><div class="bar"><div class="{fill}" style="width:{conf}%"></div></div></div>'
    html += '</div>'
html += '</div>'
st.markdown(html, unsafe_allow_html=True)

if played > 0:
    st.markdown('<div class="section-label">Results vs Predictions</div>', unsafe_allow_html=True)
    merged["result"] = merged["correct"].map({True: "✓", False: "✗"})
    st.dataframe(merged[["date","group","team1","team2","prediction","actual","result"]], use_container_width=True, hide_index=True)
else:
    st.markdown('<div class="section-label">Tracking activates June 11</div>', unsafe_allow_html=True)