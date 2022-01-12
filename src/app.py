import streamlit as st
import pandas as pd
from pipeline import ottobasket_values_pipeline

st.title("Ottobasket Player Values")
values_df = ottobasket_values_pipeline(False)
st.dataframe(values_df)
