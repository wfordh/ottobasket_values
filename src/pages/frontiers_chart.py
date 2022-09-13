import altair as alt
import pandas as pd
import streamlit as st

from calc_stats import calc_categories_value, calc_fantasy_pts
from transform import get_scoring_minutes_combo, prep_stats_df
from utils import convert_df, ottoneu_streamlit_footer

st.markdown("# Replacement Level Frontier")

scoring_input = st.sidebar.radio(
    "Scoring Format", ["Simple Points", "Traditional Points", "Categories"], 0
)
scoring_map = {
    "Simple Points": "simple_points",
    "Traditional Points": "trad_points",
    "Categories": "categories",
}
scoring_type = scoring_map[scoring_input]
stats_df = prep_stats_df()
ros_df = get_scoring_minutes_combo("rest_of_season", stats_df)
# get projected minutes, per 100 stats fantasy value, and if they are
# projected to be above replacement value
stats_df.columns = [col.replace("_100", "_game") for col in stats_df.columns]
stats_df.rename(
    columns={
        "points_game": "pts_game",
        "assists_game": "ast_game",
        "rebounds_game": "reb_game",
        "steals_game": "stl_game",
        "blocks_game": "blk_game",
    },
    inplace=True,
)
stats_df["simple_points_per_100"] = calc_fantasy_pts(stats_df, is_simple_scoring=True)
stats_df["trad_points_per_100"] = calc_fantasy_pts(stats_df, is_simple_scoring=False)
stats_df["categories_per_100"] = calc_categories_value(stats_df)
stats_df_cols = [
    "player",
    "nba_player_id",
    "simple_points_per_100",
    "trad_points_per_100",
    "categories_per_100",
]
ros_df_cols = [
    "nba_player_id",
    "total_ros_minutes",
    "simple_points_value",
    "trad_points_value",
    "categories_value",
]
frontier_df = stats_df[stats_df_cols].merge(
    ros_df[ros_df_cols], how="inner", on="nba_player_id"
)
frontier_df["above_repl_simple_points"] = frontier_df.simple_points_value.apply(
    lambda val: 1 if val > 0 else 0
)
frontier_df["above_repl_trad_points"] = frontier_df.trad_points_value.apply(
    lambda val: 1 if val > 0 else 0
)
frontier_df["above_repl_categories"] = frontier_df.categories_value.apply(
    lambda val: 1 if val > 0 else 0
)
chart = (
    alt.Chart(frontier_df)
    .mark_circle()
    .encode(
        x="total_ros_minutes",
        y=f"{scoring_type}_per_100",
        tooltip="player",
        color=f"above_repl_{scoring_type}",
    )
    .interactive()
)
st.altair_chart(chart, use_container_width=True)

st.text(
    """
	This chart plots the players' projected production scaled to per 100 possessions
	against their rest of season minutes projections and is meant to show the "frontier"
	dividing the replacement level from above replacement level players. It could be
	useful to see who may become above replacement level with a minutes boost or who
	could be steady, dependable depth.

	You can zoom and pan on the chart, and if you hover over a point, then the player's
	name will show up.
	"""
)

ottoneu_streamlit_footer("frontier_values")
