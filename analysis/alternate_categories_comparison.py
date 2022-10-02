import os
import sys
from typing import Union

import pandas as pd

sys.path.append(os.path.abspath("src"))
from calc_stats import calc_per_game_projections, calc_player_values
from transform import (find_surplus_positions, get_draftable_players,
                       prep_stats_df)


def calc_categories_value_alternates(
    df: pd.DataFrame, is_rollup: bool = True
) -> Union[pd.Series, pd.DataFrame]:
    """
    Calculates players' value in each category according the the normalization /
    z-scores methodology. The values are then summed and either the sum or all
    of the values may be returned, depending on the use case.
    """
    roto_cols = [
        "pts_game",
        "reb_game",
        "ast_game",
        "stl_game",
        "blk_game",
        "tov_game",
        "ftm_game",
        "fta_game",
        "fgm_game",
        "fga_game",
        "fg3m_game",
        "fg3a_game",
    ]

    league_averages = df[roto_cols].mean()
    league_averages["fg_pct"] = (
        league_averages["fgm_game"] / league_averages["fga_game"]
    )
    league_averages["fg3_pct"] = (
        league_averages["fg3m_game"] / league_averages["fg3a_game"]
    )
    league_averages["ft_pct"] = (
        league_averages["ftm_game"] / league_averages["fta_game"]
    )
    league_stdevs = df[roto_cols].std()
    value_df = df[["player", "nba_player_id"]].copy()
    value_df["aFGM"] = df["fgm_game"] - league_averages["fg_pct"] * df["fga_game"]
    value_df["aFG3M"] = df["fg3m_game"] - league_averages["fg3_pct"] * df["fg3a_game"]
    value_df["aFTM"] = df["ftm_game"] - league_averages["ft_pct"] * df["fta_game"]
    value_df["vPTS"] = (df["pts_game"] - league_averages["pts_game"]) / league_stdevs[
        "pts_game"
    ]
    value_df["vREB"] = (df["reb_game"] - league_averages["reb_game"]) / league_stdevs[
        "reb_game"
    ]
    value_df["vAST"] = (df["ast_game"] - league_averages["ast_game"]) / league_stdevs[
        "ast_game"
    ]
    value_df["vBLK"] = (df["blk_game"] - league_averages["blk_game"]) / league_stdevs[
        "blk_game"
    ]
    value_df["vSTL"] = (df["stl_game"] - league_averages["stl_game"]) / league_stdevs[
        "stl_game"
    ]
    # swap order for TOV? or actually maybe not?
    value_df["vTOV"] = (
        -1.0
        * (df["tov_game"] - league_averages["tov_game"])
        / league_stdevs["tov_game"]
    )
    value_df["vFTM"] = (df["ftm_game"] - league_averages["ftm_game"]) / league_stdevs[
        "ftm_game"
    ]
    # want vFG3M
    value_df["vFG3M"] = (
        df["fg3m_game"] - league_averages["fg3m_game"]
    ) / league_stdevs["fg3m_game"]
    value_df["vFG_PCT"] = value_df.aFGM / value_df.aFGM.std()
    value_df["vFG3_PCT"] = value_df.aFG3M / value_df.aFG3M.std()
    value_df["vFT_PCT"] = value_df.aFTM / value_df.aFTM.std()
    value_df["total_value_v1"] = value_df.drop(
        ["player", "nba_player_id", "aFGM", "aFG3M", "aFTM", "vFG3M", "vFT_PCT"], axis=1
    ).sum(axis=1)
    value_df["total_value_v2"] = value_df.drop(
        [
            "player",
            "nba_player_id",
            "aFGM",
            "aFG3M",
            "aFTM",
            "vFG3M",
            "vFTM",
            "total_value_v1",
        ],
        axis=1,
    ).sum(axis=1)
    value_df["total_value_v3"] = value_df.drop(
        [
            "player",
            "nba_player_id",
            "aFGM",
            "aFG3M",
            "aFTM",
            "vFG3_PCT",
            "vFTM",
            "total_value_v1",
            "total_value_v2",
        ],
        axis=1,
    ).sum(axis=1)
    value_df["total_value_v4"] = value_df.drop(
        [
            "player",
            "nba_player_id",
            "aFGM",
            "aFG3M",
            "aFTM",
            "vFG3_PCT",
            "vFT_PCT",
            "total_value_v1",
            "total_value_v2",
            "total_value_v3",
        ],
        axis=1,
    ).sum(axis=1)

    return value_df.total_value if is_rollup else value_df


def main():
    stats_df = prep_stats_df()
    projection_type = "year_to_date"
    stats_df.to_csv("data/stats_df_test.csv", index=False)
    df = calc_per_game_projections(stats_df, projection_type)
    df.to_csv("data/year_to_date_test.csv", index=False)
    cats_df = calc_categories_value_alternates(df, is_rollup=False)
    df = df.merge(
        cats_df[
            [
                "nba_player_id",
                "total_value_v1",
                "total_value_v2",
                "total_value_v3",
                "total_value_v4",
            ]
        ],
        how="inner",
        on="nba_player_id",
    )
    df = df.drop_duplicates()
    # still need to convert to values
    for value in [
        "total_value_v1",
        "total_value_v2",
        "total_value_v3",
        "total_value_v4",
    ]:
        cats_copy = df.copy()
        cats_copy.rename(columns={value: "categories"}, inplace=True)
        cats_copy["categories_position"] = find_surplus_positions(
            cats_copy, scoring_type="categories"
        )
        draftable_players = get_draftable_players(cats_copy, scoring_type="categories")
        cats_copy.to_csv(f"data/{value}_test.csv", index=False)
        df[f"{value}_dollars"] = calc_player_values(
            cats_copy, scoring_type="categories", draftable_players=draftable_players
        )

    df.to_csv("./data/alternate_categories_comparison.csv", index=False)


if __name__ == "__main__":
    main()
