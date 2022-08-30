# split transform into files for merging and calculating stats?
import pandas as pd


def get_name_map():
    return pd.read_csv("./data/mappings.csv")


def get_hashtag_ros_projections():
    sheet_id = "1RiXnGk2OFnGRmW9QNQ_1CFde0xfSZpyC9Cn3OLLojsY"
    return pd.read_csv(
        f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&gid=284274620"
    )


def get_ottoneu_leaderboard():
    return pd.read_csv(
        "https://ottoneu.fangraphs.com/basketball/31/ajax/player_leaderboard?positions[]=G&positions[]=F&positions[]=C&minimum_minutes=0&sort_by=salary&sort_direction=DESC&free_agents_only=false&include_my_team=false&export=export"
    ).rename(columns={"id": "ottoneu_player_id"})


def combine_darko_drip_df(darko_df, drip_df, name_mapping):
    # everything is per 100 to start, so keep it there and translate to per game later
    # this won't work because need to make sure they're in the right order
    combined_df = darko_df.merge(
        name_mapping, how="inner", left_on="nba_id", right_on="nba_player_id"
    ).merge(drip_df, how="outer", left_on="stats_player_id", right_on="player_id")
    combined_df["points_100"] = combined_df[["pts_100_darko", "PTS_drip"]].mean(axis=1)
    combined_df["reb_100_darko"] = combined_df.orb_100_darko + combined_df.drb_100_darko
    combined_df["reb_100_drip"] = (
        combined_df.ORB_drip + combined_df.DRB_drip
    )  # do this earlier?
    combined_df["rebounds_100"] = combined_df[["reb_100_darko", "reb_100_drip"]].mean(
        axis=1
    )
    combined_df["assists_100"] = combined_df[["ast_100_darko", "AST_drip"]].mean(axis=1)
    combined_df["steals_100"] = combined_df[["stl_100_darko", "STL_drip"]].mean(axis=1)
    combined_df["blocks_100"] = combined_df[["blk_100_darko", "BLK_drip"]].mean(axis=1)
    combined_df["fga_100"] = combined_df[["fga_100_darko", "fga_drip"]].mean(axis=1)
    combined_df["fgm_100"] = combined_df[["fgm_100_darko", "fgm_drip"]].mean(axis=1)
    combined_df["fg_pct"] = combined_df.fgm_100 / combined_df.fga_100
    combined_df["fg3a_100"] = combined_df[["fg3a_100_darko", "fg3a_drip"]].mean(axis=1)
    combined_df["fg3m_100"] = combined_df[["fg3m_100_darko", "fg3m_drip"]].mean(axis=1)
    combined_df["fg3_pct"] = combined_df.fg3m_100 / combined_df.fg3a_100
    combined_df["fta_100"] = combined_df[["fta_100_darko", "fta_drip"]].mean(axis=1)
    combined_df["ftm_100"] = combined_df[["ftm_100_darko", "ftm_drip"]].mean(axis=1)
    combined_df["ft_pct"] = combined_df.ftm_100 / combined_df.fta_100
    combined_df["tov_100"] = combined_df[["tov_100_darko", "TOV_drip"]].mean(axis=1)

    keep_cols = [
        "name",
        "nba_player_id",
        "ottoneu_player_id",
        "hashtag_id",
        "tm_id",
        "ottoneu_position",
        "current_min",
        "fs_min",
        # "minutes_forecast",
        # "games_forecast",
        "minutes",
        # "minutes_ytd",
        "pace",
        "points_100",
        "rebounds_100",
        "assists_100",
        "steals_100",
        "blocks_100",
        "tov_100",
        "fga_100",
        "fgm_100",
        "fg_pct",
        "fg3a_100",
        "fg3m_100",
        "fg3_pct",
        "fta_100",
        "ftm_100",
        "ft_pct",
    ]

    # temporary fix - should update at some point
    return combined_df[keep_cols].rename(columns={"name": "player"})


