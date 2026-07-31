#==========================================================================
# LIBRARIES
#==========================================================================
import streamlit as st
import pandas as pd
from pathlib import Path
import plotly.express as px

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
if st.button("Go To Home Page", width="stretch"):
    st.switch_page("Home_page.py")
if st.button("Go To Team Deep Dive Page", width="stretch"):
    st.switch_page("pages/team_deep_dive.py")
if st.button("Go To League Overview", width="stretch"):
    st.switch_page("pages/league_overview.py")
if st.button("Go To Head to Head", width="stretch"):
    st.switch_page("pages/head_to_head.py")

st.divider()

#==========================================================================
# TABLE
#==========================================================================
st.subheader("Peak ELO vs Current ELO Table")

recent_idx = df.groupby("Team")["Year"].idxmax()
recent_df = (
    df.loc[recent_idx, ["Team", "Average ELO", "Average Ranking"]]
      .rename(columns={
          "Average ELO": "Current ELO",
          "Average Ranking": "Current Ranking"
      })
)

peak_elo_idx = df.groupby("Team")["Average ELO"].idxmax()
peak_elo_df = (
    df.loc[peak_elo_idx, ["Team", "Year", "Average ELO", "Average Ranking"]]
      .rename(columns={
          "Year": "Peak ELO Year",
          "Average ELO": "Peak ELO",
          "Average Ranking": "Peak Ranking"
      })
)

best_rank_idx = df.groupby("Team")["Average Ranking"].idxmin()
best_rank_df = (
    df.loc[best_rank_idx, ["Team", "Year", "Average Ranking"]]
    .rename(columns={
        "Year": "Best Ranking Year",
        "Average Ranking": "Best Ranking"
    })
)

volatility_df = df.groupby("Team")["Average ELO"].std().reset_index()
volatility_df.columns = ["Team", "StdDev"]
volatility_df["ELO Volatility"] = pd.qcut(
    volatility_df["StdDev"],
    q=3,
    labels=["Low", "Medium", "High"]
)

final_df = recent_df.merge(peak_elo_df, on="Team", how="inner")
final_df = final_df.merge(best_rank_df, on="Team", how="inner")
final_df = final_df.merge(volatility_df[["Team", "ELO Volatility"]], on="Team", how="left")
display_df = final_df.copy()
cols_to_format = ["Current ELO", "Current Ranking", "Peak ELO", "Best Ranking"]
display_df[cols_to_format] = display_df[cols_to_format].apply(lambda s: s.map(lambda x: f"{x:.2f}"))

display_df = display_df[["Team", "Current ELO", "Current Ranking", "Peak ELO", "Peak ELO Year", "Best Ranking", "Best Ranking Year", "ELO Volatility"]]

st.dataframe(display_df, hide_index=True, width="stretch")

st.divider()

#==========================================================================
# ELO GRAPHS
#==========================================================================
st.subheader("Peak ELO vs Current ELO Scatterplot")

final_df["Drop ELO From Peak"] = final_df["Peak ELO"] - final_df["Current ELO"]
final_df["Drop Rank From Peak"] = final_df["Best Ranking"] - final_df["Current Ranking"]

scatter_fig1 = px.scatter(
    final_df,
    x="Peak ELO",
    y="Current ELO",
    color="Drop ELO From Peak",
    color_continuous_scale="Reds",
    hover_name="Team",
    hover_data={
        "Current Ranking": True,
        "Peak Ranking": True,
        "Peak ELO": ':.2f',
        "Current ELO": ':.2f',
        "Drop ELO From Peak": ':.2f'
    },
    title="How Close Teams Are to Their ELO Peak"
)

min_val = min(final_df["Current ELO"].min(), final_df["Peak ELO"].min())
max_val = max(final_df["Current ELO"].max(), final_df["Peak ELO"].max())

scatter_fig1.add_shape(
    type="line",
    x0=min_val, y0=min_val,
    x1=max_val, y1=max_val,
    line=dict(color="blue", dash="dash")
)

scatter_fig2 = px.scatter(
    final_df,
    x="Current Ranking",
    y="Best Ranking",
    color="Drop Rank From Peak",
    color_continuous_scale="Reds_r",
    hover_name="Team",
    hover_data={
        "Current Ranking": True,
        "Peak Ranking": True,
        "Peak ELO": ':.2f',
        "Current ELO": ':.2f',
        "Drop Rank From Peak": ':.2f'
    },
    title="How Close Teams Are to Their Rank Peak"
)

min_val = min(final_df["Current Ranking"].min(), final_df["Best Ranking"].min())
max_val = max(final_df["Current Ranking"].max(), final_df["Best Ranking"].max())

scatter_fig2.add_shape(
    type="line",
    x0=min_val, y0=min_val,
    x1=max_val, y1=max_val,
    line=dict(color="blue", dash="dash")
)

st.plotly_chart(scatter_fig1, use_container_width=True)
st.plotly_chart(scatter_fig2, use_container_width=True)
