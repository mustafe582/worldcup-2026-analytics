# World Cup 2026 prediction model
# strength + last-10 form + travel + altitude + host advantage, Poisson scoreline
import requests, pandas as pd, io
from math import radians, sin, cos, asin, sqrt, exp, factorial

FIX_URL = "https://raw.githubusercontent.com/openfootball/worldcup.json/master/2026/worldcup.json"
RES_URL = "https://raw.githubusercontent.com/martj42/international_results/master/results.csv"
WC_START = pd.Timestamp("2026-06-11")

STRENGTH = {
 "Argentina":93,"France":92,"Spain":92,"England":90,"Brazil":90,"Portugal":89,
 "Netherlands":88,"Germany":86,"Belgium":85,"Uruguay":84,"Colombia":84,"Morocco":84,
 "Croatia":83,"Japan":81,"Senegal":81,"Switzerland":81,"USA":80,"Mexico":80,
 "Ecuador":80,"Austria":80,"Norway":80,"South Korea":78,"Scotland":78,"Turkey":78,
 "Czech Republic":78,"Algeria":78,"Egypt":77,"Bosnia & Herzegovina":77,"Sweden":76,
 "Australia":76,"Ivory Coast":76,"Ghana":76,"Paraguay":76,"Iran":76,"DR Congo":75,
 "Tunisia":75,"South Africa":74,"Qatar":74,"Saudi Arabia":73,"Uzbekistan":73,
 "Iraq":72,"Jordan":72,"Panama":72,"New Zealand":70,"Cape Verde":70,"Curaçao":68,"Haiti":68,
}
DEFAULT = 70
NAME_MAP = {"USA":"United States","Bosnia & Herzegovina":"Bosnia and Herzegovina"}
ALTITUDE_OK = {"Mexico","Ecuador","Colombia","Bolivia","Peru"}
VENUES = {
 "Mexico City":(19.30,-99.15,2240,"Mexico"),"Guadalajara (Zapopan)":(20.68,-103.46,1566,"Mexico"),
 "Monterrey (Guadalupe)":(25.67,-100.24,540,"Mexico"),"Atlanta":(33.76,-84.40,320,"United States"),
 "Boston (Foxborough)":(42.09,-71.26,90,"United States"),"Dallas (Arlington)":(32.75,-97.09,180,"United States"),
 "Houston":(29.68,-95.41,15,"United States"),"Kansas City":(39.05,-94.48,270,"United States"),
 "Los Angeles (Inglewood)":(33.95,-118.34,40,"United States"),"Miami (Miami Gardens)":(25.96,-80.24,2,"United States"),
 "New York/New Jersey (East Rutherford)":(40.81,-74.07,10,"United States"),"Philadelphia":(39.90,-75.17,12,"United States"),
 "San Francisco Bay Area (Santa Clara)":(37.40,-121.97,8,"United States"),"Seattle":(47.59,-122.33,50,"United States"),
 "Toronto":(43.63,-79.42,76,"Canada"),"Vancouver":(49.28,-123.11,70,"Canada"),
}
FORM_W, TRAVEL_W, ALT_W, HOST_BOOST = 6, 3, 4, 2.5

def haversine(a,b):
    (lat1,lon1),(lat2,lon2)=a,b
    dlat,dlon=radians(lat2-lat1),radians(lon2-lon1)
    h=sin(dlat/2)**2+cos(radians(lat1))*cos(radians(lat2))*sin(dlon/2)**2
    return 2*6371*asin(sqrt(h))

fix=requests.get(FIX_URL,timeout=30).json()
matches=pd.DataFrame(fix["matches"])
groups=matches[matches["group"].astype(str).str.startswith("Group")].copy()
groups["dt"]=pd.to_datetime(groups["date"])
res=pd.read_csv(io.StringIO(requests.get(RES_URL,timeout=60).text))
res["date"]=pd.to_datetime(res["date"])
res=res[(res["date"]<WC_START)&res["home_score"].notna()]
teams=sorted(set(groups["team1"])|set(groups["team2"]))

