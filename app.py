import os
import streamlit as st

st.write("Current working directory:", os.getcwd())
st.write("Files in directory:", os.listdir())
