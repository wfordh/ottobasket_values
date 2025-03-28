import pandas as pd
import streamlit as st

import darko
import drip
# from hashtag_rookies import get_hashtag_rookie_per_game_stats
from calc_stats import (calc_categories_value, calc_fantasy_pts,
                        calc_per_game_projections, calc_player_values)
from utils import (get_hashtag_rookie_projections, get_hashtag_ros_projections,
                   get_name_map, get_ottoneu_leaderboard)


def combine_darko_drip_df(
    darko_df: pd.DataFrame, drip_df: pd.DataFrame, name_mapping: pd.DataFrame
) -> pd.DataFrame:
    """
    Merges the DARKO and DRIP dataframes into one and takes the mean of each
    relevant statistic for each player. Returns the transformed dataframe.
    """
    # everything is per 100 to start, so keep it there and translate to per game later
    # this won't work because need to make sure they're in the right order
    combined_df = darko_df.merge(
        name_mapping, how="outer", left_on="nba_id", right_on="nba_player_id"
    ).merge(drip_df, how="outer", left_on="stats_player_id", right_on="player_id")
    combined_df["points_100"] = combined_df[["pts_100_darko", "PTS_drip"]].mean(axis=1)
    combined_df["rebounds_100"] = combined_df[["reb_100_darko", "reb_drip"]].mean(
        axis=1
    )
    combined_df["assists_100"] = combined_df[["ast_100_darko", "AST_drip"]].mean(axis=1)
    combined_df["steals_100"] = combined_df[["stl_100_darko", "STL_drip"]].mean(axis=1)
    combined_df["blocks_100"] = combined_df[["blk_100_darko", "BLK_drip"]].mean(axis=1)
    combined_df["fga_100"] = combined_df[["fga_100_darko", "fga_drip"]].mean(axis=1)
    combined_df["fgm_100"] = combined_df[["fgm_100_darko", "fgm_drip"]].mean(axis=1)
    combined_df["fg_pct"] = combined_df.fgm_100 / combined_df.fga_100
    combined_df["fg3a_100"] = combined_df[["fg3a_100_darko", "fg3a_drip"]].mean(axis=1)
    combined_df["fg3m_100"] = combined_df[["fg3m_100_darko", "fg3m_drip"]].mean(axis=1)
    combined_df["fg3_pct"] = combined_df.fg3m_100 / combined_df.fg3a_100
    combined_df["fta_100"] = combined_df[["fta_100_darko", "fta_drip"]].mean(axis=1)
    combined_df["ftm_100"] = combined_df[["ftm_100_darko", "ftm_drip"]].mean(axis=1)
    combined_df["ft_pct"] = combined_df.ftm_100 / combined_df.fta_100
    combined_df["tov_100"] = combined_df[["tov_100_darko", "TOV_drip"]].mean(axis=1)

    keep_cols = [
        "name",
        "nba_player_id",
        "ottoneu_player_id",
        "hashtag_id",
        "tm_id",
        "ottoneu_position",
        # "current_min",
        # "fs_min",
        # "minutes_forecast",
        # "games_forecast",
        "minutes",
        # "minutes_ytd",
        "pace",
        "points_100",
        "rebounds_100",
        "assists_100",
        "steals_100",
        "blocks_100",
        "tov_100",
        "fga_100",
        "fgm_100",
        "fg_pct",
        "fg3a_100",
        "fg3m_100",
        "fg3_pct",
        "fta_100",
        "ftm_100",
        "ft_pct",
    ]

    # temporary fix - should update at some point
    return combined_df[keep_cols].rename(columns={"name": "player"})


def find_surplus_positions(fantasy_df: pd.DataFrame, scoring_type: str) -> pd.Series:
    """
    Assigns the position each player will be considered for the value calculations
    according to where they are eligible and their ranked production.
    """
    # Need to figure out the full strength thing here - 1/11/21
    fantasy_df["is_center"] = fantasy_df.ottoneu_position.str.contains("C").map(
        {False: None, True: True}
    )
    fantasy_df["is_forward"] = fantasy_df.ottoneu_position.str.contains("F").map(
        {False: None, True: True}
    )
    fantasy_df["is_guard"] = fantasy_df.ottoneu_position.str.contains("G").map(
        {False: None, True: True}
    )
    fantasy_df["center_rk"] = fantasy_df.groupby("is_center")[scoring_type].rank(
        ascending=False, na_option="bottom"
    )
    fantasy_df["forward_rk"] = fantasy_df.groupby("is_forward")[scoring_type].rank(
        ascending=False, na_option="bottom"
    )
    fantasy_df["guard_rk"] = fantasy_df.groupby("is_guard")[scoring_type].rank(
        ascending=False, na_option="bottom"
    )
    fantasy_df["center_rk"] = fantasy_df.apply(
        lambda row: row.center_rk if row.is_center else None, axis="columns"
    )
    fantasy_df["forward_rk"] = fantasy_df.apply(
        lambda row: row.forward_rk if row.is_forward else None, axis="columns"
    )
    fantasy_df["guard_rk"] = fantasy_df.apply(
        lambda row: row.guard_rk if row.is_guard else None, axis="columns"
    )
    # should I worry about ties? 1/11/21
    return (
        fantasy_df[["center_rk", "forward_rk", "guard_rk"]]
        .idxmin(axis="columns")
        .map({"center_rk": "C", "forward_rk": "F", "guard_rk": "G"})
    )


