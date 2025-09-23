"""
Notes:
- how to do it besides during period between cut deadline and draft?
- https://fantasy.fangraphs.com/how-to-account-for-keeper-inflation-in-your-auction-draft/

"""

import logging
import os
import sys
from datetime import date

import pandas as pd
import requests
from bs4 import BeautifulSoup
from great_tables import GT, html, loc, md, style

from leagues import get_league_info, get_league_rosters, get_league_scoring
from utils import _sleep_unif

sys.path.append(os.path.abspath("src"))

logging.basicConfig(level=logging.INFO)


def scrape_league_transactions(
    league_id: int, page_id: int, pull_headers=True
) -> pd.DataFrame:
    url = f"https://ottoneu.fangraphs.com/basketball/{league_id}/transactions?page={page_id}"
    resp = requests.get(url)
    soup = BeautifulSoup(resp.content, "html.parser")
    txn_table = soup.find("main").find("table")
    txn_headers = [
        th.text.strip() for th in txn_table.find("thead").find("tr").find_all("th")
    ]
    txn_rows = [
        [td.text.strip() for td in tr.find_all("td")]
        for tr in txn_table.find("tbody").find_all("tr")
        # if tr.find_all("td")[3].text.strip() == "increase"
    ]
    if pull_headers:
        return (txn_headers, txn_rows)
    return txn_rows


def get_league_inflation(
    league_id: int = 26, league_scoring: str = "trad_points"
) -> float:
    _sleep_unif()
    league_salaries = get_league_rosters(league_id)
    TOTAL_BUDGET = 12 * 400
    # 25*12 = 300
    # each transaction page is 50 long
    # 	# get values
    sheet_id = "1GgwZpflcyoRYMP0yL2hrbNwndJjVFm34x3jXnUooSfA"
    values_df = pd.read_csv(
        f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"
    )
    league_values_df = league_salaries.merge(
        values_df, on="ottoneu_player_id", how="left"
    )
    league_values_df.player.fillna(
        league_values_df.player_name, inplace=True
    )  # swap player_name for ottoneu_name??
    league_values_df.ottoneu_position.fillna(league_values_df.position, inplace=True)
    # fill the rest of columns NA's with 0
    league_values_df.fillna(0, inplace=True)

    if league_scoring == "categories":
        scoring_col = f"{league_scoring}_value"
    elif league_scoring == "simple_points":
        scoring_col = f"{league_scoring}_value"
    else:
        scoring_col = "trad_points_value"
    league_values_df["ros_surplus"] = (
        league_values_df[f"{scoring_col}_ros"] - league_values_df.salary
    )

    keeper_value = league_values_df[f"{scoring_col}_ros"].sum()
    keeper_cost = league_values_df.salary.sum()
    remaining_budget = TOTAL_BUDGET - keeper_cost
    remaining_value = TOTAL_BUDGET - keeper_value
    inflation_idx = remaining_budget / remaining_value
    logging.info(f"Keeper value is {keeper_value} and cost is {keeper_cost}")
    logging.info(
        f"Remaining budget is {remaining_budget} and remaining value is {remaining_value}"
    )
    logging.info(f"Inflation is {round(inflation_idx, 2)}")
    return inflation_idx


