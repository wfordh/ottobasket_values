"""
- start with team surplus by player
- top 12 by RoS are rotation
- next 5 are depth
- bottom 8 are other (injured & prospects)

to do: 
- extend to other scoring types
- incorporate into existing league_values page
"""
import os
import sys

sys.path.append(os.path.abspath("src"))
import pandas as pd

from leagues import get_league_rosters, get_league_scoring
from pipeline import ottobasket_values_pipeline
from transform import (find_surplus_positions, get_draftable_players,
                       get_scoring_minutes_combo, prep_stats_df)

LEAGUE = 31


def main():
    stats_df = prep_stats_df()
    values_df = get_scoring_minutes_combo("rest_of_season", stats_df)
    league_salaries = get_league_rosters(LEAGUE)
    league_values_df = league_salaries.merge(
        values_df, on="ottoneu_player_id", how="left"
    )
    league_values_df.player.fillna(
        league_values_df.player_name, inplace=True
    )  # swap player_name for ottoneu_name??
    league_values_df.ottoneu_position.fillna(league_values_df.position, inplace=True)
    # fill the rest of columns NA's with 0
    league_values_df.fillna(0, inplace=True)
    league_scoring = get_league_scoring(LEAGUE)
    if league_scoring == "categories":
        scoring_col = f"{league_scoring}_value"
    elif league_scoring == "simple_points":
        scoring_col = f"{league_scoring}_value"
    else:
        scoring_col = "trad_points_value"
    # need it to be RoS for now...so only doing ros for now
    league_values_df.rename(columns={scoring_col: scoring_col + "_ros"}, inplace=True)
    league_values_df["ros_surplus"] = (
        league_values_df[f"{scoring_col}_ros"] - league_values_df.salary
    )
    # might incorporate this later somehow
    # league_values_df["ytd_surplus"] = (
    #     league_values_df[f"{scoring_col}_ytd"] - league_values_df.salary
    # )
    # league_values_df["simple_points"] = league_values_df.simple_points_value_ros
    # need to pick one value type and stick with it as just "simple_points"
    league_values_df["in_rotation"] = None
    league_values_df["prospects"] = None
    team_values = league_values_df.groupby("team_name")
    team_frames = list()

    for team_name, team_data in team_values:

        team_data[f"{scoring_col}_position"] = find_surplus_positions(
            team_data, scoring_type=league_scoring
        )
        draftable_players = get_draftable_players(
            team_data,
            scoring_type=league_scoring,
            num_centers=1,
            num_forwards=2,
            num_guards=3,
            num_f_c=1,
            num_g_f=1,
            num_util=4,
        )
        # have rotation / depth / other (prospects & injured)?
        team_data["in_rotation"] = team_data.nba_player_id.apply(
            lambda p: 1 if p in draftable_players else 0
        )
        prospects = (
            team_data.sort_values(by=league_scoring, ascending=True)
            .head(8)
            .nba_player_id.tolist()
        )
        team_data["other_players"] = team_data.nba_player_id.apply(
            lambda p: 1 if p in prospects else 0
        )
        team_data["depth"] = team_data.apply(
            lambda p: 1 if p.in_rotation + p.other_players == 0 else 0, axis=1
        )
        # print(team_data)
        rotation_value = (
            team_data.loc[team_data.nba_player_id.isin(draftable_players)]
            .simple_points_value_ros.sum()
            .round()
        )
        # need to drop duplicates before doing any summing
        team_data["team_name"] = team_name
        team_frames.append(team_data)

    league_values_df = pd.concat(team_frames)
    # now roll up to team level data
    sum_cols = ["simple_points_value_ros", "ros_surplus"]
    rotation_data = (
        league_values_df.where(league_values_df.in_rotation == 1)
        .groupby("team_name")[sum_cols]
        .sum()
        .add_prefix("rotation_")
        .reset_index()
    )
    depth_data = (
        league_values_df.where(league_values_df.depth == 1)
        .groupby("team_name")[sum_cols]
        .sum()
        .add_prefix("depth_")
        .reset_index()
    )
    other_players_data = (
        league_values_df.where(league_values_df.other_players == 1)
        .groupby("team_name")[sum_cols]
        .sum()
        .add_prefix("other_")
        .reset_index()
    )
    print(rotation_data)
    team_value_by_rotation_levels = pd.DataFrame()
    team_value_by_rotation_levels["team_name"] = league_values_df.team_name.unique()
    team_value_by_rotation_levels = (
        team_value_by_rotation_levels.merge(rotation_data, how="inner", on="team_name")
        .merge(depth_data, how="inner", on="team_name")
        .merge(other_players_data, how="inner", on="team_name")
    )
    print(team_value_by_rotation_levels)


if __name__ == "__main__":
    main()
