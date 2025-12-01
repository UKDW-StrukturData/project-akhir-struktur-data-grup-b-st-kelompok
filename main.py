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
        # Menggunakan versi HEAD yang ada bold-nya
        st.write(f"Halo, **{st.session_state['username']}**")
    
    halaman_baca = st.Page(page_read, title="Read Bible")
    halaman_ai = st.Page(page_ai, title="AI Assistant")
    halaman_bookmark = st.Page(page_bookmark, title="Bookmark")
    halaman_saved = st.Page(page_saved, title="Saved") # Definisi halaman 
    
    
    st.session_state['objek_halaman_ai'] = halaman_ai # ai nya simpan ke session_state biar bisa dipanggil switch page

    pg = st.navigation({
        "Menu Utama": [halaman_baca, halaman_ai, halaman_bookmark, halaman_saved]
    })

    pg.run()

    st.sidebar.divider()
    if st.sidebar.button("Logout", type="secondary"):
        logout()