import chompjs
import pandas as pd
import requests
import tqdm
from bs4 import BeautifulSoup

stat_mapping = {
    "42": "games_played",
    "40": "minutes",
    "19": "fg_pct",
    "20": "ft_pct",
    "17": "fg3m",
    "6": "reb",
    "3": "ast",
    "35": "ast_tov",
    "2": "stl",
    "1": "blk",
    "11": "tov",
    "0": "pts",
    "18": "fg3a",
    "15": "ftm",
    "16": "fta",
    "13": "fgm",
    "14": "fga",
    "21": "fg3_pct",
    "23": None,
    "24": None,
    "25": None,
    "26": None,  # rounded assists
    "27": None,  # rounded blocks
    "28": "minutes_per_game",
    "29": "points_per_game",
    "30": "reb_per_game",
    "31": "stl_per_game",
    "32": "tov_per_game",
    "33": None,
    "34": None,
    "36": None,  # rounded 3p%??
}


def main():
    # will need to update season each year in both URL and headers
    params = {"view": "kona_player_info"}
    url = "https://lm-api-reads.fantasy.espn.com/apis/v3/games/fba/seasons/2024/segments/0/leaguedefaults/1"
    headers = {
        "X-Fantasy-Source": "kona",
        "X-Fantasy-Filter": '{"players":{"filterStatsForExternalIds":{"value":[2023,2024]},"filterSlotIds":{"value":[0,1,2,3,4,5,6,7,8,9,10,11]},"filterStatsForSourceIds":{"value":[0,1]},"useFullProjectionTable":{"value":true},"sortAppliedStatTotal":{"sortAsc":false,"sortPriority":3,"value":"102024"},"sortDraftRanks":{"sortPriority":2,"sortAsc":true,"value":"STANDARD"},"sortPercOwned":{"sortPriority":4,"sortAsc":false},"limit":500,"filterStatsForTopScoringPeriodIds":{"value":5,"additionalValue":["002024","102024","002023","012024","022024","032024","042024"]}}}',
    }
    r = requests.get(url, headers=headers, params=params)
    soup = BeautifulSoup(r.content, "html.parser")
    players = chompjs.parse_js_object(soup.get_text()).get("players", None)

    cleaned_players = list()
    # 500 players returned - can adjust in headers
    for player in tqdm.tqdm(players):
        # 5 is the projections
        # the id for it is 102024
        # getting totals instead of averages
        projected_stats = dict()
        projected_stats["player_name"] = player["player"]["fullName"]
        projected_stats["espn_id"] = player["player"]["id"]
        player_stats = player["player"].get("stats")
        while player_stats:
            stats = player_stats.pop()
            # will also need to update season here
            if stats["id"] == "102024":
                player_proj_stats = stats.get("stats")
                for k, v in player_proj_stats.items():
                    projected_stats[k] = v
                break
        # this is a dict
        # need player name and ID

        cleaned_players.append(projected_stats)

    espn_df = pd.DataFrame(cleaned_players)
    new_columns = [
        stat_mapping[col] if col in stat_mapping.keys() else col
        for col in espn_df.columns
    ]
    espn_df.columns = new_columns
    espn_df.to_csv(
        "data/2023-24_preseason_projections/espn_projections_2023-24.csv", index=False
    )


if __name__ == "__main__":
    main()
