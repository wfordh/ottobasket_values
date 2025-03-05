import argparse
import logging
import os
import sys

import pandas as pd

sys.path.append(os.path.abspath("src"))

from leagues import get_average_values  # type: ignore
from utils import (_setup_gdrive, _upload_data,  # type: ignore
                   clean_avg_vals_df, get_name_map)

logging.basicConfig(level=logging.INFO)

parser = argparse.ArgumentParser()

parser.add_argument(
    "-s",
    "--save_method",
    help="Where to save the data. Local, GDrive, or not at all.",
    choices=["local", "gdrive"],
    type=str,
)


def get_ottoneu_player_universe():
    ottoverse = pd.read_csv("https://ottoneu.fangraphs.com/basketball/player_universe")
    ottoverse.columns = pd.Index(
        [col.lower().replace(" ", "_") for col in ottoverse.columns]
    )
    return ottoverse.rename(columns={"ottoneu_id": "ottoneu_player_id"})


def main():
    args = parser.parse_args()
    command_args = dict(vars(args))
    save_method = command_args.pop("save_method", None)

    ottoverse = get_ottoneu_player_universe()
    avg_values = clean_avg_vals_df(get_average_values())

    # can check check if ID is in avg values, no join necessary
    target = ottoverse.loc[
        ottoverse.ottoneu_player_id.isin(avg_values.ottoneu_player_id)
    ]
    target = target.loc[
        ((target.level == "NBA") & (target.team != "FA"))
    ]  # this is basically who the mapping should include

    mappings = get_name_map()
    player_pool = target.merge(
        mappings, on="ottoneu_player_id", how="left", suffixes=("_otto", "")
    )[
        [
            "name_otto",
            "level",
            "ottoneu_player_id",
            "name",
            "nba_player_id",
            "stats_player_id",
            "bref_id",
            "espn_id",
            "hashtag_id",
            "ottoneu_positions",
        ]
    ].rename(
        columns={"ottoneu_positions": "ottoneu_position"}
    )

    player_pool["name"] = player_pool.name.fillna(player_pool.name_otto)

    missing = player_pool.loc[
        (player_pool.level == "NBA")
        & (
            (player_pool.nba_player_id.isna())
            | (player_pool.stats_player_id.isna())
            | (player_pool.hashtag_id.isna())
        )
    ]

    logging.info(missing)

    if save_method == "local":
        missing.to_csv("data/test_mapping_update.csv", index=False)
    elif save_method == "gdrive":
        client_key_string = os.environ.get("SERVICE_BLOB", None)
        gc = _setup_gdrive(client_key_string)
        sheet_key = "1M5n0yZGIWbZSwrju2q014dGjvWJ1JQIsHanDyRaI0Sw"
        _upload_data(gc, missing, sheet_key, clear=True)


if __name__ == "__main__":
    main()
