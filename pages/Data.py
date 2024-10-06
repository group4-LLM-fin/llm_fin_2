import streamlit as st
from OCR.fin_data import get_fin_data

st.title("Page 2")
st.write("Welcome to Page 2!")

fin_data = get_fin_data()
st.dataframe(fin_data)