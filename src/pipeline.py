"""
The pipeline for pulling the stats and deriving the values for each player, scoring
type, and minutes type. It forms the basis for the homepage of the app.
"""

import argparse
import logging
import os
from datetime import datetime
from typing import Union
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

import darko
# all of the relative imports here
import drip
## not ideal, but will figure it out later
from transform import get_scoring_minutes_combo, prep_stats_df  # type: ignore
from utils import _setup_gdrive, _upload_data  # type: ignore

logging.basicConfig(level=logging.INFO)

parser = argparse.ArgumentParser()

parser.add_argument(
    "-s",
    "--save_method",
    help="Where to save the data. Local, GDrive, or not at all.",
    choices=["local", "gdrive"],
    type=str,
)


# code for the pipeline here
@st.cache_data(ttl=12 * 60 * 60)  # type: ignore
def ottobasket_values_pipeline(
    save_method: Union[str, None] = "local", filter_cols: bool = True
) -> Union[None, pd.DataFrame]:
    stats_df = prep_stats_df()

    # current
    current_minutes_df = get_scoring_minutes_combo("current", stats_df)

    # rest of season
    ros_df = get_scoring_minutes_combo("rest_of_season", stats_df)

    # year to date
    ytd_df = get_scoring_minutes_combo("year_to_date", stats_df)

    join_cols = [
        "player",
        "nba_player_id",
        "ottoneu_player_id",
        "tm_id",
        "ottoneu_position",
        "minutes",
        "total_ros_minutes",
        "minutes_ytd",
    ]
    all_values_df = current_minutes_df.merge(
        ros_df, how="left", on=join_cols, suffixes=("", "_ros")
    ).merge(ytd_df, how="left", on=join_cols, suffixes=("", "_ytd"))
    # need to rename the columns from the base dataframe in the merge
    # to accurately reflect their source
    all_values_df.rename(
        columns={
            "simple_points_value": "simple_points_value_current",
            "categories_value": "categories_value_current",
            "trad_points_value": "trad_points_value_current",
        },
        inplace=True,
    )
    if filter_cols:
        all_values_df = all_values_df[
            join_cols + [col for col in all_values_df.columns if "value" in col]
        ]
    all_values_df.drop_duplicates(inplace=True)
    all_values_df = all_values_df.loc[
        (all_values_df.total_ros_minutes > 0) | (all_values_df.minutes_ytd > 0)
    ]

    if save_method == "local":
        logging.info("Saving locally!")
        all_values_df.to_csv("./data/all_values_df.csv", index=False)
    elif save_method == "gdrive":
        logging.info("Uploading to GDrive!")
        client_key_string = os.environ.get("SERVICE_BLOB", None)
        gc = _setup_gdrive(client_key_string)
        sheet_key = "1GgwZpflcyoRYMP0yL2hrbNwndJjVFm34x3jXnUooSfA"
        _upload_data(gc, all_values_df, sheet_key, clear=True)

        # add the run date
        now = datetime.now(tz=ZoneInfo("US/Pacific")).strftime("%Y-%m-%d %H:%M:%S")
        now_df = pd.DataFrame([now], columns=["most_recent_run"])
        _upload_data(gc, now_df, sheet_key, wks_num=1, clear=False)
    return all_values_df


def main():
    args = parser.parse_args()
    command_args = dict(vars(args))
    save_method = command_args.pop("save_method", None)
    logging.info(f"Save method is {save_method}")
    ottobasket_values_pipeline(save_method)


if __name__ == "__main__":
    main()
