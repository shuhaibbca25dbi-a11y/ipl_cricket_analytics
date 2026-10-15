"""IPL Analytics Dashboard — Teams & Venues (Streamlit)

Run:  pip install -r requirements.txt
      streamlit run app.py
Keep matches.csv, teams.csv, venues.csv (and the .streamlit/config.toml theme) next to this file.
"""
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="IPL Analytics | Teams & Venues", page_icon="🏏", layout="wide")
DATA = Path(__file__).parent

# ------------------------------------------------------------------ constants
CODE = {
    "Royal Challengers Bangalore": "RCB", "Sunrisers Hyderabad": "SRH", "Mumbai Indians": "MI",
    "Rising Pune Supergiant": "RPS", "Gujarat Lions": "GL", "Kolkata Knight Riders": "KKR",
    "Chennai Super Kings": "CSK", "Rajasthan Royals": "RR", "Delhi Capitals": "DC",
    "Punjab Kings": "PBKS", "Lucknow Super Giants": "LSG", "Gujarat Titans": "GT",
    "Kochi Tuskers Kerala": "KTK", "Pune Warriors": "PWI",
}
NAME = {v: k for k, v in CODE.items()}
COLORS = {"RCB": "#e5383b", "SRH": "#ff7a1a", "MI": "#2f7df6", "RPS": "#c04fb0", "GL": "#d9902f",
          "KKR": "#7c4dff", "CSK": "#ffd23f", "RR": "#ff5fa2", "DC": "#27c4f5", "PBKS": "#ff8a8a",
          "LSG": "#2dd4bf", "GT": "#8ba7d6", "KTK": "#a07c4a", "PWI": "#4ade80"}
ORANGE, BLUE, GREEN, GREY = "#ff8a3d", "#38bdf8", "#4ade80", "#64748b"
REGION_COLORS = {"India": BLUE, "UAE": ORANGE, "South Africa": GREEN}
CHASE_SCALE = [[0, BLUE], [0.5, "#e2e8f0"], [1, ORANGE]]
WL_SCALE = [[0, "#b91c1c"], [0.5, "#334155"], [1, "#16a34a"]]

# keyword in raw venue name -> (clean venue, city, region, lat, lon).  Merges naming variants of the same ground.
VENUES = [
    ("Sheikh Zayed", "Sheikh Zayed Stadium", "Abu Dhabi", "UAE", 24.416, 54.543),
    ("Zayed Cricket", "Sheikh Zayed Stadium", "Abu Dhabi", "UAE", 24.416, 54.543),
    ("Narendra Modi", "Narendra Modi Stadium", "Ahmedabad", "India", 23.092, 72.597),
    ("Sardar Patel", "Narendra Modi Stadium", "Ahmedabad", "India", 23.092, 72.597),
    ("Chinnaswamy", "M Chinnaswamy Stadium", "Bengaluru", "India", 12.979, 77.600),
    ("OUTsurance", "OUTsurance Oval", "Bloemfontein", "South Africa", -29.107, 26.208),
    ("Newlands", "Newlands", "Cape Town", "South Africa", -33.972, 18.469),
    ("SuperSport", "SuperSport Park", "Centurion", "South Africa", -25.858, 28.174),
    ("Maharaja Yadavindra", "Maharaja Yadavindra Singh Stadium", "New Chandigarh", "India", 30.800, 76.720),
    ("Punjab Cricket Association", "PCA IS Bindra Stadium", "Mohali", "India", 30.691, 76.737),
    ("Chidambaram", "MA Chidambaram Stadium", "Chennai", "India", 13.063, 80.279),
    ("Barabati", "Barabati Stadium", "Cuttack", "India", 20.474, 85.870),
    ("Arun Jaitley", "Arun Jaitley Stadium", "Delhi", "India", 28.638, 77.243),
    ("Feroz Shah", "Arun Jaitley Stadium", "Delhi", "India", 28.638, 77.243),
    ("Himachal", "HPCA Stadium", "Dharamsala", "India", 32.198, 76.326),
    ("Dubai International", "Dubai International Stadium", "Dubai", "UAE", 25.047, 55.218),
    ("Kingsmead", "Kingsmead", "Durban", "South Africa", -29.849, 31.029),
    ("Buffalo Park", "Buffalo Park", "East London", "South Africa", -32.999, 27.919),
    ("Barsapara", "Barsapara Stadium", "Guwahati", "India", 26.139, 91.778),
    ("Rajiv Gandhi", "Rajiv Gandhi Intl Stadium", "Hyderabad", "India", 17.406, 78.550),
    ("Holkar", "Holkar Stadium", "Indore", "India", 22.724, 75.880),
    ("Sawai Mansingh", "Sawai Mansingh Stadium", "Jaipur", "India", 26.894, 75.804),
    ("New Wanderers", "New Wanderers Stadium", "Johannesburg", "South Africa", -26.132, 28.060),
    ("Green Park", "Green Park", "Kanpur", "India", 26.480, 80.332),
    ("De Beers", "De Beers Diamond Oval", "Kimberley", "South Africa", -28.742, 24.764),
    ("Nehru Stadium", "Nehru Stadium", "Kochi", "India", 9.999, 76.302),
    ("Eden Gardens", "Eden Gardens", "Kolkata", "India", 22.565, 88.343),
    ("Ekana", "BRSABV Ekana Stadium", "Lucknow", "India", 26.810, 80.990),
    ("Brabourne", "Brabourne Stadium", "Mumbai", "India", 18.932, 72.825),
    ("DY Patil", "DY Patil Stadium", "Mumbai", "India", 19.043, 73.026),
    ("Wankhede", "Wankhede Stadium", "Mumbai", "India", 18.939, 72.826),
    ("Vidarbha", "VCA Stadium", "Nagpur", "India", 21.093, 79.116),
    ("St George", "St George's Park", "Port Elizabeth", "South Africa", -33.936, 25.604),
    ("Maharashtra Cricket", "MCA Stadium", "Pune", "India", 18.674, 73.706),
    ("Subrata Roy", "MCA Stadium", "Pune", "India", 18.674, 73.706),
    ("Shaheed Veer", "Shaheed Veer Narayan Singh Stadium", "Raipur", "India", 21.200, 81.780),
    ("Saurashtra", "Saurashtra Cricket Stadium", "Rajkot", "India", 22.270, 70.790),
    ("JSCA", "JSCA Stadium", "Ranchi", "India", 23.315, 85.275),
    ("Sharjah", "Sharjah Cricket Stadium", "Sharjah", "UAE", 25.328, 55.419),
    ("Rajasekhara", "ACA-VDCA Stadium", "Visakhapatnam", "India", 17.799, 83.352),
]

