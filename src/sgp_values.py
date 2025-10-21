import argparse
import logging
import os
import sys
import time

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup

sys.path.append(os.path.abspath("src"))

from calc_stats import (calc_per_game_projections, calc_player_values,
                        calc_sgp_slopes, ratio_stat_sgp)
from leagues import get_schedule_week, get_standings_page
from transform import (find_surplus_positions, get_draftable_players,
                       prep_stats_df)
from utils import (_setup_gdrive, _upload_data, get_existing_sgp_data,
                   get_leagues_metadata, get_name_map, get_ottoneu_leaderboard)

logging.basicConfig(level=logging.INFO)


def main():
    leagues_metadata = get_leagues_metadata()
    sgp_records = get_existing_sgp_data()
    # ASSIGN SEASON UP HERE?
    SEASON = "2025-26"
    # same key that's used in sgp_records()
    sheet_key = "17NoW7CT-AvQ9-VtT22nzaXnVCYNgunGDlYeDeDEn_Mc"

    # could use created_year from the metadata to check if need to scrape in the for loop?
    cats_leagues = leagues_metadata.loc[
        leagues_metadata.points_system == "Categories"
    ].league_id.tolist()

    leagues_sgp_data = list()
    for league_id in cats_leagues:
        # functionalize?
        time.sleep(1.3)
        try:
            logging.info(f"Getting data for league {league_id}!")
            standings_df = get_standings_page(league_id, SEASON)
        except IndexError:
            logging.info(
                f"League {league_id} is either private or did not exist in {SEASON}!"
            )
            continue
        sgp_slopes = calc_sgp_slopes(standings_df)
        sgp_ratios = ratio_stat_sgp(standings_df)
        sgp_data = pd.Series(sgp_slopes)
        sgp_data["league_id"] = league_id

        # HOW TO ASSIGN SEASON?
        sgp_data["season"] = SEASON
        sgp_data["avg_team_fga"] = sgp_ratios[0][0]
        sgp_data["avg_team_fgm"] = sgp_ratios[0][1]
        sgp_data["avg_team_fg_pct"] = sgp_ratios[0][2]
        sgp_data["avg_team_fg3a"] = sgp_ratios[1][0]
        sgp_data["avg_team_fg3m"] = sgp_ratios[1][1]
        sgp_data["avg_team_fg3_pct"] = sgp_ratios[1][2]
        leagues_sgp_data.append(sgp_data)

    current_sgp_df = pd.concat(leagues_sgp_data, axis=1).T

    client_key_string = os.environ.get("SERVICE_BLOB", None)
    gc = _setup_gdrive(client_key_string)

    updated_sgp_records = pd.concat(
        [sgp_records.loc[sgp_records.season != SEASON].copy(), current_sgp_df], axis=0
    )

    updated_sgp_records.to_csv("data/sgp_test.csv")

    _upload_data(gc, updated_sgp_records, sheet_key)

    sgp_league_averages = updated_sgp_records.groupby("season").mean().reset_index()
    sgp_league_averages["week"] = get_schedule_week()

    _upload_data(
        gc,
        sgp_league_averages,
        sheet_key,
        wks_num=1,
    )
    ### for next steps (separate script? or part of main pipeline?)
    ### get week. get sgp_records.
    ### weighted average of last two seasons: week_num - 1 = current_wt. num_weeks (22) - current_wt = last_season_wt
    ### NOW I can go straight to main pipeline


if __name__ == "__main__":
    main()
