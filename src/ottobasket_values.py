import datetime

import pandas as pd
import streamlit as st

from pipeline import ottobasket_values_pipeline  # type: ignore

st.set_page_config(page_title="Ottobasket Values")
st.sidebar.markdown("Ottobasket Values")


def convert_df(df):
    # Index is set to either player or team at all times
    return df.to_csv(index=True).encode("utf-8")


st.title("Ottobasket Player Values")
sheet_id = "1GgwZpflcyoRYMP0yL2hrbNwndJjVFm34x3jXnUooSfA"
values_df = pd.read_csv(
    f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"
)

most_recent_run_date = pd.read_csv(
    f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=1905916816"
).values[0][0]

format_cols = {
    col: "${:.0f}" if "value" in col else "{:.0f}"
    for col in values_df.columns
    if col not in ["player", "ottoneu_position"]
}
format_cols["tfppg_ros"] = "{:.2f}"
format_cols["sfppg_ros"] = "{:.2f}"
ros_check = st.sidebar.checkbox("Rest of Season columns", value=True)
ytd_check = st.sidebar.checkbox("Year to Date columns", value=True)
current_min_check = st.sidebar.checkbox("Current minutes columns")
id_columns = st.sidebar.checkbox("Show player IDs?", value=False)
base_columns = [
    "player",
    "ottoneu_position",
]

if ros_check:
    base_columns.extend(
        [
            "total_ros_minutes",
            "games_forecast_ros",
            "simple_points_value_ros",
            "sfppg_ros",
            "trad_points_value_ros",
            "tfppg_ros",
            "categories_value_ros",
        ]
    )
if ytd_check:
    base_columns.extend(
        [
            "minutes_ytd",
            "simple_points_value_ytd",
            "trad_points_value_ytd",
            "categories_value_ytd",
        ]
    )
if current_min_check:
    base_columns.extend(
        [
            "minutes",
            "simple_points_value_current",
            "trad_points_value_current",
            "categories_value_current",
        ]
    )
if id_columns:
    base_columns.extend(
        [
            "nba_player_id",
            "ottoneu_player_id",
        ]
    )
if not any([ros_check, ytd_check, current_min_check]):
    st.text("Please select a minutes option!!")
player_input = (
    st.sidebar.text_input("Player name", placeholder="Stephen Curry").lower().strip()
)
if player_input:
    values_df = values_df.loc[values_df.player.str.lower().str.contains(player_input)]
position_input = st.sidebar.multiselect(
    "Positon", options=values_df.ottoneu_position.unique()
)
if position_input:
    values_df = values_df.loc[values_df.ottoneu_position.isin(position_input)]

display_df = values_df[base_columns].copy().set_index("player")
st.dataframe(display_df.style.format(format_cols))  # type: ignore
st.markdown(
    "About page / README can be found [here](https://github.com/wfordh/ottobasket_values/blob/main/README.md)"
)
st.text("ros = rest of season. ytd = year to date. Full glossary found in the sidebar.")
st.text(f"Last updated: {most_recent_run_date}")
values_csv = convert_df(display_df)
st.download_button(
    "Press to download",
    values_csv,
    "ottobasket_values.csv",
    "text/csv",
    key="download-csv",
)
