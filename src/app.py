import streamlit as st
import pandas as pd
import datetime
from zoneinfo import ZoneInfo
from pipeline import ottobasket_values_pipeline
from leagues import get_league_salary_data


@st.cache
def convert_df(df):
    return df.to_csv(index=False).encode("utf-8")


st.title("Ottobasket Player Values")
values_df = ottobasket_values_pipeline(False)
format_cols = {
    col: "{:.1f}"
    for col in values_df.columns
    if col not in ["player", "ottoneu_position"]
}
player_input = st.sidebar.text_input("Player name", placeholder="Stephen Curry").lower()
if player_input:
    values_df = values_df.loc[values_df.player.str.lower().str.contains(player_input)]
position_input = st.sidebar.multiselect(
    "Positon", options=values_df.ottoneu_position.unique()
)
if position_input:
    values_df = values_df.loc[values_df.ottoneu_position.isin(position_input)]
league_input = st.sidebar.text_input("League ID", placeholder="1")
if league_input:
    league_salaries = get_league_salary_data(league_input)
    st.dataframe(league_salaries)
display_df = (
    values_df.drop(["nba_player_id", "ottoneu_player_id", "tm_id"], axis=1)
    .drop_duplicates()
    .copy()
)
st.dataframe(display_df.style.format(format_cols))
now = datetime.datetime.now(tz=ZoneInfo("US/Pacific"))
st.text(f"Last updated: {now.strftime('%Y-%m-%d %I:%M %p (Pacific)')}")
values_csv = convert_df(values_df)
st.download_button(
    "Press to download",
    values_csv,
    "ottobasket_values.csv",
    "text/csv",
    key="download-csv",
)
