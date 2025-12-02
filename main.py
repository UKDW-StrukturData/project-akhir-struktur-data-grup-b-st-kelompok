import streamlit as st
from page_login import login_page
from page_read import page_read
from page_ai import page_ai
from page_bookmark import page_bookmark
from page_saved import page_saved
from page_register import register_page

st.set_page_config(
    page_title='Real Bread: A Bible Study App',
    page_icon='icon.png',
    layout='wide'
)

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = "User"

def logout():
    st.session_state['logged_in'] = False
    st.session_state['username'] = ""
    st.session_state.chat = [] 
    st.rerun()

if 'auth_page' not in st.session_state:
    st.session_state['auth_page'] = "login"

if not st.session_state['logged_in']:
    st.title("Real Bread: A Bible Study App")
    col1, col2 = st.columns(2)

    with col1:
        st.write("Silakan login ke akun anda")
        if st.button('Login', type='primary', use_container_width=True):
            st.session_state['auth_page'] = "login"
            st.rerun()

    with col2:
        st.write("Belum punya akun? Daftar sekarang")
        if st.button('Sign up', type='primary', use_container_width=True):
            st.session_state['auth_page'] = "register"
            st.rerun()

    if st.session_state['auth_page'] == "login":
        login_page()
    else:
        register_page()
else:
    with st.sidebar:
        st.title("Real Bread")
        st.write(f"Halo, **{st.session_state['username']}**!") # ngasih nama
    
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