def main():
    LEAGUE_ID = 26
    if 1 == 0:
        all_leagues = get_league_info()
        league_ids = all_leagues.league_id.unique().tolist()
        # need to figure out the league scoring to reduce the # of calls to the GSheet
        league_inflation_values = list()
        for league_id in league_ids:
            league_scoring = get_league_scoring(league_id, all_leagues)
            inflation_idx = get_league_inflation(league_id, league_scoring)
            league_inflation_values.append(inflation_idx)

        all_leagues["inflation_idx"] = league_inflation_values
        logging.info(
            f"Group by year: {all_leagues.groupby('created_year').inflation_idx.mean()}"
        )
        logging.info(
            f"Group by year and format: {all_leagues.groupby(['created_year', 'points_system']).inflation_idx.mean()}"
        )
        logging.info(all_leagues)
        summary_df = all_leagues.groupby(["created_year", "points_system"]).agg(
            {"inflation_idx": ["mean", "count", "min", "max"]}
        )
        summary_df.to_csv("./data/inflation_values_by_scoring_and_age.csv")
    else:
        summary_df = pd.read_csv("./data/inflation_values_by_scoring_and_age.csv")
        summary_df["league_age"] = (
            date.today().year
            - summary_df.created_year.str.slice(stop=4).astype(int)
            + 1
        )
        logging.info(summary_df)
        gt = (
            GT(summary_df)
            .cols_hide("created_year")
            .cols_move_to_start("league_age")
            .tab_header(
                title="Inflation in Ottoneu Basketball", subtitle="By format and age"
            )
            .tab_spanner(label="League Info", columns=["league_age", "points_system"])
            .tab_spanner(
                label="Inflation Index Stats",
                columns=[
                    "inflation_idx_mean",
                    "count",
                    "inflation_idx_min",
                    "inflation_idx_max",
                ],
            )
            .cols_label(
                league_age="League Age",
                points_system="Scoring Format",
                inflation_idx_mean="Mean",
                count="# of Leagues",
                inflation_idx_min="Minimum",
                inflation_idx_max="Maximum",
            )
            .fmt_number(
                columns=["inflation_idx_mean", "inflation_idx_min", "inflation_idx_max"]
            )
            .tab_style(
                style=style.fill("lightgray"),
                locations=loc.body(rows=list(range(0, summary_df.shape[0], 2))),
            )
            # .tab_style(
            #     style=style.fill("#f5c6a9"), locations=loc.body(rows=list(range(1, summary_df.shape[0] + 1, 2)))
            # )
            .tab_style(
                style=style.borders(sides="right", style="solid", color="white"),
                locations=loc.body(columns=["points_system"]),
            )
            .tab_source_note(source_note=md("@wfordh | Data: Ottoneu Basketball"))
        )

        gt.save("./analysis/images/inflation_values_by_scoring_and_age_2025.png")

    # old code...
    # num_rostered_players = league_salaries.shape[0]
    # # if num rostered is < 150 --> page 4
    # MAX_PLAYERS = 300
    # start_page_id = 1 + (MAX_PLAYERS - num_rostered_players) // 50
    # # get txns
    # # return lists
    # increase_txns = False
    # pull_headers = True
    # page_id = start_page_id
    # txn_list = list()
    # while increase_txns:
    # 	if pull_headers:
    # 		txn_headers, txn_rows = scrape_league_transactions(league_id=LEAGUE_ID, page_id=page_id, pull_headers=pull_headers)
    # 		pull_headers = False
    # 	# append now? or filter first? basically when to check if setting increase_txns to False
    # 	num_increases = sum([1 if txn[3] == "increase" else 0 for txn in txn_rows ])
    # 	if num_increases == 50:
    # 		txn_list.extend(txn_rows)
    # 	elif txn_rows[0][3] != "increase":
    # 		# filter out non-increase and append
    # 		txn_list.extend([txn for txn in txn_rows if txn[3] == "increase"])
    # 	elif txn_rows[0][3] == "increase" and txn_rows[-1][3] == "increase" and num_increases < 50:
    # 		# less than 50 in season moves. grab all increases and then drop duplicates later?
    # 		for txn in txn_rows:
    # 			if txn[3] == "increase":
    # 				txn_list.extend(txn)
    # 			else:
    # 				break
    # 	elif txn_rows[-1][3] != "increase":
    # 		# filter out non-increase and append. set increase_txns to False.
    # 		txn_list.extend([txn for txn in txn_rows if txn[3] == "increase"])
    # 		increase_txns = False
    # 	else:
    # 		logging.warn(txn_rows)

    # postseason_salaries = pd.DataFrame(data=txn_list, columns=txn_headers)


if __name__ == "__main__":
    main()
