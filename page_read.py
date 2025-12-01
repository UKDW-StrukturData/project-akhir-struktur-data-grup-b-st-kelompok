import streamlit as st
from funcs import kitab, getChapter, getPassage, ask_gemini

def page_read():
    st.title('Baca Alkitab & Analisis AI')
    
    if 'show_result' not in st.session_state:
        st.session_state['show_result'] = False
    if 'ref' not in st.session_state:
        st.session_state['ref'] = ""
    if 'verses' not in st.session_state:
        st.session_state['verses'] = []  #buat memori untuk hasil, ref ama ayat
    
    with st.expander(label='Cari Pasal/Ayat', expanded=True): 
        c1, c2, c3, c4 = st.columns(4)
        with c1: 
            book = st.selectbox("Kitab:", list(kitab.keys()), key="book")
        with c2: 
            max_ch = kitab[book]
            chapter = st.number_input("Pasal:", 1, max_ch, 1, key="chapter") # Input angka Pasal
        with c3: 
            mode = st.selectbox('Mode:', ['Pasal', 'Ayat'], key="mode")
        
        passage = None
        if mode == 'Ayat':
            with c4: 
                passage_options = [str(x) for x in range(1, 177)] # ngambil ayat dari 1 sampe 176 (punya mazmur terbanyak)
                passage = st.multiselect('Ayat:', passage_options, key="passage") 
        
        tampilkan_ayat = st.button('Tampilkan Ayat', use_container_width=True)

    st.write("---")

    if tampilkan_ayat:
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
                    st.session_state['show_result'] = False

            if st.session_state['show_result']:
                if not raw_verses:  # kalo misal list kosong ya ga ketemu/ api mai/ gagal ambil
                    st.error(f"Maaf, Gagal mengambil data {st.session_state['ref']}. Kemungkinan server sedang gangguan.") 
                    st.session_state['verses'] = [] 
                else:               
                    st.session_state['verses'] = raw_verses # kalo bisa simpen ke raw_verse
                    st.session_state['ai_result'] = None #hasil ai di reset biar g nyampur
            
        except Exception as e:
            st.error(f"Error: {e}")
            st.session_state['show_result'] = False

    if st.session_state.get('show_result') and st.session_state.get('verses'): # kalo dah neken tombol tampilin ayat
        st.subheader(f"{st.session_state.get('ref')}")
        
        text_for_ai = "\n".join(st.session_state['verses']) #gabung semua item list jadi teks
        
        with st.container(height=300, border=True):
            for baris_ayat in st.session_state['verses']:
                st.write(baris_ayat)  # bakal nampilin ayat per ayat biar ke jarak

        col1, col2, col3, col4 = st.columns(4)
        
        with col1: 
            st.button('Page Sebelum', use_container_width=True)
            
        with col2:
            ask_ai = st.button('Tanya AI (Disini)', use_container_width=True) # muncul dibawah
        
        with col3:
            if st.button('Diskusi Lanjut (Chat)', use_container_width=True): #kalo misal nya mau membahas lebih lanjut dengan ai
                prompt_pindah = f"""
                Kamu adalah asisten studi Alkitab. 
                Jelaskan arti yang penting dari bahasa asli untuk setiap kata yang penting.
                Berikan cross referencenya juga.
                
                Ayat yang Anda pilih:
                {text_for_ai}
                """
                st.session_state['paket_prompt'] = prompt_pindah
                st.session_state['paket_judul'] = f"Diskusi Ayat: {st.session_state['ref']}"
                st.session_state['pindah_dari_read'] = True
                
                st.switch_page(st.session_state['objek_halaman_ai']) # Pindah Halaman ke ai tadi dah di buat di main

        with col4:
            st.button('Page Sesudah', use_container_width=True)

        st.write("---")
        
        if ask_ai and st.session_state['verses']:
            prompt = f"""
            Kamu adalah asisten studi Alkitab. 
            Jelaskan arti yang penting dari bahasa asli untuk setiap kata yang penting.
            Berikan cross referencenya juga.
            JANGAN berikan balasan lain selain jawaban analisisnya saja.

            Ayat yang Anda pilih:
            {text_for_ai}
            """

            with st.spinner(f"AI sedang menganalisis {st.session_state['ref']}..."):
                hasil_ai = ask_gemini(prompt)
                st.session_state['ai_result'] = hasil_ai
                st.session_state['ai_ref'] = st.session_state['ref'] # mengisi AI_ref sama ayat yang sekarang bakal dikunci
                st.rerun() 

    if st.session_state.get('ai_result') and st.session_state.get('ai_ref') == st.session_state.get('ref'): 
        st.subheader("Ringkasan & Makna (AI)")
        st.markdown(st.session_state['ai_result'])
        
        if st.button('Sembunyikan Hasil AI'):
            st.session_state['ai_result'] = None
            st.rerun() #buat nampilin hasil lokal
