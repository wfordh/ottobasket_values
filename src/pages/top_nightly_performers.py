"""
strategies for pictures:
- save to namedtempfiles and store info in df column?
- save to streamlit static file storage
"""

import os
import sys
from datetime import date, datetime, timedelta

import pandas as pd
import requests
import streamlit as st
from great_tables import GT, loc, style

sys.path.append(os.path.abspath("src"))

from leagues import get_league_leaderboard
from utils import get_last_night_stats, get_name_map


def get_player_headshot(nba_id: int):
    url = f"https://cdn.nba.com/headshots/nba/latest/1040x760/{nba_id}.png"
    # return requests.get(url).content
    return url


df = get_last_night_stats(sheet_num=0)
yesterday = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
mappings = get_name_map()
df = df.merge(mappings, on="ottoneu_player_id", how="left")

st.title("Last Night's Top Performers")
st.subheader(f"{yesterday}")

st.header("Six Picks")
six_picks_df = get_last_night_stats(sheet_num=1)
six_picks_df = six_picks_df.merge(
    mappings[["ottoneu_player_id", "nba_player_id"]], on="ottoneu_player_id", how="left"
)
# six_picks_df["player_headshot"] = six_picks_df.nba_player_id.apply(lambda x: get_player_headshot(x))

totals = pd.DataFrame.from_dict(
    {
        "name": ["Totals"],
        "price": [six_picks_df.price.sum()],
        "pick_pct": [""],
        "pts": [six_picks_df.pts.sum()],
        "ottoneu_position": [""],
        "ottoneu_player_id": [None],
        "G": [None],
        "F": [None],
        "C": [None],
        # "player_headshot": [None],
        "nba_player_id": [None],
    }
)
six_picks_df["ottoneu_player_id"] = six_picks_df.ottoneu_player_id.astype(str)
six_picks_df = pd.concat([six_picks_df, totals], axis=0)
st.html(
    GT(six_picks_df.sort_values(by="ottoneu_position", ascending=False))
    .tab_header(f"Top Six Picks Lineup for {yesterday}")
    # .cols_move_to_start("player_headshot")
    .cols_hide(["G", "F", "C", "nba_player_id", "ottoneu_player_id"])
    .cols_label(
        name="Name",
        price="Price",
        pick_pct="Pick %",
        pts="FP",
        ottoneu_position="Position",
        ottoneu_player_id="",
    )
    .fmt_currency("price", currency="USD")
    .fmt_integer("pts")
    .tab_style(style=style.text(style="italic"), locations=loc.body(rows=[-1]))
)

st.header("Overall Leaderboard")
with st.container():
    st.dataframe(
        df.set_index("player_name")[
            [
                "pro_team",
                "positions",
                "minutes",
                "fantasy_points",
                "points",
                "field_goals_made",
                "field_goal_attempts",
                "free_throws_made",
                "free_throw_attempts",
                "rebounds",
                "assists",
                "steals",
                "blocks",
                "turnovers",
            ]
        ].sort_values(by="fantasy_points", ascending=False)
    )
