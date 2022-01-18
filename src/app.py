import streamlit as st
import pandas as pd
import datetime
from zoneinfo import ZoneInfo
from pipeline import ottobasket_values_pipeline


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
# player_input = st.sidebar.selectbox("Player name", sorted(values_df.player.unique()))
# st.write(player_input)
# values_df = values_df.loc[values_df.player == player_input]
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
