"""
TODO
- scrape all cats leagues - must read in leagues info from sheets
- push SGP data to gdrive

"""

import argparse
import logging
import os
import sys

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup

sys.path.append(os.path.abspath("src"))

from calc_stats import (calc_per_game_projections,  # type: ignore
                        calc_player_values)
from transform import find_surplus_positions  # type: ignore
from transform import (get_draftable_players, get_name_map,
                       get_ottoneu_leaderboard, prep_stats_df)

parser = argparse.ArgumentParser()

league_id = parser.add_argument(
    "-l", "--league_id", required=True, type=int, default=26
)
season_type = parser.add_argument(
    "-s",
    "--season_type",
    required=True,
    type=str,
    choices=["year_to_date", "rest_of_season"],
)


def get_table(table) -> pd.DataFrame:
    headers = [
        th.text.lower().strip() for th in table.find("thead").find("tr").find_all("th")
    ]
    rows = [
        [td.text.strip() for td in row.find_all("td")]
        for row in table.find("tbody").find_all("tr")
    ]
    return pd.DataFrame(rows, columns=headers)


def get_standings_page(league_id: int) -> pd.DataFrame:
    # make season map
    # 4 = 2023-24, 3 = 2022-23, 2 = 2021-22
    url = f"https://ottoneu.fangraphs.com/basketball/{league_id}/standings/4"
    r = requests.get(url, timeout=None)
    soup = BeautifulSoup(r.content, "html.parser")
    tables = soup.find_all("table")
    print(url)
    print(len(tables))
    main_table = get_table(tables[1])
    shots_table = get_table(tables[2])
    overall_table = main_table.merge(
        shots_table, how="inner", on=["team", "g", "mins"], suffixes=("", "_foo")
    )
    for col in overall_table.columns:
        if col == "team":
            continue
        overall_table[col] = overall_table[col].astype(float)
    return overall_table


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


def get_existing_sgp_data():
    sheet_key = "17NoW7CT-AvQ9-VtT22nzaXnVCYNgunGDlYeDeDEn_Mc"
    return pd.read_csv(
        f"https://docs.google.com/spreadsheets/d/{sheet_key}/gviz/tq?tqx=out:csv&gid=284274620"
    )


def main():
    args = parser.parse_args()
    command_args = dict(vars(args))
    league_id = command_args.pop("league_id", None)
    season_type = command_args.pop("season_type", None)
    sgp_records = get_existing_sgp_data()
    # if league_id in sgp_records.league_id:
    if False:
        # need a season mapping thing??
        season = 3
        sgp_data = sgp_records.loc[
            (sgp_records.league_id == league_id) & (sgp_records.season == season)
        ].squeeze()
    else:
        standings_df = get_standings_page(league_id)
        sgp_slopes = calc_sgp_slopes(standings_df)
        sgp_ratios = ratio_stat_sgp(standings_df)
        sgp_data = pd.Series(sgp_slopes)
        sgp_data["league_id"] = league_id
        sgp_data["season"] = "2022-23"
        sgp_data["avg_team_fga"] = sgp_ratios[0][0]
        sgp_data["avg_team_fgm"] = sgp_ratios[0][1]
        sgp_data["avg_team_fg_pct"] = sgp_ratios[0][2]
        sgp_data["avg_team_fg3a"] = sgp_ratios[1][0]
        sgp_data["avg_team_fg3m"] = sgp_ratios[1][1]
        sgp_data["avg_team_fg3_pct"] = sgp_ratios[1][2]
    logging.info(sgp_data)
    sgp_data.to_csv("data/raw_sgp_data.csv")

    ##
    ## Everything after this is related to calculating the values
    ## Balancing current year with former year?
    ##
    if season_type == "year_to_date":
        leaders_df = get_ottoneu_leaderboard()
        stats_df = leaders_df.rename(
            columns={
                "turnovers": "tov",
                "points": "pts",
                "rebounds": "reb",
                "assists": "ast",
                "steals": "stl",
                "blocks": "blk",
                "free_throws_made": "ftm",
                "fg_pct": "fg%",
                "three_pt_pct": "3pt%",
            },
        )
    else:
        ## for ros, need prep_stats_df() and calc_per_game_projections()
        ## check calc_pg for name matching
        ros_df = prep_stats_df()
        ros_per_game_df = calc_per_game_projections(ros_df, "rest_of_season")
        stats_df = ros_per_game_df.rename(
            columns={
                "pts_game": "pts",
                "reb_game": "reb",
                "ast_game": "ast",
                "stl_game": "stl",
                "blk_game": "blk",
                "tov_game": "tov",
                "fg_pct": "fg%",
                "fg3_pct": "3pt%",
                "ftm_game": "ftm",
                "fgm_game": "field_goals_made",
                "fga_game": "field_goal_attempts",
                "fg3m_game": "three_points_made",
                "fg3a_game": "three_point_attempts",
            },
        )

    print(sgp_slopes)
    print(sgp_ratios)

    #######
    ####### move this stuff to calc_stats()?
    #######
    columns = ["pts", "reb", "ast", "stl", "blk", "ftm", "tov", "fg%", "3pt%"]
    for col in columns:
        if col == "fg%":
            stats_df[f"{col}_sgp"] = stats_df.apply(
                lambda row: (
                    (row.field_goals_made + sgp_ratios[0][1])
                    / (row.field_goal_attempts + sgp_ratios[0][0])
                    - sgp_ratios[0][2]
                )
                / sgp_slopes[col],
                axis=1,
            )
        elif col == "3pt%":
            stats_df[f"{col}_sgp"] = stats_df.apply(
                lambda row: (
                    (row.three_points_made + sgp_ratios[1][1])
                    / (row.three_point_attempts + sgp_ratios[1][0])
                    - sgp_ratios[1][2]
                )
                / sgp_slopes[col],
                axis=1,
            )
        else:
            stats_df[f"{col}_sgp"] = stats_df[col].apply(
                lambda row: row / sgp_slopes[col]
            )

    mappings = get_name_map()
    df = stats_df.merge(
        mappings,
        how="inner",
        on=["ottoneu_player_id", "nba_player_id", "hashtag_id", "ottoneu_position"],
    )
    df["categories"] = df[[col for col in df.columns if "sgp" in col]].sum(axis=1)

    #######
    #######
    #######

    scoring_type = "categories"
    print(df.columns)
    df[f"{scoring_type}_position"] = find_surplus_positions(
        df, scoring_type=scoring_type
    )
    draftable_players = get_draftable_players(df, scoring_type=scoring_type)
    df[f"{scoring_type}_value"] = calc_player_values(
        df, scoring_type=scoring_type, draftable_players=draftable_players
    )

    df.to_csv(f"data/sgp_test_{scoring_type}.csv", index=False)


if __name__ == "__main__":
    main()
