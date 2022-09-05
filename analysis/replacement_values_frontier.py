import os
import sys

import altair as alt
import pandas as pd

sys.path.append(os.path.abspath("src"))
from calc_stats import calc_categories_value, calc_fantasy_pts
from transform import get_scoring_minutes_combo, prep_stats_df


def main():
    stats_df = prep_stats_df()
    ros_df = get_scoring_minutes_combo("rest_of_season", stats_df)
    # get projected minutes, per 100 stats fantasy value, and if they are
    # projected to be above replacement value
    stats_df.columns = [col.replace("_100", "_game") for col in stats_df.columns]
    stats_df.rename(
        columns={
            "points_game": "pts_game",
            "assists_game": "ast_game",
            "rebounds_game": "reb_game",
            "steals_game": "stl_game",
            "blocks_game": "blk_game",
        },
        inplace=True,
    )
    stats_df["simple_points_per_100"] = calc_fantasy_pts(
        stats_df, is_simple_scoring=True
    )
    stats_df["trad_points_per_100"] = calc_fantasy_pts(
        stats_df, is_simple_scoring=False
    )
    stats_df["cats_value_per_100"] = calc_categories_value(stats_df)
    # print(stats_df.shape, ros_df.shape)
    stats_df_cols = [
        "player",
        "nba_player_id",
        "simple_points_per_100",
        "trad_points_per_100",
        "cats_value_per_100",
    ]
    ros_df_cols = [
        "nba_player_id",
        "total_ros_minutes",
        "simple_points_value",
        "trad_points_value",
        "categories_value",
    ]
    frontier_df = stats_df[stats_df_cols].merge(
        ros_df[ros_df_cols], how="inner", on="nba_player_id"
    )
    frontier_df["above_repl_simple"] = frontier_df.simple_points_value.apply(
        lambda val: 1 if val > 0 else 0
    )
    c = (
        alt.Chart(frontier_df)
        .mark_circle()
        .encode(
            x="total_ros_minutes",
            y="simple_points_per_100",
            tooltip="player",
            color="above_repl_simple",
        )
    )
    c.save("chart.html")


if __name__ == "__main__":
    main()
