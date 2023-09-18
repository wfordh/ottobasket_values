import pandas as pd
from nba_api.stats.endpoints import playerindex

import ros_minutes_projections as rmp
from leagues import get_average_values

nba_to_ottoneu_name_map = {
    "Nicolas Claxton": "Nic Claxton",
}

"""
add season arg for CLI use?
"""


def main():
    existing_data = pd.read_csv("./data/mappings.csv")
    # ottoneu data
    values = get_average_values()

    # hashtag basketball data
    driver = rmp._setup_chrome_scraper()
    projections_url = "https://hashtagbasketball.com/fantasy-basketball-projections"
    proj_content = rmp._get_projections_page(projections_url, driver)
    proj_data = rmp._extract_projections(True, proj_content)
    rmp._shutdown_chrome_scraper(driver)

    # nba data
    nba_raw = playerindex.PlayerIndex(season="2023-24").get_dict()["resultSets"][0]
    nba_data = pd.DataFrame(nba_raw["rowSet"], columns=nba_raw["headers"])
    # only want new players and a few columns
    nba_data_new = nba_data.loc[
        nba_data.FROM_YEAR == "2023",
        ["PERSON_ID", "PLAYER_LAST_NAME", "PLAYER_FIRST_NAME", "TEAM_ID"],
    ]
    nba_data_new["name"] = (
        nba_data_new.PLAYER_FIRST_NAME + " " + nba_data_new.PLAYER_LAST_NAME
    )

    rookies = nba_data_new.merge(proj_data, how="outer", on="name").merge(
        values, how="outer", on="name"
    )
    rookies[["name", "ottoneu_player_id", "pid", "PERSON_ID"]].rename(
        columns={"pid": "hashtag_id", "PERSON_ID": "nba_player_id"}
    ).dropna(subset="nba_player_id").to_csv("./data/rookies.csv", index=False)

    ###
    # do the steps above, but don't write to CSV
    # rookies.assign(stats_player_id = None, espn_id = None, bref_id = None, ottoneu_position = None)[mappings.columns]
    # rookies.dropna(subset="ottoneu_player_id").set_index("ottoneu_player_id")
    # mappings.dropna(subset="ottoneu_player_id").set_index("ottoneu_player_id")
    # mappings.update(rookies)
    # mappings.reset_index()
    # won't have the players in mappings who don't have an ottoneu ID, ie those w/ espn/bref IDs
    # still need stats_player_id from DRIP
    # run something weekly to alert to who is rostered, in the NBA, and doesn't have
    # non - Ottoneu IDs?
    ###


if __name__ == "__main__":
    main()
