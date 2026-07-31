#==========================================================================
# LIBRARIES
#==========================================================================
import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path

#==========================================================================
# PAGE/PATH CONFIGURATION
#==========================================================================
st.set_page_config(
    page_title="NVSL ELO Dashboard - Home Page",
    layout="centered"
)

st.markdown("""
    <style>
        h1, h2, h3 { text-align: center; }
    </style>
""", unsafe_allow_html=True)

st.title("Home Page")
              
data_directory = Path(__file__).parent.parent / 'Data'

df = pd.read_csv(data_directory / 'elo_all_years.csv')

#==========================================================================
# PAGE NAVIGATION
#==========================================================================
if st.button("Go To All Time Team Records Page", width="stretch"):
    st.switch_page("pages/All_Time_Records.py")
if st.button("Go To Team Deep Dive Page", width="stretch"):
    st.switch_page("pages/team_deep_dive.py")
if st.button("Go To League Overview", width="stretch"):
    st.switch_page("pages/league_overview.py")
if st.button("Go To Head to Head", width="stretch"):
    st.switch_page("pages/head_to_head.py")

st.divider()

#==========================================================================
# METRICS
#==========================================================================
highest_year = max(df['Year'])
best_current_team = df[(df['Year'] == highest_year) & (df['Rank'] == 1)].reset_index(drop=True)
worst_current_team = df[(df['Year'] == highest_year) & (df['Rank'] == 102)].reset_index(drop=True)

most_recent = df[df['Year'] == highest_year]
second_most_recent = df[df['Year'] == highest_year-1]

sorted_teams_list = sorted(list(most_recent["Team"]))

add_diff = 0
for i in range(len(sorted_teams_list)):
    team = sorted_teams_list[i]
    most_recent_rank = most_recent.loc[most_recent["Team"] == team]["Rank"].iloc[-1]
    second_most_recent_rank = second_most_recent.loc[second_most_recent["Team"] == team]["Rank"].iloc[-1]
    new_diff = second_most_recent_rank - most_recent_rank
    if new_diff > add_diff:
        most_improved = team
        add_diff = new_diff

sub_diff = 0
for i in range(len(sorted_teams_list)):
    team = sorted_teams_list[i]
    most_recent_rank = most_recent.loc[most_recent["Team"] == team]["Rank"].iloc[-1]
    second_most_recent_rank = second_most_recent.loc[second_most_recent["Team"] == team]["Rank"].iloc[-1]
    new_diff = second_most_recent_rank - most_recent_rank
    if new_diff < sub_diff:
        least_improved = team
        sub_diff = new_diff
        
grouped_df = df.groupby("Team").mean()
dominant_team = grouped_df["Rank"].idxmin()
least_dominant_team = grouped_df["Rank"].idxmax()

#---- CURRENT BEST AND WORST ---- #
st.subheader("Current Best and Worst Teams")
col1, col2 = st.columns(2)
col1.metric("Current Best Team", best_current_team["Team"].iloc[-1], border=True)
col2.metric("Teams Average ELO", best_current_team["Average ELO"].iloc[-1], border=True)

col1, col2 = st.columns(2)
col1.metric("Current Worst Team", worst_current_team['Team'].iloc[-1], border=True)
col2.metric("Teams Average ELO", worst_current_team["Average ELO"].iloc[-1], border=True)

st.divider()

#---- MOST AND LEAST IMPROVED ----#
st.subheader("Most Improved and Largest Fall Off")
col1, col2 = st.columns(2)
col1.metric(f"Most Improved Team from {highest_year}", most_improved, border=True)
col2.metric("Improved by", f"{add_diff} Places", border=True)

col1, col2 = st.columns(2)
col1.metric(f"Biggest Fall from {highest_year}", least_improved, border=True)
col2.metric("Fell by", f"{sub_diff} Places", border=True)
st.divider()

#----HISTORICAL BEST AND WORST ----#
st.subheader("Historically Most and Least Dominant")
col1, col2 = st.columns(2)
col1.metric("Most Dominant Team", dominant_team, border=True)
col2.metric("Average Historical Ranking", np.round(grouped_df.loc[dominant_team, "Rank"], 2), border=True)

col1, col2 = st.columns(2)
col1.metric("Least Dominant Team", least_dominant_team, border=True)
col2.metric("Average Historical Ranking", np.round(grouped_df.loc[least_dominant_team, "Rank"], 2), border=True)   
st.divider()