# ------------------------------------------------------------------ page style
st.markdown("""
<style>
.stApp{background:radial-gradient(1100px 520px at 8% -8%,#1b2660 0%,transparent 60%),
 radial-gradient(900px 480px at 100% 0%,#4a1d5c66 0%,transparent 58%),#090d18;color:#e6e9f2}
header[data-testid="stHeader"]{background:transparent}
#MainMenu,footer{visibility:hidden}
.block-container{padding-top:1.2rem;max-width:1440px}
section[data-testid="stSidebar"]{background:#0d1322;border-right:1px solid #1f2a44}
.hero{border-radius:22px;padding:30px 34px;margin-bottom:18px;position:relative;overflow:hidden;
 background:linear-gradient(115deg,#1a2a8a 0%,#6d28d9 52%,#ff7a3d 118%);box-shadow:0 18px 50px rgba(80,40,200,.35)}
.hero:after{content:"🏏";position:absolute;right:26px;top:-6px;font-size:9rem;opacity:.12;transform:rotate(18deg)}
.hero h1{margin:0;font-size:2.25rem;font-weight:800;letter-spacing:-.025em;color:#fff;padding:0}
.hero p{margin:6px 0 14px;color:#dfe6ff;font-size:1.02rem}
.pill{display:inline-block;margin:0 8px 0 0;padding:4px 12px;border-radius:999px;font-size:.78rem;font-weight:600;
 background:rgba(255,255,255,.16);color:#fff;border:1px solid rgba(255,255,255,.22)}
.kgrid{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));margin:4px 0 18px}
.kpi{padding:16px 18px;border-radius:16px;background:rgba(18,26,46,.8);border:1px solid #1f2a44;position:relative;overflow:hidden}
.kpi:before{content:"";position:absolute;left:0;top:0;bottom:0;width:4px;background:var(--c,#38bdf8)}
.kpi .l{font-size:.74rem;text-transform:uppercase;letter-spacing:.08em;color:#8b98b8;font-weight:600}
.kpi .v{font-size:1.9rem;font-weight:800;color:#fff;line-height:1.25}
.kpi .n{font-size:.78rem;color:#7d8bad}
.ins{padding:14px 16px;border-radius:14px;background:linear-gradient(160deg,rgba(30,41,75,.9),rgba(18,26,46,.9));border:1px solid #26335a;height:100%}
.ins .i{font-size:1.4rem}.ins .l{font-size:.72rem;text-transform:uppercase;letter-spacing:.08em;color:#8b98b8;font-weight:600}
.ins .v{font-size:1.12rem;font-weight:700;color:#fff;margin:2px 0}.ins .n{font-size:.8rem;color:#9fb0d6}
[class*="st-key-panel"]{background:rgba(16,23,42,.78);border:1px solid #1f2a44;border-radius:18px;padding:16px 18px 10px;
 box-shadow:0 6px 24px rgba(0,0,0,.25)}
.pt{font-size:1.02rem;font-weight:700;color:#f1f5ff}.ps{font-size:.8rem;color:#8b98b8;margin:1px 0 8px}
.stTabs [data-baseweb="tab-list"]{gap:8px;border-bottom:none}
.stTabs [data-baseweb="tab"]{background:#121a2e;border-radius:12px;padding:9px 20px;height:auto;border:1px solid #1f2a44;color:#aab6d3}
.stTabs [aria-selected="true"]{background:linear-gradient(120deg,#3b4bd8,#7c3aed)!important;color:#fff!important;border-color:transparent}
.stTabs [data-baseweb="tab-highlight"],.stTabs [data-baseweb="tab-border"]{display:none}
.sec{font-size:1.25rem;font-weight:800;color:#fff;margin:18px 0 6px}

/* ---------- animations ---------- */
@keyframes fadeUp{from{opacity:0;transform:translateY(20px)}to{opacity:1;transform:none}}
@keyframes fadeIn{from{opacity:0}to{opacity:1}}
@keyframes gradShift{0%{background-position:0% 50%}50%{background-position:100% 50%}100%{background-position:0% 50%}}
@keyframes floatBat{0%,100%{transform:rotate(18deg) translateY(0)}50%{transform:rotate(8deg) translateY(-14px)}}
@keyframes sheen{0%{left:-45%}60%,100%{left:130%}}
@keyframes pulseDot{0%{box-shadow:0 0 0 0 rgba(255,138,61,.75)}100%{box-shadow:0 0 0 10px rgba(255,138,61,0)}}
@keyframes grow{from{width:0}to{width:52px}}

.hero{background-size:220% 220%;animation:fadeUp .8s ease both,gradShift 14s ease infinite}
.hero:after{animation:floatBat 6s ease-in-out infinite}
.hero:before{content:"";position:absolute;top:0;left:-45%;width:35%;height:100%;pointer-events:none;
 background:linear-gradient(100deg,transparent,rgba(255,255,255,.16),transparent);transform:skewX(-20deg);animation:sheen 7s ease-in-out infinite}
.pill{animation:fadeUp .7s ease both;transition:transform .25s,background .25s}
.pill:hover{transform:translateY(-2px);background:rgba(255,255,255,.28)}
.pill:nth-of-type(1){animation-delay:.25s}.pill:nth-of-type(2){animation-delay:.4s}
.pill:nth-of-type(3){animation-delay:.55s}.pill:nth-of-type(4){animation-delay:.7s}
.pill:first-of-type:before{content:"";display:inline-block;width:8px;height:8px;margin-right:8px;border-radius:50%;
 background:#ff8a3d;animation:pulseDot 1.6s infinite}

.kpi{animation:fadeUp .7s ease both;transition:transform .25s,box-shadow .25s,border-color .25s}
.kpi:hover{transform:translateY(-5px);border-color:var(--c,#38bdf8);box-shadow:0 12px 30px rgba(0,0,0,.35)}
.kpi:after{content:"";position:absolute;top:0;left:-60%;width:40%;height:100%;pointer-events:none;
 background:linear-gradient(100deg,transparent,rgba(255,255,255,.10),transparent);transform:skewX(-20deg);transition:left .7s ease}
.kpi:hover:after{left:140%}
.kgrid .kpi:nth-child(1){animation-delay:.1s}.kgrid .kpi:nth-child(2){animation-delay:.2s}
.kgrid .kpi:nth-child(3){animation-delay:.3s}.kgrid .kpi:nth-child(4){animation-delay:.4s}
.kgrid .kpi:nth-child(5){animation-delay:.5s}.kgrid .kpi:nth-child(6){animation-delay:.6s}

[class*="st-key-panel"]{animation:fadeUp .8s ease both;transition:border-color .3s,box-shadow .3s}
[class*="st-key-panel"]:hover{border-color:#4a5bd8;box-shadow:0 10px 34px rgba(79,70,229,.28),0 0 0 1px rgba(124,58,237,.25)}

.stTabs [data-baseweb="tab"]{transition:transform .25s,color .25s,border-color .25s,background .25s}
.stTabs [data-baseweb="tab"]:hover{transform:translateY(-2px);color:#fff;border-color:#4a5bd8}
.stTabs [aria-selected="true"]{background-size:220% 220%!important;animation:gradShift 6s ease infinite}
.stTabs [data-baseweb="tab-panel"]{animation:fadeUp .55s ease both}

section[data-testid="stSidebar"]{animation:fadeIn .9s ease both}
.sec{position:relative;animation:fadeUp .6s ease both}
.sec:after{content:"";display:block;height:3px;width:52px;margin-top:5px;border-radius:3px;
 background:linear-gradient(90deg,#ff8a3d,#7c3aed);animation:grow 1s ease .3s both}
.stDownloadButton button,.stButton button{transition:transform .25s,box-shadow .25s}
.stDownloadButton button:hover,.stButton button:hover{transform:translateY(-2px);box-shadow:0 8px 22px rgba(255,138,61,.3)}

@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
</style>""", unsafe_allow_html=True)

