from funcs import (
    st, pd, datetime, GSheetsConnection, io, textwrap, # Library
    ask_gemini, canvas, letter # Logic & Variable
)

def create_pdf(chat_history):
    """Membuat file PDF dari riwayat chat dalam memori (BytesIO)."""
    if not canvas:
        return None
        
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    margin = 50
    y = height - margin
    
    # Header PDF
    c.setTitle("Riwayat Chat Real Bread")
    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin, y, "Riwayat Percakapan Real Bread")
    y -= 20
    c.setFont("Helvetica", 10)
    c.drawString(margin, y, f"Diexport pada: {datetime.datetime.now().strftime('%d %B %Y, %H:%M')}")
    y -= 30
    
    # Loop pesan
    for msg in chat_history:
        role = "User" if msg["role"] == "user" else "AI Assistant"
        content = msg["content"]
        
        # Cek sisa halaman
        if y < margin + 40:
            c.showPage()
            y = height - margin
            
        # Role
        c.setFont("Helvetica-Bold", 10)
        c.drawString(margin, y, f"[{role}]")
        y -= 15
        
        # Konten wrapping
        c.setFont("Helvetica", 10)
        lines = textwrap.wrap(content, width=95)
        
        for line in lines:
            if y < margin:
                c.showPage()
                y = height - margin
            c.drawString(margin, y, line)
            y -= 12
            
        y -= 10 

    c.save()
    buffer.seek(0)
    return buffer

def page_ai(): 
    st.title("Chat Bebas")
    
    if "chat" not in st.session_state:
        st.session_state.chat = [] 

    # --- LOGIC TERIMA LEMPARAN DARI HALAMAN BACA ---
    if st.session_state.get('pindah_dari_read'): 
        
        prompt_kiriman = st.session_state.get('paket_prompt')
        judul_user = st.session_state.get('paket_judul', "Analisis Ayat")
        
        with st.spinner(f"Sedang menganalisis topik: {judul_user}..."):
            jawaban = ask_gemini(prompt_kiriman)
        
        st.session_state.chat.append({
            "role": "user", 
            "avatar": "user.png", 
            "content": judul_user
        })
        
        st.session_state.chat.append({
            "role": "assistant", 
            "avatar": "logo.png", 
            "content": jawaban
        })
        
        st.session_state['pindah_dari_read'] = False 
        st.session_state['paket_prompt'] = None 
        
        st.rerun()
        
    # --- TAMPILKAN RIWAYAT CHAT ---
    for pesan in st.session_state.chat: 
        avatar_path = pesan.get("avatar") 
        st.chat_message(pesan["role"], avatar=avatar_path).write(pesan["content"])
    
    # --- AREA TOMBOL (DI BAWAH CHAT, DI ATAS INPUT) ---
    st.write("---")
    
    # Bagi layar jadi 3 kolom sama besar agar penuh (tidak kosong)
    c_reset, c_save, c_pdf = st.columns(3)
    
    # 1. TOMBOL RESET
    with c_reset:
        if st.button("Reset Chat", use_container_width=True, type="secondary"):
            st.session_state.chat = []
            st.rerun()

    # 2. TOMBOL SIMPAN
    with c_save:
        if st.button("Simpan Chat", use_container_width=True, type="primary"):
            if not st.session_state.chat:
                st.warning("Chat kosong.")
            else:
                # Format text
                chat_text = ""
                for msg in st.session_state.chat:
                    role_name = "Anda" if msg['role'] == 'user' else "AI"
                    chat_text += f"**{role_name}:**\n{msg['content']}\n\n---\n\n"
                
                conn = st.connection("gsheets", type=GSheetsConnection)
                try:
                    # Baca sheet 'saved'
                    try:
                        data = conn.read(worksheet="saved", ttl=0)
                        df_notes = pd.DataFrame(data)
                    except:
                        df_notes = pd.DataFrame(columns=['title', 'content', 'username'])

                    if df_notes.empty:
                         df_notes = pd.DataFrame(columns=['title', 'content', 'username'])
                    
                    # Buat 1 entri baru khusus chat ini
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    new_note = pd.DataFrame({
                        'title': [f"Chat Session ({timestamp})"],
                        'content': [chat_text],
                        'username': [st.session_state['username']]
                    })

                    # Gabung
                    updated_df = pd.concat([df_notes, new_note], ignore_index=True)
                    
                    # Update sheet
                    conn.update(data=updated_df, worksheet="saved")
                    st.toast("Chat berhasil disimpan!")
                    
                except Exception as e:
                    st.error(f"Gagal simpan ke 'saved': {e}")

    # 3. TOMBOL EXPORT PDF
    with c_pdf:
        if st.session_state.chat and canvas:
            pdf_bytes = create_pdf(st.session_state.chat)
            if pdf_bytes:
                st.download_button(
                    label="Export PDF",
                    data=pdf_bytes,
                    file_name=f"chat_{datetime.datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
        else:
            # Tombol dummy jika kosong/library tidak ada, biar layout tetap rapi
            st.button("Export PDF", disabled=True, use_container_width=True)

    # --- INPUT CHAT ---
    userinput = st.chat_input("Tanya tentang Alkitab atau teologi...")
    
    if userinput:
        st.chat_message("user", avatar='user.png').write(userinput) 
        st.session_state.chat.append({"role":"user", "avatar":"user.png", "content":userinput}) 
        
        prompt_dgn_constraint = """Instruksi Utama:
1. Jawablah pertanyaan HANYA jika berkaitan dengan: Alkitab, Teologi, Sejarah Gereja, Kehidupan Rohani.
2. Tolak topik lain dengan sopan.
3. Jawablah dengan nada pastoral.

Riwayat percakapan:
"""
        for message in st.session_state.chat[-10:]: 
            role_label = "User" if message["role"] == "user" else "Assistant"
            prompt_dgn_constraint += f"{role_label}: {message['content']}\n"

        prompt_dgn_constraint += f"User: {userinput}\nAssistant:"

        with st.chat_message("assistant", avatar='logo.png'): 
            with st.spinner("Mengetik..."):
                jawaban = ask_gemini(prompt_dgn_constraint) 
                st.write(jawaban) 
                
        st.session_state.chat.append({"role":"assistant", "avatar":"logo.png", "content":jawaban})
        st.rerun()