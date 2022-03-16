from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.by import By

chrome_ptions = Options()
chrome_ptions.add_argument("--headless")
driver = webdriver.Chrome(
    options=chrome_ptions,
    executable_path="../chromedriver",
)
url = "https://hashtagbasketball.com/fantasy-basketball-projections"
driver.get(url)

dropdown = Select(driver.find_element(By.ID, "ContentPlaceHolder1_DDSHOW"))
dropdown.select_by_value("600")
# does it reload automatically?
driver.implicitly_wait(15)
content = driver.page_source
# feed this into BeautifulSoup()
# https://discuss.streamlit.io/t/issue-with-selenium-on-a-streamlit-app/11563/26

soup = BeautifulSoup(content, 'html.parser')

rows = soup.find_all("table", {"class":"table table-bordered"})[-1].find_all('tr')
all_players = list()

for row in rows:
	if row.find('td') is None or row.find('b'):
		continue
	row_data = row.find_all('td')
	player_data = dict()
	try:
		player_data['name'] = row_data[1].span.text.strip()
		player_data['pid'] = row_data[1].a['href'].split("/")[1]
		player_data['games_forecast'] = int(row_data[4].text.strip())
		player_data['minutes_forecast'] = float(row_data[5].text.strip())
	except:
		pass # I think?
	all_players.append(player_data)
	


