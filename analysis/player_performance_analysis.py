# mypy: ignore-errors
import argparse
import math
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.append(os.path.abspath("src"))

import numpy as np
import pandas as pd
from great_tables import GT, loc, md, style
from lets_plot import geom_abline  # type: ignore
from lets_plot import (aes, coord_cartesian, geom_area_ridges, geom_density,
                       geom_point, geom_vline, ggplot, labs)
from nba_api.stats.endpoints import (leaguedashteamstats,  # type: ignore
                                     playergamelogs)
from nba_api.stats.static import teams  # type: ignore

from calc_stats import calc_fantasy_pts  # type: ignore

parser = argparse.ArgumentParser()

# add season
parser.add_argument(
    "-s", "--season", type=str, help="Season, in the form 20XX-XY", required=True
)


def get_opponent(row: pd.Series):
    opponent = None
    if row.is_home:
        opponent = row.MATCHUP.split("vs.")[-1].strip()
    else:
        opponent = row.MATCHUP.split("@")[-1].strip()
    return opponent


def extract_data(season: str):
    player_games = playergamelogs.PlayerGameLogs(
        season_nullable=season
    ).get_data_frames()[0]

    # home games
    player_games["is_home"] = player_games.MATCHUP.str.contains("vs.")

    player_games["opponent"] = player_games.apply(get_opponent, axis=1)
    team_abbrev_id_map = {
        team["abbreviation"]: team["id"] for team in teams.get_teams()
    }

    player_games["opposing_team_id"] = player_games.opponent.map(team_abbrev_id_map)

    # b2b games
    convert_time = lambda x: datetime.strptime(x, "%Y-%m-%dT%H:%M:%S")
    player_games["GAME_DATE"] = player_games.GAME_DATE.apply(convert_time)
    player_grps = player_games.groupby(["PLAYER_ID", "PLAYER_NAME"])
    diffs_list = list()
    for player_info, player_df in player_grps:
        game_date_diffs = player_df.GAME_DATE - player_df.shift(-1).GAME_DATE
        diffs_list.append(game_date_diffs)

    player_games = player_games.merge(
        pd.concat(diffs_list),
        left_index=True,
        right_index=True,
        suffixes=["", "_dt_diff"],
    )

    player_games["is_b2b"] = player_games.GAME_DATE_dt_diff.eq(pd.Timedelta("1 days"))

    minutes_summary = player_games.groupby(["PLAYER_ID", "PLAYER_NAME"])["MIN"].agg(
        ["mean", "std", "sum"]
    )
    team_adv_stats = leaguedashteamstats.LeagueDashTeamStats(
        season=season, measure_type_detailed_defense="Advanced"
    ).get_data_frames()[0]

    player_games.drop(
        [col for col in player_games.columns if "RANK" in col], axis=1, inplace=True
    )

    player_games = player_games.merge(
        team_adv_stats[["TEAM_ID", "DEF_RATING", "DEF_RATING_RANK"]],
        how="inner",
        left_on="opposing_team_id",
        right_on="TEAM_ID",
        suffixes=["", "_adv_stats"],
    )

    # add trad points calculation
    # time to drop a lot of columns and change to lowercase?
    player_games.rename(
        columns={
            "PTS": "pts_game",
            "AST": "ast_game",
            "REB": "reb_game",
            "BLK": "blk_game",
            "STL": "stl_game",
            "TOV": "tov_game",
            "FGM": "fgm_game",
            "FGA": "fga_game",
            "FTM": "ftm_game",
            "FTA": "fta_game",
        },
        inplace=True,
    )

    player_games["trad_pts"] = calc_fantasy_pts(player_games, is_simple_scoring=False)
    return player_games


def calc_dimension_diffs(df: pd.DataFrame, dim: str):
    baseline = df.groupby(dim).agg({"trad_pts": "mean", "MIN": "mean"}).reset_index()

    player_cols = ["PLAYER_NAME"]
    dim_df = df.groupby(player_cols + [dim]).agg(
        {
            "trad_pts": "mean",
            "MIN": "mean",
            "GAME_ID": "count",
            "DEF_RATING_RANK": "mean",
        }
    )
    wide_df = dim_df.reset_index().pivot(index=player_cols, columns=dim)
    if dim in ["is_b2b", "is_home"]:
        wide_df["trad_pts_diff"] = (
            wide_df["trad_pts"][True] - wide_df["trad_pts"][False]
        )
        new_df = wide_df.reset_index()
        new_df.columns = pd.Index(
            [
                "PLAYER_NAME",
                f"trad_pts_no_{dim}",
                f"trad_pts_yes_{dim}",
                f"MIN_no_{dim}",
                f"MIN_yes_{dim}",
                f"num_games_no_{dim}",
                f"num_games_yes_{dim}",
                f"avg_def_rtg_rk_no_{dim}",
                f"avg_def_rtg_rk_yes_{dim}",
                "trad_pts_diff",
            ]
        )
    else:
        # how to do this for bums?
        wide_df["trad_pts_diff_good_mid"] = (
            wide_df["trad_pts"]["good"] - wide_df["trad_pts"]["mid"]
        )
        wide_df["trad_pts_diff_mid_bum"] = (
            wide_df["trad_pts"]["mid"] - wide_df["trad_pts"]["bum"]
        )
        wide_df["trad_pts_diff_good_bum"] = (
            wide_df["trad_pts_diff_good_mid"] + wide_df["trad_pts_diff_mid_bum"]
        )
        new_df = wide_df.reset_index()
        # columns
        new_df.columns = pd.Index(
            [
                "PLAYER_NAME",
                "trad_pts_bum",
                "trad_pts_good",
                "trad_pts_mid",
                "MIN_bum",
                "MIN_good",
                "MIN_mid",
                "num_games_bum",
                "num_games_good",
                "num_games_mid",
                "avg_def_rtg_rk_bum",
                "avg_def_rtg_rk_good",
                "avg_def_rtg_rk_mid",
                "trad_pts_diff_good_mid",
                "trad_pts_diff_mid_bum",
                "trad_pts_diff_good_bum",
            ]
        )
    return new_df


