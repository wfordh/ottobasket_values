from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.by import By

def setup_chrome_scraper():
	chrome_options = Options()
	chrome_options.add_argument("--headless")
	chrome_service = Service("../chromedriver") # pip install webdriver_manager and use ChromeDriverManager().install()?
	driver = webdriver.Chrome(
	    options=chrome_options,
	    service = chrome_service
	)
	return driver

def get_projections_page(driver):
	url = "https://hashtagbasketball.com/fantasy-basketball-projections"
	driver.get(url)

	dropdown = Select(driver.find_element(By.ID, "ContentPlaceHolder1_DDSHOW"))
	# "All" is represented as 600 in the webpage
	dropdown.select_by_value("600")
	driver.implicitly_wait(15)
	content = driver.page_source
	# does this need to be outside the function?
	driver.close()
	driver.quit()
	return content

# https://discuss.streamlit.io/t/issue-with-selenium-on-a-streamlit-app/11563/26

def extract_projections(content):
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
			# specify error. do I want to do anything?
			pass # I think?
		all_players.append(player_data)

	return all_players

# put it all together
# other functions private
# factory pattern?
def function():
	pass


