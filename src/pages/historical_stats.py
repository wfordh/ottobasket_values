import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st


def convert_df(df):
    # Index is set to either player or team at all times
    return df.to_csv(index=True).encode("utf-8")


st.markdown("# Historical Stats")
st.sidebar.markdown("# Historical Stats")

values_df = pd.read_csv("./data/box_stats_revised.csv")

# probably a better way to do this
format_cols = {
    col: "{:.1f}"
    for col in values_df.columns
    if col
    not in [
        "player",
        "team",
        "season",
        "position",
        "simple_points_position",
        "categories_position",
        "trad_points_position",
    ]
}

seasons = st.sidebar.multiselect("Seasons", values_df.season.unique().tolist())
if seasons:
    values_df = values_df.loc[values_df.season.isin(seasons)]
player_input = (
    st.sidebar.text_input("Player name", placeholder="Stephen Curry").lower().strip()
)
if player_input:
    values_df = values_df.loc[values_df.player.str.lower().str.contains(player_input)]

base_columns = ["player", "team", "age", "minutes", "season", "position"]
cats_check = st.sidebar.checkbox("Categories data", value=True)
simple_pts_check = st.sidebar.checkbox("Simple points data", value=True)
trad_pts_check = st.sidebar.checkbox("Trad points data", value=True)
if cats_check:
    base_columns.extend(["category_points", "categories_position", "categories_value"])
if simple_pts_check:
    base_columns.extend(
        ["simple_points", "simple_points_position", "simple_points_value"]
    )
if trad_pts_check:
    base_columns.extend(["trad_points", "trad_points_position", "trad_points_value"])
if not any([cats_check, simple_pts_check, trad_pts_check]):
    st.text("Please select a scoring format!")

display_df = values_df[base_columns].set_index("player").copy()

st.dataframe(display_df.style.format(format_cols))
now = datetime.datetime.now(tz=ZoneInfo("US/Pacific"))
description_string = """
    Historical stats have been taken from NBA.com and go back to the 1996-97 season as a result. The values are calculated using the position designations listed on NBA.com, and so may not match the positions given to players on Ottoneu, though 
    this is only relevant for players who are still active or played in seasons since Ottoneu Basketball started. The historical 
    values do not contain data for the current season.
        
    About page / README can be found [here](https://github.com/wfordh/ottobasket_values/blob/main/README.md).
    """
st.markdown(description_string)
st.text(f"Last updated: Prior to 2023-24 season, so 2022-23 data is not yet included.")
values_csv = convert_df(display_df)
st.download_button(
    "Press to download",
    values_csv,
    "ottobasket_values.csv",
    "text/csv",
    key="download-csv",
)
