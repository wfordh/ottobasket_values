import datetime
from zoneinfo import ZoneInfo

import streamlit as st

st.markdown(
    """
	# Glossary and Data Sources

	## Glossary
	- Rest of season minutes: A projection of how many minutes the player will play for the remaining duration of the season. The associated values do not take into account any stats players have already accumulated. It should be read as "if the season started today, this is what Player X is projected to do."
	- Year to date values: Reflect players' production for the season to date. It uses Ottoneu's basketball leaderboard, so it will use the previous season's data during the offseason until the next season starts.
	- Current minutes: An estimate of how many minutes a player would play today given the state of the league (ie injuries, rest, etc). It is not reasonable to project this number forward since you cannot expect the state of the league to remain the same as other players heal or get injured, or rotations change. It is best thought of as a DFS projection.
	- Full strength minutes (deprecated): An estimate of how many minutes a player would play if their team's roster was at full strength, ie everyone was healthy and active.
	

	## Data Sources
	- [DARKO](https://docs.google.com/spreadsheets/d/1mhwOLqPu2F9026EQiVxFPIN1t9RGafGpl-dokaIsm9c/edit#gid=284274620)
		- Current minutes come from DARKO.
		- Accounts for half of the stats projections.
	- [DRIP](https://dataviz.theanalyst.com/nba-stats-hub/)
		- Accounts for half of the stats projections.
	- [Hashtag Basketball](https://hashtagbasketball.com/fantasy-basketball-projections)
		- Minute and game projections account for the rest of season minutes projection.
	- [538](https://fivethirtyeight.com/methodology/how-our-nba-predictions-work/)
		- [Deprecated] Full strength minutes come from 538 and are pulled in via DARKO.

	## Player ID Mapping
	You may find the mapping / crosswalk file I use [here](https://github.com/wfordh/ottobasket_values/blob/main/data/mappings_update_2023-09-14.csv). It is updated in a semi-manual manner. Please open an [issue on GitHub](https://github.com/wfordh/ottobasket_values/issues), DM me in the Ottoneu Slack, tag me on the [Ottoneu forums](https://www.community.ottoneu.com/), or tag [me on Twitter](https://twitter.com/wfordh)(don't check Twitter that often anymore) if a player is missing.

	Feel free to request clarifications or additions on the [community forums](https://www.community.ottoneu.com/).
	"""
)

now = datetime.datetime.now(tz=ZoneInfo("US/Pacific"))
st.markdown(
    "About page / README can be found [here](https://github.com/wfordh/ottobasket_values/blob/main/README.md)"
)
st.text("ros = rest of season. ytd = year to date.")
st.text(f"Last updated: {now.strftime('%Y-%m-%d %I:%M %p (Pacific)')}")
