import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import matplotlib.pyplot as plt

def page_bookmark():
    st.title("Bookmark")
    conn = st.connection("gsheets", type=GSheetsConnection)
    data = conn.read(worksheet="bookmarks", ttl=0)
    df = pd.DataFrame(data)

    # hanya tampilkan yang satu username

    st.write('---')
    with st.expander(label='Distribusi kitab yang dibookmark oleh pengguna Real Bread lainnya'):
        pie, bar = st.columns(2)
        hitung = dict()
        for i in df['book']:
            if i not in hitung:
                hitung[i] = 1
            else:
                hitung[i] += 1

        labels = list(hitung.keys())
        values = list(hitung.values())
        
        with pie:
            fig, ax = plt.subplots()
            ax.pie(values, labels=labels, autopct="%1.1f%%")
            ax.axis('equal')
            st.pyplot(fig)

        with bar:
            fig2, ax2 = plt.subplots()
            ax2.bar(labels, values)
            st.pyplot(fig2)


    st.write('---')

    df = df[df['username'] == st.session_state['username']]
    if df.empty:
        st.info('Belum ada bookmark di akun ini.')
    else:
        for idx, baris in df.iterrows():
            with st.container(border=True):
                st.write(f'### {baris['book']} {int(baris['chapter'])}: {int(baris['verse'])}')
                st.write(baris['content'])