def form_adj(team):
    name=NAME_MAP.get(team,team)
    s=res[(res["home_team"]==name)|(res["away_team"]==name)].sort_values("date").tail(10)
    if len(s)==0: return 0.0
    pts=gd=0
    for _,m in s.iterrows():
        gf,ga=(m["home_score"],m["away_score"]) if m["home_team"]==name else (m["away_score"],m["home_score"])
        pts+=3 if gf>ga else 1 if gf==ga else 0; gd+=gf-ga
    ppg,gdpg=pts/len(s),gd/len(s)
    return round((0.6*((ppg-1.5)/1.5)+0.4*max(-3,min(3,gdpg))/3)*FORM_W,2)
FORM={t:form_adj(t) for t in teams}

sched={t:list(zip(groups[(groups.team1==t)|(groups.team2==t)].sort_values("dt")["dt"],
                  groups[(groups.team1==t)|(groups.team2==t)].sort_values("dt")["ground"])) for t in teams}
def travel_pen(team,dt,ground):
    seq=sched[team]; idx=[i for i,(d,g) in enumerate(seq) if d==dt and g==ground]
    if not idx or idx[0]==0: return 0.0
    i=idx[0]; pd_,pg=seq[i-1]
    pen=min(haversine(VENUES[pg][:2],VENUES[ground][:2])/4000,1)*TRAVEL_W
    rest=(dt-pd_).days
    if rest<4: pen+=0.5*(4-rest)
    return round(pen,2)
def alt_pen(team,ground):
    if team in ALTITUDE_OK or NAME_MAP.get(team,team) in ALTITUDE_OK: return 0.0
    return round(max(0,(VENUES[ground][2]-1000)/1500)*ALT_W,2)
def host(team,ground):
    return HOST_BOOST if VENUES[ground][3]==NAME_MAP.get(team,team) else 0.0
def eff(team,dt,ground):
    return STRENGTH.get(team,DEFAULT)+FORM[team]-travel_pen(team,dt,ground)-alt_pen(team,ground)+host(team,ground)

def pois(k,l): return exp(-l)*l**k/factorial(k)
def predict(t1,t2,dt,ground):
    diff=eff(t1,dt,ground)-eff(t2,dt,ground)
    l1=max(0.15,min(4.5,1.5*exp(0.022*diff))); l2=max(0.15,min(4.5,1.5*exp(-0.022*diff)))
    P1=[pois(i,l1) for i in range(7)]; P2=[pois(i,l2) for i in range(7)]
    w1=dr=w2=0; cells={}
    for i in range(7):
        for j in range(7):
            p=P1[i]*P2[j]; cells[(i,j)]=p
            if i>j: w1+=p
            elif i==j: dr+=p
            else: w2+=p
    probs={t1:w1,"Draw":dr,t2:w2}; outcome=max(probs,key=probs.get)
    if outcome==t1: v={k:p for k,p in cells.items() if k[0]>k[1]}
    elif outcome==t2: v={k:p for k,p in cells.items() if k[1]>k[0]}
    else: v={k:p for k,p in cells.items() if k[0]==k[1]}
    b=max(v,key=v.get)
    return outcome,round(probs[outcome]*100),f"{b[0]}-{b[1]}"

rows=[]
for _,m in groups.iterrows():
    o,c,sc=predict(m["team1"],m["team2"],m["dt"],m["ground"])
    rows.append({"date":m["date"],"group":m["group"],"team1":m["team1"],"team2":m["team2"],
                 "prediction":o,"confidence_%":c,"score":sc})
out=pd.DataFrame(rows)
out.to_csv("predictions.csv",index=False)
print(f"Generated {len(out)} predictions -> predictions.csv")
print(out.head(10).to_string(index=False))