_n = 0


@contextmanager
def panel(title, sub=""):
    """A styled card."""
    global _n
    _n += 1
    with st.container(key=f"panel_{_n}"):
        st.markdown(f"<div class='pt'>{title}</div><div class='ps'>{sub}</div>", unsafe_allow_html=True)
        yield


def sty(fig, h=380, legend=False, **kw):
    fig.update_layout(height=h, margin=dict(l=6, r=6, t=6, b=6), paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", showlegend=legend,
                      font=dict(color="#cbd5e1", family="Inter, system-ui, sans-serif", size=12),
                      legend=dict(orientation="h", y=-0.2, x=0, bgcolor="rgba(0,0,0,0)"),
                      hoverlabel=dict(bgcolor="#0b1026", bordercolor="#334155", font_color="#e2e8f0"), **kw)
    ax = dict(gridcolor="rgba(148,163,184,.12)", zeroline=False, linecolor="rgba(148,163,184,.2)")
    fig.update_xaxes(**ax)
    fig.update_yaxes(**ax)
    return fig


def show(fig, key):
    st.plotly_chart(fig, key=key, config={"displayModeBar": False})


# ------------------------------------------------------------------ data
@st.cache_data
def load():
    teams = pd.read_csv(DATA / "teams.csv")
    venues = pd.read_csv(DATA / "venues.csv")
    m = pd.read_csv(DATA / "matches.csv")

    names = teams.set_index("team_id").team_name  # teams.csv -> names
    for c in ["team1", "team2", "toss_winner", "match_winner"]:
        m[c] = m[f"{c}_id"].map(names)

    vcity = venues.dropna(subset=["city"]).drop_duplicates("venue").set_index("venue").city  # venues.csv -> city
    raw_city = m.venue.map(vcity).fillna(m.city)
    info = {}
    for v in m.venue.unique():
        hit = next((r for r in VENUES if r[0].lower() in v.lower()), None)
        info[v] = hit[1:] if hit else (v, raw_city[m.venue == v].iloc[0], "India", np.nan, np.nan)
    m[["venue_name", "venue_city", "region", "lat", "lon"]] = m.venue.map(info).apply(pd.Series)
    m[["lat", "lon"]] = m[["lat", "lon"]].astype(float)

    m["match_date"] = pd.to_datetime(m.match_date)
    m.loc[m.result == "no result", "match_winner"] = np.nan  # source lists a winner for one washed-out game
    m["won_by"] = np.where(m.win_by_runs.notna(), "Batting first", np.where(m.win_by_wickets.notna(), "Chasing", None))
    other = np.where(m.toss_winner == m.team1, m.team2, m.team1)
    m["bat_first_team"] = np.where(m.toss_decision == "bat", m.toss_winner, other)
    m["margin"] = np.select(
        [m.result == "tie", m.result == "no result", m.win_by_runs.notna(), m.win_by_wickets.notna()],
        ["Super over", "No result", m.win_by_runs.fillna(0).astype(int).astype(str) + " runs",
         m.win_by_wickets.fillna(0).astype(int).astype(str) + " wkts"], "")
    seasons = sorted(m.season.unique(), key=lambda s: int(s[:4]))
    m["season_i"] = m.season.map({s: i for i, s in enumerate(seasons)})
    return m, seasons


