import logging
import time

import pandas as pd
import requests
import streamlit as st
from bs4 import BeautifulSoup


# not sure I need st.cache on all of them...
@st.cache_data(ttl=12 * 60 * 60)  # type: ignore
def get_league_scoring(league_id: int) -> str:
    """Scrapes the league's settings page. Returns the scoring type."""
    league_url = f"https://ottoneu.fangraphs.com/basketball/{league_id}/settings"
    resp = requests.get(league_url)
    soup = BeautifulSoup(resp.content, "html.parser")
    # pytype: disable=attribute-error
    table = soup.find("main").find("table").find("tbody").find_all("tr")  # type: ignore
    points_row = table[2]  # better way to do this??
    scoring = points_row.find_all("td")[-1].get_text().strip().lower().replace(" ", "_")
    # pytype: enable=attribute-error
    if scoring == "traditional_points":
        return "trad_points"
    return scoring


@st.cache_data(ttl=12 * 60 * 60)  # type: ignore
def get_league_rosters(league_id: int) -> pd.DataFrame:
    """Pulls the league's rosters and cleans them. Returns a dataframe."""
    league_url = (
        f"https://ottoneu.fangraphs.com/basketball/{league_id}/csv/rosters?web=1"
    )
    league_salaries = pd.read_csv(league_url)
    league_salaries.columns = pd.Index(
        [col.lower().replace(" ", "_") for col in league_salaries.columns]
    )
    league_salaries["salary"] = league_salaries.salary.str.replace(
        "$", "", regex=False
    ).astype(int)
    league_salaries.rename(
        columns={"player_id": "ottoneu_player_id", "position(s)": "position"},
        inplace=True,
    )
    return league_salaries


def get_league_leaderboard(
    league_id: int,
    start_date: str = "",
    end_date: str = "",
    free_agents_only: bool = False,
) -> pd.DataFrame:
    """Basically duplicating the `get_ottoneu_leaderboard() function
    in transform.py, but with more arguments.
    """
    if (start_date and not end_date) or (not start_date and end_date):
        logging.warn("Need either both dates or neither!")
    base_url = f"https://ottoneu.fangraphs.com/basketball/26/ajax/player_leaderboard?positions[]=G&positions[]=F&positions[]=C&minimum_minutes=0&sort_by=salary&sort_direction=DESC&free_agents_only={free_agents_only}&include_my_team=false&export=export&game_range_start_date={start_date}&game_range_end_date={end_date}"
    return pd.read_csv(base_url).rename(columns={"id": "ottoneu_player_id"})


def get_average_values() -> pd.DataFrame:
    """
    Pulls the average values and roster percentages across all of Ottoneu basketball.
    Returns a dataframe.
    """
    df = pd.read_csv("https://ottoneu.fangraphs.com/basketball/average_values?csv=1")
    df.columns = pd.Index([col.lower() for col in df.columns])
    return df.rename(
        columns={
            "id": "ottoneu_player_id",
            # "position": "ottoneu_position",
        }
    )
