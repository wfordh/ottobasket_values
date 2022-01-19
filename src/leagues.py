import time
import requests
import pandas as pd
from bs4 import BeautifulSoup


def get_league_teams(league_id):
    # using this URL as it's easier to pull the team names and IDs
    league_url = f"https://ottoneu.fangraphs.com/basketball/{league_id}/finances"
    resp = requests.get(league_url)
    soup = BeautifulSoup(resp.content, "html.parser")
    rows = (
        soup.find_all("section", {"class": "section-container"})[1]
        .find("div", {"class": "table-container"})
        .find("tbody")
        .find_all("tr")
    )
    teams = dict()
    for row in rows:
        td = row.find("td")
        team_name = td.get_text()
        team_id = td.a["href"].rsplit("/", maxsplit=1)[1]
        teams[team_id] = team_name
    return teams


def get_team_players(league_id, team_data):
    players = dict()
    for team_id, team_name in team_data.items():
        team_url = (
            f"https://ottoneu.fangraphs.com/basketball/{league_id}/team/{team_id}"
        )
        resp = requests.get(team_url)
        soup = BeautifulSoup(resp.content, "html.parser")
        table = (
            soup.find("main")
            .find("div", {"class": "split-layout__primary"})
            .find("table")
            .find("tbody")
        )
        for row in table.find_all("tr"):
            time.sleep(0.7)
            player_data = row.find_all("td")
            salary = int(player_data[-1].get_text().strip().replace("$", ""))
            player_id = player_data[0].a["href"].rsplit("/", maxsplit=1)[1]
            players[player_id] = {"salary": salary, "team_id": team_id}
    return players


def get_league_salary_data(league_id):
    teams = get_league_teams(league_id)
    salary_data = get_team_players(league_id, teams)
    return (
        pd.DataFrame.from_dict(salary_data, orient="index")
        .reset_index()
        .rename(columns={"index": "ottoneu_player_id"})
    )
