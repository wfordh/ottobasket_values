import datetime
from zoneinfo import ZoneInfo

import streamlit as st

st.markdown(
    """
	# Glossary and Data Sources

	## Glossary
	- Current minutes: An estimate of how many minutes a player would play today based on roster construction and health.
	- Full strength minutes: An estimate of how many minutes a player would play if their team's roster was at full strength, ie everyone was healthy and active.
	- Rest of season minutes: A projection of how many minutes the player will play for the remaining duration of the season. 
	- Year to date values: Reflect players' production for the season to date. It uses Ottoneu's basketball leaderboard, so it will use the previous season's data during the offseason until the next season starts.

	## Data Sources
	- [DARKO](https://docs.google.com/spreadsheets/d/1mhwOLqPu2F9026EQiVxFPIN1t9RGafGpl-dokaIsm9c/edit#gid=284274620)
		- Current minutes come from DARKO.
		- Accounts for half of the stats projections.
	- [DRIP](https://dataviz.theanalyst.com/nba-stats-hub/)
		- Accounts for half of the stats projections.
	- [Hashtag Basketball](https://hashtagbasketball.com/fantasy-basketball-projections)
		- Minute and game projections account for the rest of season minutes projection.
	- [538](https://fivethirtyeight.com/methodology/how-our-nba-predictions-work/)
		- Full strength minutes come from 538 and are pulled in via DARKO.


	Feel free to request clarifications or additions on the [community forums](https://www.community.ottoneu.com/)
	"""
)

now = datetime.datetime.now(tz=ZoneInfo("US/Pacific"))
st.markdown(
    "About page / README can be found [here](https://github.com/wfordh/ottobasket_values/blob/main/README.md)"
)
st.text("ros = rest of season. fs = full strength. ytd = year to date.")
st.text(f"Last updated: {now.strftime('%Y-%m-%d %I:%M %p (Pacific)')}")
