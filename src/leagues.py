import requests
import pandas as pd
from bs4 import BeautifulSoup

def get_league_teams(league_id):
    # using this URL as it's easier to pull the team names and IDs
    league_url = f"https://ottoneu.fangraphs.com/basketball/{league_id}/finances"
    resp = requests.get(league_url)
    soup = BeautifulSoup(resp.content, 'html.parser')
    rows = soup.find_all("section", {"class": "section-container"})[1].find("div", {"class": "table-container"}).find('tbody').find_all('tr')
    teams = dict()
    for row in rows:
        td = row.find('td')
        team_name = td.get_text()
        team_id = td.a['href'].rsplit("/", maxsplit=1)[1]
        teams[team_id] = team_name
    return teams

def get_team_players(team_data):
    pass
