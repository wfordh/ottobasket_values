import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from calc_stats import calc_categories_value  # type: ignore
from calc_stats import calc_per_game_projections, calc_player_values
from leagues import get_league_rosters  # type: ignore
from transform import (find_surplus_positions,  # type: ignore
                       get_draftable_players, prep_stats_df)


# from utils import convert_df, ottoneu_streamlit_footer
def convert_df(df):
    # Index is set to either player or team at all times
    return df.to_csv(index=True).encode("utf-8")


st.markdown("# Categories Value Breakdown")


stats_df = prep_stats_df()

league_input = st.sidebar.number_input("League ID", placeholder="1", min_value=1)
if league_input:
    # make this an input?
    projection_type = "rest_of_season"
    df = calc_per_game_projections(stats_df.copy(), projection_type=projection_type)
    cats_df = calc_categories_value(df, is_rollup=False)
    league_salaries = get_league_rosters(league_input)
    league_values_df = league_salaries.merge(
        cats_df, on="ottoneu_player_id", how="left"
    )

    league_values_df.fillna(
        {
            "player": league_values_df.player_name,
            "ottoneu_position": league_values_df.position,
        },
        inplace=True,
    )  # swap player_name for ottoneu_name??
    league_values_df.fillna(0, inplace=True)
    format_cols = {
        col: "{:.1f}"
        for col in league_values_df.columns
        if league_values_df[col].dtype in [float, int]
    }
    team_or_league_input = st.sidebar.radio(
        "All league or group by team", ["League", "Teams"], 0
    )
    if team_or_league_input == "Teams":
        display_df = league_values_df.groupby(["team_name"])[
            [
                "pts_sgp",
                "reb_sgp",
                "ast_sgp",
                "blk_sgp",
                "stl_sgp",
                "tov_sgp",
                "ftm_sgp",
                "fg%_sgp",
                "3pt%_sgp",
            ]
        ].sum()
        st.dataframe(display_df.style.format(format_cols))
    else:
        display_df = league_values_df[
            [
                "team_name",
                "player",
                "ottoneu_position",
                "total_ros_minutes",
                "pts_sgp",
                "reb_sgp",
                "ast_sgp",
                "blk_sgp",
                "stl_sgp",
                "tov_sgp",
                "ftm_sgp",
                "fg%_sgp",
                "3pt%_sgp",
                "total_value",
            ]
        ].set_index("player")
        st.dataframe(display_df.style.format(format_cols))
else:
    st.markdown("Please input a league ID!")
    display_df = pd.DataFrame()

# ottoneu_streamlit_footer("categories_breakdown", display_df)
now = datetime.datetime.now(tz=ZoneInfo("US/Pacific"))
st.markdown(
    "About page / README can be found [here](https://github.com/wfordh/ottobasket_values/blob/main/README.md)"
)
st.text("ros = rest of season. ytd = year to date.")
st.text(f"Last updated: {now.strftime('%Y-%m-%d %I:%M %p (Pacific)')}")
cats_breakdown_csv = convert_df(display_df)
st.download_button(
    "Press to download",
    cats_breakdown_csv,
    "categories_breakdown.csv",
    "text/csv",
    key="download-csv",
)
