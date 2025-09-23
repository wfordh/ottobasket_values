# mypy: ignore-errors
import logging
import time

import pandas as pd
import requests
import streamlit as st
from bs4 import BeautifulSoup


# not sure I need st.cache on all of them...
@st.cache_data(ttl=12 * 60 * 60)  # type: ignore
def get_league_scoring(league_id: int, df: pd.DataFrame) -> str:
    """Scrapes the league's settings page. Returns the scoring type."""
    if df.empty:
        sheet_key = "14TkjXjFSWDQsHZy6Qt77elLnVpi1HwrpbqzVC4JKDjc"
        df = pd.read_csv(
            f"https://docs.google.com/spreadsheets/d/{sheet_key}/export?format=csv&gid=0"
        )
    scoring = (
        df.loc[df.league_id == league_id, "points_system"]
        .values[0]
        .strip()
        .lower()
        .replace(" ", "_")
    )
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
    base_url = f"https://ottoneu.fangraphs.com/basketball/{league_id}/ajax/player_leaderboard?positions[]=G&positions[]=F&positions[]=C&minimum_minutes=0&sort_by=salary&sort_direction=DESC&free_agents_only={free_agents_only}&include_my_team=false&export=export&game_range_start_date={start_date}&game_range_end_date={end_date}"
    return pd.read_csv(base_url).rename(columns={"id": "ottoneu_player_id"})


def get_average_values() -> pd.DataFrame:
    """
    Pulls the average values and roster percentages across all of Ottoneu basketball.
    Returns a dataframe.

    Move to utils.py?
    """
    df = pd.read_csv("https://ottoneu.fangraphs.com/basketball/average_values?csv=1")
    df.columns = pd.Index([col.lower().replace(" ", "_") for col in df.columns])
    return df.rename(
        columns={
            "id": "ottoneu_player_id",
            # "position": "ottoneu_position",
        }
    )


def get_league_settings(league_id: int) -> dict:
    """
    Pulls the settings of interest for each league
    """
    league_url = f"https://ottoneu.fangraphs.com/basketball/{league_id}/settings"
    r = requests.get(league_url)
    soup = BeautifulSoup(r.content, "html.parser")
    table = soup.find("table")
    body = table.find("tbody")
    rows = body.find_all("tr")
    dimensions_of_interest = [
        "Roster Settings",
        "Playoff Settings",
        "Points System",
        "Matchups Per Week",
    ]
    league_settings = dict()
    for row in rows:
        row_data = row.find_all("td")
        if row_data[0].text in dimensions_of_interest:
            dim = row_data[0].text.strip().lower().replace(" ", "_")
            league_settings[dim] = row_data[1].text.strip()
    return league_settings


def get_league_first_year(league_id: int) -> str:
    league_url = f"https://ottoneu.fangraphs.com/basketball/{league_id}/draft_history"
    r = requests.get(league_url)
    soup = BeautifulSoup(r.content, "html.parser")
    drafts = (
        soup.find("main")
        .find("div", {"class": "page-header__secondary"})
        .find("div", {"class": "page-header__section"})
        .find_all("h5")
    )
    first_year = drafts.pop()
    return first_year.text.strip()


def get_standings_page(league_id: int, season: str) -> pd.DataFrame:
    # make season map
    # 4 = 2023-24, 3 = 2022-23, 2 = 2021-22
    season_map = {"2024-25": 5, "2023-24": 4, "2022-23": 3, "2021-22": 2, "2020-21": 1}
    url = f"https://ottoneu.fangraphs.com/basketball/{league_id}/standings/{season_map[season]}"
    r = requests.get(url, timeout=None)
    soup = BeautifulSoup(r.content, "html.parser")
    tables = soup.find_all("table")
    main_table = get_table(tables[1])
    shots_table = get_table(tables[2])
    # why is the suffix _foo???
    overall_table = main_table.merge(
        shots_table, how="inner", on=["team", "g", "mins"], suffixes=("", "_foo")
    )
    for col in overall_table.columns:
        if col == "team":
            continue
        overall_table[col] = overall_table[col].astype(float)
    return overall_table


def get_table(table) -> pd.DataFrame:
    """
    Helper function used in get_standings_page()
    """
    headers = [
        th.text.lower().strip() for th in table.find("thead").find("tr").find_all("th")
    ]
    rows = [
        [td.text.strip() for td in row.find_all("td")]
        for row in table.find("tbody").find_all("tr")
    ]
    return pd.DataFrame(rows, columns=headers)


def get_schedule_week(league_id: int = 26) -> int:
    url = f"https://ottoneu.fangraphs.com/basketball/{league_id}/"
    r = requests.get(url)
    soup = BeautifulSoup(r.content, "html.parser")
    schedule_header = soup.find("h3").text.strip().split()
    schedule_week = int(schedule_header[-2])
    return schedule_week


def get_league_info() -> pd.DataFrame:
    """
    should probably merge this and the get_league_scoring function somehow since they pull the same sheet
    """
    sheet_key = "14TkjXjFSWDQsHZy6Qt77elLnVpi1HwrpbqzVC4JKDjc"
    return pd.read_csv(
        f"https://docs.google.com/spreadsheets/d/{sheet_key}/export?format=csv&gid=0"
    )
