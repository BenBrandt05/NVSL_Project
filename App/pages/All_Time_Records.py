#==========================================================================
# LIBRARIES
#==========================================================================
import streamlit as st
import pandas as pd
from pathlib import Path

#==========================================================================
# PAGE/PATH CONFIGURATION
#==========================================================================
st.set_page_config(
    page_title = "NVSL ELO Dashboard - All Time Records",
    layout="centered"
)

st.markdown("""
    <style>
        h1, h2, h3 { text-align: center; }
    </style>
""", unsafe_allow_html=True)

st.title("All-Time Records")

data_directory = Path(__file__).parent.parent.parent / 'Data'

df = pd.read_csv(data_directory / 'elo_all_years.csv')

#==========================================================================
# PAGE NAVIGATION
#==========================================================================
if st.button("Go To Home Page", use_container_width=True):
    st.switch_page("Home_page.py")
if st.button("Go To Team Deep Dive Page", use_container_width=True):
    st.switch_page("team_deep_dive.py")
if st.button("Go To League Overview", use_container_width=True):
    st.switch_page("league_overview.py")
if st.button("Go To Head to Head", use_container_width=True):
    st.switch_page("head_to_head.py")

st.divider()

#==========================================================================
# TABLE
#==========================================================================
recent_idx = df.groupby("Team")["Year"].idxmax()
recent_df = (
    df.loc[recent_idx, ["Team", "Average ELO", "Average Ranking"]]
      .rename(columns={
          "Average ELO": "Current ELO",
          "Average Ranking": "Current Ranking"
      })
)

peak_rank_idx = df.groupby("Team")["Average Ranking"].idxmin()
peak_rank_df = (
    df.loc[peak_rank_idx, ["Team", "Average ELO", "Average Ranking"]]
      .rename(columns={
          "Year": "Peak Year",
          "Average ELO": "Peak ELO",
          "Average Ranking": "Peak Ranking"
      })
)

volatility_df = df.groupby("Team")["Average ELO"].std().reset_index()
volatility_df.columns = ["Team", "StdDev"]
volatility_df["ELO Volatility"] = pd.qcut(
    volatility_df["StdDev"],
    q=3,
    labels=["Low", "Medium", "High"]
)

final_df = recent_df.merge(peak_rank_df, on="Team", how="inner")
final_df = final_df.merge(volatility_df[["Team", "ELO Volatility"]], on="Team", how="left")
cols = ["Current ELO", "Current Ranking", "Peak ELO", "Peak Ranking"]
display_df = final_df.copy()
display_df[cols] = display_df[cols].apply(lambda s: s.map(lambda x: f"{x:.2f}"))
st.dataframe(display_df, hide_index=True, use_container_width=True)