def long_form(mf):
    """One row per team per decided match."""
    t = pd.concat([mf.assign(team=mf.team1, opp=mf.team2), mf.assign(team=mf.team2, opp=mf.team1)], ignore_index=True)
    t = t[t.result != "no result"].copy()
    t["won"] = t.team == t.match_winner
    t["bat_first"] = t.team == t.bat_first_team
    t["toss_won"] = t.team == t.toss_winner
    t["code"] = t.team.map(CODE)
    return t


def team_stats(t):
    g = t.groupby("code")
    ts = pd.DataFrame({"p": g.size(), "w": g.won.sum()})
    bf, ch = t[t.bat_first].groupby("code").won.agg(["sum", "size"]), t[~t.bat_first].groupby("code").won.agg(["sum", "size"])
    ts["pct"] = 100 * ts.w / ts.p
    ts["bf_pct"], ts["ch_pct"] = 100 * bf["sum"] / bf["size"], 100 * ch["sum"] / ch["size"]
    ts["l"] = ts.p - ts.w
    return ts.sort_values("w", ascending=False)


def venue_stats(mf):
    g = mf.groupby(["venue_name", "venue_city", "region", "lat", "lon"], dropna=False)
    vs = g.agg(matches=("match_id", "size"), decided=("won_by", lambda s: s.notna().sum()),
               chase_wins=("won_by", lambda s: (s == "Chasing").sum()), bat_wins=("won_by", lambda s: (s == "Batting first").sum()),
               ties=("result", lambda s: (s == "tie").sum()), field_pct=("toss_decision", lambda s: 100 * (s == "field").mean()),
               top_team=("match_winner", lambda s: CODE.get(s.mode()[0], "") if s.notna().any() else "")).reset_index()
    vs = vs.rename(columns={"venue_city": "city"})
    vs["chase_pct"] = 100 * vs.chase_wins / vs.decided.replace(0, np.nan)
    return vs


