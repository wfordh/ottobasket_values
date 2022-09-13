import pandas as pd
import streamlit as st

from leagues import get_league_rosters, get_league_scoring
from pipeline import ottobasket_values_pipeline
from utils import convert_df, ottoneu_streamlit_footer

st.markdown("# League Values")
st.sidebar.markdown("# League Values")


values_df = ottobasket_values_pipeline(False)
format_cols = {
    col: "{:.1f}"
    for col in values_df.columns
    if col not in ["player", "ottoneu_position"]
}

league_input = st.sidebar.text_input("League ID", placeholder="1")
if league_input:
    try:
        league_salaries = get_league_rosters(league_input)
    except pd.errors.ParserError:
        st.error("Invalid league ID. Try again!")

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
    league_values_df["ros_surplus"] = (
        league_values_df[f"{scoring_col}_ros"] - league_values_df.salary
    )
    league_values_df["ytd_surplus"] = (
        league_values_df[f"{scoring_col}_ytd"] - league_values_df.salary
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
                f"{scoring_col}_ros",
                f"{scoring_col}_ytd",
                "current_surplus",
                "fs_surplus",
                "ros_surplus",
                "ytd_surplus",
            ]
        ].sum()
        st.dataframe(display_df.style.format(format_cols))
    else:
        display_df = league_values_df[
            [
                "player",
                "team_name",
                "ottoneu_position",
                "salary",
                "minutes",
                "fs_min",
                "total_ros_minutes",
                "minutes_ytd",
                f"{scoring_col}_current",
                f"{scoring_col}_fs",
                f"{scoring_col}_ros",
                f"{scoring_col}_ytd",
                "current_surplus",
                "fs_surplus",
                "ros_surplus",
                "ytd_surplus",
            ]
        ].set_index("player")
        st.dataframe(display_df.style.format(format_cols))
else:
    st.markdown("Please input a league ID!")
    display_df = pd.DataFrame()

ottoneu_streamlit_footer("league_values")
