import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from calc_stats import calc_categories_value  # type: ignore
from calc_stats import calc_per_game_projections, calc_player_values
from leagues import get_league_rosters  # type: ignore
from transform import (find_surplus_positions,  # type: ignore
                       get_draftable_players, prep_stats_df)

st.markdown("# Categories Punt-One Values")

stats_df = prep_stats_df()

# make this an input?
projection_type = "rest_of_season"
df = calc_per_game_projections(stats_df.copy(), projection_type=projection_type)
# cats_df = calc_categories_value(df, is_rollup=False)

scoring_type = "categories"
categories = ["pts", "reb", "ast", "stl", "blk", "ftm", "tov", "fg_pct", "fg3_pct"]
for cat in categories:
    if "pct" not in cat:
        punted_cat = cat + "_game"
    punt_df = df.drop(punted_cat, axis=1)
    punt_df[f"{scoring_type}"] = calc_categories_value(punt_df, is_rollup=True)
    punt_df[f"{scoring_type}_position"] = find_surplus_positions(
        punt_df, scoring_type=scoring_type
    )
    draftable_players = get_draftable_players(punt_df, scoring_type=scoring_type)
    df[f"punt_{cat}_value"] = calc_player_values(
        punt_df, scoring_type=scoring_type, draftable_players=draftable_players
    )
keep_cols = ["player", "ottoneu_position"] + [
    col for col in df.columns if "value" in col
]
format_cols = {col: "{:.1f}" for col in df.columns if df[col].dtype in [float, int]}
st.dataframe(df[keep_cols].set_index("player"))
