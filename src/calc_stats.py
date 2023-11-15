from typing import Dict, List, Union

import pandas as pd

# use enums here?
simple_scoring_values = {
    "points": 1,
    "rebounds": 1,
    "assists": 1,
    "steals": 1,
    "blocks": 1,
    "turnovers": -1,
    "fga": 0,
    "fgm": 0,
    "fta": 0,
    "ftm": 0,
}

trad_scoring_values = {
    "points": 1,
    "rebounds": 1,
    "assists": 2,
    "steals": 4,
    "blocks": 4,
    "turnovers": -2,
    "fga": -1,
    "fgm": 2,
    "fta": -1,
    "ftm": 1,
}


def calc_per_game_projections(
    df: pd.DataFrame, projection_type: str = "full_strength"
) -> pd.DataFrame:
    """
    Translates the provided dataframe from a per 100 basis to per game basis,
    calculating it using the relevant number of possessions for each projection
    type.

    Incorrectly titled for RoS and YTD stats since it's calculating the totals
    for that time period and not just per game.
    """
    stats_df = df.copy()
    if projection_type not in (
        "full_strength",
        "current",
        "rest_of_season",
        "year_to_date",
    ):
        raise ValueError(f"{projection_type} is not a valid projection type!")
    if projection_type == "full_strength":
        possessions = stats_df.pace * stats_df.fs_min / 48
    elif projection_type == "current":
        # should this be re-labeled?
        possessions = stats_df.pace * stats_df.minutes / 48
    elif projection_type == "rest_of_season":
        # pace = poss / game
        # total_ros_minutes = minutes
        # 48 = 1 game / 48 minutes
        # poss / game * minutes * game / minutes ==> possessions
        # 100 since the stats are on a per 100 possession basis
        possessions = (stats_df.pace / 100) * (stats_df.total_ros_minutes / 48)
    else:
        # year to date
        possessions = stats_df.pace * stats_df.minutes_ytd / stats_df.games_played

    if projection_type == "year_to_date":
        # super hacky but w/e
        # stats are already coming in as totals so don't need to do anything
        stats_df["pts_game"] = stats_df.points
        stats_df["reb_game"] = stats_df.rebounds
        stats_df["ast_game"] = stats_df.assists
        stats_df["stl_game"] = stats_df.steals
        stats_df["blk_game"] = stats_df.blocks
        stats_df["tov_game"] = stats_df.turnovers
        stats_df["fga_game"] = stats_df.field_goal_attempts
        stats_df["fgm_game"] = stats_df.field_goals_made
        stats_df["fta_game"] = stats_df.free_throw_attempts
        stats_df["ftm_game"] = stats_df.free_throws_made
        stats_df["fg3a_game"] = stats_df.three_point_attempts
        stats_df["fg3m_game"] = stats_df.three_points_made
    elif projection_type == "rest_of_season":
        stats_df["pts_game"] = stats_df.points_100 * possessions
        stats_df["reb_game"] = stats_df.rebounds_100 * possessions
        stats_df["ast_game"] = stats_df.assists_100 * possessions
        stats_df["stl_game"] = stats_df.steals_100 * possessions
        stats_df["blk_game"] = stats_df.blocks_100 * possessions
        stats_df["tov_game"] = stats_df.tov_100 * possessions
        stats_df["fga_game"] = stats_df.fga_100 * possessions
        stats_df["fgm_game"] = stats_df.fgm_100 * possessions
        stats_df["fta_game"] = stats_df.fta_100 * possessions
        stats_df["ftm_game"] = stats_df.ftm_100 * possessions
        stats_df["fg3a_game"] = stats_df.fg3a_100 * possessions
        stats_df["fg3m_game"] = stats_df.fg3m_100 * possessions
    else:
        # don't think I need "possessions_played" anymore
        stats_df["possessions_played"] = stats_df.pace * stats_df.minutes / 48
        stats_df["pts_game"] = stats_df.points_100 * possessions / 100
        stats_df["reb_game"] = stats_df.rebounds_100 * possessions / 100
        stats_df["ast_game"] = stats_df.assists_100 * possessions / 100
        stats_df["stl_game"] = stats_df.steals_100 * possessions / 100
        stats_df["blk_game"] = stats_df.blocks_100 * possessions / 100
        stats_df["tov_game"] = stats_df.tov_100 * possessions / 100
        stats_df["fga_game"] = stats_df.fga_100 * possessions / 100
        stats_df["fgm_game"] = stats_df.fgm_100 * possessions / 100
        stats_df["fta_game"] = stats_df.fta_100 * possessions / 100
        stats_df["ftm_game"] = stats_df.ftm_100 * possessions / 100
        stats_df["fg3a_game"] = stats_df.fg3a_100 * possessions / 100
        stats_df["fg3m_game"] = stats_df.fg3m_100 * possessions / 100

    keep_cols = [
        "player",
        "nba_player_id",
        "ottoneu_player_id",
        "hashtag_id",
        "tm_id",
        "ottoneu_position",
        "minutes",
        # "fs_min",
        "games_forecast",
        "minutes_forecast",
        "total_ros_minutes",
        "minutes_ytd",
        "pts_game",
        "reb_game",
        "ast_game",
        "stl_game",
        "blk_game",
        "tov_game",
        "fga_game",
        "fgm_game",
        "fg3a_game",
        "fg3m_game",
        "fg_pct",
        "fg3_pct",
        "fta_game",
        "ftm_game",
    ]
    return stats_df[keep_cols]


