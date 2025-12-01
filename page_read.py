import streamlit as st
from funcs import kitab, getChapter, getPassage, ask_gemini

def page_read():
    st.title('Baca Alkitab & Analisis AI')
    
    if 'show_result' not in st.session_state:
        st.session_state['show_result'] = False
    if 'ref' not in st.session_state:
        st.session_state['ref'] = ""
    if 'verses' not in st.session_state:
        st.session_state['verses'] = [] #buat memori untuk hasil referensi ama ayat
    
    with st.expander(label='Cari Pasal/Ayat', expanded=True): 
        c1, c2, c3, c4 = st.columns(4) # Bagi layar jadi 4 kolom
        with c1: 
            book = st.selectbox("Kitab:", list(kitab.keys()), key="b")
        with c2: 
            max_ch = kitab[book]
            chapter = st.number_input("Pasal:", 1, max_ch, 1, key="c") # Input angka Pasal
        with c3: 
            mode = st.selectbox('Mode:', ['Pasal', 'Ayat'], key="m")
        
        passage = None
        if mode == 'Ayat':
            with c4: 
                passage_options = [str(x) for x in range(1, 177)] # ngambil ayat dari 1 sampe 176 (punya mazmur terbanyak)
                passage = st.multiselect('Ayat:', passage_options, key="p") 
        
        tampilkan_ayat = st.button('Tampilkan Ayat', use_container_width=True)

    st.write("---")

    if tampilkan_ayat:
        st.session_state['show_result'] = True
        raw_verses = []
        try:
            if mode == 'Pasal': #ngambil data pasal di funcs
                st.session_state['ref'] = f"{book} {chapter}"
                raw_verses = getChapter(book, chapter)
            else:
                if passage:
                    st.session_state['ref'] = f"{book} {chapter}: {', '.join(passage)}"
                    raw_verses = getPassage(book, chapter, passage)
                else:
                    st.warning("Pilih ayat dulu.")
                    st.session_state['show_result'] = False

            if st.session_state['show_result']:
                if not raw_verses:  # kalo misal list kosong ya ga ketemu
                    st.error(f"Maaf, Gagal mengambil data {st.session_state['ref']}. Kemungkinan server sedang gangguan.") 
                    st.session_state['verses'] = [] 
                else:               
                    st.session_state['verses'] = raw_verses
                    st.session_state['ai_result'] = None
            
        except Exception as e:
            st.error(f"Error: {e}")
            st.session_state['show_result'] = False

    if st.session_state.get('show_result') and st.session_state.get('verses'):
        st.subheader(f"{st.session_state.get('ref')}")
        
        text_for_ai = "\n".join(st.session_state['verses']) #dikirim ke ringkasan ai
        
        with st.container(height=300, border=True):
            for baris_ayat in st.session_state['verses']:
                st.write(baris_ayat) # di loop satu satu biar hasil nya berjarak

        col1, col2, col3 = st.columns(3)
        
        with col1: 
            st.button('page sebelum', use_container_width=True)
            
        with col2:
            ask_ai = st.button('Tanya AI', use_container_width=True)
        
        with col3:
            st.button('page sesudah', use_container_width=True)

        st.write("---")
        
        if ask_ai and st.session_state['verses']:
            prompt = f"""
            Kamu adalah asisten studi Alkitab. 
            Jelaskan arti yang penting dari bahasa asli untuk setiap kata yang penting (minimal 3 kata kunci).
            Berikan cross referencenya juga (minimal 2 ayat terkait) dan penjelasannya tentang hubungannya dengan ayat ini.
            Tolong buatkan ringkasan singkat (minimal 3 bullet points) tentang poin utama teologis/praktis dari ayat-ayat ini.
            JANGAN berikan balasan lain selain jawaban analisisnya saja.

            Ayat yang Anda pilih:
            {text_for_ai}
            """
            
            with st.spinner(f"AI sedang menganalisis {st.session_state['ref']}..."):
                hasil_ai = ask_gemini(prompt)
                
                st.session_state['ai_result'] = hasil_ai
                st.session_state['ai_ref'] = st.session_state['ref']
                st.rerun()

    if st.session_state.get('ai_result') and st.session_state.get('ai_ref') == st.session_state.get('ref'):
        st.subheader("Ringkasan & Makna (AI)")
        st.markdown(st.session_state['ai_result'])
        
        if st.button('Sembunyikan Hasil AI'):
            st.session_state['ai_result'] = None
            st.rerun()