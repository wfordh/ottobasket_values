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


def _get_projections_page(driver: webdriver.firefox.webdriver.WebDriver) -> str:
    """
    Pulls the content of the projections page and reloads it after selecting the
    correct dropdown to return all players instead of the initially given top
    200, with a sleep period added for courtesy and to prevent blacklisting.
    """
    url = "https://hashtagbasketball.com/fantasy-basketball-projections"
    driver.get(url)
    time.sleep(1.2)
    dropdown = Select(driver.find_element(By.ID, "ContentPlaceHolder1_DDSHOW"))
    # "All" is represented as 900 in the webpage
    dropdown.select_by_value("900")
    time.sleep(3)
    content = driver.page_source
    return content


def _extract_projections(content: str) -> pd.DataFrame:
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

    for row in rows:
        if row.find("td") is None or row.find("b"):
            continue
        row_data = row.find_all("td")
        player_data = dict()
        try:
            player_data["name"] = row_data[1].a.text.strip()
            player_data["pid"] = row_data[1].a["href"].split("/")[1]
            player_data["games_forecast"] = str(row_data[4].text.strip())
            player_data["minutes_forecast"] = str(row_data[5].text.strip())
            all_players.append(player_data)
        except:
            # specify error. do I want to do anything?
            pass  # I think?
    return pd.DataFrame(all_players).dropna(axis=0)


def _setup_gdrive(client_key_string: str) -> gspread.client.Client:
    print(client_key_string)
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
    content = _get_projections_page(driver)
    data = _extract_projections(content)
    print("got projections")
    gc = _setup_gdrive(client_key_string)
    _upload_data(gc, data)
    _shutdown_chrome_scraper(driver)
    print("done!")


if __name__ == "__main__":
    main()
