import os
import sys
from datetime import date, datetime, timedelta

import pandas as pd

sys.path.append(os.path.abspath("src"))

from leagues import get_league_leaderboard

LEAGUE_ID = 39  # can be any trad pts league


def main():
    yesterday = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")

    leaders = get_league_leaderboard(
        league_id=LEAGUE_ID, start_date=yesterday, end_date=yesterday
    )
    leaders.to_csv(sys.stdout, index=False)


if __name__ == "__main__":
    main()
