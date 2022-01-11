import pandas as pd

def get_current_darko():
	return pd.read_csv(
        "https://docs.google.com/spreadsheets/d/1mhwOLqPu2F9026EQiVxFPIN1t9RGafGpl-dokaIsm9c/gviz/tq?tqx=out:csv&gid=284274620"
    )

def get_darko_fgm(darko_df):
    darko_df["fgm_100"] = darko_df.fg_pct * darko_df.fga_100
    return darko_df


def get_darko_fg3m(darko_df):
    darko_df["fg3m_100"] = darko_df.fg3a_100 * darko_df.fg3_pct
    return darko_df


def get_darko_ftm(darko_df):
    darko_df["ftm_100"] = darko_df.fta_100 * darko_df.ft_pct
    return darko_df

def rename_darko_cols(darko_columns):
	ignore_cols = [
        "nba_id",
        "available",
        "tm_id",
        "current_min",
        "fs_min",
        "minutes",
        "pace",
    ]
	return [
        col + "_darko" if col not in ignore_cols else col
        for col in darko_columns
    ]
    

def transform_darko_df(darko_df):
	keep_cols = [
            "nba_id",
            "available",
            "tm_id",
            "current_min",
            "fs_min",
            "minutes",
            "pace",
            "pts_100",
            "orb_100",
            "drb_100",
            "ast_100",
            "blk_100",
            "stl_100",
            "tov_100",
            "fga_100",
            "fta_100",
            "fg3a_100",
            "fg_pct",
            "fg3_pct",
            "ft_pct",
        ]
    

    darko_df = darko_df[keep_cols]
    # trying pipe, not sure if this will work...
    darko_df = darko_df.pipe(get_darko_fgm).pipe(get_darko_fg3m).pipe(get_darko_ftm)
    darko_df.columns = rename_darko_cols(darko_df.columns)

    return darko_df