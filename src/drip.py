"""
This file contains all the necessary functions for extracting and transforming
the projections coming from DRIP. All of the provided statistics are already in
a per 100 possessions format.
"""

from typing import List

import pandas as pd


def get_current_drip() -> pd.DataFrame:
    """Pulls the current DRIP projections online."""
    return pd.io.json.read_json(
        "https://dataviz.theanalyst.com/nba-stats-hub/drip.json"
    )


def get_drip_fga(drip_df: pd.DataFrame) -> pd.DataFrame:
    """Creates a field goal attempts column."""
    drip_df["fga"] = drip_df.PTS / (
        2 * drip_df.fg2_pct * (1 - drip_df["3PAr"])
        + 3 * drip_df.fg3_pct * drip_df["3PAr"]
        + drip_df.ft_pct * drip_df.FTr
    )
    return drip_df


def get_drip_fg_pct(drip_df: pd.DataFrame) -> pd.DataFrame:
    """Creates a field goal percentage column."""
    drip_df["fg_pct"] = (
        drip_df.fg2_pct * (1 - drip_df["3PAr"]) + drip_df.fg3_pct * drip_df["3PAr"]
    )
    return drip_df


def get_drip_fg3a(drip_df: pd.DataFrame) -> pd.DataFrame:
    """Creates a three point field goals attempted column."""
    drip_df["fg3a"] = drip_df.fga * drip_df["3PAr"]
    return drip_df


def get_drip_fg3m(drip_df: pd.DataFrame) -> pd.DataFrame:
    """Creates a three point field goals made column."""
    drip_df["fg3m"] = drip_df.fg3a * drip_df.fg3_pct
    return drip_df


def get_drip_fgm(drip_df: pd.DataFrame) -> pd.DataFrame:
    """Creates a field goals made column."""
    drip_df["fgm"] = drip_df.fga * drip_df.fg_pct
    return drip_df


def get_drip_fta(drip_df: pd.DataFrame) -> pd.DataFrame:
    """Creates a free throws attempted column."""
    drip_df["fta"] = drip_df.FTr * drip_df.fga
    return drip_df


def get_drip_ftm(drip_df: pd.DataFrame) -> pd.DataFrame:
    """Creates a free throws made column."""
    drip_df["ftm"] = drip_df.fta * drip_df.ft_pct
    return drip_df


def get_drip_reb(drip_df: pd.DataFrame) -> pd.DataFrame:
    """Creates a total rebounds column."""
    drip_df["reb"] = drip_df.ORB + drip_df.DRB
    return drip_df


def rename_drip_cols(drip_columns: List) -> List:
    """
    Adds the '_drip' suffix to some columns to help differentiating between
    DARKO and DRIP projections in downstream calculations.
    """
    ignore_cols = ["player", "player_id"]
    return [col + "_drip" if col not in ignore_cols else col for col in drip_columns]


def transform_drip(drip_df: pd.DataFrame) -> pd.DataFrame:
    keep_cols = [
        "player",
        "player_id",
        "PTS",
        "AST",
        "STL",
        "ORB",
        "DRB",
        "BLK",
        "TOV",
        "FT%",
        "3PT%",
        "2PT%",
        "3PAr",
        "FTr",
    ]
    drip_df.rename(
        columns={"FT%": "ft_pct", "3PT%": "fg3_pct", "2PT%": "fg2_pct"}, inplace=True
    )
    drip_df = (
        drip_df.pipe(get_drip_fga)
        .pipe(get_drip_fg_pct)
        .pipe(get_drip_fg3a)
        .pipe(get_drip_fg3m)
        .pipe(get_drip_fgm)
        .pipe(get_drip_fta)
        .pipe(get_drip_ftm)
        .pipe(get_drip_reb)
    )
    drip_df.columns = rename_drip_cols(drip_df.columns)

    return drip_df
