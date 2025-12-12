import streamlit as st
import time
import hashlib
import pandas as pd
from streamlit_gsheets import GSheetsConnection

@st.cache_data(ttl=0, show_spinner=False)

def load_data_users():
    conn = st.connection("gsheets", type=GSheetsConnection)
    return conn.read(worksheet="users")

def login_page():
    data = load_data_users()
    df = pd.DataFrame(data)

    st.subheader("Login ke akun anda")

    with st.form(key='login_form'):
        username = st.text_input("Username", placeholder='Masukkan username')
        password = st.text_input("Password", placeholder='Masukkan password', type="password")

        if st.form_submit_button('Login', type='primary', use_container_width=True):
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