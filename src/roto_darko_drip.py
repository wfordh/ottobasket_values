import pandas as pd


# prob just combine all of these at some point
def get_darko_fgm(darko_df):
    darko_df["fgm_100"] = darko_df.fg_pct * darko_df.fga_100
    return darko_df


def get_darko_fg3m(darko_df):
    darko_df["fg3m_100"] = darko_df.fg3a_100 * darko_df.fg3_pct
    return darko_df


def get_darko_ftm(darko_df):
    darko_df["ftm_100"] = darko_df.fta_100 * darko_df.ft_pct
    return darko_df


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


# combine through concat and collapse? would have to line up the columns correctly
# can't do straight average of FG% and FT% b/c of differences in number of attempts
# will have to use DARKO pace and minutes for converting DRIP to per game values
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
    # multiply by pace and minutes projections
    # map to point values
    # voila, per game projections
    # then need ottoneu positions in order to establish baseline # of players / posn
    # https://ottoneu.slack.com/archives/C03AH95K2/p1629141175006100
    keep_cols = [
        "player",
        "nba_player_id",
        "tm_id",
        "current_min",
        "fs_min",
        "minutes",
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
    return combined_df[keep_cols]


def calc_per_game_projections(stats_df):
    stats_df["possessions_played"] = stats_df.pace * stats_df.minutes / 48
    stats_df["pts_game"] = stats_df.points_100 * stats_df.possessions_played / 100
    stats_df["reb_game"] = stats_df.rebounds_100 * stats_df.possessions_played / 100
    stats_df["ast_game"] = stats_df.assists_100 * stats_df.possessions_played / 100
    stats_df["stl_game"] = stats_df.steals_100 * stats_df.possessions_played / 100
    stats_df["blk_game"] = stats_df.blocks_100 * stats_df.possessions_played / 100
    stats_df["tov_game"] = stats_df.tov_100 * stats_df.possessions_played / 100
    stats_df["fga_game"] = stats_df.fga_100 * stats_df.possessions_played / 100
    stats_df["fgm_game"] = stats_df.fgm_100 * stats_df.possessions_played / 100
    stats_df["fta_game"] = stats_df.fta_100 * stats_df.possessions_played / 100
    stats_df["ftm_game"] = stats_df.ftm_100 * stats_df.possessions_played / 100
    stats_df["fg3a_game"] = stats_df.fg3a_100 * stats_df.possessions_played / 100
    stats_df["fg3m_game"] = stats_df.fg3m_100 * stats_df.possessions_played / 100

    stats_df["possessions_played_fs"] = stats_df.pace * stats_df.fs_min / 48
    stats_df["pts_game_fs"] = stats_df.points_100 * stats_df.possessions_played_fs / 100
    stats_df["reb_game_fs"] = (
        stats_df.rebounds_100 * stats_df.possessions_played_fs / 100
    )
    stats_df["ast_game_fs"] = (
        stats_df.assists_100 * stats_df.possessions_played_fs / 100
    )
    stats_df["stl_game_fs"] = stats_df.steals_100 * stats_df.possessions_played_fs / 100
    stats_df["blk_game_fs"] = stats_df.blocks_100 * stats_df.possessions_played_fs / 100
    stats_df["tov_game_fs"] = stats_df.tov_100 * stats_df.possessions_played_fs / 100
    stats_df["fga_game_fs"] = stats_df.fga_100 * stats_df.possessions_played_fs / 100
    stats_df["fgm_game_fs"] = stats_df.fgm_100 * stats_df.possessions_played_fs / 100
    stats_df["fta_game_fs"] = stats_df.fta_100 * stats_df.possessions_played_fs / 100
    stats_df["ftm_game_fs"] = stats_df.ftm_100 * stats_df.possessions_played_fs / 100
    stats_df["fg3a_game_fs"] = stats_df.fg3a_100 * stats_df.possessions_played_fs / 100
    stats_df["fg3m_game_fs"] = stats_df.fg3m_100 * stats_df.possessions_played_fs / 100

    keep_cols = [
        "player",
        "nba_player_id",
        "tm_id",
        "Position",
        "minutes",
        "fs_min",
        "pts_game",
        "reb_game",
        "ast_game",
        "stl_game",
        "blk_game",
        "tov_game",
        "fga_game",
        "fgm_game",
        "fg3a_game",
        "fg3m_game",
        "fg_pct",
        "fg3_pct",
        "fta_game",
        "ftm_game",
        "pts_game_fs",
        "reb_game_fs",
        "ast_game_fs",
        "stl_game_fs",
        "blk_game_fs",
        "tov_game_fs",
        "fga_game_fs",
        "fgm_game_fs",
        "fg3a_game_fs",
        "fg3m_game_fs",
        "fta_game_fs",
        "ftm_game_fs",
    ]
    return stats_df[keep_cols]


simple_scoring_values = {
    "points": 1,
    "rebounds": 1,
    "assists": 1,
    "steals": 1,
    "blocks": 1,
    "turnovers": -1,
    "fga": 0,
    "fgm": 0,
    "fta": 0,
    "ftm": 0,
}

trad_scoring_values = {
    "points": 1,
    "rebounds": 1,
    "assists": 2,
    "steals": 4,
    "blocks": 4,
    "turnovers": -2,
    "fga": -1,
    "fgm": 2,
    "fta": -1,
    "ftm": 1,
}


def calc_fantasy_pts(stats_df, is_simple_scoring=True):
    scoring_dict = simple_scoring_values if is_simple_scoring else trad_scoring_values
    fantasy_df = stats_df.copy()
    fantasy_df["proj_fantasy_pts"] = (
        stats_df["pts_game"] * scoring_dict["points"]
        + stats_df["reb_game"] * scoring_dict["rebounds"]
        + stats_df["ast_game"] * scoring_dict["assists"]
        + stats_df["stl_game"] * scoring_dict["steals"]
        + stats_df["blk_game"] * scoring_dict["blocks"]
        + stats_df["tov_game"] * scoring_dict["turnovers"]
        + stats_df["fga_game"] * scoring_dict["fga"]
        + stats_df["fgm_game"] * scoring_dict["fgm"]
        + stats_df["fta_game"] * scoring_dict["fta"]
        + stats_df["ftm_game"] * scoring_dict["ftm"]
    )
    fantasy_df["roto_val"] = (
        stats_df["pts_game_fs"] * scoring_dict["points"]
        + stats_df["reb_game_fs"] * scoring_dict["rebounds"]
        + stats_df["ast_game_fs"] * scoring_dict["assists"]
        + stats_df["stl_game_fs"] * scoring_dict["steals"]
        + stats_df["blk_game_fs"] * scoring_dict["blocks"]
        + stats_df["tov_game_fs"] * scoring_dict["turnovers"]
        + stats_df["fga_game_fs"] * scoring_dict["fga"]
        + stats_df["fgm_game_fs"] * scoring_dict["fgm"]
        + stats_df["fta_game_fs"] * scoring_dict["fta"]
        + stats_df["ftm_game_fs"] * scoring_dict["ftm"]
    )
    return fantasy_df


def calc_surplus_by_position(df, position):
    if position == "guard":
        posn_df = df.loc[df.surplus_position == "G"]
        posn_repl_rank = 43
    elif position == "forward":
        posn_df = df.loc[df.surplus_position == "F"]
        posn_repl_rank = 37
    else:
        posn_df = df.loc[df.surplus_position == "C"]
        posn_repl_rank = 24


def calc_roto_value(df, is_full_strength=True):
    # ignoring rate stats for now...
    roto_cols = [
        "pts_game",
        "reb_game",
        "ast_game",
        "stl_game",
        "blk_game",
        "tov_game",
        "ftm_game",
        "fgm_game",
        "fga_game",
        "fg3m_game",
        "fg3a_game",
    ]
    if is_full_strength:
        roto_cols = [col + "_fs" for col in roto_cols]

    league_averages = df[roto_cols].mean()
    league_averages["fg_pct_fs"] = (
        league_averages["fgm_game_fs"] / league_averages["fga_game_fs"]
    )
    league_averages["fg3_pct_fs"] = (
        league_averages["fg3m_game_fs"] / league_averages["fg3a_game_fs"]
    )
    league_stdevs = df[roto_cols].std()
    value_df = df[["player", "nba_player_id"]].copy()
    value_df["aFGM"] = (
        df["fgm_game_fs"] - league_averages["fg_pct_fs"] * df["fga_game_fs"]
    )
    value_df["aFG3M"] = (
        df["fg3m_game_fs"] - league_averages["fg3_pct_fs"] * df["fg3a_game_fs"]
    )
    value_df["vPTS"] = (
        df["pts_game_fs"] - league_averages["pts_game_fs"]
    ) / league_stdevs["pts_game_fs"]
    value_df["vREB"] = (
        df["reb_game_fs"] - league_averages["reb_game_fs"]
    ) / league_stdevs["reb_game_fs"]
    value_df["vAST"] = (
        df["ast_game_fs"] - league_averages["ast_game_fs"]
    ) / league_stdevs["ast_game_fs"]
    value_df["vBLK"] = (
        df["blk_game_fs"] - league_averages["blk_game_fs"]
    ) / league_stdevs["blk_game_fs"]
    value_df["vSTL"] = (
        df["stl_game_fs"] - league_averages["stl_game_fs"]
    ) / league_stdevs["stl_game_fs"]
    # swap order for TOV? or actually maybe not?
    value_df["vTOV"] = (
        df["tov_game_fs"] - league_averages["tov_game_fs"]
    ) / league_stdevs["tov_game_fs"]
    value_df["vFTM"] = (
        df["ftm_game_fs"] - league_averages["ftm_game_fs"]
    ) / league_stdevs["ftm_game_fs"]
    value_df["vFGM"] = value_df.aFGM / value_df.aFGM.std()
    value_df["vFG3M"] = value_df.aFG3M / value_df.aFG3M.std()
    value_df["total_value"] = value_df.drop(
        ["player", "nba_player_id", "aFGM", "aFG3M"], axis=1
    ).sum(axis=1)
    print(value_df.head())
    # ignore positional adjustments for now since need surplus position so need to calc
    # later on than this
    # position_mins = value_df.groupby("surplus_position").total_value.min().to_dict()
    # value_df[
    #     "total_value_posn_adj"
    # ] = value_df.total_value + value_df.surplus_position.map(position_mins)
    value_df.to_csv("./data/roto_values_df.csv", index=False)
    return value_df.total_value


def main():
    current_darko_df = pd.read_csv(
        "https://docs.google.com/spreadsheets/d/1mhwOLqPu2F9026EQiVxFPIN1t9RGafGpl-dokaIsm9c/gviz/tq?tqx=out:csv&gid=284274620"
    )
    current_drip_df = pd.io.json.read_json(
        "https://dataviz.theanalyst.com/nba-stats-hub/drip.json"
    )
    current_darko_df = current_darko_df[
        [
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
    ]
    ignore_cols_darko = [
        "nba_id",
        "available",
        "tm_id",
        "current_min",
        "fs_min",
        "minutes",
        "pace",
    ]
    current_darko_df = get_darko_fgm(current_darko_df)
    current_darko_df = get_darko_fg3m(current_darko_df)
    current_darko_df = get_darko_ftm(current_darko_df)
    darko_cols = [
        col + "_darko" if col not in ignore_cols_darko else col
        for col in current_darko_df.columns
    ]
    current_darko_df.columns = darko_cols
    current_drip_df = current_drip_df[
        [
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
    ]
    current_drip_df.rename(
        columns={"FT%": "ft_pct", "3PT%": "fg3_pct", "2PT%": "fg2_pct"}, inplace=True
    )
    current_drip_df = get_drip_fga(current_drip_df)
    current_drip_df = get_drip_fg_pct(current_drip_df)
    current_drip_df = get_drip_fg3m(current_drip_df)
    current_drip_df = get_drip_fgm(current_drip_df)
    current_drip_df = get_drip_ft(current_drip_df)
    ignore_cols_drip = ["player", "player_id"]
    drip_cols = [
        col + "_drip" if col not in ignore_cols_drip else col
        for col in current_drip_df.columns
    ]
    current_drip_df.columns = drip_cols
    current_darko_df.to_csv("./data/darko.csv", index=False)
    current_drip_df.to_csv("./data/drip.csv", index=False)

    name_map = pd.read_csv("./data/drip_nba_id_mapping.csv")
    otto_nba = pd.read_csv("./data/otto_nba_id_merge.csv")
    otto_nba.rename(columns={"ID": "otto_id"}, inplace=True)
    stats_df = combine_darko_drip_df(current_darko_df, current_drip_df, name_map)
    stats_df = stats_df.merge(
        otto_nba.loc[
            otto_nba.otto_id.notna(),
            ["nba_player_id", "sr_player_id", "srus_player_id", "otto_id", "Position"],
        ],
        how="inner",
        on="nba_player_id",
    )
    stats_df = stats_df.loc[stats_df.nba_player_id.notna()].copy()

    per_game_df = calc_per_game_projections(stats_df)

    fantasy_pts_df = calc_fantasy_pts(per_game_df, is_simple_scoring=True)
    fantasy_pts_df["roto_val"] = calc_roto_value(fantasy_pts_df)

    # going with full strength projections so players who are out are included
    fantasy_pts_df["is_center"] = fantasy_pts_df.Position.str.contains("C").map(
        {False: None, True: True}
    )
    fantasy_pts_df["is_forward"] = fantasy_pts_df.Position.str.contains("F").map(
        {False: None, True: True}
    )
    fantasy_pts_df["is_guard"] = fantasy_pts_df.Position.str.contains("G").map(
        {False: None, True: True}
    )
    fantasy_pts_df["center_rk"] = fantasy_pts_df.groupby("is_center").roto_val.rank(
        ascending=False, na_option="bottom"
    )
    fantasy_pts_df["forward_rk"] = fantasy_pts_df.groupby("is_forward").roto_val.rank(
        ascending=False, na_option="bottom"
    )
    fantasy_pts_df["guard_rk"] = fantasy_pts_df.groupby("is_guard").roto_val.rank(
        ascending=False, na_option="bottom"
    )
    fantasy_pts_df["center_rk"] = fantasy_pts_df.apply(
        lambda row: row.center_rk if row.is_center else None, axis="columns"
    )
    fantasy_pts_df["forward_rk"] = fantasy_pts_df.apply(
        lambda row: row.forward_rk if row.is_forward else None, axis="columns"
    )
    fantasy_pts_df["guard_rk"] = fantasy_pts_df.apply(
        lambda row: row.guard_rk if row.is_guard else None, axis="columns"
    )
    fantasy_pts_df["surplus_position"] = (
        fantasy_pts_df[["center_rk", "forward_rk", "guard_rk"]]
        .idxmin(axis="columns")
        .map({"center_rk": "C", "forward_rk": "F", "guard_rk": "G"})
    )
    # slice DF into three - one for each position - now?
    salary_games_allotment = {
        "G": 138 / (138 + 120 + 76),
        "F": 120 / (138 + 120 + 76),
        "C": 76 / (138 + 120 + 76),
    }
    total_position_surplus = {
        "C": fantasy_pts_df.loc[
            (fantasy_pts_df.center_rk < 24) & (fantasy_pts_df.surplus_position == "C")
        ].roto_val.sum(),
        "F": fantasy_pts_df.loc[
            (fantasy_pts_df.forward_rk < 37) & (fantasy_pts_df.surplus_position == "F")
        ].roto_val.sum(),
        "G": fantasy_pts_df.loc[
            (fantasy_pts_df.guard_rk < 43) & (fantasy_pts_df.surplus_position == "G")
        ].roto_val.sum(),
    }

    center_surplus_factor = (
        salary_games_allotment["C"] * 4500 / total_position_surplus["C"]
    )
    forward_surplus_factor = (
        salary_games_allotment["F"] * 4500 / total_position_surplus["F"]
    )
    guard_surplus_factor = (
        salary_games_allotment["G"] * 4500 / total_position_surplus["G"]
    )
    # alternative method:
    # get top 12 C and add name/ID to list. Top 24 F and add. Top 36 G and add.
    # Top X from remaining C and F and add. Top Y from remaining F and G. Top Z from all remaining.
    # sum up fantasy points for those players and then divide 4500 by that total for the surplus factor
    draftable_players = list()
    draftable_players.extend(
        fantasy_pts_df.loc[
            (fantasy_pts_df.is_center)
            & (~fantasy_pts_df.nba_player_id.isin(draftable_players))
        ]
        .sort_values(by="roto_val", ascending=False)
        .nba_player_id.head(12)
        .tolist()
    )
    draftable_players.extend(
        fantasy_pts_df.loc[
            (fantasy_pts_df.is_forward)
            & (~fantasy_pts_df.nba_player_id.isin(draftable_players))
        ]
        .sort_values(by="roto_val", ascending=False)
        .nba_player_id.head(24)
        .tolist()
    )
    draftable_players.extend(
        fantasy_pts_df.loc[
            (fantasy_pts_df.is_guard)
            & (~fantasy_pts_df.nba_player_id.isin(draftable_players))
        ]
        .sort_values(by="roto_val", ascending=False)
        .nba_player_id.head(36)
        .tolist()
    )
    draftable_players.extend(
        fantasy_pts_df.loc[
            ((fantasy_pts_df.is_forward) | (fantasy_pts_df.is_center))
            & (~fantasy_pts_df.nba_player_id.isin(draftable_players))
        ]
        .sort_values(by="roto_val", ascending=False)
        .nba_player_id.head(12)
        .tolist()
    )
    draftable_players.extend(
        fantasy_pts_df.loc[
            ((fantasy_pts_df.is_forward) | (fantasy_pts_df.is_guard))
            & (~fantasy_pts_df.nba_player_id.isin(draftable_players))
        ]
        .sort_values(by="roto_val", ascending=False)
        .nba_player_id.head(12)
        .tolist()
    )
    draftable_players.extend(
        fantasy_pts_df.loc[~fantasy_pts_df.nba_player_id.isin(draftable_players)]
        .sort_values(by="roto_val", ascending=False)
        .nba_player_id.head(12)
        .tolist()
    )
    replacement_values = (
        fantasy_pts_df.loc[~fantasy_pts_df.nba_player_id.isin(draftable_players)]
        .groupby("surplus_position")
        .roto_val.max()
        .to_dict()
    )
    print(replacement_values)
    total_league_value = fantasy_pts_df.loc[
        fantasy_pts_df.nba_player_id.isin(draftable_players)
    ].roto_val.sum()
    surplus_factor = (4800 - len(draftable_players)) / total_league_value
    print(f"Total league value: {total_league_value}")
    print(f"Surplus factor: {surplus_factor}")

    # correct calculation is lower
    # fantasy_pts_df["surplus_value"] = (
    #     fantasy_pts_df.roto_val * surplus_factor + 1
    # )

    #     fantasy_pts_df.apply(
    #     lambda row: row.roto_val * center_surplus_factor
    #     if row.surplus_position == "C"
    #     else (
    #         row.roto_val * forward_surplus_factor
    #         if row.surplus_position == "F"
    #         else row.roto_val * guard_surplus_factor
    #     ),
    #     axis="columns",
    # )

    fantasy_pts_df["points_above_repl"] = fantasy_pts_df.apply(
        lambda row: row.roto_val - replacement_values["C"]
        if row.surplus_position == "C"
        else (
            row.roto_val - replacement_values["F"]
            if row.surplus_position == "F"
            else row.roto_val - replacement_values["G"]
        ),
        axis="columns",
    )
    total_league_value = fantasy_pts_df.loc[
        fantasy_pts_df.points_above_repl > 0
    ].points_above_repl.sum()
    surplus_factor = (
        4800 - len(fantasy_pts_df.loc[fantasy_pts_df.points_above_repl > 0])
    ) / total_league_value
    print(f"Total league value (take 2): {total_league_value}")
    print(f"Surplus factor (take 2): {surplus_factor}")
    fantasy_pts_df["surplus_value"] = (
        fantasy_pts_df.points_above_repl * surplus_factor + 1
    )

    fantasy_pts_df.to_csv("./data/ottoneu_fantasy_pts_roto.csv", index=False)


if __name__ == "__main__":
    main()
