import streamlit as st
import time
from funcs import kitab, getChapter, getPassage
from login import login_page  # <-- ambil fungsi login dari file login.py

st.set_page_config(page_title="Real Bread", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if 'username' not in st.session_state:
    st.session_state['username'] = "User"

def page_read():
    st.title('Baca Alkitab')
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        book = st.selectbox("Kitab:", list(kitab.keys()), key="book")
    with col2:
        max_chapter = kitab[book]
        chapter = st.number_input("Pasal:", min_value=1, max_value=max_chapter, step=1, key="chapter")
    with col3:
        ayatORpasal = st.selectbox('Mode', ['Pasal', 'Ayat'], key="mode")
    with col4:
        if ayatORpasal == 'Ayat':
            passage = st.multiselect('Pilih Ayat:', [str(x) for x in range(1, kitab[book]+1)], key="passage")
        else:
            passage = None

    st.write("---")

    if st.button("Tampilkan", key="show", type="primary"):
        try:
            if ayatORpasal == 'Pasal':
                st.subheader(f"{book} {chapter}")
                getChapter(book, chapter)
            else:
                if passage:
                    st.subheader(f"{book} {chapter} : {', '.join(passage)}")
                    getPassage(book, chapter, passage)
                else:
                    st.warning("Pilih ayat dulu.")
        except Exception as e:
            st.error(f"Error: {e}")

def page_ai():
    st.title("AI Assistant")
    st.info("Fitur AI belum tersedia.")

def page_bookmark():
    st.title("Bookmark")
    st.info("Halaman Bookmark (Segera Hadir)")

def page_saved():
    st.title("Saved Notes")
    st.info("Halaman Catatan (Segera Hadir)")

def logout():
    st.session_state['logged_in'] = False
    st.session_state['username'] = ""
    st.rerun()

if not st.session_state['logged_in']:
    pg = st.navigation([st.Page(login_page, title="Login")], position="hidden")  # <-- pakai login_page dari login.py
    pg.run()
else:
    st.sidebar.title("Real Bread")
    st.sidebar.write(f"Halo, {st.session_state['username']}")
    
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
    if st.sidebar.button("Logout"):
        logout()
