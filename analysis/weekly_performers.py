import logging
import os
import sys
from datetime import date, datetime, timedelta

import pandas as pd
from great_tables import GT

sys.path.append(os.path.abspath("src"))

from leagues import get_average_values, get_league_leaderboard  # type: ignore

LEAGUE_ID = 39  # must be trad points league


def get_last_week_average_values(sheet_key: str) -> pd.DataFrame:
    return pd.read_csv(
        f"https://docs.google.com/spreadsheets/d/{sheet_key}/gviz/tq?tqx=out:csv&gid=284274620"
    )


def clean_avg_vals_df(avg_vals: pd.DataFrame) -> pd.DataFrame:
    avg_vals_cols = [
        col.replace("(", "").replace(")", "").replace(" ", "_").replace("%", "_pct")
        for col in avg_vals.columns
    ]
    avg_vals.columns = pd.Index(avg_vals_cols)
    avg_vals["avg_salary"] = avg_vals.avg_salary.str.replace("$", "").astype(float)
    try:
        avg_vals["roster_pct"] = avg_vals.roster_pct.str.replace("%", "").astype(float)
    except AttributeError:
        logging.info("Could not adjust 'roster pct' column!")
        pass

    return avg_vals


def main():
    sheet_key = "15clwCO60P7lIxJU8B91tRRRZA7X0g7-tTqdnc-K1pa0"
    today = date.today().strftime("%Y-%m-%d")
    last_week = (date.today() - timedelta(days=7)).strftime("%Y-%m-%d")
    first_day_of_season = "2024-10-22"
    logging.info(f"Today: {today}")
    logging.info(f"Last Monday: {last_week}")

    avg_vals = get_average_values()
    avg_vals = clean_avg_vals_df(avg_vals)

    # last_week_avg_vals = get_last_week_average_values(sheet_key)
    # last_week_avg_vals = clean_avg_vals_df(last_week_avg_vals)

    last_week_stats = get_league_leaderboard(
        league_id=LEAGUE_ID, start_date=last_week, end_date=today
    )
    season_minus_week_stats = get_league_leaderboard(
        league_id=LEAGUE_ID, start_date=first_day_of_season, end_date=last_week
    )

    avg_vals.to_csv("data/test_current_avg_vals.csv", index=False)
    print(avg_vals.isna().sum())

    # analysis time
    ## roster stats
    avg_vals["avg_salary_current"] = avg_vals["avg_salary"].fillna(0)

    avg_vals["roster_pct_current"] = avg_vals["roster_pct"].fillna(0)

    avg_vals.fillna(0, inplace=True)

    print(
        avg_vals.loc[avg_vals.name.isin(["Amen Thompson", "Josh Hart", "Jayson Tatum"])]
    )

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

    print(
        comp_stat_values.loc[
            comp_stat_values.player_name.isin(
                ["Amen Thompson", "Josh Hart", "Jayson Tatum"]
            )
        ]
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
    gt = (
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
            ].head(
                10
            )
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
            fantasy_points_avg_last_week="Last Week",
            fantasy_points_avg_season_minus_one="Before Last Week",
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
    )

    gt.save("analysis/images/weekly_performers_best.png")

    gt = (
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
            ].head(10)
        )
        .tab_header(
            title="Biggest Risers of Last Week",
            subtitle="Largest Difference in FPPG Between Last Week and Season Before Last Week",
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
            fantasy_points_avg_last_week="Last Week",
            fantasy_points_avg_season_minus_one="Before Last Week",
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
    )

    gt.save("analysis/images/weekly_performers_diff.png")

    gt = (
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
            fantasy_points_avg_last_week="Last Week",
            fantasy_points_avg_season_minus_one="Before Last Week",
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
    )

    gt.save("analysis/images/weekly_performers_free_agents.png")


if __name__ == "__main__":
    main()