def create_dim_table(df, dim: str, title: str, comp: str = ""):
    # prob want to adjust title somehow
    # add sort logic? or do outside of the function?
    if dim == "is_b2b":
        no_tab_label = "Non B2B"
        yes_tab_label = "Yes B2B"
    elif dim == "is_home":
        no_tab_label = "Away"
        yes_tab_label = "Home"
    elif dim == "bum_status":
        if comp == "good_bum":
            no_tab_label = "Bum"
            yes_tab_label = "Good"
        elif comp == "good_mid":
            no_tab_label = "Mid"
            yes_tab_label = "Good"
    # if dim in ["is_b2b", "is_home"]:
    #     fp_tab_cols = [f"trad_pts_no_{dim}", f"trad_pts_yes_{dim}", "trad_pts_diff"]
    #     min_tab_cols = [f"MIN_no_{dim}", f"MIN_yes_{dim}"]
    # else:
    #     fp_tab_cols = ["trad_pts_bum", "trad_pts_good", 'trad_pts_mid',
    #         "trad_pts_diff_good_mid",
    #         'trad_pts_diff_mid_bum',
    #         "trad_pts_diff_good_bum"
    #     ]
    #     min_tab_cols = ["MIN_bum", "MIN_good", "MIN_mid"]
    gt = (
        GT(df)
        .tab_header(title=title, subtitle="Traditional Fantasy Points")
        .tab_spanner(
            label=yes_tab_label,
            columns=[
                f"trad_pts_yes_{dim}",
                f"MIN_yes_{dim}",
                f"num_games_yes_{dim}",
                f"avg_def_rtg_rk_yes_{dim}",
            ],
        )
        .tab_spanner(
            label=no_tab_label,
            columns=[
                f"trad_pts_no_{dim}",
                f"MIN_no_{dim}",
                f"num_games_no_{dim}",
                f"avg_def_rtg_rk_no_{dim}",
            ],
        )
        .cols_move(
            columns=[
                f"MIN_no_{dim}",
                f"trad_pts_no_{dim}",
                f"num_games_no_{dim}",
                f"avg_def_rtg_rk_no_{dim}",
            ],
            after="PLAYER_NAME",
        )
        .cols_move(
            columns=[
                f"MIN_yes_{dim}",
                f"trad_pts_yes_{dim}",
                f"num_games_yes_{dim}",
                f"avg_def_rtg_rk_yes_{dim}",
            ],
            after=f"avg_def_rtg_rk_no_{dim}",
        )
        .fmt_number(
            columns=[
                f"trad_pts_no_{dim}",
                f"trad_pts_yes_{dim}",
                f"MIN_no_{dim}",
                f"MIN_yes_{dim}",
                f"avg_def_rtg_rk_no_{dim}",
                f"avg_def_rtg_rk_yes_{dim}",
            ],
            decimals=1,
        )
        .fmt_integer(columns=[f"num_games_no_{dim}", f"num_games_yes_{dim}"])
        .fmt_number(columns="trad_pts_diff", decimals=2)
        .tab_source_note(
            source_note=md(
                "Traditional fantasy points: https://ottoneu.fangraphs.com/basketball/help/rosters_and_scoring"
            )
        )
        # .tab_stubhead(label="Player")
    )
    return gt


def create_dim_scatter(df, dim: str):
    if dim == "is_b2b":
        x_lab = "Not B2B"
        y_lab = "Yes B2B"
        x_data = "trad_pts_no_is_b2b"
        y_data = "trad_pts_yes_is_b2b"
        title = "Scoring by Back to Back Status"
    elif dim == "is_home":
        x_lab = "Home"
        y_lab = "Away"
        x_data = "trad_pts_yes_is_home"
        y_data = "trad_pts_no_is_home"
        title = "Scoring in Home and Away Games"
    else:
        x_lab = ""
        y_lab = ""
    ax_lim_min = 5 * math.floor(
        min(df[f"trad_pts_no_{dim}"].min(), df[f"trad_pts_yes_{dim}"].min()) / 5
    )
    ax_lim_max = 5 * math.ceil(
        max(df[f"trad_pts_no_{dim}"].max(), df[f"trad_pts_yes_{dim}"].max()) / 5
    )
    m, c = np.linalg.lstsq(
        np.vstack(
            [np.array(df[f"trad_pts_no_{dim}"]), np.ones(len(df[f"trad_pts_no_{dim}"]))]
        ).T,
        np.array(df[f"trad_pts_yes_{dim}"]),
        rcond=1,
    )[0]
    return (
        ggplot(df, aes(x=x_data, y=y_data))
        + geom_point()
        + labs(
            x=x_lab,
            y=y_lab,
            subtitle="Traditional Fantasy Points",
            title=title,
            caption="Red line: y=x. Blue line: line of best fit.",
        )
        + coord_cartesian(xlim=(ax_lim_min, ax_lim_max), ylim=(ax_lim_min, ax_lim_max))
        + geom_abline(slope=1, color="red", linetype="longdash")
        + geom_abline(slope=m, intercept=c, color="blue")
    )


def create_dim_diff_distribution(df, dim: str):
    mean = df.trad_pts_diff.mean()
    if dim == "is_b2b":
        x_lab = "Diff (Non B2B - Yes B2B)"
        y_lab = "Yes B2B"
        title = "Scoring Differential by Back to Back Status"
    elif dim == "is_home":
        x_lab = "Diff (Home - Away)"
        y_lab = "Away"
        title = "Scoring Differential in Home and Away Games"
    else:
        x_lab = ""
        y_lab = ""
    return (
        ggplot(df, aes(x="trad_pts_diff"))
        # + geom_histogram()
        + geom_density()
        + geom_vline(xintercept=mean, color="red", linetype="longdash")
        + labs(x=x_lab, y="", title=title, subtitle="Traditional Fantasy Points")
    )


