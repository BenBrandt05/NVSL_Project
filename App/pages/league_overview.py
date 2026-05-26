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
    page_title="NVSL ELO Dashboard - League Overview",
    layout="centered"
)

st.markdown("""
    <style>
        h1, h2, h3 { text-align: center; }
    </style>
""", unsafe_allow_html=True)

st.title("League Overview")
              
data_directory = Path(__file__).parent.parent.parent / 'Data'

df = pd.read_csv(data_directory / 'elo_all_years.csv')

#==========================================================================
# PAGE NAVIGATION
#==========================================================================
if st.button("Go To Home Page", use_container_width=True):
    st.switch_page("Home_page.py")
if st.button("Go To All Time Team Records Page", use_container_width=True):
    st.switch_page("all_time_records.py")
if st.button("Go To Team Deep Dive Page", use_container_width=True):
    st.switch_page("team_deep_dive.py")
if st.button("Go To Head to Head", use_container_width=True):
    st.switch_page("head_to_head.py")

st.divider()

#==========================================================================
# SCATTERPLOTS
#==========================================================================
st.subheader("Overview of League ELOs")

years_list = list(df["Year"].drop_duplicates().sort_values())
selected_year = st.selectbox("Select a Year", years_list)

year_df = df[df["Year"] == selected_year]

slope, intercept = np.polyfit(year_df["Average Ranking"], year_df["Average ELO"], 1)
year_df["Trend"] = slope * year_df["Average Ranking"] + intercept
year_df["Position"] = np.where(year_df["Average ELO"] >= year_df["Trend"], "Above", "Below")

scatter_fig_1 = px.scatter(year_df,
                         x="Average Ranking",
                         y="Average ELO",
                         color="Position",
                         color_discrete_map={"Above": "green", "Below": "red"},
                         trendline="ols",
                         trendline_scope="overall",
                         hover_name="Team",
                         hover_data={"Position":False})

for trace in scatter_fig_1.data:
    if trace.mode == "lines":
        trace.update(line=dict(dash="dot"), opacity=0.4, hoverinfo="skip", hovertemplate=None)
        
st.plotly_chart(scatter_fig_1)

st.divider()

st.subheader("Number of Wins VS ELO")

matrix_df = pd.read_csv(data_directory / "all_records_matrix.csv")
matrix_year = matrix_df[["Team", str(selected_year)]]

merged = matrix_year.merge(year_df, on="Team", how="inner").sort_values(by="Average Ranking")
merged[["Wins", "Losses"]] = merged[str(selected_year)].str.split("-", expand=True)
merged["Wins"] = merged["Wins"].astype(int)
merged["Losses"] = merged["Losses"].astype(int)

scatter_fig_2 = px.scatter(merged,
                           x="Wins",
                           y="Average ELO",
                           trendline="ols",
                           hover_name="Team")
for trace in scatter_fig_2.data:
    if trace.mode == "lines":
        trace.update(line=dict(dash="dot"), opacity=0.4, hoverinfo="skip", hovertemplate=None)
st.plotly_chart(scatter_fig_2)

st.divider()

#==========================================================================
# DIVISIONS TABLE
#==========================================================================

st.subheader(f"Correct Divisions for {selected_year}")

cols = ["Average ELO", "Average Ranking"]

if selected_year > 2010:
    previous_df = df[df["Year"] == selected_year - 1].copy()
    previous_df = previous_df.rename(columns={"Average ELO": "Previous ELO"})
    
    merged = merged.merge(previous_df[["Team", "Previous ELO"]], on="Team", how="left")
    merged["YOY ▲▼"] = merged["Average ELO"] - merged["Previous ELO"]
    merged["YOY ▲▼"] = merged["YOY ▲▼"].apply(lambda x: f"+{x:.2f}▲" if pd.notna(x) and x > 0 else f"{x:.2f}▼" if pd.notna(x) and x < 0 else "-")
else:
    merged["YOY ▲▼"] = "-"

merged = merged[["Team", "Wins", "Losses", "Average ELO", "Average Ranking", "YOY ▲▼"]]

for i in range(17):
    division_df = merged.iloc[i*6:(i+1)*6].copy()
    display_df = division_df.copy()
    display_df[cols] = display_df[cols].apply(lambda s: s.map(lambda x: f"{x:.2f}"))
    st.write(f"Division {i+1}")
    st.table(display_df, hide_index=True)
    st.divider()
        


