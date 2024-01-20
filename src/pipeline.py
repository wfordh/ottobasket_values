"""
The pipeline for pulling the stats and deriving the values for each player, scoring
type, and minutes type. It forms the basis for the homepage of the app.
"""

from typing import Union

import pandas as pd
import streamlit as st

import darko
# all of the relative imports here
import drip
## not ideal, but will figure it out later
from transform import get_scoring_minutes_combo, prep_stats_df


# code for the pipeline here
@st.cache_data(ttl=12 * 60 * 60)  # type: ignore
def ottobasket_values_pipeline(
    save_df: bool = False, filter_cols: bool = True
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
        ros_df, how="left", on=join_cols, suffixes=["", "_ros"]
    ).merge(ytd_df, how="left", on=join_cols, suffixes=["", "_ytd"])
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

    if save_df:
        all_values_df.to_csv("./data/all_values_df.csv", index=False)
    return all_values_df


def main():
    ottobasket_values_pipeline(True)


if __name__ == "__main__":
    main()
