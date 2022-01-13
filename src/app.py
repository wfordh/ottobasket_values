import streamlit as st
import pandas as pd
import datetime
from zoneinfo import ZoneInfo
from pipeline import ottobasket_values_pipeline

@st.cache
def convert_df(df):
   return df.to_csv(index=False).encode('utf-8')

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
values_csv = convert_df(values_df)
st.download_button("Press to download", values_csv, "ottobasket_values.csv", "text/csv", key="download-csv")
