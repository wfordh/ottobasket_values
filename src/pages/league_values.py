import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from leagues import get_league_rosters, get_league_scoring  # type: ignore
from pipeline import ottobasket_values_pipeline  # type: ignore
from transform import get_roster_depth  # type: ignore

st.markdown("# League Values")
st.sidebar.markdown("# League Values")


def convert_df(df):
    # Index is set to either player or team at all times
    return df.to_csv(index=True).encode("utf-8")


def find_format_cols(df):
    return {
        col: "{:.0f}"
        for col in df.columns
        if col not in ["player", "ottoneu_position", "team_name"]
    }


sheet_id = "1GgwZpflcyoRYMP0yL2hrbNwndJjVFm34x3jXnUooSfA"
values_df = pd.read_csv(
    f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"
)


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
    league_values_df["ros_surplus"] = (
        league_values_df[f"{scoring_col}_ros"] - league_values_df.salary
    )
    league_values_df["ytd_surplus"] = (
        league_values_df[f"{scoring_col}_ytd"] - league_values_df.salary
    )
    team_or_league_input = st.sidebar.radio(
        "All league or group by team", ["League", "Teams"], 0
    )
    # why are surplus columns not getting formatted???
    # not working because the columns for formatting are getting chosen
    # before the surplus columns are created...need a function?
    if team_or_league_input == "Teams":
        league_values_df["in_rotation"] = None
        league_values_df["prospects"] = None
        rotation_df = get_roster_depth(league_values_df, league_scoring, scoring_col)
        # currently rotation / depth / other only for ytd
        display_df = league_values_df.groupby("team_name")[
            [
                "salary",
                f"{scoring_col}_current",
                f"{scoring_col}_ros",
                f"{scoring_col}_ytd",
                "current_surplus",
                "ros_surplus",
                "ytd_surplus",
            ]
        ].sum()
        display_df = display_df.merge(
            rotation_df, how="inner", left_index=True, right_on="team_name"
        ).set_index("team_name")
        format_cols = find_format_cols(display_df)
        st.dataframe(display_df.style.format(format_cols))
        body_string = """
        The 'rotation', 'depth', and 'other' columns are estimations of where
        a team is spending their money in their roster construction. I designate the
        top 3 guards, top 2 forwards, top center, G / F, and F / C, and
        the next 4 best players by total value as 'rotation' players, the bottom 8
        players as 'other', and the middle as depth. This is subject to change during
        the season as injured players may go in and out of the rotation. Other players
        are typically pre-NBA prospects and injured players.

        The rotation level columns are currently only calculated using year-to-date
        statistics. I hope to add rest of season statistics to it at some point.
        """
        st.markdown(body_string)
    else:
        display_df = league_values_df[
            [
                "player",
                "team_name",
                "ottoneu_position",
                "salary",
                "minutes",
                "total_ros_minutes",
                "minutes_ytd",
                f"{scoring_col}_current",
                f"{scoring_col}_ros",
                f"{scoring_col}_ytd",
                "current_surplus",
                "ros_surplus",
                "ytd_surplus",
            ]
        ].set_index("player")
        format_cols = find_format_cols(display_df)
        st.dataframe(display_df.style.format(format_cols))
else:
    st.markdown("Please input a league ID!")
    display_df = pd.DataFrame()

now = datetime.datetime.now(tz=ZoneInfo("US/Pacific"))
st.markdown(
    "About page / README can be found [here](https://github.com/wfordh/ottobasket_values/blob/main/README.md)"
)
st.text("ros = rest of season. ytd = year to date.")
st.text(f"Last updated: {now.strftime('%Y-%m-%d %I:%M %p (Pacific)')}")
values_csv = convert_df(display_df)
st.download_button(
    "Press to download",
    values_csv,
    "league_values.csv",
    "text/csv",
    key="download-csv",
)
