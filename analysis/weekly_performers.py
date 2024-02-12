import logging
import os
import sys
from datetime import date, datetime, timedelta

import pandas as pd

sys.path.append(os.path.abspath("src"))

import darko  # type: ignore
import drip  # type: ignore
from leagues import get_average_values, get_league_leaderboard  # type: ignore
from transform import combine_darko_drip_df  # type: ignore
from transform import (get_hashtag_ros_projections, get_name_map,
                       get_scoring_minutes_combo)
from utils import _setup_gdrive, _upload_data  # type: ignore

LEAGUE_ID = 26


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
    avg_vals["ottoneu_av"] = avg_vals.ottoneu_av.str.replace("$", "").astype(float)
    try:
        avg_vals["ottoneu_roster_pct"] = avg_vals.ottoneu_roster_pct.str.replace(
            "%", ""
        ).astype(float)
    except AttributeError:
        pass

    return avg_vals


def prep_weekly_performers_stats_df(stats_segment_df: pd.DataFrame) -> pd.DataFrame:
    drip_df = drip.get_current_drip()
    drip_df = drip.transform_drip(drip_df)

    darko_df = darko.get_current_darko()
    darko_df = darko.transform_darko(darko_df)

    name_map = get_name_map()

    hashtag_minutes = get_hashtag_ros_projections()
    stats_df = combine_darko_drip_df(darko_df, drip_df, name_map)
    stats_df = stats_df.loc[stats_df.nba_player_id.notna()].copy()
    # stick with inner join for now
    stats_df = stats_df.merge(
        hashtag_minutes, left_on="hashtag_id", right_on="pid", how="left"
    ).merge(stats_segment_df, on="ottoneu_player_id", how="left", suffixes=("", "_ytd"))
    stats_df["total_ros_minutes"] = stats_df.minutes_forecast * stats_df.games_forecast
    return stats_df