def get_draftable_players(
    fantasy_df: pd.DataFrame,
    scoring_type: str,
    num_centers: int = 12,
    num_forwards: int = 24,
    num_guards: int = 36,
    num_f_c: int = 12,
    num_g_f: int = 12,
    num_util: int = 36,
) -> list:
    """
    Finds the draftable players for each position group, moving from centers down
    the positional spectrum to guards and repeating for the combined positions.
    Once a player is deemed 'draftable' at a position, then he is removed from
    the pool for future positions.
    """
    # Need to figure out the full strength thing here - 1/11/21
    draftable_players: list = list()
    draftable_players.extend(
        fantasy_df.loc[
            (fantasy_df.is_center) & (~fantasy_df.nba_player_id.isin(draftable_players))
        ]
        .sort_values(by=scoring_type, ascending=False)
        .nba_player_id.head(num_centers)
        .tolist()
    )
    draftable_players.extend(
        fantasy_df.loc[
            (fantasy_df.is_forward)
            & (~fantasy_df.nba_player_id.isin(draftable_players))
        ]
        .sort_values(by=scoring_type, ascending=False)
        .nba_player_id.head(num_forwards)
        .tolist()
    )
    draftable_players.extend(
        fantasy_df.loc[
            (fantasy_df.is_guard) & (~fantasy_df.nba_player_id.isin(draftable_players))
        ]
        .sort_values(by=scoring_type, ascending=False)
        .nba_player_id.head(num_guards)
        .tolist()
    )
    draftable_players.extend(
        fantasy_df.loc[
            ((fantasy_df.is_forward) | (fantasy_df.is_center))
            & (~fantasy_df.nba_player_id.isin(draftable_players))
        ]
        .sort_values(by=scoring_type, ascending=False)
        .nba_player_id.head(num_f_c)
        .tolist()
    )
    draftable_players.extend(
        fantasy_df.loc[
            ((fantasy_df.is_forward) | (fantasy_df.is_guard))
            & (~fantasy_df.nba_player_id.isin(draftable_players))
        ]
        .sort_values(by=scoring_type, ascending=False)
        .nba_player_id.head(num_g_f)
        .tolist()
    )
    draftable_players.extend(
        fantasy_df.loc[~fantasy_df.nba_player_id.isin(draftable_players)]
        .sort_values(by=scoring_type, ascending=False)
        .nba_player_id.head(num_util)
        .tolist()
    )

    return draftable_players


def prep_stats_df() -> pd.DataFrame:
    """Prepares the statistics by pulling and merging all of the relevant data."""
    drip_df = drip.get_current_drip()
    drip_df = drip.transform_drip(drip_df)

    darko_df = darko.get_current_darko()
    darko_df = darko.transform_darko(darko_df)

    name_map = get_name_map()

    hashtag_minutes = get_hashtag_ros_projections()
    leaderboards = get_ottoneu_leaderboard()

    stats_df = combine_darko_drip_df(darko_df, drip_df, name_map)
    stats_df = stats_df.loc[stats_df.nba_player_id.notna()].copy()

    stats_df = stats_df.merge(
        hashtag_minutes, left_on="hashtag_id", right_on="pid", how="left"
    ).merge(leaderboards, on="ottoneu_player_id", how="left", suffixes=("", "_ytd"))
    stats_df["total_ros_minutes"] = stats_df.minutes_forecast * stats_df.games_forecast

    stats_df.minutes_ytd.fillna(0, inplace=True)
    stats_df.total_ros_minutes.fillna(0, inplace=True)
    stats_df.minutes.fillna(0, inplace=True)
    stats_df.tm_id.fillna(0, inplace=True)

    return stats_df