def find_surplus_positions(fantasy_df, scoring_type):
    # Need to figure out the full strength thing here - 1/11/21
    fantasy_df["is_center"] = fantasy_df.ottoneu_position.str.contains("C").map(
        {False: None, True: True}
    )
    fantasy_df["is_forward"] = fantasy_df.ottoneu_position.str.contains("F").map(
        {False: None, True: True}
    )
    fantasy_df["is_guard"] = fantasy_df.ottoneu_position.str.contains("G").map(
        {False: None, True: True}
    )
    fantasy_df["center_rk"] = fantasy_df.groupby("is_center")[scoring_type].rank(
        ascending=False, na_option="bottom"
    )
    fantasy_df["forward_rk"] = fantasy_df.groupby("is_forward")[scoring_type].rank(
        ascending=False, na_option="bottom"
    )
    fantasy_df["guard_rk"] = fantasy_df.groupby("is_guard")[scoring_type].rank(
        ascending=False, na_option="bottom"
    )
    fantasy_df["center_rk"] = fantasy_df.apply(
        lambda row: row.center_rk if row.is_center else None, axis="columns"
    )
    fantasy_df["forward_rk"] = fantasy_df.apply(
        lambda row: row.forward_rk if row.is_forward else None, axis="columns"
    )
    fantasy_df["guard_rk"] = fantasy_df.apply(
        lambda row: row.guard_rk if row.is_guard else None, axis="columns"
    )
    # should I worry about ties? 1/11/21
    return (
        fantasy_df[["center_rk", "forward_rk", "guard_rk"]]
        .idxmin(axis="columns")
        .map({"center_rk": "C", "forward_rk": "F", "guard_rk": "G"})
    )


def get_draftable_players(
    fantasy_df,
    scoring_type,
    num_centers=12,
    num_forwards=24,
    num_guards=36,
    num_f_c=12,
    num_g_f=12,
    num_util=36,
):
    # Need to figure out the full strength thing here - 1/11/21
    draftable_players = list()
    draftable_players.extend(
        fantasy_df.loc[
            (fantasy_df.is_center) & (~fantasy_df.nba_player_id.isin(draftable_players))
        ]
        .sort_values(by=scoring_type, ascending=False)
        .nba_player_id.head(num_centers)
        .tolist()
    )
    draftable_players.extend(
        fantasy_df.loc[
            (fantasy_df.is_forward)
            & (~fantasy_df.nba_player_id.isin(draftable_players))
        ]
        .sort_values(by=scoring_type, ascending=False)
        .nba_player_id.head(num_forwards)
        .tolist()
    )
    draftable_players.extend(
        fantasy_df.loc[
            (fantasy_df.is_guard) & (~fantasy_df.nba_player_id.isin(draftable_players))
        ]
        .sort_values(by=scoring_type, ascending=False)
        .nba_player_id.head(num_guards)
        .tolist()
    )
    draftable_players.extend(
        fantasy_df.loc[
            ((fantasy_df.is_forward) | (fantasy_df.is_center))
            & (~fantasy_df.nba_player_id.isin(draftable_players))
        ]
        .sort_values(by=scoring_type, ascending=False)
        .nba_player_id.head(num_f_c)
        .tolist()
    )
    draftable_players.extend(
        fantasy_df.loc[
            ((fantasy_df.is_forward) | (fantasy_df.is_guard))
            & (~fantasy_df.nba_player_id.isin(draftable_players))
        ]
        .sort_values(by=scoring_type, ascending=False)
        .nba_player_id.head(num_g_f)
        .tolist()
    )
    draftable_players.extend(
        fantasy_df.loc[~fantasy_df.nba_player_id.isin(draftable_players)]
        .sort_values(by=scoring_type, ascending=False)
        .nba_player_id.head(num_util)
        .tolist()
    )

    return draftable_players
