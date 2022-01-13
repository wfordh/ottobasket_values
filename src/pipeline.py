import pandas as pd
import streamlit as st

# all of the relative imports here
import drip
import darko

## not ideal, but will figure it out later
from transform import (
    get_name_map,
    combine_darko_drip_df,
    find_surplus_positions,
    get_draftable_players,
)
from calc_stats import (
    calc_per_game_projections,
    calc_fantasy_pts,
    calc_categories_value,
    calc_player_values,
)

# code for the pipeline here
@st.cache
def ottobasket_values_pipeline(save_df=False):
    drip_df = drip.get_current_drip()
    drip_df = drip.transform_drip(drip_df)

    darko_df = darko.get_current_darko()
    darko_df = darko.transform_darko(darko_df)

    name_map = get_name_map()

    stats_df = combine_darko_drip_df(darko_df, drip_df, name_map)
    stats_df = stats_df.loc[stats_df.nba_player_id.notna()].copy()

    # full strength
    full_strength_df = calc_per_game_projections(stats_df, is_full_strength=True)
    ## simple points
    full_strength_df["simple_points"] = calc_fantasy_pts(
        full_strength_df, is_simple_scoring=True
    )
    full_strength_df["simple_points_position"] = find_surplus_positions(
        full_strength_df, scoring_type="simple_points"
    )
    simple_fs_draftable = get_draftable_players(
        full_strength_df, scoring_type="simple_points"
    )
    full_strength_df["simple_points_value"] = calc_player_values(
        full_strength_df,
        scoring_type="simple_points",
        draftable_players=simple_fs_draftable,
    )
    ## trad points
    full_strength_df["trad_points"] = calc_fantasy_pts(
        full_strength_df, is_simple_scoring=False
    )
    full_strength_df["trad_points_position"] = find_surplus_positions(
        full_strength_df, scoring_type="trad_points"
    )
    trad_fs_draftable = get_draftable_players(
        full_strength_df, scoring_type="trad_points"
    )
    full_strength_df["trad_points_value"] = calc_player_values(
        full_strength_df,
        scoring_type="trad_points",
        draftable_players=trad_fs_draftable,
    )
    ## roto
    full_strength_df["categories"] = calc_categories_value(full_strength_df)
    full_strength_df["categories_position"] = find_surplus_positions(
        full_strength_df, scoring_type="categories"
    )
    cats_fs_draftable = get_draftable_players(
        full_strength_df, scoring_type="categories"
    )
    full_strength_df["categories_value"] = calc_player_values(
        full_strength_df, scoring_type="categories", draftable_players=cats_fs_draftable
    )

    # current
    current_minutes_df = calc_per_game_projections(stats_df, is_full_strength=False)
    ## simple points
    current_minutes_df["simple_points"] = calc_fantasy_pts(
        current_minutes_df, is_simple_scoring=True
    )
    current_minutes_df["simple_points_position"] = find_surplus_positions(
        current_minutes_df, scoring_type="simple_points"
    )
    simple_fs_draftable = get_draftable_players(
        current_minutes_df, scoring_type="simple_points"
    )
    current_minutes_df["simple_points_value"] = calc_player_values(
        current_minutes_df,
        scoring_type="simple_points",
        draftable_players=simple_fs_draftable,
    )
    ## trad points
    current_minutes_df["trad_points"] = calc_fantasy_pts(
        current_minutes_df, is_simple_scoring=False
    )
    current_minutes_df["trad_points_position"] = find_surplus_positions(
        current_minutes_df, scoring_type="trad_points"
    )
    trad_fs_draftable = get_draftable_players(
        current_minutes_df, scoring_type="trad_points"
    )
    current_minutes_df["trad_points_value"] = calc_player_values(
        current_minutes_df,
        scoring_type="trad_points",
        draftable_players=trad_fs_draftable,
    )
    ## roto
    current_minutes_df["categories"] = calc_categories_value(current_minutes_df)
    current_minutes_df["categories_position"] = find_surplus_positions(
        current_minutes_df, scoring_type="categories"
    )
    cats_fs_draftable = get_draftable_players(
        current_minutes_df, scoring_type="categories"
    )
    current_minutes_df["categories_value"] = calc_player_values(
        current_minutes_df,
        scoring_type="categories",
        draftable_players=cats_fs_draftable,
    )

    join_cols = [
        "player",
        "nba_player_id",
        "tm_id",
        "ottoneu_position",
        "minutes",
        "fs_min",
    ]
    all_values_df = current_minutes_df.merge(
        full_strength_df,
        how="inner",
        on=[
            "player",
            "nba_player_id",
            "tm_id",
            "ottoneu_position",
            "minutes",
            "fs_min",
        ],
        suffixes=["_current", "_fs"],
    )
    all_values_df = all_values_df[
        join_cols + [col for col in all_values_df.columns if "value" in col]
    ]

    if save_df:
        all_values_df.to_csv("./data/all_values_df.csv", index=False)
    else:
        return all_values_df.drop(['nba_player_id', 'tm_id'], axis=1)


def main():
    ottobasket_values_pipeline(True)


if __name__ == "__main__":
    main()
