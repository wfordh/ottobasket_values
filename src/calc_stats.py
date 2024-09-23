from typing import Dict, List, Union

import numpy as np
import pandas as pd

from utils import get_sgp_rollup

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
    df: pd.DataFrame, projection_type: str = "year_to_date"
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
        "games_played",
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


def calc_z_score_values():
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
    return value_df


def calc_sgp_values(stats_df: pd.DataFrame) -> pd.DataFrame:
    # need to 1) get sgp data
    # 2) balance the weeks (22-csw)*lss + csw*css / 22
    # 3)

    df = stats_df.copy()
    NUM_WEEKS = 22
    sgp_rollup = get_sgp_rollup().tail(2)
    current_week = sgp_rollup.week.values.tolist().pop()
    current_season = sgp_rollup.season.values.tolist().pop()

    sgp_values = (
        (
            (
                (NUM_WEEKS - current_week)
                * sgp_rollup.loc[sgp_rollup.season != current_season].drop(
                    ["season", "week"], axis=1
                )
            ).add(
                current_week
                * sgp_rollup.loc[sgp_rollup.season == current_season].drop(
                    ["season", "week"], axis=1
                ),
                fill_value=0,
            )
        )
        .div(NUM_WEEKS)
        .sum()
    ).to_dict()

    columns = ["pts", "reb", "ast", "stl", "blk", "ftm", "tov", "fg%", "3pt%"]
    for col in columns:
        if col == "fg%":
            df[f"{col}_sgp"] = df.apply(
                lambda row: (
                    (row.fgm_game + sgp_values["avg_team_fgm"])
                    / (row.fga_game + sgp_values["avg_team_fga"])
                    - sgp_values["avg_team_fg_pct"]
                )
                / sgp_values[col],
                axis=1,
            )
        elif col == "3pt%":
            df[f"{col}_sgp"] = df.apply(
                lambda row: (
                    (row.fg3m_game + sgp_values["avg_team_fg3m"])
                    / (row.fg3a_game + sgp_values["avg_team_fg3a"])
                    - sgp_values["avg_team_fg3_pct"]
                )
                / sgp_values[col],
                axis=1,
            )
        else:
            df[f"{col}_sgp"] = df[f"{col}_game"].apply(
                lambda row: row / sgp_values[col]
            )
    df["total_value"] = df[[col for col in df.columns if "sgp" in col]].sum(axis=1)
    return df


def calc_categories_value(
    df: pd.DataFrame, is_rollup: bool = True
) -> Union[pd.Series, pd.DataFrame]:
    """
    Calculates players' value in each category according the the normalization /
    z-scores methodology. The values are then summed and either the sum or all
    of the values may be returned, depending on the use case.
    """
    value_df = calc_sgp_values(df)

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
        lambda row: (
            row[scoring_type] - replacement_values["C"]
            if row[f"{scoring_type}_position"] == "C"
            else (
                row[scoring_type] - replacement_values["F"]
                if row[f"{scoring_type}_position"] == "F"
                else row[scoring_type] - replacement_values["G"]
            )
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
        lambda row: (
            round(row.points_above_repl * surplus_factor + 1, 1)
            if row.points_above_repl > 0
            else 0
        ),
        axis=1,
    )


def calc_sgp_slopes(df: pd.DataFrame) -> dict:
    columns = ["pts", "reb", "ast", "stl", "blk", "ftm", "tov", "fg%", "3pt%"]
    num_teams = 12  # make an arg?
    stat_diffs = dict()
    for col in columns:
        sorted_values = df[col].sort_values(ascending=True).tolist()
        stat_diffs[col] = np.polyfit(range(1, num_teams + 1), sorted_values, deg=1)[0]
        # stat_diffs[col] = (df[col].max() - df[col].min()) / (num_teams - 1)
        if col == "tov":
            stat_diffs[col] = -1.0 * stat_diffs[col]
    return stat_diffs


def ratio_stat_sgp(df: pd.DataFrame):
    #
    num_teams = 12
    num_players = 3 + 2 + 1 + 1 + 1 + 2  # 3 G 2 F 1 C 1 G/F 1 F/C 2 UTIL
    # should this just be the number of above replacement level? no, since repl level is figured out later
    total_players = num_teams * num_players
    # need projected FGA for total_players
    # use avg FG% - but projected or from last year???
    # need to bank the values for: num FGA / player and num FGM / player
    # use that to get proj FG% for average player to serve as baseline to comp
    # get num FGM and FGA for (num_players - 1)

    # let's just use past stuff for now
    total_fga = df.fga.sum()
    total_fgm = df.fgm.sum()
    avg_fg_pct = total_fgm / total_fga

    avg_fga = total_fga / total_players
    avg_fgm = total_fgm / total_players

    team_minus_one_fga = (num_players - 1) * avg_fga
    team_minus_one_fgm = (num_players - 1) * avg_fgm

    total_fg3a = df["3pta"].sum()
    total_fg3m = df["3ptm"].sum()
    avg_fg3_pct = total_fg3m / total_fg3a

    avg_fg3a = total_fg3a / total_players
    avg_fg3m = total_fg3m / total_players

    team_minus_one_fg3a = (num_players - 1) * avg_fg3a
    team_minus_one_fg3m = (num_players - 1) * avg_fg3m
    return (
        (team_minus_one_fga, team_minus_one_fgm, avg_fg_pct),
        (team_minus_one_fg3a, team_minus_one_fg3m, avg_fg3_pct),
    )
