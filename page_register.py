import streamlit as st
import time
import hashlib
import pandas as pd
from streamlit_gsheets import GSheetsConnection

def register_page():
    conn = st.connection("gsheets", type=GSheetsConnection)
    data = conn.read(worksheet="users", ttl=0)
    df = pd.DataFrame(data)

    # Pastikan kolom ada
    if df.empty or 'username' not in df.columns:
        df = pd.DataFrame({"username": [], "password": []})

    df['username'] = df['username'].astype(str).str.strip()

    st.subheader("Daftar akun baru")

    with st.form(key='register_form'):
        username = st.text_input("Username (maksimal 25 karakter)", placeholder='Masukkan username')
        password = st.text_input("Password (8-25 karakter)", placeholder='Masukkan password', type="password")
        password_confirm = st.text_input("Konfirmasi Password", placeholder='Masukkan password', type="password")

        if st.form_submit_button('Sign up', type='primary', use_container_width=True):

            if len(username) > 25:
                st.error("Username maksimal 25 karakter!")
                return
            
            if len(password) < 8 or len(password) > 25:
                st.error("Password harus antara 8-25 karakter!")
                return

            if password != password_confirm:
                st.error("Password dan konfirmasi password tidak sesuai!")
                return

            if username in df['username'].values:
                st.error("Username sudah terdaftar! Silakan gunakan username lain.")
                return

            # hashing password
            hashed_pw = hashlib.sha256(password.encode('utf-8')).hexdigest()

            new_user = pd.DataFrame({
                'username': [username],
                'password': [hashed_pw]
            })

            updated_df = pd.concat([df, new_user], ignore_index=True)

            try:
                conn.update(data=updated_df, worksheet="users")
            except Exception as e:
                st.error(f"Gagal menulis ke Google Sheets: {e}")

            with st.status("Mendaftarkan akun...", expanded=False) as s:
                time.sleep(1)
                s.update(label="Pendaftaran berhasil! Silakan login ke akun anda.", state="complete")
                time.sleep(0.8)
            
            st.session_state['auth_page'] = "login"
            st.rerun()
