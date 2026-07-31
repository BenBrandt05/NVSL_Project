#==========================================================================
# LIBRARIES
#==========================================================================
import streamlit as st
import pandas as pd
from pathlib import Path
import plotly.express as px
import numpy as np

#==========================================================================
# PAGE/PATH CONFIGURATION
#==========================================================================
st.set_page_config(
    page_title = "NVSL ELO Dashboard - Team Deep Dive",
    layout="centered"
)

st.markdown("""
    <style>
        h1, h2, h3 { text-align: center; }
    </style>
""", unsafe_allow_html=True)

st.title("Team Deep Dive")

data_directory = Path(__file__).parent.parent.parent / 'Data'

df = pd.read_csv(data_directory / 'elo_all_years.csv')

#==========================================================================
# PAGE NAVIGATION
#==========================================================================
if st.button("Go To Home Page", width="stretch"):
    st.switch_page("Home_page.py")
if st.button("Go To All Time Records", width="stretch"):
    st.switch_page("pages/All_Time_Records.py")
if st.button("Go To League Overview", width="stretch"):
    st.switch_page("pages/league_overview.py")
if st.button("Go To Head to Head", width="stretch"):
    st.switch_page("pages/head_to_head.py")

st.divider()

#==========================================================================
# ELO AND RANK LINE CHART
#==========================================================================
team_list = list(df["Team"].drop_duplicates().sort_values())

selected_team = st.selectbox("Select a Team", team_list)

filtered_df = df.copy()
team_df = filtered_df[filtered_df["Team"] == selected_team]

st.subheader(f"ELO and Rank Line Charts for {selected_team}")

elo_fig = px.line(team_df, x="Year", y="Average ELO", title="ELO Change Over Time", markers=True)
elo_fig.update_layout(yaxis_title="ELO", yaxis=dict(range=[-50,3250]))

ranking_fig = px.line(team_df, x="Year", y=team_df["Average Ranking"], title="Ranking Change Over Time", markers=True)
ranking_fig.update_layout(yaxis_title="Ranking", yaxis=dict(range=[105,1]))

col1, col2 = st.columns(2)
col1.plotly_chart(elo_fig)
col2.plotly_chart(ranking_fig)

st.divider()

#==========================================================================
# YEAR BY YEAR STATS
#==========================================================================
years_list = list(df["Year"].drop_duplicates().sort_values())
earliest_year = min(years_list)
selected_year = st.selectbox("Select a Year", years_list)
st.subheader(f"{selected_team} Season Stats for {selected_year}")

matrix_df = pd.read_csv(data_directory / "all_records_matrix.csv")
wl_history = matrix_df[matrix_df["Team"] == selected_team]
wl_year = wl_history[str(selected_year)]

def parse_win_loss(wl_year):
    score = wl_year.iloc[0]
    record = score.rsplit("-", 1)
    wins = int(record[0])
    losses = int(record[1])
    return wins, losses

num_wins, num_losses = parse_win_loss(wl_year)

if selected_year > earliest_year:
    current_elo = team_df.loc[team_df["Year"] == selected_year, "Average ELO"].iloc[0]
    previous_elo = team_df.loc[team_df["Year"] == selected_year - 1, "Average ELO"].iloc[0]
    elo_delta = np.round(current_elo - previous_elo, 2)

    current_ranking = team_df.loc[team_df["Year"] == selected_year, "Average Ranking"].iloc[0]
    previous_ranking = team_df.loc[team_df["Year"] == selected_year - 1, "Average Ranking"].iloc[0]
    ranking_delta = np.round(current_ranking - previous_ranking, 2)
else:
    elo_delta = 0
    ranking_delta = 0
     
col1, col2, col3 = st.columns(3)
col1.metric("Wins", num_wins, border=True)
col2.metric("Losses", num_losses, border=True)
col3.metric("Win %", f"{np.round((num_wins/(num_wins + num_losses))*100, 2)}%", border=True)

col1, col2 = st.columns(2)
col1.metric("Season ELO",
            team_df[team_df["Year"] == selected_year]["Average ELO"],
            delta = elo_delta,
            border=True)
col2.metric("Season Ranking",
            team_df[team_df["Year"] == selected_year]["Average Ranking"],
            delta = ranking_delta,
            delta_color="inverse",
            border=True)
st.divider()

#==========================================================================
# OVERALL STATS
#==========================================================================
st.subheader(f"{selected_team} Overall Stats since {earliest_year}")

num_total_wins = 0
num_total_losses = 0
for i in range(len(years_list)):
    num_wins, num_losses = parse_win_loss(wl_history[str(years_list[i])])
    num_total_wins += num_wins
    num_total_losses += num_losses

col1, col2, col3 = st.columns(3)
col1.metric(f"Total Wins since {earliest_year}", num_total_wins, border=True)
col2.metric(f"Total Losses since {earliest_year}", num_total_losses, border=True)
col3.metric("Total Win %", f"{np.round((num_total_wins/(num_total_wins+num_total_losses))*100, 2)}%", border=True)

peak_elo = max(team_df["Average ELO"])
peak_rank = min(team_df["Average Ranking"])

col1, col2 = st.columns(2)
col1.metric(f"{selected_team} Peak ELO", peak_elo, border=True)
col2.metric(f"{selected_team} Peak Rank", peak_rank, border=True)
    
