# add this https://ottoneu.fangraphs.com/basketball/average_values


import pandas as pd
import streamlit as st

from leagues import get_average_values, get_league_rosters, get_league_scoring
from pipeline import ottobasket_values_pipeline
from transform import get_scoring_minutes_combo, prep_stats_df
from utils import convert_df, ottoneu_streamlit_footer

st.markdown("# Free Agents")


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
    display_df.reset_index(drop=True, inplace=True)
    format_cols.update({f"{league_scoring}_proj_production": "{:.2f}"})

    st.dataframe(display_df.style.format(format_cols))
    st.text("Free agents are sorted by projected rest of season value and production.")
else:
    st.markdown("Please input a league ID!")
    display_df = pd.DataFrame()


ottoneu_streamlit_footer("league_free_agents")
