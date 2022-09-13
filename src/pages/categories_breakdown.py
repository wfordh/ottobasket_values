import pandas as pd
import streamlit as st

from calc_stats import calc_categories_value, calc_per_game_projections
from leagues import get_league_rosters
from transform import prep_stats_df
from utils import convert_df, ottoneu_streamlit_footer

st.markdown("# Categories Value Breakdown")


stats_df = prep_stats_df()

league_input = st.sidebar.text_input("League ID", placeholder="1")
if league_input:
    # make this an input?
    projection_type = "rest_of_season"
    df = calc_per_game_projections(stats_df, projection_type=projection_type)
    cats_df = calc_categories_value(df, is_rollup=False)
    cats_df = cats_df.merge(
        df[
            [
                "ottoneu_player_id",
                "nba_player_id",
                "total_ros_minutes",
                "ottoneu_position",
            ]
        ],
        how="left",
        on="nba_player_id",
    )
    league_salaries = get_league_rosters(26)
    league_values_df = league_salaries.merge(
        cats_df, on="ottoneu_player_id", how="left"
    )
    league_values_df.player.fillna(
        league_values_df.player_name, inplace=True
    )  # swap player_name for ottoneu_name??
    league_values_df.ottoneu_position.fillna(league_values_df.position, inplace=True)
    # fill the rest of columns NA's with 0
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
        display_df = league_values_df.groupby(["team_id", "team_name"])[
            ["vPTS", "vREB", "vAST", "vBLK", "vSTL", "vTOV", "vFTM", "vFGM", "vFG3M"]
        ].sum()
        st.dataframe(display_df.style.format(format_cols))
    else:
        display_df = league_values_df[
            [
                "team_name",
                "player",
                "ottoneu_position",
                "total_ros_minutes",
                "vPTS",
                "vREB",
                "vAST",
                "vBLK",
                "vSTL",
                "vTOV",
                "vFTM",
                "vFGM",
                "vFG3M",
                "total_value",
            ]
        ].set_index("player")
        st.dataframe(display_df.style.format(format_cols))
else:
    st.markdown("Please input a league ID!")
    display_df = pd.DataFrame()

ottoneu_streamlit_footer("categories_breakdown", display_df)
