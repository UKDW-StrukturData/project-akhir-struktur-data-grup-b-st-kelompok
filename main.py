import streamlit as st
from page_login import login_page
from page_read import page_read
from page_ai import page_ai
from page_bookmark import page_bookmark
from page_saved import page_saved

st.set_page_config(page_title="Real Bread", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = "User"

def logout():
    st.session_state['logged_in'] = False
    st.session_state['username'] = ""
    st.session_state.chat = [] 
    st.rerun()

if not st.session_state['logged_in']:
    pg = st.navigation([st.Page(login_page, title="Login")], position="hidden")
    pg.run()
else:
    with st.sidebar:
        st.title("Real Bread")
        st.write(f"Halo, {st.session_state['username']}")
        st.divider()

    pg = st.navigation({
        "Menu Utama": [
            st.Page(page_read, title="Read Bible"),
            st.Page(page_ai, title="AI Assistant"),
            st.Page(page_bookmark, title="Bookmark"),
            st.Page(page_saved, title="Saved"),
        ]
    })


    pg.run()

    st.sidebar.divider()
    if st.sidebar.button("Logout", type="secondary"):
        logout()