# Ottobasket Values
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/wfordh/ottobasket_values/main/src/app.py/)

## What is this?
Ottoneu launched fantasy basketball this year and these are player values for those in the Ottoverse. Values are commonly homebrewed by players in Ottoneu's flagship baseball service, with Justin Vibber's Surplus Calculator being the most prominent and public example. There are values for each of the three formats available in Ottoneu basketball - traditional points, simple points, and categories - and cover "current" and "full strength" minutes projections.

## How is it done?
<details>
  <summary>Methodology</summary>

  The values are built off of the [DARKO](https://apanalytics.shinyapps.io/DARKO/) and [DRIP](https://theanalyst.com/na/2021/10/nba-drip-daily-updated-rating-of-individual-performance/) projections, which are per 100 projections for a variety of stats. I average and convert the relevant stats into two per game projections based on DARKO's current minute projections and 538's full strength minute projections. The current minute projections update often and incorporate injury status and other information, while the full strength minutes are a prediction of how a team's minutes would break down assuming everyone's healthy and available ([full explanation here](https://fivethirtyeight.com/methodology/how-our-nba-predictions-work/)). The per game projections are converted into a points value for each of the three scoring systems - simple and traditional fantasy points, and categories (calculated using z-scores).

  Once the point values are calculated, positions are assigned and the replacement value cutoff is found. Ottoneu uses 3 guard spots, 2 forwards, 1 center, 1 guard / forward, 1 forward / center, and 1 utility spot across 12 teams. Each player has a "surplus position" assigned to them based on their position eligibility and which of the three main positions (G, F, C) they rank highest in by the point values. The top players are found for each position by taking their "surplus position" and finding the top players for each position, with the cutoff determined by the number of position spots times the number of teams. For example, the top 36 guards are ranked and so on for the forwards and centers before taking the next 12 best players that are eligible for forward or center. I decided to rank the top 24 utility players instead of the top 12 in order to lower the cutoff for replacement value since there are players on the bench that will provide value when filling in and are a step above the rest of the players.

  With the player pool identified, I find the lowest points value and set it as the replacement level and calculate the surplus factor. Each player's projected points value is multiplied by the surplus factor to get their dollar value, and players outside of the pool are given a value of $0. Surplus values can then be calculated by comparing the player's value to their current salary.
</details>

## How to use the values
<details>
  <summary>Click to expand!</summary>

  The values are a good signpost to see how your team stacks up based on how much you are spending on players versus the amount of value they are generating. If you have positive surplus, then you have more wiggle room for taking chances on prospects, moving high surplus, low salary players for par-valued stars, or other moves.

  The difference between current and full strength minutes is important to understand considering I do not have a reliable input for a games played projection at the moment. This should not be an issue for currently healthy starters, but for injured players who may have minutes restrictions upon returning or the players whose role will be reduced once the starter returns, it will be difficult to calibrate. I mostly look at the full strength values only for players who are out such as Zion Williamson or Ben Simmons to see how they might stack up whenever they do return to action. However, on the whole the current values and projections should be used over the full strength ones.

  This dichotomy can distort how teams look when the individual player surplus is rolled up to the team level as someone with a lot of players currently filling big roles and providing value may not look the same once other players return. Additionally, team rollups for surplus do not take positions into account, so having all of your surplus value at one position where some players may not get into games is not helpful.
</details>

## Roadmap
<details>
  <summary>A look at what's next</summary>

  ### Standings Gain Points
  I want to at least add, and maybe transition to, [standings gain points (SGP)](https://www.smartfantasybaseball.com/2013/03/create-your-own-fantasy-baseball-rankings-part-5-understanding-standings-gain-points/) for categories values. It seems to be a more difficult but more robust method for handling categories from what I've read online. The difficulty mainly lies in finding historical data, though since the majority of Ottoneu basketball leagues are categories based, I think there will be enough data to use it for the 2022-23 season.

  ### Games forecast
  Right now everything is at a per game level because I have not been able to find any reliable public source for projected games played. This means that players are a bit unbalanced because we can expect some to miss a game here and there for rest or injury management while others will play every game. This shouldn't have that much of an impact on the values, but would result in some changes.

  ### Analysis and Tuning
  I really want to do some additional analysis around positions, production, and other factors. This would hopefully bring to light some strategies for roster building and lineup choices. An offshoot of the analysis could be making some of the intermediate data, such as per game production or value, available to see which players are on the cusp of being worthwhile and which are truly below replacement value or identifying tiers of players.

  I want to investigate if any of my baked in assumptions need adjusting, such as where the replacement value cutoff should be and positional distributions.

  ### Polish app
  The app is currently functional but could use some smoothing out in some areas, both in what's visible to the users and under the hood. The best example right now is that the user cannot filter for a certain player if league data has been brought in.

</details>

## TO DO:
<details>
  <summary>Laundry list of ideas</summary>
  - incorporate games played and projected games played into calculations
    - basketballmonster?
  - current minutes: save last 10 days and get min / max / avg from that to contextualize
  - use SGP instead of z-scores for roto dollar values
  - future applications of projections:
    - lineup optimizer
    - matchup analysis
  - add validation to make sure DRIP / DARKO dfs have not changed structure
  - write script for all of the ID mappings?
  - github actions to run it at 7 am, 11 am, 3 pm PST?
  - draft model for predicting incomign rookie values?
  - Some way of testing value for each player if they were a starter
    - user input?
    - running each player with minutes at 36? Removing the minutes delta from players who share the position with them?
  - add [wampum.codes](https://foundation.mozilla.org/en/blog/indigenous-wisdom-model-software-design-and-development/) file?
</details>