import streamlit as st
from funcs import kitab, getChapter, getPassage, ask_gemini

# --- FUNGSI BANTUAN CACHE (TANPA CLASS) ---

def get_neighbor_ref(book, chapter, direction):
    """
    Hitung referensi tetangga (Next/Prev).
    direction: 1 (Next), -1 (Prev)
    Returns: (new_book, new_chapter) or (None, None)
    """
    list_kitab = list(kitab.keys())
    try:
        curr_idx = list_kitab.index(book)
        max_ch = kitab[book]
    except ValueError:
        return None, None 

    new_book, new_ch = book, chapter

    if direction == 1: # MAJU
        if chapter < max_ch:
            new_ch = chapter + 1
        elif curr_idx < len(list_kitab) - 1:
            new_book = list_kitab[curr_idx + 1]
            new_ch = 1
        else:
            return None, None # Mentok Wahyu
    else: # MUNDUR
        if chapter > 1:
            new_ch = chapter - 1
        elif curr_idx > 0:
            new_book = list_kitab[curr_idx - 1]
            new_ch = kitab[new_book] # Ambil pasal terakhir
        else:
            return None, None # Mentok Kejadian

    return new_book, new_ch

def fetch_data_dict(book, chapter):
    """Ambil data dan bungkus jadi Dictionary"""
    verses = getChapter(book, chapter)
    return {
        "book": book,
        "chapter": chapter,
        "verses": verses,
        "ref": f"{book} {chapter}"
    }

def init_cache(center_book, center_chapter):
    """
    Inisialisasi List Cache [Prev2, Prev1, CENTER, Next1, Next2]
    """
    # 1. Mulai dengan Center
    cache_list = [None] * 5 # Slot kosong [0, 1, 2, 3, 4]
    cache_list[2] = fetch_data_dict(center_book, center_chapter) # Isi Tengah

    # 2. Isi Kiri (Mundur)
    curr_b, curr_c = center_book, center_chapter
    for i in range(1, -1, -1): # index 1 lalu 0
        pb, pc = get_neighbor_ref(curr_b, curr_c, -1)
        if pb:
            cache_list[i] = fetch_data_dict(pb, pc)
            curr_b, curr_c = pb, pc
    
    # 3. Isi Kanan (Maju)
    curr_b, curr_c = center_book, center_chapter
    for i in range(3, 5): # index 3 lalu 4
        nb, nc = get_neighbor_ref(curr_b, curr_c, 1)
        if nb:
            cache_list[i] = fetch_data_dict(nb, nc)
            curr_b, curr_c = nb, nc
            
    return cache_list

def shift_cache(cache_list, direction):
    """
    Geser Window Cache.
    Direction: 'next' (geser kiri, tambah kanan), 'prev' (geser kanan, tambah kiri)
    """
    # Ambil referensi ujung untuk fetching data baru
    
    if direction == 'next':
        # Cek apakah current (tengah) punya next? (index 3)
        if cache_list[3] is None:
            st.toast("Sudah di akhir Alkitab")
            return cache_list, False

        # Ambil info node paling kanan (buntut) untuk cari next-nya lagi
        last_item = cache_list[4] if cache_list[4] else cache_list[3] 
        # Kalau list penuh [A,B,C,D,E], last=E. Kalau [A,B,C,D,None], last=D.
        
        new_data = None
        if last_item:
            nb, nc = get_neighbor_ref(last_item['book'], last_item['chapter'], 1)
            if nb:
                new_data = fetch_data_dict(nb, nc)
        
        # PROSES GESER: Hapus index 0 (paling kiri), Append new_data di kanan
        cache_list.pop(0)
        cache_list.append(new_data)
        return cache_list, True

    elif direction == 'prev':
        # Cek apakah current (tengah) punya prev? (index 1)
        if cache_list[1] is None:
            st.toast("Sudah di awal Alkitab")
            return cache_list, False

        # Ambil info node paling kiri (kepala) untuk cari prev-nya lagi
        first_item = cache_list[0] if cache_list[0] else cache_list[1]
        
        new_data = None
        if first_item:
            pb, pc = get_neighbor_ref(first_item['book'], first_item['chapter'], -1)
            if pb:
                new_data = fetch_data_dict(pb, pc)
        
        # PROSES GESER: Hapus index terakhir (kanan), Insert new_data di kiri (0)
        cache_list.pop()
        cache_list.insert(0, new_data)
        return cache_list, True

    return cache_list, False


# --- HALAMAN UTAMA ---

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