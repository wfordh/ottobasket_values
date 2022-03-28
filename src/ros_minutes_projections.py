
import json
import os

import gspread
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from webdriver_manager.chrome import ChromeDriverManager



def _setup_chrome_scraper():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(options=chrome_options, service=chrome_service)
    return driver

def _shutdown_chrome_scraper(driver):
	driver.close()
    driver.quit()

def _get_projections_page(driver):
    url = "https://hashtagbasketball.com/fantasy-basketball-projections"
    driver.get(url)

    dropdown = Select(driver.find_element(By.ID, "ContentPlaceHolder1_DDSHOW"))
    # "All" is represented as 600 in the webpage
    dropdown.select_by_value("600")
    driver.implicitly_wait(30)
    content = driver.page_source
    return content


# https://discuss.streamlit.io/t/issue-with-selenium-on-a-streamlit-app/11563/26


def _extract_projections(content):
    soup = BeautifulSoup(content, "html.parser")

    rows = soup.find_all("table", {"class": "table table-bordered"})[-1].find_all("tr")
    all_players = list()

    for row in rows:
        if row.find("td") is None or row.find("b"):
            continue
        row_data = row.find_all("td")
        player_data = dict()
        try:
            player_data["name"] = row_data[1].span.text.strip()
            player_data["pid"] = row_data[1].a["href"].split("/")[1]
            player_data["games_forecast"] = str(row_data[4].text.strip())
            player_data["minutes_forecast"] = str(row_data[5].text.strip())
        except:
            # specify error. do I want to do anything?
            pass  # I think?
        all_players.append(player_data)
    print(len(all_players))
    return pd.DataFrame(all_players).dropna(axis=0)


def _setup_gdrive(client_key_string, is_local=False):
    credentials = json.loads(client_key_string)
    return gspread.service_account_from_dict(credentials)


def _upload_data(gc, data):
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
    print(data.shape)
    print("got projections")
    gc = _setup_gdrive(client_key_string)
    _upload_data(gc, data)
    _shutdown_chrome_scraper(driver)
    print("done!")


if __name__ == "__main__":
    main()
