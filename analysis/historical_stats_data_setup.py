"""
Keep this script here and create a page that just pulls the data from the
data folder and trims it down to the relevant columns, with filters and some
documentation explaining some of the assumptions.

The box stats revised uses Ottoneu positions for 2022-23 onward since I have 
those values stored in the retrodictions. Maybe not best if I want to do some
modeling work but w/e. Can fix that when necessary?
"""

import argparse
import os
import sys
import time

sys.path.append(os.path.abspath("src"))

import pandas as pd
import requests

# ignoring import error for now
# https://stackoverflow.com/questions/68695851/mypy-cannot-find-implementation-or-library-stub-for-module
from calc_stats import calc_categories_value  # type: ignore
from calc_stats import calc_fantasy_pts, calc_player_values
from transform import (find_surplus_positions,  # type: ignore
                       get_draftable_players)

parser = argparse.ArgumentParser()

parser.add_argument(
    "-s", "--start_year", type=int, help="Start year to provide for pulling the data."
)

parser.add_argument(
    "-e", "--end_year", type=int, help="End year to provide for pulling the data."
)

parser.add_argument(
    "-p",
    "--pull_players",
    type=str,
    help="Pull all players again.",
    default="yes",
    choices=["yes", "no"],
)

# headers and params for scraping NBA data, not needed after initial scrape

headers = {
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "If-Modified-Since": "Fri, 13 Jan 2023 18:48:41 GMT",
    "Origin": "https://www.stats.nba.com",
    "Referer": "https://www.stats.nba.com/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
    "sec-ch-ua": '"Not?A_Brand";v="8", "Chromium";v="108", "Google Chrome";v="108"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
}

index_params = {
    "College": "",
    "Country": "",
    "DraftPick": "",
    "DraftRound": "",
    "DraftYear": "",
    "Height": "",
    "Historical": "1",
    "LeagueID": "00",
    "Season": "2022-23",
    "SeasonType": "Regular Season",
    "TeamID": "0",
    "Weight": "",
}


def get_season_box_stats(season: int) -> pd.DataFrame:
    season_params = {
        "College": "",
        "Conference": "",
        "Country": "",
        "DateFrom": "",
        "DateTo": "",
        "Division": "",
        "DraftPick": "",
        "DraftYear": "",
        "GameScope": "",
        "GameSegment": "",
        "Height": "",
        "LastNGames": "0",
        "LeagueID": "00",
        "Location": "",
        "MeasureType": "Base",
        "Month": "0",
        "OpponentTeamID": "0",
        "Outcome": "",
        "PORound": "0",
        "PaceAdjust": "N",
        "PerMode": "Totals",
        "Period": "0",
        "PlayerExperience": "",
        "PlayerPosition": "",
        "PlusMinus": "N",
        "Rank": "N",
        "Season": season,
        "SeasonSegment": "",
        "SeasonType": "Regular Season",
        "ShotClockRange": "",
        "StarterBench": "",
        "TeamID": "0",
        "VsConference": "",
        "VsDivision": "",
        "Weight": "",
    }

    season_path = f"./data/box_stats_{season}.csv"
    if not os.path.exists(season_path):
        time.sleep(1.8)
        season_params["Season"] = season
        response = requests.get(
            "https://stats.nba.com/stats/leaguedashplayerstats",
            params=season_params,  # type: ignore
            headers=headers,
        )
        if response.status_code != 200:
            print(response.status_code)
        response_json = response.json().pop("resultSets")[0]
        season_df = pd.DataFrame(
            response_json["rowSet"], columns=response_json["headers"]
        )
        season_df["season"] = season_params["Season"]
        season_df.to_csv(f"./data/box_stats_{season}.csv", index=False)
        print(f"done with {season}")
    else:
        season_df = pd.read_csv(f"./data/box_stats_{season}.csv")

    return season_df


