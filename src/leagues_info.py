import logging
import os
import sys
import time

import pandas as pd

sys.path.append(os.path.abspath("src"))
logging.basicConfig(level=logging.INFO)

from leagues import get_league_first_year, get_league_settings
from utils import _setup_gdrive, _upload_data

# 19 total leagues at the moment - 7/16/24
# or is it 20??? do private leagues (ie league 4) not show up on the
# avg salary page?
# could use this page? https://ottoneu.fangraphs.com/basketball/browse_leagues
# at least use it as a reference point...just one more call to Ottoneu


def main():
    client_key_string = os.environ.get("SERVICE_BLOB", None)
    sheet_key = "14TkjXjFSWDQsHZy6Qt77elLnVpi1HwrpbqzVC4JKDjc"

    leagues_counter = 0
    num_leagues = 19
    bad_leagues = 0
    league_id = 1
    leagues_data = dict()
    while leagues_counter <= num_leagues:
        logging.info(f"Fetching data for league {league_id}!")
        try:
            time.sleep(1.3)
            leagues_data[league_id] = get_league_settings(league_id)
            time.sleep(1.1)
            leagues_data[league_id]["created_year"] = get_league_first_year(league_id)
            leagues_counter += 1
        except AttributeError:
            # league is invalid (checking implicitly)
            # can check if request URL
            # 'https://ottoneu.fangraphs.com/basketball/?invalidLeague=1'
            bad_leagues += 1
        league_id += 1

    league_info_df = (
        pd.DataFrame.from_dict(leagues_data, orient="index")
        .reset_index()
        .rename(columns={"index": "league_id"})
    )

    logging.info("Got information for all leagues")
    gc = _setup_gdrive(client_key_string)

    _upload_data(gc, league_info_df, sheet_key)


if __name__ == "__main__":
    main()
