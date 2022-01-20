import time

import pandas as pd
import requests
import streamlit as st
from bs4 import BeautifulSoup


# not sure I need st.cache on all of them...
@st.cache
def get_league_scoring(league_id):
    league_url = f"https://ottoneu.fangraphs.com/basketball/{league_id}/settings"
    resp = requests.get(league_url)
    soup = BeautifulSoup(resp.content, "html.parser")
    table = soup.find("main").find("table").find("tbody").find_all("tr")
    points_row = table[2]  # better way to do this??
    return points_row.find_all("td")[-1].get_text().strip().lower().replace(" ", "_")


@st.cache
def get_league_rosters(league_id):
    league_url = (
        f"https://ottoneu.fangraphs.com/basketball/{league_id}/csv/rosters?web=1"
    )
    league_salaries = pd.read_csv(league_url)
    league_salaries.columns = [
        col.lower().replace(" ", "_") for col in league_salaries.columns
    ]
    league_salaries["salary"] = league_salaries.salary.str.replace("$", "", regex=False).astype(int)
    league_salaries.rename(
        columns={"player_id": "ottoneu_player_id", "position(s)": "position"},
        inplace=True,
    )
    return league_salaries
