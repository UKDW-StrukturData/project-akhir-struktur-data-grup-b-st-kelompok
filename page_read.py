from funcs import (
    st, pd, time, datetime, GSheetsConnection, # Library
    kitab, getPassage, ask_gemini, getVerseCount, initCache, shiftCache # Logic
)

def navCallback(direction):
    """Navigasi prev/next menggunakan linked list."""
    curr = st.session_state.get("cacheNode")
    if not curr: return

    newCurr, success = shiftCache(curr, direction)
    if success:
        st.session_state["cacheNode"] = newCurr
        st.session_state["book"] = newCurr.book
        st.session_state["chapter"] = newCurr.chapter
        
        # UPDATE: Langsung update verses dan ref agar teks berubah saat navigasi
        st.session_state["verses"] = newCurr.verses
        st.session_state["ref"] = newCurr.ref
        
        # Pastikan tetap tampil
        st.session_state["show_result"] = True 
        st.session_state["ai_result"] = None

def page_read():
    st.title("Baca Alkitab & Analisis AI")

    # --- PERBAIKAN 1: AUTO-LOAD KEJADIAN 1 SAAT LOGIN ---
    
    # 1. Default show_result jadi True
    if "show_result" not in st.session_state:
        st.session_state["show_result"] = True 
    
    if "ref" not in st.session_state:
        st.session_state["ref"] = "Kejadian 1"
    if "verses" not in st.session_state:
        st.session_state["verses"] = []

    # State kitab & pasal
    if "book" not in st.session_state:
        st.session_state["book"] = list(kitab.keys())[0] # Default Kejadian
    if "chapter" not in st.session_state:
        st.session_state["chapter"] = 1
    
    # 2. Inisialisasi Cache Otomatis jika kosong
    if "cacheNode" not in st.session_state or st.session_state["cacheNode"] is None:
        st.session_state["cacheNode"] = initCache("Kejadian", 1)
        # Isi data agar langsung muncul tanpa klik tombol
        curr = st.session_state["cacheNode"]
        st.session_state["verses"] = curr.verses
        st.session_state["ref"] = curr.ref
        st.session_state["book"] = "Kejadian"
        st.session_state["chapter"] = 1

    list_kitab = list(kitab.keys())

    # ==========================
    # UI INPUT
    # ==========================
    with st.expander(label="Cari Pasal/Ayat", expanded=True):
        c1, c2, c3, c4 = st.columns(4)

        # Dropdown kitab
        with c1:
            book = st.selectbox("Kitab:", list_kitab, key="book")

        # Pilih pasal
        with c2:
            max_ch = kitab[book]
            if st.session_state.get("chapter", 1) > max_ch:
                st.session_state["chapter"] = 1
            chapter = st.number_input("Pasal:", min_value=1, max_value=max_ch, key="chapter")

        # Mode ayat/pasal
        with c3:
            mode = st.selectbox("Mode:", ["Pasal", "Ayat"], key="mode")

        passage_options = [str(x) for x in range(1, getVerseCount(book, chapter) + 1)]
        passage = None

        if mode == "Ayat":
            with c4:
                passage = st.multiselect("Ayat:", passage_options, key="passage")
        
        label_tombol = "Tampilkan Pasal" if mode == "Pasal" else "Tampilkan Ayat"
        
        # Tombol manual (tetap ada untuk pencarian spesifik)
        if st.button(label_tombol, use_container_width=True, type="primary"):
            st.session_state["show_result"] = True
            st.session_state["ai_result"] = None # Reset AI
            
            # Init Cache baru
            st.session_state["cacheNode"] = initCache(book, chapter)
            curr = st.session_state["cacheNode"]
            
            if mode == "Ayat" and passage:
                st.session_state["ref"] = f"{book} {chapter}: {', '.join(passage)}"
                st.session_state["verses"] = getPassage(book, chapter, passage)
            else:
                st.session_state["ref"] = curr.ref
                st.session_state["verses"] = curr.verses

    st.write("---")

    # ==========================
    # FITUR BOOKMARK
    # ==========================
    if st.session_state.get("show_result"):
        with st.expander(label='Pilih Ayat untuk Bookmark', expanded=False):
            pilih = st.multiselect('Pilih Ayat', passage_options)
            if st.button('Simpan Bookmark', type='secondary', use_container_width=True):
                conn = st.connection("gsheets", type=GSheetsConnection)
                try:
                    data = conn.read(worksheet="bookmarks", ttl=0)
                    df = pd.DataFrame(data)
                except:
                    df = pd.DataFrame(columns=['book', 'chapter', 'verse', 'content', 'username'])
                
                if df.empty:
                    df = pd.DataFrame(columns=['book', 'chapter', 'verse', 'content', 'username'])

                new_entries = []
                for verse in pilih:
                    content = getPassage(book, chapter, verse)
                    if isinstance(content, list): content = " ".join(content)
                    
                    new_entries.append({
                        'book': book, 'chapter': chapter, 'verse': verse,
                        'content': content, 'username': st.session_state['username']
                    })
                
                if new_entries:
                    new_user = pd.DataFrame(new_entries)
                    updated_df = pd.concat([df, new_user], ignore_index=True)
                    try:
                        conn.update(data=updated_df, worksheet="bookmarks")
                        st.success(f"Berhasil bookmark {len(new_entries)} ayat.")
                    except Exception as e:
                        st.error(f"Error Sheets: {e}")

    # ==========================
    # TAMPILAN HASIL AYAT
    # ==========================
    if st.session_state.get("show_result") and st.session_state.get("verses"):
        st.subheader(f"{st.session_state.get('ref')}")
        text_for_ai = "\n".join(st.session_state["verses"])

        with st.container(height=600, border=True):
            for v in st.session_state["verses"]:
                st.write(v)

        # Navigasi & AI
        col1, col2, col3, col4 = st.columns(4)
        can_nav = mode == "Pasal"

        with col1:
            st.button("Sebelumnya", use_container_width=True, on_click=navCallback, args=("prev",), disabled=not can_nav)
        
        with col2:
            ask_ai = st.button("Tanya AI (Disini)", use_container_width=True, type='primary')
            
        with col3:
             if st.button("Diskusi Lanjut (Chat)", use_container_width=True):
                prompt_pindah = f"""
                Kamu adalah asisten studi Alkitab.
                Ayat: {text_for_ai}
                """
                st.session_state["paket_prompt"] = prompt_pindah
                st.session_state["paket_judul"] = f"Diskusi: {st.session_state['ref']}"
                st.session_state["pindah_dari_read"] = True
                st.switch_page(st.session_state["objek_halaman_ai"])
                
        with col4:
            st.button("Setelahnya", use_container_width=True, on_click=navCallback, args=("next",), disabled=not can_nav)

        # ==========================
        # ANALISIS AI
        # ==========================
        if ask_ai:
            prompt = f"""
            Kamu adalah asisten studi Alkitab.
            Jelaskan arti penting bahasa asli dan cross reference.
            Ayat: {text_for_ai}
            """
            with st.spinner(f"AI sedang menganalisis {st.session_state['ref']}..."):
                hasil_ai = ask_gemini(prompt)
                st.session_state["ai_result"] = hasil_ai
                st.session_state["ai_ref"] = st.session_state["ref"]
                st.rerun()

    # ==========================
    # HASIL AI & SAVE NOTE
    # ==========================
    if st.session_state.get("ai_result") and st.session_state.get("ai_ref") == st.session_state.get("ref"):
        st.divider()
        st.subheader("Ringkasan & Makna (AI)")
        st.markdown(st.session_state["ai_result"])

        c_save, c_hide = st.columns([1, 4])
        with c_save:
            if st.button("💾 Simpan Note"):
                conn = st.connection("gsheets", type=GSheetsConnection)
                try:
                    data = conn.read(worksheet="saved", ttl=0) # Update sheet name
                    df_notes = pd.DataFrame(data)
                except:
                    df_notes = pd.DataFrame(columns=['title', 'content', 'username'])
                
                if df_notes.empty:
                    df_notes = pd.DataFrame(columns=['title', 'content', 'username'])

                new_note = pd.DataFrame({
                    'title': [st.session_state['ai_ref']], 
                    'content': [st.session_state['ai_result']],
                    'username': [st.session_state['username']]
                })
                
                try:
                    updated_df = pd.concat([df_notes, new_note], ignore_index=True)
                    conn.update(data=updated_df, worksheet="saved") # Update sheet name
                    st.toast("Catatan disimpan!", icon="✅")
                except Exception as e:
                    st.error(f"Gagal simpan ke sheet 'saved': {e}")
        
        with c_hide:
            if st.button("Tutup"):
                st.session_state["ai_result"] = None
                st.rerun()