def main():
    """
    PSEUDOCODE
    - get player game logs
    - calc fantasy points (trad)
    - pull opponent and home / away from game log
            - derive if B2B
    - get team defensive ratings and attach opponents' rank and rating
    - visualize?
    - is bumslaying predictive? do young players who bumslay then get gud?
    - use net rating instead of def rating since blocks and steals are
        included in tPTS

    - repl level just over 21 ppg
    """
    args = parser.parse_args()
    command_args = dict(vars(args))
    season = command_args.pop("season", None)

    if Path(f"data/player_game_performance_{season}.csv").is_file():
        player_games = pd.read_csv(f"data/player_game_performance_{season}.csv")
    else:
        player_games = extract_data(season)
        player_games.to_csv(f"data/player_game_performance_{season}.csv", index=False)

    # ready for analysis!!
    ## basic tPTS and minutes
    player_cols = ["PLAYER_ID", "PLAYER_NAME"]

    player_games["bum_status"] = player_games.DEF_RATING_RANK.apply(
        lambda rk: "bum" if rk >= 22 else "good" if rk <= 8 else "mid"
    )

    top_150_minutes_players = (
        player_games.groupby("PLAYER_ID")["trad_pts"]
        .sum()
        .sort_values(ascending=False)
        .head(150)
        .index
    )
    top_player_games = player_games.loc[
        player_games.PLAYER_ID.isin(top_150_minutes_players)
    ].copy()
    print(f"baseline: {top_player_games[['trad_pts', 'MIN']].mean()}")
    print(f"b2b sample sizes: {top_player_games['is_b2b'].value_counts()}")
    print(f"home / away sample sizes: {top_player_games['is_home'].value_counts()}")

    if 1 == 1:
        ## b2b
        b2b_df = calc_dimension_diffs(top_player_games, dim="is_b2b")
        print(b2b_df.head(10))
        # print(b2b_df.sort_values(f"trad_pts_no_is_b2b", ascending=False).head(10).reset_index(drop=True))
        # could add the minutes back in and have a tab spaner for it...
        # plot the diffs as a distribution / histogram
        # scatterplot with yes on one axis and no on other?
        # include number of games somehow??
        b2b_gt_no_sort = (
            create_dim_table(
                b2b_df.sort_values(f"trad_pts_no_is_b2b", ascending=False)
                .head(10)
                .reset_index(drop=True),
                dim="is_b2b",
                title="Top 10 Players by Non-B2B Scoring",
            )
            .cols_label(
                PLAYER_NAME="Player",
                trad_pts_no_is_b2b="FPTS",
                trad_pts_yes_is_b2b="FPTS",
                trad_pts_diff="Diff",
                MIN_no_is_b2b="Minutes",
                MIN_yes_is_b2b="Minutes",
                avg_def_rtg_rk_no_is_b2b="Avg DRTG Rk",
                avg_def_rtg_rk_yes_is_b2b="Avg DRTG Rk",
                num_games_yes_is_b2b="# of Games",
                num_games_no_is_b2b="# of Games",
            )
            .data_color(
                columns=["trad_pts_no_is_b2b", "trad_pts_yes_is_b2b"],
                domain=[
                    min(
                        b2b_df.trad_pts_no_is_b2b.min(),
                        b2b_df.trad_pts_yes_is_b2b.min(),
                    ),
                    max(
                        b2b_df.trad_pts_no_is_b2b.max(),
                        b2b_df.trad_pts_yes_is_b2b.max(),
                    ),
                ],
                palette="PRGn",
            )
            .data_color(
                columns="trad_pts_diff",
                domain=[b2b_df.trad_pts_diff.min(), b2b_df.trad_pts_diff.max()],
                palette="PRGn",
            )
        )

        b2b_gt_no_sort.save(
            f"analysis/images/top_players_b2b_no_sort_{season}_table.png"
        )

        b2b_gt_yes_sort = (
            create_dim_table(
                b2b_df.sort_values(f"trad_pts_yes_is_b2b", ascending=False)
                .head(10)
                .reset_index(drop=True),
                dim="is_b2b",
                title="Top 10 Players by Scoring on a B2B",
            )
            .cols_label(
                PLAYER_NAME="Player",
                trad_pts_no_is_b2b="FPTS",
                trad_pts_yes_is_b2b="FPTS",
                trad_pts_diff="Diff",
                MIN_no_is_b2b="Minutes",
                MIN_yes_is_b2b="Minutes",
                avg_def_rtg_rk_no_is_b2b="Avg DRTG Rk",
                avg_def_rtg_rk_yes_is_b2b="Avg DRTG Rk",
                num_games_yes_is_b2b="# of Games",
                num_games_no_is_b2b="# of Games",
            )
            .data_color(
                columns=["trad_pts_no_is_b2b", "trad_pts_yes_is_b2b"],
                domain=[
                    min(
                        b2b_df.trad_pts_no_is_b2b.min(),
                        b2b_df.trad_pts_yes_is_b2b.min(),
                    ),
                    max(
                        b2b_df.trad_pts_no_is_b2b.max(),
                        b2b_df.trad_pts_yes_is_b2b.max(),
                    ),
                ],
                palette="PRGn",
            )
            .data_color(
                columns="trad_pts_diff",
                domain=[b2b_df.trad_pts_diff.min(), b2b_df.trad_pts_diff.max()],
                palette="PRGn",
            )
        )

        b2b_gt_yes_sort.save(
            f"analysis/images/top_players_b2b_yes_sort_{season}_table.png"
        )

        b2b_gt_diff_desc_sort = (
            create_dim_table(
                b2b_df.sort_values(f"trad_pts_diff", ascending=False)
                .head(10)
                .reset_index(drop=True),
                dim="is_b2b",
                title="Top 10 Players by Scoring Differential on a B2B",
            )
            .cols_label(
                PLAYER_NAME="Player",
                trad_pts_no_is_b2b="FPTS",
                trad_pts_yes_is_b2b="FPTS",
                trad_pts_diff="Diff",
                MIN_no_is_b2b="Minutes",
                MIN_yes_is_b2b="Minutes",
                avg_def_rtg_rk_no_is_b2b="Avg DRTG Rk",
                avg_def_rtg_rk_yes_is_b2b="Avg DRTG Rk",
                num_games_yes_is_b2b="# of Games",
                num_games_no_is_b2b="# of Games",
            )
            .data_color(
                columns=["trad_pts_no_is_b2b", "trad_pts_yes_is_b2b"],
                domain=[
                    min(
                        b2b_df.trad_pts_no_is_b2b.min(),
                        b2b_df.trad_pts_yes_is_b2b.min(),
                    ),
                    max(
                        b2b_df.trad_pts_no_is_b2b.max(),
                        b2b_df.trad_pts_yes_is_b2b.max(),
                    ),
                ],
                palette="PRGn",
            )
            .data_color(
                columns="trad_pts_diff",
                domain=[b2b_df.trad_pts_diff.min(), b2b_df.trad_pts_diff.max()],
                palette="PRGn",
            )
        )

        b2b_gt_diff_desc_sort.save(
            f"analysis/images/top_players_b2b_diff_desc_sort_{season}_table.png"
        )

        b2b_gt_diff_asc_sort = (
            create_dim_table(
                b2b_df.sort_values(f"trad_pts_diff", ascending=True)
                .head(10)
                .reset_index(drop=True),
                dim="is_b2b",
                title="Bottom 10 Players by Scoring Differential on a B2B",
            )
            .cols_label(
                PLAYER_NAME="Player",
                trad_pts_no_is_b2b="FPTS",
                trad_pts_yes_is_b2b="FPTS",
                trad_pts_diff="Diff",
                MIN_no_is_b2b="Minutes",
                MIN_yes_is_b2b="Minutes",
                avg_def_rtg_rk_no_is_b2b="Avg DRTG Rk",
                avg_def_rtg_rk_yes_is_b2b="Avg DRTG Rk",
                num_games_yes_is_b2b="# of Games",
                num_games_no_is_b2b="# of Games",
            )
            .data_color(
                columns=["trad_pts_no_is_b2b", "trad_pts_yes_is_b2b"],
                domain=[
                    min(
                        b2b_df.trad_pts_no_is_b2b.min(),
                        b2b_df.trad_pts_yes_is_b2b.min(),
                    ),
                    max(
                        b2b_df.trad_pts_no_is_b2b.max(),
                        b2b_df.trad_pts_yes_is_b2b.max(),
                    ),
                ],
                palette="PRGn",
            )
            .data_color(
                columns="trad_pts_diff",
                domain=[b2b_df.trad_pts_diff.min(), b2b_df.trad_pts_diff.max()],
                palette="PRGn",
            )
        )

        b2b_gt_diff_asc_sort.save(
            f"analysis/images/top_players_b2b_diff_asc_sort_{season}_table.png"
        )

        b2b_scatter = create_dim_scatter(b2b_df, dim="is_b2b")
        ggsave(
            b2b_scatter,
            f"top_players_b2b_{season}_scatter.png",
            path="analysis/images/",
            scale=2,
        )
        b2b_diff_dist = create_dim_diff_distribution(b2b_df, dim="is_b2b")
        ggsave(
            b2b_diff_dist,
            f"top_players_b2b_{season}_diff_dist.png",
            path="analysis/images/",
        )

        ggsave(
            gggrid([b2b_scatter, b2b_diff_dist], ncol=2),
            f"b2b_scatter_dist_combo.png",
            path="analysis/images/",
        )

        ## home / away
        home_away_df = calc_dimension_diffs(top_player_games, dim="is_home")
        print(home_away_df.trad_pts_diff.median(), home_away_df.trad_pts_diff.mean())
        ha_gt_diff_desc_sort = (
            create_dim_table(
                home_away_df.sort_values(f"trad_pts_diff", ascending=False)
                .head(10)
                .reset_index(drop=True),
                dim="is_home",
                title="Top 10 Players by Scoring Differential Home vs Away",
            )
            .cols_hide(
                columns=[
                    "avg_def_rtg_rk_no_is_home",
                    "avg_def_rtg_rk_yes_is_home",
                    "num_games_no_is_home",
                    "num_games_yes_is_home",
                ]
            )
            .cols_move(
                columns=["MIN_no_is_home", "trad_pts_no_is_home"],
                after="trad_pts_yes_is_home",
            )
            .cols_label(
                PLAYER_NAME="Player",
                trad_pts_no_is_home="FPTS",
                trad_pts_yes_is_home="FPTS",
                trad_pts_diff="Diff",
                MIN_no_is_home="Minutes",
                MIN_yes_is_home="Minutes",
            )
            .data_color(
                columns=["trad_pts_no_is_home", "trad_pts_yes_is_home"],
                domain=[
                    min(
                        home_away_df.trad_pts_no_is_home.min(),
                        home_away_df.trad_pts_yes_is_home.min(),
                    ),
                    max(
                        home_away_df.trad_pts_no_is_home.max(),
                        home_away_df.trad_pts_yes_is_home.max(),
                    ),
                ],
                palette="PRGn",
            )
            .data_color(
                columns="trad_pts_diff",
                domain=[
                    home_away_df.trad_pts_diff.min(),
                    home_away_df.trad_pts_diff.max(),
                ],
                palette="PRGn",
            )
        )

        ha_gt_diff_desc_sort.save(
            f"analysis/images/top_players_ha_diff_desc_sort_{season}_table.png"
        )

        ha_gt_diff_asc_sort = (
            create_dim_table(
                home_away_df.sort_values(f"trad_pts_diff", ascending=True)
                .head(10)
                .reset_index(drop=True),
                dim="is_home",
                title="Bottom 10 Players by Scoring Differential Home vs Away",
            )
            .cols_hide(
                columns=[
                    "avg_def_rtg_rk_no_is_home",
                    "avg_def_rtg_rk_yes_is_home",
                    "num_games_no_is_home",
                    "num_games_yes_is_home",
                ]
            )
            .cols_move(
                columns=["MIN_no_is_home", "trad_pts_no_is_home"],
                after="trad_pts_yes_is_home",
            )
            .cols_label(
                PLAYER_NAME="Player",
                trad_pts_no_is_home="FPTS",
                trad_pts_yes_is_home="FPTS",
                trad_pts_diff="Diff",
                MIN_no_is_home="Minutes",
                MIN_yes_is_home="Minutes",
            )
            .data_color(
                columns=["trad_pts_no_is_home", "trad_pts_yes_is_home"],
                domain=[
                    min(
                        home_away_df.trad_pts_no_is_home.min(),
                        home_away_df.trad_pts_yes_is_home.min(),
                    ),
                    max(
                        home_away_df.trad_pts_no_is_home.max(),
                        home_away_df.trad_pts_yes_is_home.max(),
                    ),
                ],
                palette="PRGn",
            )
            .data_color(
                columns="trad_pts_diff",
                domain=[
                    home_away_df.trad_pts_diff.min(),
                    home_away_df.trad_pts_diff.max(),
                ],
                palette="PRGn",
            )
        )

        ha_gt_diff_asc_sort.save(
            f"analysis/images/top_players_ha_diff_asc_sort_{season}_table.png"
        )

        ha_scatter = create_dim_scatter(home_away_df, dim="is_home")
        ggsave(
            ha_scatter,
            f"top_players_ha_{season}_scatter.png",
            path="analysis/images/",
            scale=2,
        )
        ha_diff_dist = create_dim_diff_distribution(home_away_df, dim="is_home")
        ggsave(
            ha_diff_dist,
            f"top_players_ha_{season}_diff_dist.png",
            path="analysis/images/",
        )

        ggsave(
            gggrid([ha_scatter, ha_diff_dist], ncol=2),
            f"home_away_scatter_dist_combo.png",
            path="analysis/images/",
        )

    ## BUM VS GOOD
    bum_df = calc_dimension_diffs(top_player_games, dim="bum_status")
    bum_gt_good_bum_desc_sort = (
        GT(
            bum_df.sort_values("trad_pts_diff_good_bum", ascending=False)
            .head(10)
            .reset_index(drop=True)
        )
        .tab_header(
            title="Playing Up to The Competition",
            subtitle="Top 10 Players by (Good - Bum) FPTS Differential",
        )
        .tab_spanner(
            label="Good (Top 8)",
            columns=[
                "MIN_good",
                "num_games_good",
                "avg_def_rtg_rk_good",
                "trad_pts_good",
            ],
        )  # good
        .tab_spanner(
            label="Mid",
            columns=["MIN_mid", "num_games_mid", "avg_def_rtg_rk_mid", "trad_pts_mid"],
        )  # mid
        .tab_spanner(
            label="Bums (Bottom 8)",
            columns=["MIN_bum", "num_games_bum", "avg_def_rtg_rk_bum", "trad_pts_bum"],
        )  # bum
        .tab_spanner(
            label="Diff",
            columns=[
                "trad_pts_diff_good_bum",
                "trad_pts_diff_mid_bum",
                "trad_pts_diff_good_mid",
            ],
        )  # diffs
        .cols_label(
            MIN_good="Minutes",
            MIN_mid="Minutes",
            MIN_bum="Minutes",
            num_games_good="# of Games",
            num_games_mid="# of Games",
            num_games_bum="# of Games",
            trad_pts_good="FPTS",
            trad_pts_mid="FPTS",
            trad_pts_bum="FPTS",
            trad_pts_diff_good_bum="Good - Bum",
            trad_pts_diff_mid_bum="Mid - Bum",
            trad_pts_diff_good_mid="Good - Mid",
        )
        .cols_hide(
            [
                "avg_def_rtg_rk_good",
                "avg_def_rtg_rk_mid",
                "avg_def_rtg_rk_bum",
                "trad_pts_diff_mid_bum",
                "trad_pts_diff_good_mid",
            ]
        )  # drtg rk
        .cols_move(
            columns=["MIN_bum", "num_games_bum", "trad_pts_bum"], after="trad_pts_mid"
        )
        .tab_source_note(
            source_note=md(
                "@wfordh | Traditional fantasy points: https://ottoneu.fangraphs.com/basketball/help/rosters_and_scoring"
            )
        )
        .fmt_number(
            columns=[
                "MIN_good",
                "MIN_mid",
                "MIN_bum",
                "trad_pts_good",
                "trad_pts_mid",
                "trad_pts_bum",
                "trad_pts_diff_good_bum",
                "trad_pts_diff_good_mid",
                "trad_pts_diff_mid_bum",
            ],
            decimals=1,
        )
        .data_color(
            palette="PRGn",
            columns="trad_pts_diff_good_bum",
            domain=[
                bum_df.trad_pts_diff_good_bum.min(),
                bum_df.trad_pts_diff_good_bum.max(),
            ],
        )
        .data_color(
            palette="PRGn",
            alpha=0.3,
            columns=["trad_pts_good", "trad_pts_mid", "trad_pts_bum"],
            domain=[
                min(
                    bum_df.trad_pts_bum.min(),
                    bum_df.trad_pts_mid.min(),
                    bum_df.trad_pts_good.min(),
                ),
                max(
                    bum_df.trad_pts_bum.max(),
                    bum_df.trad_pts_mid.max(),
                    bum_df.trad_pts_good.max(),
                ),
            ],
        )
        .tab_style(
            style=style.borders(sides="left", weight="8px", color="white"),
            locations=loc.body(columns="trad_pts_diff_good_bum"),
        )
    )

    bum_gt_good_bum_desc_sort.save(f"analysis/images/good_bum_desc_{season}_table.png")

    bum_gt_good_bum_asc_sort = (
        GT(
            bum_df.sort_values("trad_pts_diff_good_bum", ascending=True)
            .head(10)
            .reset_index(drop=True)
        )
        .tab_header(
            title="Bumslayers - Beating Up on Bad Teams",
            subtitle="Bottom 10 Players by (Good - Bum) FPTS Differential",
        )
        .tab_spanner(
            label="Good (Top 8)",
            columns=[
                "MIN_good",
                "num_games_good",
                "avg_def_rtg_rk_good",
                "trad_pts_good",
            ],
        )  # good
        .tab_spanner(
            label="Mid",
            columns=["MIN_mid", "num_games_mid", "avg_def_rtg_rk_mid", "trad_pts_mid"],
        )  # mid
        .tab_spanner(
            label="Bums (Bottom 8)",
            columns=["MIN_bum", "num_games_bum", "avg_def_rtg_rk_bum", "trad_pts_bum"],
        )  # bum
        .tab_spanner(
            label="Diff",
            columns=[
                "trad_pts_diff_good_bum",
                "trad_pts_diff_mid_bum",
                "trad_pts_diff_good_mid",
            ],
        )  # diffs
        .cols_label(
            MIN_good="Minutes",
            MIN_mid="Minutes",
            MIN_bum="Minutes",
            num_games_good="# of Games",
            num_games_mid="# of Games",
            num_games_bum="# of Games",
            trad_pts_good="FPTS",
            trad_pts_mid="FPTS",
            trad_pts_bum="FPTS",
            trad_pts_diff_good_bum="Good - Bum",
            trad_pts_diff_mid_bum="Mid - Bum",
            trad_pts_diff_good_mid="Good - Mid",
        )
        .cols_hide(
            [
                "avg_def_rtg_rk_good",
                "avg_def_rtg_rk_mid",
                "avg_def_rtg_rk_bum",
                "trad_pts_diff_mid_bum",
                "trad_pts_diff_good_mid",
                # "MIN_mid",
                # "num_games_mid",
                # "trad_pts_mid"
            ]
        )  # drtg rk
        .cols_move(
            columns=["MIN_bum", "num_games_bum", "trad_pts_bum"], after="trad_pts_mid"
        )
        .tab_source_note(
            source_note=md(
                "@wfordh | Traditional fantasy points: https://ottoneu.fangraphs.com/basketball/help/rosters_and_scoring"
            )
        )
        .fmt_number(
            columns=[
                "MIN_good",
                "MIN_mid",
                "MIN_bum",
                "trad_pts_good",
                "trad_pts_mid",
                "trad_pts_bum",
                "trad_pts_diff_good_bum",
                "trad_pts_diff_good_mid",
                "trad_pts_diff_mid_bum",
            ],
            decimals=1,
        )
        .data_color(
            palette="PRGn",
            columns="trad_pts_diff_good_bum",
            domain=[
                bum_df.trad_pts_diff_good_bum.min(),
                bum_df.trad_pts_diff_good_bum.max(),
            ],
        )
        .data_color(
            palette="PRGn",
            alpha=0.3,
            columns=["trad_pts_good", "trad_pts_mid", "trad_pts_bum"],
            domain=[
                min(
                    bum_df.trad_pts_bum.min(),
                    bum_df.trad_pts_mid.min(),
                    bum_df.trad_pts_good.min(),
                ),
                max(
                    bum_df.trad_pts_bum.max(),
                    bum_df.trad_pts_mid.max(),
                    bum_df.trad_pts_good.max(),
                ),
            ],
        )
        .tab_style(
            style=style.borders(sides="left", weight="8px", color="white"),
            locations=loc.body(columns="trad_pts_diff_good_bum"),
        )
    )

    bum_gt_good_bum_asc_sort.save(f"analysis/images/good_bum_asc_{season}_table.png")

    ax_lim_min = 5 * math.floor(
        min(
            bum_df.trad_pts_bum.min(),
            bum_df.trad_pts_mid.min(),
            bum_df.trad_pts_good.min(),
        )
        / 5
    )
    ax_lim_max = 5 * math.ceil(
        max(
            bum_df.trad_pts_bum.max(),
            bum_df.trad_pts_mid.max(),
            bum_df.trad_pts_good.max(),
        )
        / 5
    )
    m, c = np.linalg.lstsq(
        np.vstack([np.array(bum_df.trad_pts_bum), np.ones(len(bum_df.trad_pts_bum))]).T,
        np.array(bum_df.trad_pts_good),
        rcond=1,
    )[0]

    p1 = (
        ggplot(bum_df, aes(x="trad_pts_bum", y="trad_pts_good"))
        + geom_point()
        + labs(
            x="Bum",
            y="Good",
            subtitle="Traditional Fantasy Points",
            title="Scoring vs Bum and Good Defenses",
        )
        + coord_cartesian(xlim=(ax_lim_min, ax_lim_max), ylim=(ax_lim_min, ax_lim_max))
        + geom_abline(slope=1, color="red", linetype="longdash")
        + geom_abline(slope=m, intercept=c, color="blue")
    )

    mean = bum_df.trad_pts_diff_good_bum.mean()
    print(f"good - bum mean: {mean}")
    p2 = (
        ggplot(bum_df, aes(x="trad_pts_diff_good_bum"))
        # + geom_histogram()
        + geom_density()
        + geom_vline(xintercept=mean, color="red", linetype="longdash")
        + labs(
            x="Diff (Good - Bum)",
            y="",
            title="Scoring Differential",
            subtitle="Games vs Bum and Good Defenses",
        )
    )

    ggsave(
        gggrid([p1, p2], ncol=2),
        f"good_bum_scatter_dist_combo_{season}.png",
        path="analysis/images/",
    )

    # repeat for other five variations of asc/desc and good/mid/bum diffs

    bum_gt_good_mid_desc_sort = (
        GT(
            bum_df.sort_values("trad_pts_diff_good_mid", ascending=False)
            .head(10)
            .reset_index(drop=True)
        )
        .tab_header(
            title="Can't Call Them Mid",
            subtitle="Top 10 Players by (Good - Mid) FPTS Differential",
        )
        .tab_spanner(
            label="Good (Top 8)",
            columns=[
                "MIN_good",
                "num_games_good",
                "avg_def_rtg_rk_good",
                "trad_pts_good",
            ],
        )  # good
        .tab_spanner(
            label="Mid",
            columns=["MIN_mid", "num_games_mid", "avg_def_rtg_rk_mid", "trad_pts_mid"],
        )  # mid
        .tab_spanner(
            label="Bums (Bottom 8)",
            columns=["MIN_bum", "num_games_bum", "avg_def_rtg_rk_bum", "trad_pts_bum"],
        )  # bum
        .tab_spanner(
            label="Diff",
            columns=[
                "trad_pts_diff_good_bum",
                "trad_pts_diff_mid_bum",
                "trad_pts_diff_good_mid",
            ],
        )  # diffs
        .cols_label(
            MIN_good="Minutes",
            MIN_mid="Minutes",
            MIN_bum="Minutes",
            num_games_good="# of Games",
            num_games_mid="# of Games",
            num_games_bum="# of Games",
            trad_pts_good="FPTS",
            trad_pts_mid="FPTS",
            trad_pts_bum="FPTS",
            trad_pts_diff_good_bum="Good - Bum",
            trad_pts_diff_mid_bum="Mid - Bum",
            trad_pts_diff_good_mid="Good - Mid",
        )
        .cols_hide(
            [
                "avg_def_rtg_rk_good",
                "avg_def_rtg_rk_mid",
                "avg_def_rtg_rk_bum",
                "trad_pts_diff_mid_bum",
                "trad_pts_diff_good_bum",
            ]
        )  # drtg rk
        .cols_move(
            columns=["MIN_bum", "num_games_bum", "trad_pts_bum"], after="trad_pts_mid"
        )
        .tab_source_note(
            source_note=md(
                "@wfordh | Traditional fantasy points: https://ottoneu.fangraphs.com/basketball/help/rosters_and_scoring"
            )
        )
        .fmt_number(
            columns=[
                "MIN_good",
                "MIN_mid",
                "MIN_bum",
                "trad_pts_good",
                "trad_pts_mid",
                "trad_pts_bum",
                "trad_pts_diff_good_bum",
                "trad_pts_diff_good_mid",
                "trad_pts_diff_mid_bum",
            ],
            decimals=1,
        )
        .data_color(
            palette="PRGn",
            columns="trad_pts_diff_good_mid",
            domain=[
                bum_df.trad_pts_diff_good_mid.min(),
                bum_df.trad_pts_diff_good_mid.max(),
            ],
        )
        .data_color(
            palette="PRGn",
            alpha=0.3,
            columns=["trad_pts_good", "trad_pts_mid", "trad_pts_bum"],
            domain=[
                min(
                    bum_df.trad_pts_bum.min(),
                    bum_df.trad_pts_mid.min(),
                    bum_df.trad_pts_good.min(),
                ),
                max(
                    bum_df.trad_pts_bum.max(),
                    bum_df.trad_pts_mid.max(),
                    bum_df.trad_pts_good.max(),
                ),
            ],
        )
        .tab_style(
            style=style.borders(sides="left", weight="8px", color="white"),
            locations=loc.body(columns="trad_pts_diff_good_mid"),
        )
    )

    bum_gt_good_mid_desc_sort.save(f"analysis/images/good_mid_desc_{season}_table.png")

    bum_gt_good_mid_asc_sort = (
        GT(
            bum_df.sort_values("trad_pts_diff_good_mid", ascending=True)
            .head(10)
            .reset_index(drop=True)
        )
        .tab_header(
            title="Midrange Specialists?",
            subtitle="Bottom 10 Players by (Good - Mid) FPTS Differential",
        )
        .tab_spanner(
            label="Good (Top 8)",
            columns=[
                "MIN_good",
                "num_games_good",
                "avg_def_rtg_rk_good",
                "trad_pts_good",
            ],
        )  # good
        .tab_spanner(
            label="Mid",
            columns=["MIN_mid", "num_games_mid", "avg_def_rtg_rk_mid", "trad_pts_mid"],
        )  # mid
        .tab_spanner(
            label="Bums (Bottom 8)",
            columns=["MIN_bum", "num_games_bum", "avg_def_rtg_rk_bum", "trad_pts_bum"],
        )  # bum
        .tab_spanner(
            label="Diff",
            columns=[
                "trad_pts_diff_good_bum",
                "trad_pts_diff_mid_bum",
                "trad_pts_diff_good_mid",
            ],
        )  # diffs
        .cols_label(
            MIN_good="Minutes",
            MIN_mid="Minutes",
            MIN_bum="Minutes",
            num_games_good="# of Games",
            num_games_mid="# of Games",
            num_games_bum="# of Games",
            trad_pts_good="FPTS",
            trad_pts_mid="FPTS",
            trad_pts_bum="FPTS",
            trad_pts_diff_good_bum="Good - Bum",
            trad_pts_diff_mid_bum="Mid - Bum",
            trad_pts_diff_good_mid="Good - Mid",
        )
        .cols_hide(
            [
                "avg_def_rtg_rk_good",
                "avg_def_rtg_rk_mid",
                "avg_def_rtg_rk_bum",
                "trad_pts_diff_mid_bum",
                "trad_pts_diff_good_bum",
                # "MIN_mid",
                # "num_games_mid",
                # "trad_pts_mid"
            ]
        )  # drtg rk
        .cols_move(
            columns=["MIN_bum", "num_games_bum", "trad_pts_bum"], after="trad_pts_mid"
        )
        .tab_source_note(
            source_note=md(
                "@wfordh | Traditional fantasy points: https://ottoneu.fangraphs.com/basketball/help/rosters_and_scoring"
            )
        )
        .fmt_number(
            columns=[
                "MIN_good",
                "MIN_mid",
                "MIN_bum",
                "trad_pts_good",
                "trad_pts_mid",
                "trad_pts_bum",
                "trad_pts_diff_good_bum",
                "trad_pts_diff_good_mid",
                "trad_pts_diff_mid_bum",
            ],
            decimals=1,
        )
        .data_color(
            palette="PRGn",
            columns="trad_pts_diff_good_mid",
            domain=[
                bum_df.trad_pts_diff_good_mid.min(),
                bum_df.trad_pts_diff_good_mid.max(),
            ],
        )
        .data_color(
            palette="PRGn",
            alpha=0.3,
            columns=["trad_pts_good", "trad_pts_mid", "trad_pts_bum"],
            domain=[
                min(
                    bum_df.trad_pts_bum.min(),
                    bum_df.trad_pts_mid.min(),
                    bum_df.trad_pts_good.min(),
                ),
                max(
                    bum_df.trad_pts_bum.max(),
                    bum_df.trad_pts_mid.max(),
                    bum_df.trad_pts_good.max(),
                ),
            ],
        )
        .tab_style(
            style=style.borders(sides="left", weight="8px", color="white"),
            locations=loc.body(columns="trad_pts_diff_good_mid"),
        )
    )

    bum_gt_good_mid_asc_sort.save(f"analysis/images/good_mid_asc_{season}_table.png")

    ax_lim_min = 5 * math.floor(
        min(
            bum_df.trad_pts_bum.min(),
            bum_df.trad_pts_mid.min(),
            bum_df.trad_pts_good.min(),
        )
        / 5
    )
    ax_lim_max = 5 * math.ceil(
        max(
            bum_df.trad_pts_bum.max(),
            bum_df.trad_pts_mid.max(),
            bum_df.trad_pts_good.max(),
        )
        / 5
    )
    m, c = np.linalg.lstsq(
        np.vstack([np.array(bum_df.trad_pts_mid), np.ones(len(bum_df.trad_pts_mid))]).T,
        np.array(bum_df.trad_pts_good),
        rcond=1,
    )[0]

    p1 = (
        ggplot(bum_df, aes(x="trad_pts_mid", y="trad_pts_good"))
        + geom_point()
        + labs(
            x="Mid",
            y="Good",
            subtitle="Traditional Fantasy Points",
            title="Scoring vs Mid and Good Defenses",
        )
        + coord_cartesian(xlim=(ax_lim_min, ax_lim_max), ylim=(ax_lim_min, ax_lim_max))
        + geom_abline(slope=1, color="red", linetype="longdash")
        + geom_abline(slope=m, intercept=c, color="blue")
    )

    mean = bum_df.trad_pts_diff_good_mid.mean()
    print(f"good - mid mean: {mean}")

    p2 = (
        ggplot(bum_df, aes(x="trad_pts_diff_good_mid"))
        # + geom_histogram()
        + geom_density()
        + geom_vline(xintercept=mean, color="red", linetype="longdash")
        + labs(
            x="Diff (Good - Mid)",
            y="",
            title="Scoring Differential",
            subtitle="Games vs Good and Mid Defenses",
        )
    )

    ggsave(
        gggrid([p1, p2], ncol=2),
        f"good_mid_scatter_dist_combo_{season}.png",
        path="analysis/images/",
    )

    bum_gt_mid_bum_desc_sort = (
        GT(
            bum_df.sort_values("trad_pts_diff_mid_bum", ascending=False)
            .head(10)
            .reset_index(drop=True)
        )
        .tab_header(
            title="Rising to the...Middle?",
            subtitle="Top 10 Players by (Mid - Bum) FPTS Differential",
        )
        .tab_spanner(
            label="Good (Top 8)",
            columns=[
                "MIN_good",
                "num_games_good",
                "avg_def_rtg_rk_good",
                "trad_pts_good",
            ],
        )  # good
        .tab_spanner(
            label="Mid",
            columns=["MIN_mid", "num_games_mid", "avg_def_rtg_rk_mid", "trad_pts_mid"],
        )  # mid
        .tab_spanner(
            label="Bums (Bottom 8)",
            columns=["MIN_bum", "num_games_bum", "avg_def_rtg_rk_bum", "trad_pts_bum"],
        )  # bum
        .tab_spanner(
            label="Diff",
            columns=[
                "trad_pts_diff_good_bum",
                "trad_pts_diff_mid_bum",
                "trad_pts_diff_good_mid",
            ],
        )  # diffs
        .cols_label(
            MIN_good="Minutes",
            MIN_mid="Minutes",
            MIN_bum="Minutes",
            num_games_good="# of Games",
            num_games_mid="# of Games",
            num_games_bum="# of Games",
            trad_pts_good="FPTS",
            trad_pts_mid="FPTS",
            trad_pts_bum="FPTS",
            trad_pts_diff_good_bum="Good - Bum",
            trad_pts_diff_mid_bum="Mid - Bum",
            trad_pts_diff_good_mid="Good - Mid",
        )
        .cols_hide(
            [
                "avg_def_rtg_rk_good",
                "avg_def_rtg_rk_mid",
                "avg_def_rtg_rk_bum",
                "trad_pts_diff_good_bum",
                "trad_pts_diff_good_mid",
            ]
        )  # drtg rk
        .cols_move(
            columns=["MIN_bum", "num_games_bum", "trad_pts_bum"], after="trad_pts_mid"
        )
        .tab_source_note(
            source_note=md(
                "@wfordh | Traditional fantasy points: https://ottoneu.fangraphs.com/basketball/help/rosters_and_scoring"
            )
        )
        .fmt_number(
            columns=[
                "MIN_good",
                "MIN_mid",
                "MIN_bum",
                "trad_pts_good",
                "trad_pts_mid",
                "trad_pts_bum",
                "trad_pts_diff_good_bum",
                "trad_pts_diff_good_mid",
                "trad_pts_diff_mid_bum",
            ],
            decimals=1,
        )
        .data_color(
            palette="PRGn",
            columns="trad_pts_diff_mid_bum",
            domain=[
                bum_df.trad_pts_diff_mid_bum.min(),
                bum_df.trad_pts_diff_mid_bum.max(),
            ],
        )
        .data_color(
            palette="PRGn",
            alpha=0.3,
            columns=["trad_pts_good", "trad_pts_mid", "trad_pts_bum"],
            domain=[
                min(
                    bum_df.trad_pts_bum.min(),
                    bum_df.trad_pts_mid.min(),
                    bum_df.trad_pts_good.min(),
                ),
                max(
                    bum_df.trad_pts_bum.max(),
                    bum_df.trad_pts_mid.max(),
                    bum_df.trad_pts_good.max(),
                ),
            ],
        )
        .tab_style(
            style=style.borders(sides="left", weight="8px", color="white"),
            locations=loc.body(columns="trad_pts_diff_mid_bum"),
        )
    )

    bum_gt_mid_bum_desc_sort.save(f"analysis/images/mid_bum_desc_{season}_table.png")

    bum_gt_mid_bum_asc_sort = (
        GT(
            bum_df.sort_values("trad_pts_diff_mid_bum", ascending=True)
            .head(10)
            .reset_index(drop=True)
        )
        .tab_header(
            title="Still Bumslaying",
            subtitle="Bottom 10 Players by (Mid - Bum) FPTS Differential",
        )
        .tab_spanner(
            label="Good (Top 8)",
            columns=[
                "MIN_good",
                "num_games_good",
                "avg_def_rtg_rk_good",
                "trad_pts_good",
            ],
        )  # good
        .tab_spanner(
            label="Mid",
            columns=["MIN_mid", "num_games_mid", "avg_def_rtg_rk_mid", "trad_pts_mid"],
        )  # mid
        .tab_spanner(
            label="Bums (Bottom 8)",
            columns=["MIN_bum", "num_games_bum", "avg_def_rtg_rk_bum", "trad_pts_bum"],
        )  # bum
        .tab_spanner(
            label="Diff",
            columns=[
                "trad_pts_diff_good_bum",
                "trad_pts_diff_mid_bum",
                "trad_pts_diff_good_mid",
            ],
        )  # diffs
        .cols_label(
            MIN_good="Minutes",
            MIN_mid="Minutes",
            MIN_bum="Minutes",
            num_games_good="# of Games",
            num_games_mid="# of Games",
            num_games_bum="# of Games",
            trad_pts_good="FPTS",
            trad_pts_mid="FPTS",
            trad_pts_bum="FPTS",
            trad_pts_diff_good_bum="Good - Bum",
            trad_pts_diff_mid_bum="Mid - Bum",
            trad_pts_diff_good_mid="Good - Mid",
        )
        .cols_hide(
            [
                "avg_def_rtg_rk_good",
                "avg_def_rtg_rk_mid",
                "avg_def_rtg_rk_bum",
                "trad_pts_diff_good_bum",
                "trad_pts_diff_good_mid",
                # "MIN_mid",
                # "num_games_mid",
                # "trad_pts_mid"
            ]
        )  # drtg rk
        .cols_move(
            columns=["MIN_bum", "num_games_bum", "trad_pts_bum"], after="trad_pts_mid"
        )
        .tab_source_note(
            source_note=md(
                "@wfordh | Traditional fantasy points: https://ottoneu.fangraphs.com/basketball/help/rosters_and_scoring"
            )
        )
        .fmt_number(
            columns=[
                "MIN_good",
                "MIN_mid",
                "MIN_bum",
                "trad_pts_good",
                "trad_pts_mid",
                "trad_pts_bum",
                "trad_pts_diff_good_bum",
                "trad_pts_diff_good_mid",
                "trad_pts_diff_mid_bum",
            ],
            decimals=1,
        )
        .data_color(
            palette="PRGn",
            columns="trad_pts_diff_mid_bum",
            domain=[
                bum_df.trad_pts_diff_mid_bum.min(),
                bum_df.trad_pts_diff_mid_bum.max(),
            ],
        )
        .data_color(
            palette="PRGn",
            alpha=0.3,
            columns=["trad_pts_good", "trad_pts_mid", "trad_pts_bum"],
            domain=[
                min(
                    bum_df.trad_pts_bum.min(),
                    bum_df.trad_pts_mid.min(),
                    bum_df.trad_pts_good.min(),
                ),
                max(
                    bum_df.trad_pts_bum.max(),
                    bum_df.trad_pts_mid.max(),
                    bum_df.trad_pts_good.max(),
                ),
            ],
        )
        .tab_style(
            style=style.borders(sides="left", weight="8px", color="white"),
            locations=loc.body(columns="trad_pts_diff_mid_bum"),
        )
    )

    bum_gt_mid_bum_asc_sort.save(f"analysis/images/mid_bum_asc_{season}_table.png")

    ax_lim_min = 5 * math.floor(
        min(
            bum_df.trad_pts_bum.min(),
            bum_df.trad_pts_mid.min(),
            bum_df.trad_pts_good.min(),
        )
        / 5
    )
    ax_lim_max = 5 * math.ceil(
        max(
            bum_df.trad_pts_bum.max(),
            bum_df.trad_pts_mid.max(),
            bum_df.trad_pts_good.max(),
        )
        / 5
    )
    m, c = np.linalg.lstsq(
        np.vstack([np.array(bum_df.trad_pts_bum), np.ones(len(bum_df.trad_pts_bum))]).T,
        np.array(bum_df.trad_pts_mid),
        rcond=1,
    )[0]
    p1 = (
        ggplot(bum_df, aes(x="trad_pts_bum", y="trad_pts_mid"))
        + geom_point()
        + labs(
            x="Bum",
            y="Mid",
            subtitle="Traditional Fantasy Points",
            title="Scoring vs Mid and Bum Defenses",
        )
        + coord_cartesian(xlim=(ax_lim_min, ax_lim_max), ylim=(ax_lim_min, ax_lim_max))
        + geom_abline(slope=1, color="red", linetype="longdash")
        + geom_abline(slope=m, intercept=c, color="blue")
    )

    mean = bum_df.trad_pts_diff_mid_bum.mean()
    print(f"mid - bum mean: {mean}")
    p2 = (
        ggplot(bum_df, aes(x="trad_pts_diff_mid_bum"))
        # + geom_histogram()
        + geom_density()
        + geom_vline(xintercept=mean, color="red", linetype="longdash")
        + labs(
            x="Diff (Mid - Bum)",
            y="",
            title="Scoring Differential",
            subtitle="Games vs Mid and Bum Defenses",
        )
    )

    ggsave(
        gggrid([p1, p2], ncol=2),
        f"mid_bum_scatter_dist_combo_{season}.png",
        path="analysis/images/",
    )

    # need to go wide to long with diff bum status diffs before plotting
    # add categorical var for the diffs
    # ggplot(bum_df, aes())
    ggsave(
        (ggplot(top_player_games, aes("trad_pts", "bum_status")) + geom_area_ridges()),
        f"trad_points_dist_bum_stats_{season}.png",
        path="analysis/images/",
    )

    print(
        player_games.groupby(["bum_status"]).agg(
            {
                "trad_pts": "mean",
                # "MIN": ["mean", "std"],
            }
        )
    )

    ###
    # how to get differentials??
    # use combo of filters and self-joins? how would that impact
    # table making and graphs?
    ###


if __name__ == "__main__":
    main()
