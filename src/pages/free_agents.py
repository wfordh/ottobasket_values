# put links to players in the table - will have both league and player id
# need projected production and value since most will presumably be $0
import pandas as pd
import streamlit as st

from leagues import get_league_rosters, get_league_scoring
from pipeline import ottobasket_values_pipeline
from transform import get_scoring_minutes_combo, prep_stats_df

# values_df = ottobasket_values_pipeline(False)
stats_df = prep_stats_df()
ros_df = get_scoring_minutes_combo("rest_of_season", stats_df)

league_input = st.sidebar.text_input("League ID", placeholder="1")
if league_input:
    try:
        league_salaries = get_league_rosters(league_input)
    except pd.errors.ParserError:
        st.error("Invalid league ID. Try again!")

    league_values_df = ros_df.merge(league_salaries, on="ottoneu_player_id", how="left")
    league_values_df = league_values_df.loc[league_values_df.salary.isna()].copy()
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

    st.dataframe(league_values_df)
else:
    st.markdown("Please input a league ID!")
    display_df = pd.DataFrame()