m, SEASONS = load()

# ------------------------------------------------------------------ sidebar filters
st.sidebar.markdown("### 🎛️ Filters")
s_a, s_b = st.sidebar.select_slider("Seasons", options=SEASONS, value=(SEASONS[0], SEASONS[-1]))
regions = st.sidebar.multiselect("Host region", ["India", "UAE", "South Africa"], default=["India", "UAE", "South Africa"])
all_teams = sorted(set(m.team1) | set(m.team2))
sel_teams = st.sidebar.multiselect("Focus teams", all_teams, placeholder="All teams")
st.sidebar.caption("Focus teams limits the team charts to the teams you choose.")
st.sidebar.markdown("---")
st.sidebar.caption("2026 is a partial season (data to 1 May 2026). No-result matches are excluded from win statistics; super-over wins count as wins.")

mf = m[(m.season_i >= SEASONS.index(s_a)) & (m.season_i <= SEASONS.index(s_b)) & m.region.isin(regions)]
if sel_teams:
    mf = mf[mf.team1.isin(sel_teams) | mf.team2.isin(sel_teams)]
season_list = SEASONS[SEASONS.index(s_a): SEASONS.index(s_b) + 1]
tm = long_form(mf) if len(mf) else pd.DataFrame()
if mf.empty or tm.empty:
    st.warning("No matches for these filters — widen the season range, region or teams.")
    st.stop()
tms = tm[tm.team.isin(sel_teams)] if sel_teams else tm
ts, vs = team_stats(tms), venue_stats(mf)
dec = mf[mf.result != "no result"]
chased = mf[mf.won_by.notna()]


def bar_h(labels, values, colors, text=None, h=380, xrange=None, key="", hover=None):
    """Simple horizontal bar chart (largest at the top)."""
    fig = go.Figure(go.Bar(y=labels, x=values, orientation="h", marker_color=colors, text=text, textposition="outside",
                           textfont=dict(color="#e2e8f0"), hovertemplate=hover or "%{y}: %{x}<extra></extra>", cliponaxis=False))
    fig.update_xaxes(title=None, range=xrange); fig.update_yaxes(title=None)
    show(sty(fig, h), key)


# ------------------------------------------------------------------ hero + KPIs
st.markdown(f"""<div class="hero"><h1>IPL Performance Dashboard</h1>
<p>How every franchise and every ground has performed across {len(season_list)} seasons.</p>
<span class="pill">{s_a} → {s_b}</span><span class="pill">{ts.shape[0]} teams</span>
<span class="pill">{vs.shape[0]} venues</span><span class="pill">{vs.city.nunique()} cities</span></div>""", unsafe_allow_html=True)


def kpis(items, cols=None):
    style = f" style='grid-template-columns:repeat({cols},1fr)'" if cols else ""
    st.markdown(f"<div class='kgrid'{style}>" + "".join(
        f"<div class='kpi' style='--c:{c}'><div class='l'>{l}</div><div class='v'>{v}</div><div class='n'>{n}</div></div>"
        for l, v, n, c in items) + "</div>", unsafe_allow_html=True)


kpis([("Matches", f"{len(mf):,}", f"{len(season_list)} seasons", BLUE),
      ("Teams", ts.shape[0], "franchises", ORANGE),
      ("Venues", vs.shape[0], f"in {vs.city.nunique()} cities", GREEN),
      ("Toss winner won", f"{100 * (dec.toss_winner == dec.match_winner).mean():.0f}%", "of decided matches", "#c084fc"),
      ("Chose to field", f"{100 * (mf.toss_decision == 'field').mean():.0f}%", "of toss winners", "#f472b6")])

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Overview", "🏆 Teams", "🏟️ Venues", "⚔️ Team vs Team", "🔎 Match Explorer"])

