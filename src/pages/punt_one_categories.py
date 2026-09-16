import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from calc_stats import calc_categories_value  # type: ignore
from calc_stats import calc_per_game_projections, calc_player_values
from leagues import get_league_rosters  # type: ignore
from transform import find_surplus_positions  # type: ignore
from transform import get_draftable_players, prep_stats_df

st.markdown("# Categories Punt-One Values")

stats_df = prep_stats_df()

# make this an input?
projection_type = "rest_of_season"
scoring_type = "categories"
categories = ["pts", "reb", "ast", "stl", "blk", "ftm", "tov", "fg_pct", "fg3_pct"]

league_input = st.sidebar.number_input("League ID", placeholder="1", min_value=1)
if league_input:
    league_salaries = get_league_rosters(league_input)
    df = calc_per_game_projections(stats_df.copy(), projection_type=projection_type)
    df[scoring_type] = calc_categories_value(df, is_rollup=True)
    df[f"{scoring_type}_position"] = find_surplus_positions(
        df, scoring_type=scoring_type
    )
    draftable_players = get_draftable_players(df, scoring_type=scoring_type)
    df["all_cats_value"] = calc_player_values(
        df, scoring_type=scoring_type, draftable_players=draftable_players
    )

    for cat in categories:
        if "pct" not in cat:
            punted_cat = cat + "_game"
        else:
            punted_cat = cat
        punt_df = df.drop(punted_cat, axis=1)
        punt_df[f"{scoring_type}"] = calc_categories_value(punt_df, is_rollup=True)
        punt_df[f"{scoring_type}_position"] = find_surplus_positions(
            punt_df, scoring_type=scoring_type
        )
        draftable_players = get_draftable_players(punt_df, scoring_type=scoring_type)
        df[f"punt_{cat}_value"] = calc_player_values(
            punt_df, scoring_type=scoring_type, draftable_players=draftable_players
        )
    keep_cols = ["player", "ottoneu_position", "team_name", "salary"] + [
        col for col in df.columns if "value" in col
    ]
    df = df.merge(league_salaries, on="ottoneu_player_id", how="left")
    df.fillna({"team_name": "Free Agent", "salary": 0}, inplace=True)
    format_cols = {col: "{:.1f}" for col in df.columns if df[col].dtype in [float, int]}
    st.dataframe(
        df[keep_cols]
        .set_index("player")
        .sort_values(by="all_cats_value", ascending=False)
    )
