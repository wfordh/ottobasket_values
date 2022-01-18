# Ottobasket Values
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/wfordh/ottobasket_values/main/src/app.py/)

## What is this?
Ottoneu launched fantasy basketball this year and these are player values for those in the Ottoverse. Values are commonly homebrewed by players in Ottoneu's flagship baseball service, with Justin Vibber's Surplus Calculator being the most prominent and public example. There are values for each of the three formats available in Ottoneu - traditional points, simple points, and categories - and cover "current" and "full strength" minutes projections.

## How is it done?
The values are built off of the [DARKO](https://apanalytics.shinyapps.io/DARKO/) and [DRIP](https://theanalyst.com/na/2021/10/nba-drip-daily-updated-rating-of-individual-performance/) projections, which both produce per 100 projections for a variety of stats. After deriving some of the necessary stats, they are averaged and then converted into two separate per game projections based on DARKO's current minute projections and 538's full strength minute projections. The current minute projections update often and incorporate injury status and other information, while the full strength minutes are a prediction of how a team's minutes would break down assuming everyone's healthy and available ([full explanation here](https://fivethirtyeight.com/methodology/how-our-nba-predictions-work/)). Once the fantasy points are calculated, then it's time to assign positions and find the replacement value. Ottoneu uses 3 guard spots, 2 forwards, 1 center, 1 guard / forward, 1 forward / center, and 1 utility spot across 12 teams. I multiplied the position spots by the number of teams and ranked the top players at each position, eg top 36 guards.

## How to use the values
The values are a good signpost to see how your team stacks up based on how much you are spending on players versus the amount of value they are generating. If you have positive surplus, then you can 

## TO DO:
- rewrite and modularize the scripts
- incorporate games played and projected games played into calculations
- write the README
- do the calculations for roto leagues
- make a streamlit app
  - allow users to input minutes projections for individual players?
- have full strength and current values to help price players who are injured or just back
  - current minutes: save last 10 days and get min / max / avg from that to contextualize
- use SGP instead of z-scores for roto dollar values
- future applications of projections:
  - lineup optimizer
  - matchup analysis
- add validation to make sure DRIP / DARKO dfs have not changed structure
- write script for all of the ID mappings?
- return more columns from pipeline and then select only a few for presentation so the others are present in the download
- github actions to run it at 7 am, 11 am, 3 pm PST?
- fix `nan` names and Enes Kanter / Freedom duplicates
- add wampum.codes file?