# ================================================================== OVERVIEW
with tab1:
    a, b = st.columns(2)
    per = mf.groupby("season").size().reindex(season_list, fill_value=0)
    with a, panel("Matches played each season", f"Busiest season: {per.idxmax()} with {per.max()} matches"):
        fig = go.Figure(go.Bar(x=per.index, y=per.values, marker_color=BLUE, text=per.values, textposition="outside",
                               textfont=dict(color="#e2e8f0"), hovertemplate="%{x}: %{y} matches<extra></extra>"))
        fig.update_xaxes(title=None); fig.update_yaxes(title=None, showgrid=False)
        fig.update_xaxes(type="category")
        show(sty(fig, 360), "ov_season")
    with b, panel("Which team has won the most matches?", f"{NAME[ts.index[0]]} lead with {int(ts.w.iloc[0])} wins"):
        t = ts.sort_values("w")
        bar_h(t.index, t.w, [COLORS[c] for c in t.index], t.w.astype(int), 360, [0, t.w.max() * 1.15], "ov_wins",
              "%{y}: %{x} wins<extra></extra>")
    c, d = st.columns(2)
    top_v = vs.nlargest(10, "matches").sort_values("matches")
    with c, panel("Which venues host the most matches?", f"{top_v.venue_name.iloc[-1]} ({top_v.city.iloc[-1]}) leads with {int(top_v.matches.iloc[-1])}"):
        bar_h(top_v.venue_name, top_v.matches, GREEN, top_v.matches, 400, [0, top_v.matches.max() * 1.15], "ov_venues")
    with d, panel("What do captains choose after winning the toss?", "Share of matches where the toss winner chose to bat or field"):
        td = mf.toss_decision.value_counts()
        fig = px.pie(names=[k.capitalize() for k in td.index], values=td.values, hole=.62,
                     color_discrete_sequence=[ORANGE, BLUE])
        fig.update_traces(textinfo="percent+label", marker_line_width=0)
        show(sty(fig, 400), "ov_toss")

# ================================================================== TEAMS
with tab2:
    a, b = st.columns(2)
    with a, panel("Win rate by team", "Wins ÷ matches played (dotted line = 50%)"):
        t = ts.sort_values("pct")
        fig = go.Figure(go.Bar(y=t.index, x=t.pct, orientation="h", marker_color=[COLORS[c] for c in t.index],
                               text=[f"{p:.0f}%  ({int(w)}/{int(n)})" for p, w, n in zip(t.pct, t.w, t.p)], textposition="outside",
                               textfont=dict(color="#e2e8f0"), customdata=[NAME[c] for c in t.index], cliponaxis=False,
                               hovertemplate="%{customdata}: %{x:.1f}%<extra></extra>"))
        fig.add_vline(x=50, line_color="#94a3b8", line_dash="dot")
        fig.update_xaxes(range=[0, 85], ticksuffix="%", title=None); fig.update_yaxes(title=None)
        show(sty(fig, 440), "tm_pct")
    with b, panel("Wins and losses by team", "How each franchise's matches ended"):
        t = ts.sort_values("p")
        fig = go.Figure([go.Bar(y=t.index, x=t.w, orientation="h", name="Wins", marker_color=GREEN),
                         go.Bar(y=t.index, x=t.l, orientation="h", name="Losses", marker_color="#ef4444")])
        fig.update_layout(barmode="stack"); fig.update_xaxes(title=None); fig.update_yaxes(title=None)
        show(sty(fig, 440, True), "tm_wl")

    with panel("Wins per season", "Pick teams to compare how their results changed over time"):
        pickt = st.multiselect("Teams to compare", list(ts.index), default=list(ts.index[:4]), label_visibility="collapsed")
        cw = tm[tm.won].groupby(["season", "code"]).size().unstack(fill_value=0).reindex(season_list, fill_value=0)
        fig = go.Figure()
        for code in pickt:
            if code in cw:
                fig.add_trace(go.Scatter(x=cw.index, y=cw[code], name=code, mode="lines+markers", line=dict(color=COLORS[code], width=3),
                                         hovertemplate=f"{NAME[code]}<br>%{{x}}: %{{y}} wins<extra></extra>"))
        fig.update_xaxes(title=None); fig.update_yaxes(title="Wins")
        fig.update_xaxes(type="category")
        show(sty(fig, 380, True), "tm_season")

    st.markdown("<div class='sec'>Team deep-dive</div>", unsafe_allow_html=True)
    pick = st.selectbox("Choose a franchise", list(ts.index), format_func=lambda c: f"{c} — {NAME[c]}", label_visibility="collapsed")
    T = tm[tm.code == pick]
    tv = T.groupby("venue_name").won.agg(w="sum", n="size").sort_values("w", ascending=False)
    kpis([("Matches", len(T), "decided matches", BLUE), ("Wins", int(T.won.sum()), f"{100 * T.won.mean():.1f}% win rate", GREEN),
          ("Win rate chasing", f"{100 * T[~T.bat_first].won.mean():.0f}%", "when batting second", ORANGE),
          ("Best venue", tv.index[0] if len(tv) else "–", f"{int(tv.w.iloc[0])} wins there" if len(tv) else "", "#c084fc")])
    d1, d2, d3 = st.columns(3)
    with d1, panel(f"{pick}: wins each season", ""):
        sw = T[T.won].groupby("season").size().reindex(season_list, fill_value=0)
        fig = go.Figure(go.Bar(x=sw.index, y=sw.values, marker_color=COLORS[pick], hovertemplate="%{x}: %{y} wins<extra></extra>"))
        fig.update_xaxes(title=None); fig.update_yaxes(title=None)
        fig.update_xaxes(type="category")
        show(sty(fig, 340), "tm_dd_season")
    with d2, panel(f"{pick}: most wins by venue", "Top 8 grounds"):
        v8 = tv.head(8).sort_values("w")
        bar_h(v8.index, v8.w, COLORS[pick], v8.w.astype(int), 340, [0, max(1, v8.w.max()) * 1.2], "tm_dd_venue")
    with d3, panel(f"{pick}: top match-winners", "Player-of-the-Match awards"):
        pm = T[T.won].player_of_match.value_counts().head(8).sort_values()
        bar_h(pm.index, pm.values, ORANGE, pm.values, 340, [0, max(1, pm.max()) * 1.2], "tm_dd_pom")

