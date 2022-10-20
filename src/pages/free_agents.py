# add this https://ottoneu.fangraphs.com/basketball/average_values

import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from leagues import get_average_values, get_league_rosters, get_league_scoring
from pipeline import ottobasket_values_pipeline
from transform import get_scoring_minutes_combo, prep_stats_df


def ottoneu_streamlit_footer():
    # get a CachedStFunctionWarning when using this in a utils.py file and
    # with every page
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
        "league_free_agents.csv",
        "text/csv",
        key="download-csv",
    )


@st.cache
def convert_df(df):
    # Index is set to either player or team at all times
    return df.to_csv(index=True).encode("utf-8")


stats_df = prep_stats_df()
ros_df = get_scoring_minutes_combo("rest_of_season", stats_df)
format_cols = {
    col: "{:.1f}" for col in ros_df.columns if col not in ["player", "ottoneu_position"]
}


league_input = st.sidebar.text_input("League ID", placeholder="1")
if league_input:
    try:
        league_salaries = get_league_rosters(league_input)
    except pd.errors.ParserError:
        st.error("Invalid league ID. Try again!")

    league_values_df = ros_df.merge(league_salaries, on="ottoneu_player_id", how="left")
    league_values_df = league_values_df.loc[league_values_df.salary.isna()].copy()
    league_values_df.player.fillna(league_values_df.player_name, inplace=True)
    league_values_df.ottoneu_position.fillna(league_values_df.position, inplace=True)
    # fill the rest of columns NA's with 0
    league_values_df.fillna(0, inplace=True)
    league_scoring = get_league_scoring(league_input)
    if league_scoring == "categories":
        scoring_col = f"{league_scoring}_value"
    elif league_scoring == "simple_points":
        scoring_col = f"{league_scoring}_value"
    else:
        # Ottoneu has it as "traditional_points", need to shorten it to be consistent
        league_scoring = "trad_points"
        scoring_col = "trad_points_value"
    average_values_df = get_average_values()
    league_values_df = league_values_df.merge(
        average_values_df, how="left", on=["ottoneu_player_id", "ottoneu_position"]
    )
    display_df = league_values_df[
        [
            "player",
            "ottoneu_position",
            "total_ros_minutes",
            f"{league_scoring}",
            f"{league_scoring}_value",
            "ottoneu av",
            "ottoneu roster%",
        ]
    ].rename(columns={f"{league_scoring}": f"{league_scoring}_proj_production"})
    display_df.sort_values(
        by=[f"{league_scoring}_value", f"{league_scoring}_proj_production"],
        ascending=False,
        inplace=True,
    )
    display_df.set_index(
        "player", inplace=True
    )  # .reset_index(drop=True, inplace=True)
    format_cols.update({f"{league_scoring}_proj_production": "{:.2f}"})

    st.dataframe(display_df.style.format(format_cols))
    st.text("Free agents are sorted by projected rest of season value and production.")
else:
    st.markdown("Please input a league ID!")
    display_df = pd.DataFrame()


ottoneu_streamlit_footer()