def main():
    sheet_key = "15clwCO60P7lIxJU8B91tRRRZA7X0g7-tTqdnc-K1pa0"
    today = date.today().strftime("%Y-%m-%d")
    last_week = (date.today() - timedelta(days=7)).strftime("%Y-%m-%d")
    first_day_of_season = "2023-10-24"
    logging.info(f"Today: {today}")
    logging.info(f"Last Monday: {last_week}")

    current_avg_vals = get_average_values()
    current_avg_vals = clean_avg_vals_df(current_avg_vals)

    last_week_avg_vals = get_last_week_average_values(sheet_key)
    last_week_avg_vals = clean_avg_vals_df(last_week_avg_vals)

    last_week_stats = get_league_leaderboard(
        league_id=LEAGUE_ID, start_date=last_week, end_date=today
    )
    season_minus_week_stats = get_league_leaderboard(
        league_id=LEAGUE_ID, start_date=first_day_of_season, end_date=last_week
    )

    # analysis time
    ## roster stats
    avg_vals = current_avg_vals.merge(
        last_week_avg_vals,
        how="outer",
        on=["ottoneu_player_id", "name", "position"],
        suffixes=["_current", "_last_week"],
    )
    avg_vals["ottoneu_av_current"] = avg_vals["ottoneu_av_current"].fillna(0)
    avg_vals["ottoneu_av_last_week"] = avg_vals["ottoneu_av_last_week"].fillna(0)

    avg_vals["ottoneu_roster_pct_current"] = avg_vals[
        "ottoneu_roster_pct_current"
    ].fillna(0)
    avg_vals["ottoneu_roster_pct_last_week"] = avg_vals[
        "ottoneu_roster_pct_last_week"
    ].fillna(0)

    avg_vals["av_diff"] = avg_vals.ottoneu_av_current - avg_vals.ottoneu_av_last_week
    avg_vals["roster_diff"] = (
        avg_vals.ottoneu_roster_pct_current - avg_vals.ottoneu_roster_pct_last_week
    )
    avg_vals.fillna(0, inplace=True)

    ### pick out top and bottom five for each??
    top_riser_ids = list()
    top_riser_ids.extend(
        avg_vals.sort_values(by="av_diff", ascending=False)
        .ottoneu_player_id.head(10)
        .tolist()
    )
    top_riser_ids.extend(
        avg_vals.sort_values(by="roster_diff", ascending=False)
        .ottoneu_player_id.head(10)
        .tolist()
    )

    top_faller_ids = list()
    top_faller_ids.extend(
        avg_vals.sort_values(by="av_diff", ascending=True)
        .ottoneu_player_id.head(10)
        .tolist()
    )
    top_faller_ids.extend(
        avg_vals.sort_values(by="roster_diff", ascending=True)
        .ottoneu_player_id.head(10)
        .tolist()
    )

    ## game stats
    # feels like overkill but necessary w/ how get_scoring_minutes_combo is set up
    last_week_stats = prep_weekly_performers_stats_df(last_week_stats)
    season_minus_week_stats = prep_weekly_performers_stats_df(season_minus_week_stats)

    last_week_stat_values = get_scoring_minutes_combo("year_to_date", last_week_stats)
    season_minus_week_stat_values = get_scoring_minutes_combo(
        "year_to_date", season_minus_week_stats
    )
    stat_keep_cols = [
        "player",
        "ottoneu_player_id",
        "ottoneu_position",
        "games_played",
        "minutes",
        "simple_points",
        "simple_points_value",
        "trad_points",
        "trad_points_value",
        "categories",
        "categories_value",
    ]

    # also get games_played and minutes / minutes_avg from the leaderboard?
    comp_stat_values = last_week_stat_values[stat_keep_cols].merge(
        season_minus_week_stat_values[stat_keep_cols],
        how="outer",
        on=["player", "ottoneu_player_id", "ottoneu_position"],
        suffixes=["_last_week", "_season_minus_one"],
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

    comp_stat_values["simple_prod_diff"] = (
        comp_stat_values.simple_points_last_week
        / comp_stat_values.games_played_last_week
    ) / (
        comp_stat_values.simple_points_season_minus_one
        / comp_stat_values.games_played_season_minus_one
    )
    comp_stat_values["simple_value_diff"] = (
        comp_stat_values.simple_points_value_last_week
        - comp_stat_values.simple_points_value_season_minus_one
    )

    comp_stat_values["trad_prod_diff"] = (
        comp_stat_values.trad_points_last_week / comp_stat_values.games_played_last_week
    ) / (
        comp_stat_values.trad_points_season_minus_one
        / comp_stat_values.games_played_season_minus_one
    )
    comp_stat_values["trad_value_diff"] = (
        comp_stat_values.trad_points_value_last_week
        - comp_stat_values.trad_points_value_season_minus_one
    )

    comp_stat_values["cats_prod_diff"] = (
        comp_stat_values.categories_last_week / comp_stat_values.games_played_last_week
    ) / (
        comp_stat_values.categories_season_minus_one
        / comp_stat_values.games_played_season_minus_one
    )
    comp_stat_values["cats_value_diff"] = (
        comp_stat_values.categories_value_last_week
        - comp_stat_values.categories_value_season_minus_one
    )
    comp_stat_values.fillna(0, inplace=True)

    ### pick out players over some sort of threshold??

    ### do some sort of formatting for the selected players?
    ### how do I deliver the results? another google sheet? slack? email?
    top_performer_ids = list()
    top_performer_ids.extend(
        comp_stat_values.sort_values(by="simple_prod_diff", ascending=True)
        .ottoneu_player_id.head()
        .tolist()
    )
    top_performer_ids.extend(
        comp_stat_values.sort_values(by="simple_value_diff", ascending=True)
        .ottoneu_player_id.head()
        .tolist()
    )
    top_performer_ids.extend(
        comp_stat_values.sort_values(by="trad_prod_diff", ascending=True)
        .ottoneu_player_id.head()
        .tolist()
    )
    top_performer_ids.extend(
        comp_stat_values.sort_values(by="trad_value_diff", ascending=True)
        .ottoneu_player_id.head()
        .tolist()
    )
    top_performer_ids.extend(
        comp_stat_values.sort_values(by="cats_prod_diff", ascending=True)
        .ottoneu_player_id.head()
        .tolist()
    )
    top_performer_ids.extend(
        comp_stat_values.sort_values(by="cats_value_diff", ascending=True)
        .ottoneu_player_id.head()
        .tolist()
    )

    bottom_performer_ids = list()
    bottom_performer_ids.extend(
        comp_stat_values.sort_values(by="simple_prod_diff", ascending=False)
        .ottoneu_player_id.head()
        .tolist()
    )
    bottom_performer_ids.extend(
        comp_stat_values.sort_values(by="simple_value_diff", ascending=False)
        .ottoneu_player_id.head()
        .tolist()
    )
    bottom_performer_ids.extend(
        comp_stat_values.sort_values(by="trad_prod_diff", ascending=False)
        .ottoneu_player_id.head()
        .tolist()
    )
    bottom_performer_ids.extend(
        comp_stat_values.sort_values(by="trad_value_diff", ascending=False)
        .ottoneu_player_id.head()
        .tolist()
    )
    bottom_performer_ids.extend(
        comp_stat_values.sort_values(by="cats_prod_diff", ascending=False)
        .ottoneu_player_id.head()
        .tolist()
    )
    bottom_performer_ids.extend(
        comp_stat_values.sort_values(by="cats_value_diff", ascending=False)
        .ottoneu_player_id.head()
        .tolist()
    )

    # upload current_avg_vals to drive in place of the old one
    client_key_string = os.environ.get("SERVICE_BLOB", None)
    gc = _setup_gdrive(client_key_string)
    _upload_data(gc, current_avg_vals, sheet_key, wks_num=0, clear=True)
    _upload_data(
        gc,
        avg_vals.loc[avg_vals.ottoneu_player_id.isin(top_riser_ids)],
        sheet_key=sheet_key,
        wks_num=1,
        clear=True,
    )
    _upload_data(
        gc,
        avg_vals.loc[avg_vals.ottoneu_player_id.isin(top_faller_ids)],
        sheet_key=sheet_key,
        wks_num=2,
        clear=True,
    )
    _upload_data(
        gc,
        comp_stat_values.loc[
            comp_stat_values.ottoneu_player_id.isin(top_performer_ids)
        ],
        sheet_key=sheet_key,
        wks_num=3,
        clear=True,
    )
    _upload_data(
        gc,
        comp_stat_values.loc[
            comp_stat_values.ottoneu_player_id.isin(bottom_performer_ids)
        ],
        sheet_key=sheet_key,
        wks_num=4,
        clear=True,
    )


if __name__ == "__main__":
    main()