@st.cache_data(ttl=12 * 60 * 60)  # type: ignore
def get_scoring_minutes_combo(
    projection_type: str, stats_df: pd.DataFrame, is_rollup: bool = True
) -> pd.DataFrame:
    """
    Finds the per game projections and player values for each scoring type based
    on the projection type, performing all of the intermediate steps.
    """
    scoring_types = ["simple_points", "trad_points", "categories"]
    # added .copy() method to maybe help with the StCachedObjectMutation warning
    # note: need to actually test that
    df = calc_per_game_projections(stats_df.copy(), projection_type=projection_type)

    if projection_type == "rest_of_season":
        hashtag_rookies = get_hashtag_rookie_projections().set_index("pid")
        hashtag_rookies["fg_pct"] = hashtag_rookies.fgm_game / hashtag_rookies.fga_game
        hashtag_rookies["fg3_pct"] = (
            hashtag_rookies.fg3m_game / hashtag_rookies.fg3a_game
        )
        temp_df = df.set_index("hashtag_id")
        temp_df.update(hashtag_rookies)
        df = temp_df.reset_index()

    for scoring_type in scoring_types:
        if scoring_type == "categories":
            if not is_rollup:
                df = calc_categories_value(df, is_rollup).rename(
                    columns={"total_value": "categories"}
                )  # type: ignore
            else:
                df[f"{scoring_type}"] = calc_categories_value(df, is_rollup)
        else:
            simple_scoring = True if scoring_type == "simple_points" else False
            df[f"{scoring_type}"] = calc_fantasy_pts(
                df, is_simple_scoring=simple_scoring
            )
        df[f"{scoring_type}_position"] = find_surplus_positions(
            df, scoring_type=scoring_type
        )
        draftable_players = get_draftable_players(df, scoring_type=scoring_type)
        df[f"{scoring_type}_value"] = calc_player_values(
            df, scoring_type=scoring_type, draftable_players=draftable_players
        )

    return df


def get_roster_depth(
    league_data: pd.DataFrame,
    league_scoring: str,
    scoring_col: str,
    n_rotation: int = 12,
    n_other: int = 8,
) -> pd.DataFrame:
    # n_rotation should match the sum of number of positions in get_draftable_players()
    team_frames = list()
    team_values = league_data.groupby("team_name")
    # maybe make this an additional arg at some point?
    minutes_format = "ytd"

    for team_name, team_data in team_values:
        team_data.drop_duplicates(inplace=True)
        team_data[f"{scoring_col}_position"] = find_surplus_positions(
            team_data, scoring_type=f"{scoring_col}_{minutes_format}"
        )
        draftable_players = get_draftable_players(
            team_data,
            scoring_type=f"{scoring_col}_{minutes_format}",
            num_centers=1,
            num_forwards=2,
            num_guards=3,
            num_f_c=1,
            num_g_f=1,
            num_util=4,
        )
        # have rotation / depth / other (prospects & injured)?
        team_data["in_rotation"] = team_data.nba_player_id.apply(
            lambda p: 1 if p in draftable_players else 0
        )
        prospects = (
            team_data.sort_values(by=f"{scoring_col}_{minutes_format}", ascending=True)
            .head(n_other)
            .nba_player_id.tolist()
        )
        team_data["other_players"] = team_data.nba_player_id.apply(
            lambda p: 1 if p in prospects else 0
        )
        team_data["depth"] = team_data.apply(
            lambda p: 1 if p.in_rotation + p.other_players == 0 else 0, axis=1
        )
        # rotation_value = (
        #     team_data.loc[team_data.nba_player_id.isin(draftable_players)]
        #     .simple_points_value_ytd.sum()
        #     .round()
        # )
        # need to drop duplicates before doing any summing
        team_data["team_name"] = team_name
        team_frames.append(team_data)

    league_values_df = pd.concat(team_frames)
    # now roll up to team level data
    sum_cols = [f"{scoring_col}_{minutes_format}", f"{minutes_format}_surplus"]
    rotation_data = (
        league_values_df.where(league_values_df.in_rotation == 1)
        .groupby("team_name")[sum_cols]
        .sum()
        .add_prefix("rotation_")
        .reset_index()
    )
    depth_data = (
        league_values_df.where(league_values_df.depth == 1)
        .groupby("team_name")[sum_cols]
        .sum()
        .add_prefix("depth_")
        .reset_index()
    )
    other_players_data = (
        league_values_df.where(league_values_df.other_players == 1)
        .groupby("team_name")[sum_cols]
        .sum()
        .add_prefix("other_")
        .reset_index()
    )

    team_value_by_rotation_levels = pd.DataFrame()
    team_value_by_rotation_levels["team_name"] = league_values_df.team_name.unique()
    team_value_by_rotation_levels = (
        team_value_by_rotation_levels.merge(rotation_data, how="left", on="team_name")
        .merge(depth_data, how="left", on="team_name")
        .merge(other_players_data, how="left", on="team_name")
    )

    return team_value_by_rotation_levels