def get_otto_values_df(
    season: str, season_df: pd.DataFrame, player_idx_df: pd.DataFrame
) -> pd.DataFrame:
    season_df.drop(
        [col for col in season_df.columns if "RANK" in col],
        axis=1,
        inplace=True,
    )
    fantasy_columns = [
        "pts",
        "reb",
        "blk",
        "stl",
        "tov",
        "ast",
        "fgm",
        "fga",
        "ftm",
        "fta",
        "fg3m",
        "fg3a",
    ]
    # not sure why these needed to be split into two lines :shrug:
    season_df.columns = pd.Index([col.lower() for col in season_df.columns])
    season_df.columns = pd.Index(
        [col + "_game" if col in fantasy_columns else col for col in season_df.columns]
    )

    # will want to use ottoneu positions where possible
    season_df = season_df.merge(
        player_idx_df[
            [
                "player_id",
                "position",
                "draft_year",
                "draft_round",
                "draft_number",
                "from_year",
                "to_year",
            ]
        ],
        on="player_id",
        how="left",
    )
    if season > "2021-22":
        # maybe shouldn't do this if looking at age curves
        ottoneu_season_positions = pd.read_csv(
            f"./data/{season}_preseason_projections/retrodiction_values.csv"
        )
        mappings = pd.read_csv("./data/mappings_update_2023-09-14.csv")
        season_df = season_df.merge(
            mappings[["ottoneu_player_id", "nba_player_id"]],
            left_on="player_id",
            right_on="nba_player_id",
            how="left",
        ).merge(
            ottoneu_season_positions[["ottoneu_player_id", "ottoneu_position"]],
            on="ottoneu_player_id",
            how="left",
        )
        season_df.ottoneu_position.fillna(season_df.position, inplace=True)
        # annoying have to do this here. again, probably a better way
        season_df.drop("nba_player_id", axis=1, inplace=True)
    else:
        # have to do this here since otherwise ottoneu_position exists as a column
        season_df.rename(columns={"position": "ottoneu_position"}, inplace=True)
    # for compatibility with `find_surplus_positions()`
    season_df.rename(
        columns={
            "player_id": "nba_player_id",
            "player_name": "player",
        },
        inplace=True,
    )
    scoring_types = ["simple_points", "trad_points", "categories"]
    for scoring_type in scoring_types:
        if scoring_type == "categories":
            season_df[f"{scoring_type}"] = calc_categories_value(season_df)
        else:
            simple_scoring = True if scoring_type == "simple_points" else False
            season_df[f"{scoring_type}"] = calc_fantasy_pts(
                season_df, is_simple_scoring=simple_scoring
            )
        season_df[f"{scoring_type}_position"] = find_surplus_positions(
            season_df, scoring_type=scoring_type
        )
        # print(season_df.head())
        draftable_players = get_draftable_players(season_df, scoring_type=scoring_type)
        season_df[f"{scoring_type}_value"] = calc_player_values(
            season_df,
            scoring_type=scoring_type,
            draftable_players=draftable_players,
        )
    return season_df


def main():
    args = parser.parse_args()
    command_args = dict(vars(args))
    start_year = command_args.pop("start_year", None)
    end_year = command_args.pop("end_year", None)
    if not end_year:
        end_year = start_year + 1
    pull_players = True if command_args.pop("pull_players") == "yes" else False

    if pull_players:
        # pull all players again if requested
        player_idx_resp = requests.get(
            "https://stats.nba.com/stats/playerindex",
            params=index_params,
            headers=headers,
        )
        player_idx_json = player_idx_resp.json().pop("resultSets")[0]
        player_idx_df = pd.DataFrame(
            player_idx_json["rowSet"],
            columns=[col.lower() for col in player_idx_json["headers"]],
        )
        player_idx_df.rename(columns={"person_id": "player_id"}, inplace=True)
        player_idx_df.to_csv("./data/player_index.csv", index=False)
    else:
        player_idx_df = pd.read_csv("./data/player_index.csv")

    # box_revised is what goes on the app page
    box_revised = pd.read_csv("./data/box_stats_revised.csv")
    box_revised_seasons = box_revised.season.unique()
    player_season_box_stats_list = [box_revised]
    # don't include this season

    for year in range(start_year, end_year):
        season = str(year) + "-" + str(year + 1)[-2:]
        if season in box_revised_seasons:
            # skip season if it's already been pulled
            continue
        season_df = get_season_box_stats(season)
        season_df = get_otto_values_df(season, season_df, player_idx_df)
        # again could probably do this upstream but yolo
        season_df.rename(
            columns={
                "team_abbreviation": "team",
                "min": "minutes",
                "categories": "category_points",
            },
            inplace=True,
        )
        # these are the box_stats_revised columns
        fantasy_df = season_df[
            [
                "nba_player_id",
                "player",
                "team",
                "age",
                "minutes",
                "season",
                "position",
                "simple_points",
                "simple_points_position",
                "simple_points_value",
                "trad_points",
                "trad_points_position",
                "trad_points_value",
                "category_points",
                "categories_position",
                "categories_value",
            ]
        ].copy()

        player_season_box_stats_list.append(fantasy_df)
        # season_df.to_csv(f"./data/box_stats_{params['Season']}")

    new_box_revised = pd.concat(player_season_box_stats_list)
    new_box_revised.to_csv("./data/box_stats_revised.csv", index=False)
    # player_data_df = season_df.merge(player_idx_df, left_on="PERSON_ID", right_on="PLAYER_ID", how='left')
    # get year in league and age. year in league should be dense rank
    # rookie status needs to be done after bringing all the seasons together


if __name__ == "__main__":
    main()
