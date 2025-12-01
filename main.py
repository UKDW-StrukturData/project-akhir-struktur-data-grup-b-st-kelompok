import streamlit as st
import time
from funcs import kitab, getChapter, getPassage, ask_gemini

from login import login_page


st.set_page_config(page_title="Real Bread", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = "User"

def page_read():
    st.title('Baca & Ringkasan AI')
    with st.expander(label='Cari Pasal/Ayat', expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        with c1: book = st.selectbox("Kitab:", list(kitab.keys()), key="b")
        with c2: max_ch = kitab[book]; chapter = st.number_input("Pasal:", 1, max_ch, 1, key="c")
        with c3: mode = st.selectbox('Mode:', ['Pasal', 'Ayat'], key="m")
        if mode == 'Ayat':
            with c4: passage = st.multiselect('Ayat:', [str(x) for x in range(1, kitab[book]+1)], key="p") if mode == 'Ayat' else None
        
        if st.button('Tampilkan Ayat'):
            pass

    st.write("---")

    if st.button("Tampilkan Ayat & Analisis", type="primary", key="go"):
        st.session_state['show_result'] = True
        
        raw_verses = []
        try:
            if mode == 'Pasal':
                st.session_state['ref'] = f"{book} {chapter}"
                raw_verses = getChapter(book, chapter)
            else:
                if passage:
                    st.session_state['ref'] = f"{book} {chapter}: {', '.join(passage)}"
                    raw_verses = getPassage(book, chapter, passage)
                else:
                    st.warning("Pilih ayat dulu.")
            st.session_state['verses'] = raw_verses
        except Exception as e:
            st.error(f"Error: {e}")

    if st.session_state.get('show_result') and st.session_state.get('verses'):
        st.subheader(f"{st.session_state.get('ref')}")
        text_for_ai = "\n".join(st.session_state['verses'])
        
        with st.container(height=300):
            for v in st.session_state['verses']:
                st.write(v)
        
        st.write("---")
        
        st.subheader("Ringkasan & Makna (AI)")
        
        prompt = f"""
        Kamu adalah asisten studi Alkitab. 
        Jelaskan arti yang penting dari bahasa asli untuk setiap kata yang penting.
        Berikan cross referencenya juga dan penjelasannya.
        Tolong buatkan ringkasan singkat (bullet points) tentang poin utama 
        dari ayat-ayat ini (Jangan berikan reply selain jawabannya saja):
        
        {text_for_ai}
        """
        
        with st.spinner("AI sedang menganalisis..."):
            hasil_ai = ask_gemini(prompt)
            st.success("Selesai!")
            st.markdown(hasil_ai)

def page_ai():
    st.title("Chat Bebas")
    if "chat" not in st.session_state: st.session_state.chat = []
    for m in st.session_state.chat: st.chat_message(m["role"]).write(m["content"])
    if q := st.chat_input("Tanya..."):
        st.session_state.chat.append({"role":"user","content":q})
        st.chat_message("user").write(q)
        with st.chat_message("assistant"):
            ans = ask_gemini(q)
            st.write(ans)
        st.session_state.chat.append({"role":"assistant","content":ans})

def page_bm(): st.title("Bookmark")
def page_sv(): st.title("Saved")

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
            st.Page(page_bm, title="Bookmark"),
            st.Page(page_sv, title="Saved"),
        ]
    })
    
    pg.run()

    st.sidebar.divider()
    if st.sidebar.button("Logout"):
        logout()