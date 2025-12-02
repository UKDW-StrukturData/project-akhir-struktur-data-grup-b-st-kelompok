import streamlit as st
import time

def login_page():
    st.title("Real Bread: A Bible Study App")

    with st.form(key='login_form'):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.form_submit_button('Login', type='primary'):
            if username == "" or password == "":
                st.error("Username atau password salah!")
            else:
                with st.status("Memverifikasi akun...", expanded=False) as s:
                    time.sleep(1)
                    s.update(label="Login berhasil!", state="complete")
                    time.sleep(0.8)

                st.session_state['logged_in'] = True
                st.session_state['username'] = username 
                st.rerun()