#==========================================================================
# LIBRARIES
#==========================================================================
import streamlit as st
import pandas as pd
from pathlib import Path
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

#==========================================================================
# PAGE/PATH CONFIGURATION
#==========================================================================
st.set_page_config(
    page_title="NVSL ELO Dashboard - Head to Head",
    layout="centered"
)

st.markdown("""
    <style>
        h1, h2, h3 { text-align: center; }
    </style>
""", unsafe_allow_html=True)

st.title("Head to Head")

data_directory = Path(__file__).parent.parent.parent / "Data"

#==========================================================================
# DATA LOADING
#==========================================================================
@st.cache_data
def load_full_df(data_directory):
    years_csvs = sorted(data_directory.glob("results_*.csv"))

    dfs = []
    for file_path in years_csvs:
        year_df = pd.read_csv(file_path)
        year_df = year_df.replace(
            ["Bren Mar-Edsall Park", "Fair Oaks ", "Brookfield ", "Oakton ", "Kings Ridge "],
            ["Edsall Park", "Fair Oaks", "Brookfield", "Oakton", "Kings Ridge"]
        )
        dfs.append(year_df)

    return pd.concat(dfs, ignore_index=True)

full_df = load_full_df(data_directory)

#==========================================================================
# PAGE NAVIGATION
#==========================================================================
if st.button("Go To Home Page", use_container_width=True):
    st.switch_page("home_page.py")
if st.button("Go To All Time Team Records Page", use_container_width=True):
    st.switch_page("pages/all_time_records.py")
if st.button("Go To Team Deep Dive Page", use_container_width=True):
    st.switch_page("pages/team_deep_dive.py")
if st.button("Go To League Overview", use_container_width=True):
    st.switch_page("pages/league_overview.py")

st.divider()

#==========================================================================
# HEAD TO HEAD
#==========================================================================
team_list = sorted(pd.unique(pd.concat([full_df["First Team"], full_df["Second Team"]])))

col1, col2 = st.columns(2)
with col1:
    team1 = st.selectbox("Team One", team_list)
with col2:
    team2 = st.selectbox("Team Two", team_list)

if team1 == team2:
    st.info("Team is the same please select two different teams")
    st.stop()

filtered_df = full_df[((full_df["First Team"] == team1) & (full_df["Second Team"] == team2))].reset_index(drop=True)

def get_team_records(filtered_df, team1, team2):
    team1_wins = 0
    team1_losses = 0
    team2_wins = 0
    team2_losses = 0

    for i in range(len(filtered_df)):
        row = filtered_df.iloc[i]
        score_parts = row["Score"].rsplit(" - ", 1)

        if len(score_parts) != 2:
            continue

        left_score = score_parts[0].strip()
        right_score = score_parts[1].strip()

        if team1 in left_score:
            team1_wins += 1
            team2_losses += 1
        else:
            team1_losses += 1
            team2_wins += 1

    return team1_wins, team1_losses, team2_wins, team2_losses

team1_wins, team1_losses, team2_wins, team2_losses = get_team_records(filtered_df, team1, team2)

col1, col2 = st.columns(2)
with col1:
    st.metric(f"{team1} Wins", team1_wins, border=True)
    st.metric(f"{team1} Losses", team1_losses, border=True)
    st.metric(f"{team1} Win %", f"{np.round((team1_wins/(team1_wins+team1_losses))*100, 2)}%", border=True)
with col2:
    st.metric(f"{team2} Wins", team2_wins, border=True)
    st.metric(f"{team2} Losses", team2_losses, border=True)
    st.metric(f"{team2} Win %", f"{np.round((team2_wins/(team2_wins+team2_losses))*100, 2)}%", border=True)

st.divider()

#==========================================================================
# ELO HISTORY OVERLAY
#==========================================================================
elo_df = pd.read_csv(data_directory / 'elo_all_years.csv')

team1_elo = elo_df[elo_df["Team"] == team1][["Year", "Average ELO"]].rename(columns={"Average ELO": "ELO"})
team2_elo = elo_df[elo_df["Team"] == team2][["Year", "Average ELO"]].rename(columns={"Average ELO": "ELO"})

team1_elo["Team"] = team1
team2_elo["Team"] = team2

combined_elo = pd.concat([team1_elo, team2_elo], ignore_index=True)

if combined_elo.empty:
    st.info("No ELO history available for these teams.")
else:
    st.subheader("ELO History Comparison")

    elo_fig = px.line(
        combined_elo,
        x="Year",
        y="ELO",
        color="Team",
        markers=True,
        title=f"{team1} vs {team2} — ELO Over Time"
    )

    elo_fig.update_layout(
        xaxis=dict(tickmode="linear", dtick=1),
        yaxis_title="Average ELO",
        legend_title="Team",
        hovermode="x unified"
    )

    st.plotly_chart(elo_fig, use_container_width=True)

st.divider()

#==========================================================================
# YEAR BY YEAR RECORD
#==========================================================================
st.subheader("Year by Year Record")

def get_yearly_records(full_df, team1, team2):
    rows = []
    all_years = sorted(full_df["First Week"].str.extract(r'(\d{4})')[0].dropna().unique()) if False else []

    yearly_filtered = full_df[
        (full_df["First Team"] == team1) & (full_df["Second Team"] == team2)
    ].copy()

    if yearly_filtered.empty:
        return pd.DataFrame()

    elo_years = sorted(elo_df["Year"].unique())

    for year in elo_years:
        results_path = data_directory / f"results_{year}.csv"
        if not results_path.exists():
            continue

        year_df = pd.read_csv(results_path)
        year_df = year_df.replace(
            ["Bren Mar-Edsall Park", "Fair Oaks ", "Brookfield ", "Oakton ", "Kings Ridge "],
            ["Edsall Park", "Fair Oaks", "Brookfield", "Oakton", "Kings Ridge"]
        )

        matchup = year_df[
            (year_df["First Team"] == team1) & (year_df["Second Team"] == team2)
        ].reset_index(drop=True)

        if matchup.empty:
            continue

        t1_wins, t1_losses, t2_wins, t2_losses = get_team_records(matchup, team1, team2)
        total = t1_wins + t1_losses

        rows.append({
            "Year": year,
            f"{team1} Wins": t1_wins,
            f"{team2} Wins": t2_wins,
            "Total": total
        })

    return pd.DataFrame(rows)

yearly_df = get_yearly_records(full_df, team1, team2)

if yearly_df.empty:
    st.info("No year by year data available for this matchup.")
else:
    bar_fig = go.Figure()

    bar_fig.add_trace(go.Bar(
        name=team1,
        x=yearly_df["Year"],
        y=yearly_df[f"{team1} Wins"],
        marker_color="#636EFA"
    ))

    bar_fig.add_trace(go.Bar(
        name=team2,
        x=yearly_df["Year"],
        y=yearly_df[f"{team2} Wins"],
        marker_color="#EF553B"
    ))

    bar_fig.update_layout(
        barmode="group",
        title=f"{team1} vs {team2} — Wins Per Year",
        xaxis=dict(tickmode="linear", dtick=1, title="Year"),
        yaxis_title="Wins",
        legend_title="Team",
        hovermode="x unified"
    )

    st.plotly_chart(bar_fig, use_container_width=True)

    display_yearly = yearly_df.drop(columns=["Total"]).set_index("Year")
    st.dataframe(display_yearly, use_container_width=True)

st.divider()
