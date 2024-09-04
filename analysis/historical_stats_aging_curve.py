import logging
import os
import sys

import pandas as pd
from lets_plot import *  # type: ignore

sys.path.append(os.path.abspath("src"))
logging.basicConfig(level=logging.INFO)


def main():
    stats_df = pd.read_csv("./data/box_stats.csv")

    stats_df["season_rank"] = stats_df.apply(
        lambda row: int(row.season.split("-")[0]) - row.from_year, axis=1
    )
    print(stats_df.season_rank.min())

    # fix positions
    stats_df["ottoneu_position"] = stats_df.ottoneu_position.map(
        {
            "G": "G",
            "F": "F",
            "C": "C",
            "G-F": "G-F",
            "F-G": "G-F",
            "F-C": "F-C",
            "C-F": "F-C",
        }
    )

    print(stats_df.head())
    print(stats_df.columns.tolist())
    # values col must be one of these
    # ["simple_points_value", "trad_points_value", "categories_value"]
    value_col = "trad_points_value"

    rookie_teen = stats_df.loc[
        (stats_df.draft_round == 1) & (stats_df.season_rank == 0) & (stats_df.age <= 19)
    ].nba_player_id
    rookie_20 = stats_df.loc[
        (stats_df.draft_round == 1) & (stats_df.season_rank == 0) & (stats_df.age == 20)
    ].nba_player_id
    rookie_21 = stats_df.loc[
        (stats_df.draft_round == 1) & (stats_df.season_rank == 0) & (stats_df.age == 21)
    ].nba_player_id
    rookie_22 = stats_df.loc[
        (stats_df.draft_round == 1) & (stats_df.season_rank == 0) & (stats_df.age == 22)
    ].nba_player_id
    rookie_old = stats_df.loc[
        (stats_df.draft_round == 1) & (stats_df.season_rank == 0) & (stats_df.age >= 23)
    ].nba_player_id

    plot_teen = (
        ggplot(
            stats_df.loc[
                (stats_df.season_rank <= 3) & (stats_df.nba_player_id.isin(rookie_teen))
            ],
            aes(x="draft_number", y=value_col, color="ottoneu_position"),
        )
        + geom_point()
        + geom_jitter()
        + facet_grid(x="season_rank")
    )
    plot_20 = (
        ggplot(
            stats_df.loc[
                (stats_df.season_rank <= 3) & (stats_df.nba_player_id.isin(rookie_20))
            ],
            aes(x="draft_number", y=value_col, color="ottoneu_position"),
        )
        + geom_point()
        + geom_jitter()
        + facet_grid(x="season_rank")
    )
    plot_21 = (
        ggplot(
            stats_df.loc[
                (stats_df.season_rank <= 3) & (stats_df.nba_player_id.isin(rookie_21))
            ],
            aes(x="draft_number", y=value_col, color="ottoneu_position"),
        )
        + geom_point()
        + geom_jitter()
        + facet_grid(x="season_rank")
    )
    plot_22 = (
        ggplot(
            stats_df.loc[
                (stats_df.season_rank <= 3) & (stats_df.nba_player_id.isin(rookie_22))
            ],
            aes(x="draft_number", y=value_col, color="ottoneu_position"),
        )
        + geom_point()
        + geom_jitter()
        + facet_grid(x="season_rank")
    )
    plot_old = (
        ggplot(
            stats_df.loc[
                (stats_df.season_rank <= 3) & (stats_df.nba_player_id.isin(rookie_22))
            ],
            aes(x="draft_number", y=value_col, color="ottoneu_position"),
        )
        # + geom_point()
        # + geom_jitter()
        + geom_smooth()
        + facet_grid(x="season_rank")
    )

    plot_grid = gggrid(
        [plot_teen, plot_22, plot_old],
        ncol=1,
    )

    ggsave(plot_grid, "age_curve_season_draft.png", path="analysis/images/", scale=2.0)


if __name__ == "__main__":
    main()


"""
- filter for players who were zeros in year one
- different cuts:
	- overall by year in league
	- year in league by top 5 / lotto / round 1 / back half round 1 / round 2 / undrafted
	- players who were zeroes in year one (should you hold on)
	- 
- If analyzing by position, need to break out by scoring type since 
  position (G / F / C) could be different for each and is a different 
  column in the data table
- next level is bringing age in?


print(
        stats_df.loc[
            (stats_df.draft_round == 1)
            & (stats_df.draft_number < 15)
            & (stats_df.season_rank == 0)
        ][value_cols].mean()
    )
    print(
        stats_df.loc[
            (stats_df.draft_round == 1)
            & (stats_df.draft_number < 15)
            & (stats_df.season_rank == 1)
        ][value_cols].mean()
    )
    print(
        stats_df.loc[
            (stats_df.draft_round == 1)
            & (stats_df.draft_number < 15)
            & (stats_df.season_rank == 2)
        ][value_cols].mean()
    )

    lotto_rookie_zeros = stats_df[
        (stats_df.draft_round == 1)
        & (stats_df.draft_number < 15)
        & (stats_df.season_rank == 0)
        & (stats_df.categories_value == 0)
    ].nba_player_id
    print(
        stats_df.loc[
            stats_df.nba_player_id.isin(lotto_rookie_zeros)
            & (stats_df.season_rank == 2)
        ][value_cols].mean()
    )



"""
