import pandas as pd
import streamlit as st

from pipeline import ottobasket_values_pipeline
from utils import convert_df, ottoneu_streamlit_footer

st.set_page_config(page_title="Ottobasket Values")
st.sidebar.markdown("Ottobasket Values")


st.title("Ottobasket Player Values")
values_df = ottobasket_values_pipeline(False)
format_cols = {
    col: "{:.1f}"
    for col in values_df.columns
    if col not in ["player", "ottoneu_position"]
}
player_input = st.sidebar.text_input("Player name", placeholder="Stephen Curry").lower()
if player_input:
    values_df = values_df.loc[values_df.player.str.lower().str.contains(player_input)]
position_input = st.sidebar.multiselect(
    "Positon", options=values_df.ottoneu_position.unique()
)
if position_input:
    values_df = values_df.loc[values_df.ottoneu_position.isin(position_input)]

display_df = (
    values_df.drop(["nba_player_id", "ottoneu_player_id", "tm_id"], axis=1)
    .copy()
    .set_index("player")
)
st.dataframe(display_df.style.format(format_cols))
ottoneu_streamlit_footer("ottobasket_values")
