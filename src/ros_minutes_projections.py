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
    num_players_dropdown = Select(
        driver.find_element(By.ID, "ContentPlaceHolder1_DDSHOW")
    )
    # "All" is represented as 900 in the webpage
    num_players_dropdown.select_by_value("900")
    time.sleep(2.1)
    totals_dropdown = Select(driver.find_element(By.ID, "ContentPlaceHolder1_DDRANK"))
    totals_dropdown.select_by_value("TOT")
    # for getting the stats for rookies
    three_point_perc_checkbox = driver.find_element(By.ID, "ContentPlaceHolder1_CB3PP")
    three_point_perc_checkbox.click()
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
    fg_data = (
        row_data[headers.index("FG%")]
        .find("span", {"class": "float-end small"})
        .text.split("/")
    )
    player_data["fga_game"] = fg_data[1].replace(")", "")
    player_data["fgm_game"] = fg_data[0].replace("(", "")
    ft_data = (
        row_data[headers.index("FT%")]
        .find("span", {"class": "float-end small"})
        .text.split("/")
    )
    player_data["fta_game"] = ft_data[1].replace(")", "")
    player_data["ftm_game"] = ft_data[0].replace("(", "")
    fg3_data = (
        row_data[headers.index("3P%")]
        .find("span", {"class": "float-end small"})
        .text.split("/")
    )
    player_data["fg3a_game"] = fg3_data[1].replace(")", "")
    player_data["fg3m_game"] = fg_data[0].replace("(", "")
    player_data["fg3m_game"] = row_data[headers.index("3PM")].span.text.strip()
    player_data["pts_game"] = row_data[headers.index("PTS")].span.text.strip()
    player_data["reb_game"] = row_data[headers.index("TREB")].span.text.strip()
    player_data["ast_game"] = row_data[headers.index("AST")].span.text.strip()
    player_data["stl_game"] = row_data[headers.index("STL")].span.text.strip()
    player_data["blk_game"] = row_data[headers.index("BLK")].span.text.strip()
    player_data["tov_game"] = row_data[headers.index("TO")].span.text.strip()
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
        if row.find("td") is None or row.find("b") or row.find("td").text == "R#":
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
        except AttributeError as e:
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


def _upload_data(gc: gspread.client.Client, data: pd.DataFrame, sheet_key: str) -> None:
    """Uploads data to the provided Google sheet."""
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
        # commented out on 2/25/23 since hashtagbasketball switched back to
        # forecasting as expected with the rest of the season without including
        # the season to date
        # data["games_forecast"] = data.games_forecast.astype(
        #    int
        # ) - data.games_played.astype(int)
        print("got projections")
        gc = _setup_gdrive(client_key_string)
        sheet_key = "1RiXnGk2OFnGRmW9QNQ_1CFde0xfSZpyC9Cn3OLLojsY"
        _upload_data(gc, data, sheet_key)
    except (KeyError, TypeError) as e:
        # again should prob use logging
        print(e)
    _shutdown_chrome_scraper(driver)
    print("done!")


if __name__ == "__main__":
    main()
