import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from leagues import (get_league_rosters, get_league_salary_data,
                     get_league_scoring)
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
player_input = st.sidebar.text_input("Player name", placeholder="Stephen Curry").lower()
if player_input:
    values_df = values_df.loc[values_df.player.str.lower().str.contains(player_input)]
position_input = st.sidebar.multiselect(
    "Positon", options=values_df.ottoneu_position.unique()
)
if position_input:
    values_df = values_df.loc[values_df.ottoneu_position.isin(position_input)]
st.sidebar.write("IN DEVELOPMENT! Right now you can only use the filters above this or below, not both")
league_input = st.sidebar.text_input("League ID", placeholder="1")
if league_input:
    league_salaries = get_league_rosters(league_input)
    league_values_df = league_salaries.merge(
        values_df, on="ottoneu_player_id", how="left"
    )
    league_values_df.player.fillna(
        league_values_df.player_name, inplace=True
    )  # swap player_name for ottoneu_name??
    league_values_df.ottoneu_position.fillna(league_values_df.position, inplace=True)
    # fill the rest of columns NA's with 0
    league_values_df.fillna(0, inplace=True)
    league_scoring = get_league_scoring(league_input)
    if league_scoring == "categories":
        scoring_col = f"{league_scoring}_value"
    elif league_scoring == "simple_points":
        scoring_col = f"{league_scoring}_value"
    else:
        scoring_col = "trad_points_value"
    league_values_df["current_surplus"] = (
        league_values_df[f"{scoring_col}_current"] - league_values_df.salary
    )
    league_values_df["fs_surplus"] = (
        league_values_df[f"{scoring_col}_fs"] - league_values_df.salary
    )
    team_or_league_input = st.sidebar.radio(
        "All league or group by team", ["League", "Teams"], 0
    )
    if team_or_league_input == "Teams":
        display_df = league_values_df.groupby("team_name")[
            [
                "salary",
                f"{scoring_col}_current",
                f"{scoring_col}_fs",
                "current_surplus",
                "fs_surplus",
            ]
        ].sum()
        st.dataframe(display_df)
    else:
        display_df = league_values_df[
            [
                "player",
                "team_name",
                "ottoneu_position",
                "salary",
                "minutes",
                "fs_min",
                f"{scoring_col}_current",
                f"{scoring_col}_fs",
                "current_surplus",
                "fs_surplus",
            ]
        ]
        print(display_df.head())
        st.dataframe(display_df)
else:
    display_df = values_df.drop(
        ["nba_player_id", "ottoneu_player_id", "tm_id"], axis=1
    ).copy()
    st.dataframe(display_df)  # .style.format(format_cols))
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
