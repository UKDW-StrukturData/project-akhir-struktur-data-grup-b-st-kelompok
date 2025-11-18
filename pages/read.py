import streamlit as st
from funcs import kitab, getChapter, getPassage

st.title('Real Bread: A Bible Study App')

col1, col2, col3, col4 = st.columns(4)
with col1:
    book = st.selectbox("Kitab:", list(kitab.keys()))
with col2:
    max_chapter = kitab[book]
    chapter = st.number_input("Pasal:", min_value=1, max_value=max_chapter, step=1)
with col3:
    ayatORpasal = st.selectbox('Satu Pasal / Ayat', ['Pasal', 'Ayat'])
with col4:
    if ayatORpasal == 'Ayat':
        passage = st.multiselect('Ayat:', [str(x) for x in range(1, kitab[book]+1)])

try:
    if ayatORpasal == 'Pasal':
        getChapter(book, chapter)
    else:
        getPassage(book, chapter, passage)
except Exception as e:
    st.error(e)