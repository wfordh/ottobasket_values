"""
Keep this script here and create a page that just pulls the data from the
data folder and trims it down to the relevant columns, with filters and some
documentation explaining some of the assumptions.
"""

import os
import sys
import time

sys.path.append(os.path.abspath("src"))

import pandas as pd
import requests

from calc_stats import (calc_categories_value, calc_fantasy_pts,
                        calc_player_values)
from transform import find_surplus_positions, get_draftable_players

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

params = {
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


def main():

    if 1 == 0:
        # I've already done this and don't want to do it again
        player_idx_resp = requests.get(
            "https://stats.nba.com/stats/playerindex", params=params, headers=headers
        )
        player_idx_json = player_idx_resp.json().pop("resultSets")[0]
        player_idx_df = pd.DataFrame(
            player_idx_json["rowSet"], columns=player_idx_json["headers"]
        )
        player_idx_df.to_csv("./data/player_index.csv", index=False)
    else:
        player_idx_df = pd.read_csv("./data/player_index.csv")
        # should probably do this before writing to csv but w/e
        player_idx_df.columns = [col.lower() for col in player_idx_df.columns]
        player_idx_df.rename(columns={"person_id": "player_id"}, inplace=True)

    params = {
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
        "Season": "2022-23",
        "SeasonSegment": "",
        "SeasonType": "Regular Season",
        "ShotClockRange": "",
        "StarterBench": "",
        "TeamID": "0",
        "VsConference": "",
        "VsDivision": "",
        "Weight": "",
    }

    player_season_box_stats_list = list()
    # don't include this season
    for year in range(1996, 2022):
        season = str(year) + "-" + str(year + 1)[-2:]
        if 1 == 0:
            time.sleep(1.8)
            params["Season"] = season
            response = requests.get(
                "https://stats.nba.com/stats/leaguedashplayerstats",
                params=params,
                headers=headers,
            )
            if response.status_code != 200:
                print(response.status_code)
            response_json = response.json().pop("resultSets")[0]
            season_df = pd.DataFrame(
                response_json["rowSet"], columns=response_json["headers"]
            )
            season_df["season"] = params["Season"]
            season_df.to_csv(f"./data/box_stats_{season}.csv", index=False)
            print(f"done with {season}")
        else:
            season_df = pd.read_csv(f"./data/box_stats_{season}.csv")
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
            season_df.columns = [col.lower() for col in season_df.columns]
            season_df.columns = [
                col + "_game" if col in fantasy_columns else col
                for col in season_df.columns
            ]
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
            # for compatibility with `find_surplus_positions()`
            season_df.rename(
                columns={
                    "position": "ottoneu_position",
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
                draftable_players = get_draftable_players(
                    season_df, scoring_type=scoring_type
                )
                season_df[f"{scoring_type}_value"] = calc_player_values(
                    season_df,
                    scoring_type=scoring_type,
                    draftable_players=draftable_players,
                )

        player_season_box_stats_list.append(season_df)
        # season_df.to_csv(f"./data/box_stats_{params['Season']}")

    season_df = pd.concat(player_season_box_stats_list)
    season_df.to_csv("./data/box_stats.csv", index=False)
    # player_data_df = season_df.merge(player_idx_df, left_on="PERSON_ID", right_on="PLAYER_ID", how='left')
    # get year in league and age. year in league should be dense rank
    # rookie status needs to be done after bringing all the seasons together


if __name__ == "__main__":
    main()
