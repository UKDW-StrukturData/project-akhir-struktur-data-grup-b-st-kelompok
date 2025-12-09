import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

def page_bookmark():
    st.title("Bookmark")
    conn = st.connection("gsheets", type=GSheetsConnection)
    data = conn.read(worksheet="bookmarks", ttl=0)
    df = pd.DataFrame(data)

    st.dataframe(df)