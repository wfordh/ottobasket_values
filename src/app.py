import streamlit as st
import pandas as pd
import datetime
from zoneinfo import ZoneInfo
from pipeline import ottobasket_values_pipeline

st.title("Ottobasket Player Values")
values_df = ottobasket_values_pipeline(False)
format_cols = {
    col: "{:.1f}"
    for col in values_df.columns
    if col not in ["player", "ottoneu_position"]
}
st.dataframe(values_df.style.format(format_cols))
now = datetime.datetime.now(tz = ZoneInfo("US/Pacific"))
st.text(f"Last updated: {now.strftime('%Y-%m-%d %I:%M %p (Pacific)')}")
st.download_button("Press to download", values_df, "ottobasket_values.csv", "text/csv", key="download-csv")
