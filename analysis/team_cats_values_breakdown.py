import os
import sys

sys.path.append(os.path.abspath("src"))
from calc_stats import calc_categories_value, calc_per_game_projections
from leagues import get_league_rosters, get_league_scoring
from transform import prep_stats_df


def main():
    stats_df = prep_stats_df()
    projection_type = "rest_of_season"
    df = calc_per_game_projections(stats_df, projection_type=projection_type)
    cats_df = calc_categories_value(df, is_rollup=False)
    cats_df = cats_df.merge(
        df[
            [
                "ottoneu_player_id",
                "nba_player_id",
                "total_ros_minutes",
                "ottoneu_position",
            ]
        ],
        how="left",
        on="nba_player_id",
    )
    league_salaries = get_league_rosters(26)
    league_values_df = league_salaries.merge(
        cats_df, on="ottoneu_player_id", how="left"
    )
    league_values_df.player.fillna(
        league_values_df.player_name, inplace=True
    )  # swap player_name for ottoneu_name??
    league_values_df.ottoneu_position.fillna(league_values_df.position, inplace=True)
    # fill the rest of columns NA's with 0
    league_values_df.fillna(0, inplace=True)
    # league_scoring = get_league_scoring(league_input)
    league_values_df.to_csv("./data/league_26_cats.csv", index=False)
    league_values_df.groupby(["team_id", "team_name"])[
        ["vPTS", "vREB", "vAST", "vBLK", "vSTL", "vTOV", "vFTM", "vFGM", "vFG3M"]
    ].sum().reset_index().to_csv("./data/league_26_cats_rollup.csv", index=False)


if __name__ == "__main__":
    main()
