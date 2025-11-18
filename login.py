import streamlit as st

st.title('Real Bread: A Bible Study App')
st.text_input('Username', placeholder='masukkan username')
st.text_input('Password', placeholder='masukkan password')

if st.button('Login', type='primary'):
    st.Page('read.py')