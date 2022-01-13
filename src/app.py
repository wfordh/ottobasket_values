import streamlit as st
import pandas as pd
import datetime
from pipeline import ottobasket_values_pipeline

st.title("Ottobasket Player Values")
values_df = ottobasket_values_pipeline(False)
format_cols = {
    col: "{:.1f}"
    for col in values_df.columns
    if col not in ["player", "ottoneu_position"]
}
st.dataframe(values_df.style.format(format_cols))
now = datetime.datetime.today()
st.text(f"Last updated: {now.strftime('%Y-%m-%d %I:%M %p')}")