# ================================================================== VENUES
with tab3:
    a, b = st.columns([3, 2])
    with a, panel("Where the matches were played", "Each bubble is a stadium — bigger means more matches hosted"):
        view = st.radio("Region", ["All"] + sorted(vs.region.unique()), horizontal=True, label_visibility="collapsed")
        mp = vs.dropna(subset=["lat"]) if view == "All" else vs[vs.region == view].dropna(subset=["lat"])
        fig = px.scatter_geo(mp, lat="lat", lon="lon", size="matches", color="matches", size_max=36, projection="natural earth",
                             color_continuous_scale=[BLUE, "#a78bfa", ORANGE], hover_name="venue_name",
                             hover_data={"lat": False, "lon": False, "city": True, "matches": True})
        fig.update_geos(fitbounds="locations", bgcolor="rgba(0,0,0,0)", showland=True, landcolor="#1b2646", showocean=True,
                        oceancolor="#0a0f1e", showcountries=True, countrycolor="#33457a", coastlinecolor="#33457a",
                        showframe=False, showlakes=False)
        fig.update_traces(marker=dict(line=dict(width=1, color="#0b0f1a"), opacity=.9))
        fig.update_coloraxes(showscale=False)
        show(sty(fig, 440), "vn_map")
    cities = vs.groupby("city").matches.sum().nlargest(10).sort_values()
    with b, panel("Matches by city", f"{cities.index[-1]} hosted the most ({int(cities.iloc[-1])})"):
        bar_h(cities.index, cities.values, ORANGE, cities.values, 440, [0, cities.max() * 1.15], "vn_city")

    with panel("Do grounds favour batting first or chasing?", "Number of wins by the team batting first vs the team chasing (top 12 venues)"):
        t12 = vs.assign(tot=vs.bat_wins + vs.chase_wins).nlargest(12, "tot").sort_values("tot")
        fig = go.Figure([go.Bar(y=t12.venue_name, x=t12.bat_wins, orientation="h", name="Won batting first", marker_color=BLUE),
                         go.Bar(y=t12.venue_name, x=t12.chase_wins, orientation="h", name="Won chasing", marker_color=ORANGE)])
        fig.update_layout(barmode="stack"); fig.update_xaxes(title=None); fig.update_yaxes(title=None)
        show(sty(fig, 460, True), "vn_defchase")

    st.markdown("<div class='sec'>Venue explorer</div>", unsafe_allow_html=True)
    vsel = st.selectbox("Choose a venue", list(vs.sort_values("matches", ascending=False).venue_name), label_visibility="collapsed")
    row = vs[vs.venue_name == vsel].iloc[0]
    kpis([("Matches", int(row.matches), f"{row.city} · {row.region}", BLUE),
          ("Chasing wins", f"{row.chase_pct:.0f}%" if pd.notna(row.chase_pct) else "–", "of decided results", ORANGE),
          ("Toss winners fielded", f"{row.field_pct:.0f}%", "chose to field", GREEN),
          ("Most successful", NAME.get(row.top_team, "–"), "most wins here", "#c084fc")])
    with panel(f"Wins by team at {vsel}", "Which franchises have won the most matches here"):
        vw = tm[(tm.venue_name == vsel) & tm.won].groupby("code").size().sort_values()
        if len(vw):
            bar_h(vw.index, vw.values, [COLORS[c] for c in vw.index], vw.values, max(260, 32 * len(vw) + 40),
                  [0, vw.max() * 1.15], "vn_teams")
        else:
            st.info("No decided matches at this venue in the current selection.")

    with panel("Venue scorecard", "Every ground in the selection"):
        tbl = vs.sort_values("matches", ascending=False)[["venue_name", "city", "region", "matches", "bat_wins", "chase_wins", "top_team"]]
        st.dataframe(tbl, hide_index=True, column_config={
            "venue_name": "Venue", "city": "City", "region": "Region",
            "matches": st.column_config.ProgressColumn("Matches", min_value=0, max_value=int(tbl.matches.max()), format="%d"),
            "bat_wins": "Won batting 1st", "chase_wins": "Won chasing", "top_team": "Most wins"})