def calc_fantasy_pts(
    stats_df: pd.DataFrame, is_simple_scoring: bool = True
) -> pd.Series:
    """
    Calculates the fantasy points for per game statistics given the scoring type.
    """
    scoring_dict = simple_scoring_values if is_simple_scoring else trad_scoring_values

    # fantasy_df = stats_df.copy()
    return (
        stats_df["pts_game"] * scoring_dict["points"]
        + stats_df["reb_game"] * scoring_dict["rebounds"]
        + stats_df["ast_game"] * scoring_dict["assists"]
        + stats_df["stl_game"] * scoring_dict["steals"]
        + stats_df["blk_game"] * scoring_dict["blocks"]
        + stats_df["tov_game"] * scoring_dict["turnovers"]
        + stats_df["fga_game"] * scoring_dict["fga"]
        + stats_df["fgm_game"] * scoring_dict["fgm"]
        + stats_df["fta_game"] * scoring_dict["fta"]
        + stats_df["ftm_game"] * scoring_dict["ftm"]
    )


def calc_categories_value(
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
    league_stdevs = df[roto_cols].std()
    value_df = df[["player", "nba_player_id"]].copy()
    value_df["aFGM"] = df["fgm_game"] - league_averages["fg_pct"] * df["fga_game"]
    value_df["aFG3M"] = df["fg3m_game"] - league_averages["fg3_pct"] * df["fg3a_game"]
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
    value_df["vFGM"] = value_df.aFGM / value_df.aFGM.std()
    value_df["vFG3M"] = value_df.aFG3M / value_df.aFG3M.std()
    value_df["total_value"] = value_df.drop(
        ["player", "nba_player_id", "aFGM", "aFG3M"], axis=1
    ).sum(axis=1)

    return value_df.total_value if is_rollup else value_df


def get_replacement_values(
    fantasy_df: pd.DataFrame, scoring_type: str, draftable_players: List
) -> Dict:
    """
    Gets the replacement level value by finding the maximum value for a player
    outside of the 'draftable players' list.
    """
    return (
        fantasy_df.loc[~fantasy_df.nba_player_id.isin(draftable_players)]
        .groupby(f"{scoring_type}_position")[scoring_type]
        .max()
        .to_dict()
    )


def calc_player_values(
    fantasy_df: pd.DataFrame, scoring_type: str, draftable_players: List
) -> pd.Series:
    """
    Calculates the player values by getting the replacement values, defining if
    and how far a player is above them, and then converting those values to dollars
    based on the surplus factor as derived from the league's total cap space and
    remaining dollars after assigning $1 to each roster spot in the league.
    """

    replacement_values = get_replacement_values(
        fantasy_df, scoring_type, draftable_players
    )

    fantasy_df[f"points_above_repl"] = fantasy_df.apply(
        lambda row: row[scoring_type] - replacement_values["C"]
        if row[f"{scoring_type}_position"] == "C"
        else (
            row[scoring_type] - replacement_values["F"]
            if row[f"{scoring_type}_position"] == "F"
            else row[scoring_type] - replacement_values["G"]
        ),
        axis="columns",
    )

    total_league_value = fantasy_df.loc[
        fantasy_df.points_above_repl > 0
    ].points_above_repl.sum()
    surplus_factor = (
        4800 - len(fantasy_df.loc[fantasy_df.points_above_repl > 0])
    ) / total_league_value
    return fantasy_df.apply(
        lambda row: round(row.points_above_repl * surplus_factor + 1, 1)
        if row.points_above_repl > 0
        else 0,
        axis=1,
    )
