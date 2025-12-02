import streamlit as st
import time
import hashlib
import pandas as pd
from streamlit_gsheets import GSheetsConnection

def login_page():
    conn = st.connection("gsheets", type=GSheetsConnection)
    data = conn.read(worksheet="users", ttl=0)
    df = pd.DataFrame(data)

    st.title("Real Bread: A Bible Study App")

    with st.form(key='login_form'):
        username = st.text_input("Username", placeholder='Masukkan username')
        password = st.text_input("Password", placeholder='Masukkan password', type="password")

        if st.form_submit_button('Login', type='primary'):
            hashed_pw = hashlib.sha256()
            hashed_pw.update(password.encode('utf-8'))
            hashed_pw = hashed_pw.hexdigest()

            try:
                cek_pw = df.loc[df['username'] == username, 'password'].iloc[0]
                
                if cek_pw == hashed_pw:
                    with st.status("Memverifikasi akun...", expanded=False) as s:
                        time.sleep(1)
                        s.update(label="Login berhasil!", state="complete")
                        time.sleep(0.8)

                    st.session_state['logged_in'] = True
                    st.session_state['username'] = username 
                    st.rerun()

                else:
                    with st.status("Memverifikasi akun...", expanded=False) as s:
                        time.sleep(1)
                        s.update(label="Login gagal! Username/password salah.", state='error')
                        time.sleep(0.8)
                    
            except IndexError:
                with st.status("Memverifikasi akun...", expanded=False) as s:
                        time.sleep(1)
                        s.update(label="Login gagal! Username/password salah.", state='error')
                        time.sleep(0.8)