# ================================================================== TEAM vs TEAM
with tab4:
    order = list(team_stats(tm).index)
    p1, p2 = st.columns(2)
    A = p1.selectbox("Team A", order, index=0, format_func=lambda c: f"{c} — {NAME[c]}")
    B = p2.selectbox("Team B", order, index=min(1, len(order) - 1), format_func=lambda c: f"{c} — {NAME[c]}")
    if A == B:
        st.info("Pick two different teams to compare.")
    else:
        na, nb = NAME[A], NAME[B]
        pr = mf[((mf.team1 == na) & (mf.team2 == nb)) | ((mf.team1 == nb) & (mf.team2 == na))]
        if pr.empty:
            st.info("These teams didn't meet in the current selection.")
        else:
            wa, wb_ = int((pr.match_winner == na).sum()), int((pr.match_winner == nb).sum())
            kpis([(f"{A} wins", wa, na, COLORS[A]), (f"{B} wins", wb_, nb, COLORS[B]), ("Meetings", len(pr), "matches played", BLUE)])
            x1, x2 = st.columns(2)
            with x1, panel("Who wins more often?", "Head-to-head wins"):
                fig = go.Figure(go.Bar(x=[A, B], y=[wa, wb_], marker_color=[COLORS[A], COLORS[B]], text=[wa, wb_],
                                       textposition="outside", textfont=dict(color="#e2e8f0")))
                fig.update_xaxes(title=None); fig.update_yaxes(title=None, showgrid=False, range=[0, max(wa, wb_, 1) * 1.2])
                show(sty(fig, 340), "h2h_wins")
            with x2, panel("Wins by season", "Each season's head-to-head result"):
                sw = pr.assign(w=pr.match_winner.map(CODE)).dropna(subset=["w"]).groupby(["season", "w"]).size().reset_index(name="wins")
                fig = px.bar(sw, x="season", y="wins", color="w", barmode="group", color_discrete_map=COLORS,
                             category_orders={"season": season_list})
                fig.update_xaxes(title=None); fig.update_yaxes(title=None, dtick=1)
                fig.update_xaxes(type="category")
                show(sty(fig, 340, True, legend_title_text=""), "h2h_season")
            with panel("Latest meetings", ""):
                lm = pr.sort_values("match_date", ascending=False).head(8)
                st.dataframe(lm.assign(winner=lm.match_winner.map(CODE).fillna("–"), date=lm.match_date.dt.date)[
                    ["date", "season", "venue_name", "winner", "margin", "player_of_match"]], hide_index=True,
                    column_config={"date": "Date", "season": "Season", "venue_name": "Venue", "winner": "Winner",
                                   "margin": "Margin", "player_of_match": "Player of the match"})

# ================================================================== EXPLORER
with tab5:
    with panel("Match explorer", "Search by team, venue, city or player — then download what you see"):
        q = st.text_input("Search", placeholder="e.g. Eden Gardens, Kohli, Chennai …", label_visibility="collapsed")
        ex = mf.assign(winner=mf.match_winner.fillna("–"), date=mf.match_date.dt.date)
        if q:
            blob = (ex.team1 + " " + ex.team2 + " " + ex.venue_name + " " + ex.venue_city + " " + ex.player_of_match.fillna("")).str.lower()
            ex = ex[blob.str.contains(q.lower(), regex=False)]
        ex = ex.sort_values("match_date", ascending=False)[["date", "season", "team1", "team2", "toss_winner", "toss_decision",
                                                          "winner", "margin", "player_of_match", "venue_name", "venue_city"]]
        st.caption(f"{len(ex):,} matches")
        st.dataframe(ex, hide_index=True, height=520)
        st.download_button("⬇️ Download CSV", ex.to_csv(index=False).encode(), "ipl_matches_filtered.csv", "text/csv")
