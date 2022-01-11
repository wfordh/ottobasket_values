import pandas as pd

def get_current_drip():
	return pd.io.json.read_json(
        "https://dataviz.theanalyst.com/nba-stats-hub/drip.json"
    )

def get_drip_fga(drip_df):
    drip_df["fga"] = drip_df.PTS / (
        2 * drip_df.fg2_pct * (1 - drip_df["3PAr"])
        + 3 * drip_df.fg3_pct * drip_df["3PAr"]
        + drip_df.ft_pct * drip_df.FTr
    )
    return drip_df


def get_drip_fg_pct(drip_df):
    drip_df["fg_pct"] = (
        drip_df.fg2_pct * (1 - drip_df["3PAr"]) + drip_df.fg3_pct * drip_df["3PAr"]
    )
    return drip_df


# get DRIP 3pm from fga, 3PAr, and 3p_pct
def get_drip_fg3m(drip_df):
    drip_df["fg3a"] = drip_df.fga * drip_df["3PAr"]
    drip_df["fg3m"] = drip_df.fg3a * drip_df.fg3_pct
    return drip_df


def get_drip_fgm(drip_df):
    drip_df["fgm"] = drip_df.fga * drip_df.fg_pct
    return drip_df


def get_drip_ft(drip_df):
    drip_df["fta"] = drip_df.FTr * drip_df.fga
    drip_df["ftm"] = drip_df.fta * drip_df.ft_pct
    return drip_df

def rename_drip_cols(drip_columns):
	ignore_cols = ["player", "player_id"]
    return [
        col + "_drip" if col not in ignore_cols else col
        for col in drip_columns
    ]

def transform_drip(drip_df):
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
    drip_df = drip_df.pipe(get_drip_fga).pipe(get_drip_fg_pct).pipe(get_drip_fg3m).pipe(get_drip_fgm).pipe(get_drip_ft)
    drip_df.columns = rename_drip_cols(drip_df.columns)

    return drip_df
