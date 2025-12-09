import streamlit as st
from funcs import kitab, getPassage, ask_gemini, init_cache, shift_cache

def page_read():
    st.title('Baca Alkitab & Analisis AI')
    
    # State Dasar
    if 'show_result' not in st.session_state: st.session_state['show_result'] = False
    if 'ref' not in st.session_state: st.session_state['ref'] = ""
    if 'verses' not in st.session_state: st.session_state['verses'] = [] 
    
    if 'book' not in st.session_state: st.session_state['book'] = list(kitab.keys())[0]
    if 'chapter' not in st.session_state: st.session_state['chapter'] = 1

    # INIT LIST CACHE DI STATE
    if 'cache_list' not in st.session_state:
        st.session_state['cache_list'] = []

    list_kitab = list(kitab.keys())
    
    # --- LOGIKA SINKRONISASI (Manual Select vs Cache) ---
    current_cache = None
    # Cek apakah cache valid (tidak kosong & index 2 isinya sama dengan pilihan user)
    cache_valid = False
    if st.session_state['cache_list'] and len(st.session_state['cache_list']) == 5:
        mid_item = st.session_state['cache_list'][2]
        if mid_item and mid_item['book'] == st.session_state['book'] and mid_item['chapter'] == st.session_state['chapter']:
            cache_valid = True
            current_cache = mid_item

    # Jika cache tidak valid/tidak sinkron (user ganti manual), Reset Cache
    if not cache_valid and st.session_state.get('show_result'):
        # Kita initialize diam-diam (tanpa spinner yg mengganggu)
        st.session_state['cache_list'] = init_cache(st.session_state['book'], st.session_state['chapter'])
        # Update current dari hasil init baru
        current_cache = st.session_state['cache_list'][2]
        if current_cache:
            st.session_state['verses'] = current_cache['verses']
            st.session_state['ref'] = current_cache['ref']

    # --- CALLBACK NAVIGASI (LIST) ---
    def nav_callback(arah):
        c_list = st.session_state.get('cache_list', [])
        if not c_list: return # Safety

        new_list, success = shift_cache(c_list, arah)
        
        if success:
            st.session_state['cache_list'] = new_list
            # Ambil data tengah (Index 2 selalu jadi "Current")
            new_current = new_list[2]
            if new_current:
                st.session_state['book'] = new_current['book']
                st.session_state['chapter'] = new_current['chapter']
                st.session_state['verses'] = new_current['verses']
                st.session_state['ref'] = new_current['ref']
                st.session_state['show_result'] = True
                st.session_state['ai_result'] = None

    # --- UI INPUT ---
    with st.expander(label='Cari Pasal/Ayat', expanded=True): 
        c1, c2, c3, c4 = st.columns(4)
        with c1: 
            book = st.selectbox("Kitab:", list_kitab, key="book")
        with c2: 
            max_ch = kitab[book]
            if st.session_state.get('chapter', 1) > max_ch:
                st.session_state['chapter'] = 1
            chapter = st.number_input("Pasal:", min_value=1, max_value=max_ch, key="chapter") 
        with c3: 
            mode = st.selectbox('Mode:', ['Pasal', 'Ayat'], key="mode")
        
        passage = None
        if mode == 'Ayat':
            with c4: 
                passage_options = [str(x) for x in range(1, 177)] 
                passage = st.multiselect('Ayat:', passage_options, key="passage") 
        
        # Tombol Manual Fetch
        if st.button('Tampilkan Ayat', use_container_width=True, type='primary'):
            st.session_state['show_result'] = True
            if mode == 'Ayat':
                 if passage:
                     st.session_state['ref'] = f"{book} {chapter}: {', '.join(passage)}"
                     st.session_state['verses'] = getPassage(book, chapter, passage)
                 else:
                     st.warning("Pilih ayat dulu.")
            else:
                 # Mode Pasal: Trigger logic sync cache di atas (saat rerun)
                 pass 

    st.write("---")

    # --- TAMPILAN HASIL ---
    if st.session_state.get('show_result') and st.session_state.get('verses'):
        st.subheader(f"{st.session_state.get('ref')}")
        
        text_for_ai = "\n".join(st.session_state['verses']) 
        
        with st.container(height=600, border=True):
            for baris_ayat in st.session_state['verses']:
                st.write(baris_ayat)

        col1, col2, col3, col4 = st.columns(4)
        can_nav = (mode == 'Pasal')

        # --- TOMBOL NAVIGASI ---
        with col1: 
            st.button('Sebelumnya', use_container_width=True, type='primary', 
                      on_click=nav_callback, args=("prev",), disabled=not can_nav)
            
        with col2:
            ask_ai = st.button('Tanya AI (Disini)', use_container_width=True)
        
        with col3:
            if st.button('Diskusi Lanjut (Chat)', use_container_width=True):
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
                st.switch_page(st.session_state['objek_halaman_ai'])

        with col4:
            st.button('Setelahnya', use_container_width=True, type='primary', 
                      on_click=nav_callback, args=("next",), disabled=not can_nav)

        st.write("---")
        
        # --- BAGIAN AI ---
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
                st.session_state['ai_ref'] = st.session_state['ref'] 
                st.rerun() 

    if st.session_state.get('ai_result') and st.session_state.get('ai_ref') == st.session_state.get('ref'): 
        st.subheader("Ringkasan & Makna (AI)")
        st.markdown(st.session_state['ai_result'])
        
        if st.button('Sembunyikan Hasil AI'):
            st.session_state['ai_result'] = None
            st.rerun()