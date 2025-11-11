"""
Need to update FIRST_DAY_OF_SEASON, LAST_DAY_OF_SEASON, and topic_id before every season.
"""

import logging
import os
import sys
import tempfile
from datetime import date, datetime, timedelta

import pandas as pd
import requests
from fluent_discourse import Discourse  # type: ignore
from great_tables import GT, md

sys.path.append(os.path.abspath("src"))

from leagues import get_average_values, get_league_leaderboard  # type: ignore
from utils import clean_avg_vals_df  # type: ignore

logging.basicConfig(level=logging.INFO)

LEAGUE_ID = 39  # must be trad points league


def discourse_img_upload(
    client: Discourse, tmp_file: tempfile.NamedTemporaryFile
) -> dict:
    # upload an image and return the JSON blob from the request
    response = requests.post(
        f"{client._base_url}/uploads.json",
        # files={"files[]": (fp_best.name, fp_best.read(), "image/png")},
        files={"files[]": open(tmp_file.name, "rb")},
        data={"type": "composer"},
        headers={"Api-Username": client._username, "Api-Key": client._api_key},
    )

    response.raise_for_status()
    assert response.json()["short_url"]

    return response.json()


def main():
    sheet_key = "15clwCO60P7lIxJU8B91tRRRZA7X0g7-tTqdnc-K1pa0"
    today = date.today().strftime("%Y-%m-%d")
    last_week = (date.today() - timedelta(days=7)).strftime("%Y-%m-%d")
    FIRST_DAY_OF_SEASON = "2025-10-21"
    LAST_DAY_OF_SEASON = "2026-04-12"
    if (today < FIRST_DAY_OF_SEASON) or (today > LAST_DAY_OF_SEASON):
        logging.warning("Today's date is out of bounds for the season. Exiting!")
        sys.exit()
    last_schedule_week = (
        datetime.today() - datetime.strptime(FIRST_DAY_OF_SEASON, "%Y-%m-%d")
    ).days // 7
    logging.info(f"Today: {today}")
    logging.info(f"Last Monday: {last_week}")

    avg_vals = get_average_values()
    avg_vals = clean_avg_vals_df(avg_vals)

    last_week_stats = get_league_leaderboard(
        league_id=LEAGUE_ID, start_date=last_week, end_date=today
    )
    season_minus_week_stats = get_league_leaderboard(
        league_id=LEAGUE_ID, start_date=FIRST_DAY_OF_SEASON, end_date=last_week
    )

    # analysis time!
    ## roster stats
    avg_vals["avg_salary_current"] = avg_vals["avg_salary"].fillna(0)

    avg_vals["roster_pct_current"] = avg_vals["roster_pct"].fillna(0)

    avg_vals.fillna(0, inplace=True)

    stat_keep_cols = [
        "player_name",
        "ottoneu_player_id",
        "positions",
        "games_played",
        "minutes",
        "fantasy_points_avg",
    ]

    # also get games_played and minutes / minutes_avg from the leaderboard?
    comp_stat_values = (
        last_week_stats[stat_keep_cols]
        .merge(
            season_minus_week_stats[stat_keep_cols],
            how="outer",
            on=["player_name", "ottoneu_player_id", "positions"],
            suffixes=["_last_week", "_season_minus_one"],
        )
        .merge(
            avg_vals.drop(["name", "position"], axis=1),
            how="outer",
            left_on=["ottoneu_player_id"],
            right_on=["ottoneu_player_id"],
        )
    )

    comp_stat_values = (
        comp_stat_values.loc[
            (
                comp_stat_values.games_played_last_week
                + comp_stat_values.games_played_season_minus_one
            )
            > 0
        ]
        .drop_duplicates()
        .copy()
    )

    comp_stat_values["trad_prod_diff"] = (
        comp_stat_values.fantasy_points_avg_last_week
    ) - (comp_stat_values.fantasy_points_avg_season_minus_one)

    comp_stat_values.fillna(0, inplace=True)

    ### do some sort of formatting for the selected players?
    ### how do I deliver the results? another google sheet? slack? email?
    gt_best = (
        GT(
            comp_stat_values.sort_values(
                by="fantasy_points_avg_last_week", ascending=False
            )[
                [
                    "player_name",
                    "positions",
                    "roster_pct_current",
                    "avg_salary_current",
                    "fantasy_points_avg_season_minus_one",
                    "fantasy_points_avg_last_week",
                ]
            ]
            .head(10)
            .reset_index(drop=True)
        )
        .tab_header(title="Top Players of Last Week")
        .tab_spanner(
            label="Trad FPPG",
            columns=[
                "fantasy_points_avg_last_week",
                "fantasy_points_avg_season_minus_one",
            ],
        )
        .tab_spanner(
            label="Player Info",
            columns=[
                "player_name",
                "positions",
                "roster_pct_current",
                "avg_salary_current",
            ],
        )
        .cols_label(
            player_name="Name",
            positions="Positions",
            roster_pct_current="Roster %",
            avg_salary_current="Avg Salary",
            fantasy_points_avg_last_week=f"Week {last_schedule_week+1}",
            fantasy_points_avg_season_minus_one=f"Weeks 1-{last_schedule_week}",
        )
        .fmt_number(
            columns=[
                "fantasy_points_avg_last_week",
                "fantasy_points_avg_season_minus_one",
            ],
            decimals=1,
        )
        .fmt_currency(columns=["avg_salary_current"], currency="USD")
        .fmt_percent(columns=["roster_pct_current"], decimals=1, scale_values=False)
        .cols_move_to_end("fantasy_points_avg_last_week")
        .data_color(
            columns=[
                "fantasy_points_avg_last_week",
                "fantasy_points_avg_season_minus_one",
            ],
            palette="PRGn",
            domain=[
                min(
                    comp_stat_values.fantasy_points_avg_season_minus_one.min(),
                    comp_stat_values.fantasy_points_avg_last_week.min(),
                ),
                max(
                    comp_stat_values.fantasy_points_avg_season_minus_one.max(),
                    comp_stat_values.fantasy_points_avg_last_week.max(),
                ),
            ],
        )
        .tab_source_note(
            source_note=md(
                "BlueSky: @wfordh | Traditional fantasy points: https://ottoneu.fangraphs.com/basketball/help/rosters_and_scoring"
            )
        )
    )

    # gt_best.save("analysis/images/weekly_performers_best.png")

    gt_diff = (
        GT(
            comp_stat_values.sort_values(by="trad_prod_diff", ascending=False)[
                [
                    "player_name",
                    "positions",
                    "roster_pct_current",
                    "avg_salary_current",
                    "fantasy_points_avg_season_minus_one",
                    "fantasy_points_avg_last_week",
                ]
            ]
            .head(10)
            .reset_index(drop=True)
        )
        .tab_header(
            title="Biggest Risers of Last Week",
            subtitle=f"Largest Difference in FPPG Between Week {last_schedule_week+1} and Weeks 1-{last_schedule_week}",
        )
        .tab_spanner(
            label="Trad FPPG",
            columns=[
                "fantasy_points_avg_last_week",
                "fantasy_points_avg_season_minus_one",
            ],
        )
        .tab_spanner(
            label="Player Info",
            columns=[
                "player_name",
                "positions",
                "roster_pct_current",
                "avg_salary_current",
            ],
        )
        .cols_label(
            player_name="Name",
            positions="Positions",
            roster_pct_current="Roster %",
            avg_salary_current="Avg Salary",
            fantasy_points_avg_last_week=f"Week {last_schedule_week+1}",
            fantasy_points_avg_season_minus_one=f"Weeks 1-{last_schedule_week}",
        )
        .fmt_number(
            columns=[
                "fantasy_points_avg_last_week",
                "fantasy_points_avg_season_minus_one",
            ],
            decimals=1,
        )
        .fmt_currency(columns=["avg_salary_current"], currency="USD")
        .fmt_percent(columns=["roster_pct_current"], decimals=1, scale_values=False)
        .cols_move_to_end("fantasy_points_avg_last_week")
        .data_color(
            columns=[
                "fantasy_points_avg_last_week",
                "fantasy_points_avg_season_minus_one",
            ],
            palette="PRGn",
            domain=[
                min(
                    comp_stat_values.fantasy_points_avg_season_minus_one.min(),
                    comp_stat_values.fantasy_points_avg_last_week.min(),
                ),
                max(
                    comp_stat_values.fantasy_points_avg_season_minus_one.max(),
                    comp_stat_values.fantasy_points_avg_last_week.max(),
                ),
            ],
        )
        .tab_source_note(
            source_note=md(
                "BlueSky: @wfordh | Traditional fantasy points: https://ottoneu.fangraphs.com/basketball/help/rosters_and_scoring"
            )
        )
    )

    # gt_diff.save("analysis/images/weekly_performers_diff.png")

    gt_fa = (
        GT(
            comp_stat_values.loc[comp_stat_values.roster_pct_current <= 50]
            .sort_values(by="fantasy_points_avg_last_week", ascending=False)[
                [
                    "player_name",
                    "positions",
                    "roster_pct_current",
                    "avg_salary_current",
                    "fantasy_points_avg_season_minus_one",
                    "fantasy_points_avg_last_week",
                ]
            ]
            .head(10)
            .reset_index(drop=True)
        )
        .tab_header(
            title="Best Free Agents of Last Week",
            subtitle="Rostered in 50% or less of leagues",
        )
        .tab_spanner(
            label="Trad FPPG",
            columns=[
                "fantasy_points_avg_last_week",
                "fantasy_points_avg_season_minus_one",
            ],
        )
        .tab_spanner(
            label="Player Info",
            columns=[
                "player_name",
                "positions",
                "roster_pct_current",
                "avg_salary_current",
            ],
        )
        .cols_label(
            player_name="Name",
            positions="Positions",
            roster_pct_current="Roster %",
            avg_salary_current="Avg Salary",
            fantasy_points_avg_last_week=f"Week {last_schedule_week+1}",
            fantasy_points_avg_season_minus_one=f"Weeks 1-{last_schedule_week}",
        )
        .fmt_number(
            columns=[
                "fantasy_points_avg_last_week",
                "fantasy_points_avg_season_minus_one",
            ],
            decimals=1,
        )
        .fmt_currency(columns=["avg_salary_current"], currency="USD")
        .fmt_percent(columns=["roster_pct_current"], decimals=1, scale_values=False)
        .cols_move_to_end("fantasy_points_avg_last_week")
        .data_color(
            columns=[
                "fantasy_points_avg_last_week",
                "fantasy_points_avg_season_minus_one",
            ],
            palette="PRGn",
            domain=[
                min(
                    comp_stat_values.fantasy_points_avg_season_minus_one.min(),
                    comp_stat_values.fantasy_points_avg_last_week.min(),
                ),
                max(
                    comp_stat_values.fantasy_points_avg_season_minus_one.max(),
                    comp_stat_values.fantasy_points_avg_last_week.max(),
                ),
            ],
        )
        .tab_source_note(
            source_note=md(
                "BlueSky: @wfordh | Traditional fantasy points: https://ottoneu.fangraphs.com/basketball/help/rosters_and_scoring"
            )
        )
    )

    # gt_fa.save("analysis/images/weekly_performers_free_agents.png")

    ## take this out when pushing to prod!!!
    logging.info("Creating the Discourse client object.")
    client = Discourse(
        base_url="https://community.ottoneu.com",
        username="higginsford",
        api_key=os.environ.get("DISCOURSE_API_KEY", None),
    )

    assert client.api_key
    topic_id = 15812
    logging.info("Making the tempfiles to save the tables to as images.")

    fp_best = tempfile.NamedTemporaryFile(suffix=".png")
    gt_best.save(fp_best.name)

    fp_fa = tempfile.NamedTemporaryFile(suffix=".png")
    gt_fa.save(fp_fa.name)

    fp_diff = tempfile.NamedTemporaryFile(suffix=".png")
    gt_diff.save(fp_diff.name)

    logging.info("Uploading the images to Discourse")
    response_best = discourse_img_upload(client, fp_best)
    response_diff = discourse_img_upload(client, fp_diff)
    response_fa = discourse_img_upload(client, fp_fa)

    content = f"![image|781x506]({response_best['short_url']})\n\n![image|781x506]({response_diff['short_url']})\n\n![image|781x506]({response_fa['short_url']})"
    data = {"topic_id": topic_id, "raw": content}
    logging.info("Posting to Discourse")
    client.posts.json.post(data)

    fp_best.close()
    fp_fa.close()
    fp_diff.close()


if __name__ == "__main__":
    main()
