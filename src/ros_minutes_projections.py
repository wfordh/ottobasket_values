"""
This file scrapes, transforms, and then loads rest of season game and minutes
projections from hashtagbasketball.com into a Google Sheet. It is set up in order
to be run daily as a cron job during the relevant months.
"""

import json
import os
import time

import gspread
import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.select import Select
from webdriver_manager.firefox import GeckoDriverManager


def _setup_chrome_scraper() -> webdriver.firefox.webdriver.WebDriver:
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_service = Service(GeckoDriverManager().install())
    driver = webdriver.Firefox(options=chrome_options, service=chrome_service)
    return driver


def _shutdown_chrome_scraper(driver: webdriver.firefox.webdriver.WebDriver) -> None:
    driver.close()
    driver.quit()


def _get_projections_page(
    url: str, driver: webdriver.firefox.webdriver.WebDriver
) -> str:
    """
    Pulls the content of the projections page and reloads it after selecting the
    correct dropdown to return all players instead of the initially given top
    200, with a sleep period added for courtesy and to prevent blacklisting.
    """
    driver.get(url)
    time.sleep(1.2)
    dropdown = Select(driver.find_element(By.ID, "ContentPlaceHolder1_DDSHOW"))
    # "All" is represented as 900 in the webpage
    dropdown.select_by_value("900")
    time.sleep(3)
    content = driver.page_source
    return content


def _get_player_projection_data(
    row_data: list, name_idx: int, game_idx: int, minutes_idx: int
) -> dict:
    player_data = dict()
    player_data["name"] = row_data[name_idx].a.text.strip()
    player_data["pid"] = row_data[name_idx].a["href"].split("/")[1]
    player_data["games_forecast"] = str(row_data[game_idx].text.strip())
    player_data["minutes_forecast"] = str(row_data[minutes_idx].text.strip())
    return player_data


def _get_player_ytd_data(row_data: list, name_idx: int, game_idx: int) -> dict:
    """Year to date minutes and games played from the rankings page."""
    player_data = dict()
    player_data["pid"] = row_data[name_idx].a["href"].split("/")[1]
    player_data["games_played"] = str(row_data[game_idx].text.strip())
    return player_data


def _extract_projections(is_projections: bool, content: str) -> pd.DataFrame:
    """
    Extracts the projections for each player from the provided page. It pulls
    and cleans the name, player ID (for mapping), and forecasts for minutes and
    games. Returns a dataframe.
    """
    soup = BeautifulSoup(content, "html.parser")

    rows = soup.find_all("table", {"id": "ContentPlaceHolder1_GridView1"})[-1].find_all(
        "tr"
    )
    all_players = list()

    headers = rows.pop(0)
    headers = [th.get_text().strip().upper() for th in headers.find_all("th")]
    NAME_INDEX = headers.index("PLAYER")
    GP_INDEX = headers.index("GP")
    MINUTES_INDEX = headers.index("MPG")

    for row in rows:
        if row.find("td") is None or row.find("b"):
            continue
        row_data = row.find_all("td")
        # player_data = dict()

        try:
            if is_projections:
                player_data = _get_player_projection_data(
                    row_data, NAME_INDEX, GP_INDEX, MINUTES_INDEX
                )
            else:
                player_data = _get_player_ytd_data(row_data, NAME_INDEX, GP_INDEX)
            all_players.append(player_data)
        except Exception as e:
            # should probably add logging here...
            # specify error. do I want to do anything?
            print(player_data, e)
    return pd.DataFrame(all_players).dropna(axis=0)


def _get_fantasypros_projections() -> pd.DataFrame:
    """
    Currently not useful as no map between FP and Hashtag. Would need
    the map to be accessible from the GH action...
    """
    url = "https://www.fantasypros.com/nba/projections/ros-overall.php"
    resp = requests.get(url)
    soup = BeautifulSoup(resp.content, "html.parser")
    headers = [th.get_text().strip() for th in soup.find("thead").find_all("th")]
    headers.append("fantasypros_id")
    rows = soup.find("tbody").find_all("tr")
    data = []
    for row in rows:
        row_data = []
        for idx, td in enumerate(row.find_all("td")):
            if idx == 0:
                # just want the name
                row_data.append(td.a.text.strip())
            else:
                row_data.append(td.get_text().strip())
        # adding the FantasyPros ID to the end
        fp_id = int(row["class"][0].rsplit("-", 1)[-1])
        data.append(fp_id)

    df = pd.DataFrame(data, columns=headers)
    return df


def _setup_gdrive(client_key_string: str) -> gspread.client.Client:
    credentials = json.loads(client_key_string)
    return gspread.service_account_from_dict(credentials)


def _upload_data(gc: gspread.client.Client, data: pd.DataFrame) -> None:
    """Uploads data to the provided Google sheet."""
    sheet_key = "1RiXnGk2OFnGRmW9QNQ_1CFde0xfSZpyC9Cn3OLLojsY"
    sheet = gc.open_by_key(sheet_key)
    worksheet = sheet.get_worksheet(0)
    worksheet.update([data.columns.values.tolist()] + data.values.tolist())


# factory pattern?
def main():
    client_key_string = os.environ.get("SERVICE_BLOB", None)
    driver = _setup_chrome_scraper()
    projections_url = "https://hashtagbasketball.com/fantasy-basketball-projections"
    rankings_url = "https://hashtagbasketball.com/fantasy-basketball-rankings"
    proj_content = _get_projections_page(projections_url, driver)
    rankings_content = _get_projections_page(rankings_url, driver)
    proj_data = _extract_projections(True, proj_content)
    rankings_data = _extract_projections(False, rankings_content)
    try:
        data = proj_data.merge(rankings_data, how="left", on="pid")
        data.fillna(0, inplace=True)
        data["games_forecast"] = data.games_forecast.astype(
            int
        ) - data.games_played.astype(int)
        print("got projections")
        gc = _setup_gdrive(client_key_string)
        _upload_data(gc, data)
    except (KeyError, TypeError) as e:
        # again should prob use logging
        print(e)
    _shutdown_chrome_scraper(driver)
    print("done!")


if __name__ == "__main__":
    main()
