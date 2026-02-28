import os
import sys
from datetime import date, datetime, timedelta

import pandas as pd

sys.path.append(os.path.abspath("src"))

from leagues import get_league_leaderboard
from utils import _setup_gdrive, _upload_data

LEAGUE_ID = 39  # can be any trad pts league


def main():
    yesterday = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")

    leaders = get_league_leaderboard(
        league_id=LEAGUE_ID, start_date=yesterday, end_date=yesterday
    ).fillna("")

    # leaders.to_csv("./data/last_night_test.csv")
    sheet_key = "1TOfcNsLBEZRP2GuXdu2oIqh6HnYf-hy4O6eqh15afCM"
    client_key_string = os.environ.get("SERVICE_BLOB", None)
    gc = _setup_gdrive(client_key_string)

    _upload_data(gc, leaders, sheet_key, wks_num=0, clear=True)


if __name__ == "__main__":
    main()
