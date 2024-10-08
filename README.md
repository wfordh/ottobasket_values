# Ottobasket Values
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](share.streamlit.io/wfordh/ottobasket_values/main/src/ottobasket_values.py) [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)


## What is this?
[Ottoneu](https://ottoneu.fangraphs.com/) is a fantasy sports platform designed to imitate the job of real GMs in different sports and launched fantasy basketball this year to complement its fantasy baseball and football offerings. An important part of the experience is valuing players within the constraints of the game - a $400 salary cap, 25 roster spots, and a scoring system - and allocating your team's resources accordingly. This project calculates and assigns dollar values to players based on projected production and presents them on a lightweight web app. There are values for each of the three scoring systems available in Ottoneu basketball - traditional points, simple points, and categories - and covers "current" minutes projections. I drew inspiration from [Justin Vibber's](https://twitter.com/justinvibber?lang=en) [Surplus](https://www.patreon.com/vibbot) [Calculator](https://fantasy.fangraphs.com/ottoneu-surplus-calculator/), which is the most prominent and public example for Ottoneu's flagship sport, baseball. 


## How is it done?

The values are built off of the [DARKO](https://apanalytics.shinyapps.io/DARKO/) and [DRIP](https://theanalyst.com/na/2021/10/nba-drip-daily-updated-rating-of-individual-performance/) projections, which are per 100 projections for a variety of stats. I average and convert the relevant stats into two per game projections based on DARKO's current minute projections and Hashtag Basketball's rest of season minute projections. The current minute projections update often and incorporate injury status and other information, while the rest of season minutes are a prediction of how a team's minutes will break down for the rest of the season. The next step is converting the per game projections into projected production for each of the three scoring systems. The points systems use linear weights for different box score statistics to arrive at a projection while category projections are slightly more complicated. I am currently using a method [calculating z-scores for each category](https://www.pitcherlist.com/fantasy-101-how-to-turn-projections-into-rankings-and-auction-values/), but may change that in the future (see [Roadmap](https://github.com/wfordh/ottobasket_values#roadmap)).

Once the point values are calculated, positions are assigned and the replacement value cutoff is found. Ottoneu uses 3 guard spots, 2 forwards, 1 center, 1 guard / forward, 1 forward / center, and 2 utility spots across 12 teams. Each player has a "most valuable position" assigned to them based on their position eligibility and which of the three main positions (G, F, C) they rank highest in by projected production. The top players are found for each position by taking their "most valuable position" and finding the top players for each position, with the cutoff determined by the number of position spots times the number of teams. For example, the top 36 guards are ranked and so on for the forwards and centers before taking the next 12 best players that are eligible for the forward / center lineup spot, which could be a mix of 12 centers and 0 forwards, 4 centers and 8 forwards, or any other combination. I decided to rank the top 36 utility players instead of the top 24 in order to lower the cutoff for replacement value since there are players on the bench that will provide value when filling in and are a step above the rest of the players.

With the player pool identified, I find the lowest projected production and set it as the replacement level and calculate the surplus factor. Each player's projected production is multiplied by the surplus factor to get their dollar value, and players outside of the pool are given a value of $0. Surplus values can then be calculated by comparing the player's value to their current salary.


## How to use the values

The values are a good signpost to see how your team stacks up based on how much you are spending on players versus the amount of value they are generating. If you have positive surplus, then it's a good indication you have a quality team and maybe have more wiggle room for taking chances on prospects, moving high surplus, low salary players for par-valued stars, or other moves.

There used to be "full strength" minutes based on projections from 538, which has since ceased operation and therefore those numbers are not available any more. Now there are three options displayed - current minutes, rest of season, and year to date. The current minutes are predictions from DARKO for _that day_ and can be helpful with in-season lineup choices. Rest of season and year to date are likely the ones to rely on when making bigger picture decisions such as trades, arbitration, pre-season cuts, and pre-season auctions.

## Roadmap

### Standings Gain Points
I want to at least add, and maybe transition to, [standings gain points (SGP)](https://www.smartfantasybaseball.com/2013/03/create-your-own-fantasy-baseball-rankings-part-5-understanding-standings-gain-points/) for categories values. It seems to be a more difficult but more robust method for handling categories from what I've read online. The difficulty mainly lies in finding historical data, though since the majority of Ottoneu basketball leagues are categories based, I think there will be enough data to use it for the 2022-23 season.

### Analysis and Tuning
I really want to do some additional analysis around positions, production, and other factors. This would hopefully bring to light some strategies for roster building and lineup choices. An offshoot of the analysis could be making some of the intermediate data, such as per game production or value, available to see which players are on the cusp of being worthwhile and which are truly below replacement value or identifying tiers of players.

I want to investigate if any of my baked in assumptions need adjusting, such as where the replacement value cutoff should be and positional distributions.

#### Blogs
I have written a few posts on the Ottoneu community message boards analyzing aspects of the game, including one on [NBA schedule artifacts and their impact on scoring](https://community.ottoneu.com/t/nba-schedule-artifacts-and-player-fantasy-scoring/14413?u=higginsford) and one on [arbitration analysis for the 2024 season](https://community.ottoneu.com/t/2024-ottobasket-arb-analysis/14414/4).

### Polish App
The app is currently functional but could use some smoothing out in some areas, both in what's visible to the users and under the hood. The best example right now is that the user cannot filter for a certain player if league data has not been brought in.


## Thank Yous
Many, many thanks to [Kostya Medvedovsky](https://twitter.com/kmedved/) for creating DARKO, [Nathan Walker](https://twitter.com/bbstats/) and his team at STATS for DRIP, [Krishna Narsu](https://twitter.com/knarsu3backup) for a whole bunch of player IDs, [Justin Vibber](https://twitter.com/JustinVibber) for help understanding how to calculate the values, [Niv Shah](https://twitter.com/nivshah) for creating Ottoneu and helping me efficiently pull data from the website, and [Hayden](https://twitter.com/hscotthiggins) for making sure this README was understandable.

## TO DO:
<details>
  <summary>Laundry list of ideas</summary>
  - current minutes: save last 10 days and get min / max / avg from that to contextualize
  - use SGP instead of z-scores for roto dollar values
  - future applications of projections:
    - lineup optimizer
    - matchup analysis
  - add validation to make sure DRIP / DARKO dfs have not changed structure
  - write script for all of the ID mappings?
  - draft model for predicting incoming rookie values?
  - Some way of testing value for each player if they were a starter
    - user input?
    - running each player with minutes at 36? Removing the minutes delta from players who share the position with them?
  - add [wampum.codes](https://foundation.mozilla.org/en/blog/indigenous-wisdom-model-software-design-and-development/) file?
  - Do some analysis on inflation
</details>
