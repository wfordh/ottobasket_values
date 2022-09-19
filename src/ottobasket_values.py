import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from pipeline import ottobasket_values_pipeline

st.set_page_config(page_title="Ottobasket Values")
st.sidebar.markdown("Ottobasket Values")


@st.cache
def convert_df(df):
    # Index is set to either player or team at all times
    return df.to_csv(index=True).encode("utf-8")


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

display_df = (
    values_df.drop(["nba_player_id", "ottoneu_player_id", "tm_id"], axis=1)
    .copy()
    .set_index("player")
)
st.dataframe(display_df.style.format(format_cols))
now = datetime.datetime.now(tz=ZoneInfo("US/Pacific"))
st.markdown(
    "About page / README can be found [here](https://github.com/wfordh/ottobasket_values/blob/main/README.md)"
)
st.text("ros = rest of season. fs = full strength. ytd = year to date.")
st.text(f"Last updated: {now.strftime('%Y-%m-%d %I:%M %p (Pacific)')}")
values_csv = convert_df(display_df)
st.download_button(
    "Press to download",
    values_csv,
    "ottobasket_values.csv",
    "text/csv",
    key="download-csv",
)