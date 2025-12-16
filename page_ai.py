from funcs import (
    st, pd, datetime, GSheetsConnection, io, textwrap, # Library
    ask_gemini, canvas, letter # Logic & Variable
)
from google.api_core.exceptions import ResourceExhausted, InvalidArgument, NotFound
import time # <--- [DITAMBAHKAN BIAR BISA NUNGGU]

# --- [BAGIAN 1: FUNGSI KHUSUS BIAR GAK MUNCUL IJO-IJO] ---
# Taruh fungsi ini di LUAR page_ai()
@st.cache_data(show_spinner=False, ttl=0)
def get_data_silent():
    """Mengambil data dari GSheet tanpa loading bar bawaan."""
    conn = st.connection("gsheets", type=GSheetsConnection)
    try:
        # show_spinner=False di sini buat mastiin library-nya diem
        return conn.read(worksheet="saved", ttl=0, show_spinner=False)
    except Exception:
        # Balikin dataframe kosong kalo error/sheet belum ada
        return pd.DataFrame(columns=['title', 'content', 'username'])

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
    
    # --- AREA TOMBOL ---
    st.write("---")
    
    # [1] BAGI KOLOM TOMBOL DULUAN
    c_reset, c_save, c_pdf = st.columns(3)

    # [2] SIAPKAN WADAH NOTIFIKASI DI BAWAHNYA (FULL WIDTH)
    status_box = st.empty() 

    # --- A. TOMBOL RESET ---
    with c_reset:
        if st.button("Reset Chat", use_container_width=True, type="secondary"):
            st.session_state.chat = []
            st.rerun()

    # --- B. TOMBOL SIMPAN (SUDAH DITAMBAH LOGIKA RETRY/ANTI-LIMIT) ---
    with c_save:
        if st.button("Simpan Chat", use_container_width=True, type="primary"):
            if not st.session_state.chat:
                status_box.warning("Chat kosong, tidak ada yang bisa disimpan.")
            else:
                # Format text chat
                chat_text = ""
                for msg in st.session_state.chat:
                    role_name = "Anda" if msg['role'] == 'user' else "AI"
                    chat_text += f"{role_name}:\n{msg['content']}\n\n---\n\n"
                
                try:
                    # TAMPILKAN LOADING BIRU (Manual Text)
                    status_box.info("Sedang menyimpan ke database...")
                    
                    # Panggil fungsi silent yang udah kita bikin di atas
                    df_notes = get_data_silent()
                    
                    if df_notes.empty:
                        df_notes = pd.DataFrame(columns=['title', 'content', 'username'])
                    
                    # SIAPKAN DATA
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    new_note = pd.DataFrame({
                        'title': [str(f"Chat Session ({timestamp})")], 
                        'content': [str(chat_text)],                     
                        'username': [str(st.session_state.get('username', 'Guest'))] 
                    })

                    # GABUNG
                    updated_df = pd.concat([df_notes, new_note], ignore_index=True)
                    
                    # --- UPDATE KE GSHEET DENGAN RETRY LOGIC (BIAR GAK ERROR 429) ---
                    conn = st.connection("gsheets", type=GSheetsConnection)
                    
                    max_retries = 5
                    for i in range(max_retries):
                        try:
                            conn.update(data=updated_df, worksheet="saved")
                            break # Sukses -> Keluar loop
                        except Exception as e:
                            # Cek Error Limit (429)
                            if "429" in str(e) or "Quota exceeded" in str(e):
                                wait_time = (i + 1) * 2 
                                time.sleep(wait_time) # Tunggu 2s, 4s, 6s...
                                
                                # Info ke user biar gak panik
                                if i > 0:
                                    status_box.info(f"Antrian padat, mencoba lagi... ({i+1}/{max_retries})")
                                continue
                            else:
                                raise e # Error lain lempar aja
                    
                    # BERHASIL
                    get_data_silent.clear() # Reset cache biar data baru kebaca nanti
                    status_box.success("Berhasil menyimpan chat!")
                    
                except Exception as e:
                    if "429" in str(e) or "Quota exceeded" in str(e):
                         status_box.error("Gagal Simpan: Server Google sibuk. Tunggu 1 menit lagi.")
                    else:
                        status_box.error(f"Gagal simpan: {e}")

    # --- C. TOMBOL PDF (UPDATED) ---
    with c_pdf:
        if st.session_state.chat:
            if canvas: # Cek apakah library reportlab tersedia
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
                # Jika canvas None (library hilang), kasih tombol mati + pesan error
                st.button("Export PDF", disabled=True, use_container_width=True)
                st.caption("Gagal: Library 'reportlab' belum terinstall.")
        else:
            st.button("Export PDF", disabled=True, use_container_width=True)

    userinput = st.chat_input("Tanya tentang Alkitab atau teologi...")
    
    if userinput:
        st.chat_message("user", avatar='user.png').write(userinput) 
        st.session_state.chat.append({"role":"user", "avatar":"user.png", "content":userinput}) 
        
        # --- PROMPT ASLI KAMU (TIDAK DIUBAH) ---
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
                
                # --- MULAI TRY-EXCEPT DISINI ---
                try:
                    # 1. Panggil AI
                    # Sekarang funcs.py akan melempar error jika gagal (bukan teks)
                    jawaban = ask_gemini(prompt_dgn_constraint) 
                    
                    # 2. Jika Sukses (Tidak ada error)
                    st.write(jawaban) 
                    st.session_state.chat.append({"role":"assistant", "avatar":"logo.png", "content":jawaban})
                    st.rerun()

                # --- BAGIAN EXCEPT (MENANGKAP ERROR) ---

                # Skenario A: Error API Key (Akses Terkunci)
                # Menangkap InvalidArgument (Google) atau ValueError (Cek manual kita tadi)
                except (InvalidArgument, ValueError) as e:
                    st.error("Akses Terkunci")
                    st.write("API Key AI salah!, Mohon Periksa Kembali API Key AI anda")
                    
                # Skenario B: Error Kuota Habis
                except ResourceExhausted:
                    st.warning("Antrian Penuh")
                    st.write("Kuota penggunaan AI penuh, Mohon coba lagi nanti")

                # Skenario C: Model Tidak Ditemukan (Misal salah nama model)
                except NotFound:
                    st.error("Model Tidak Ditemukan")
                    st.write("Nama model AI di `funcs.py` tidak dikenali oleh Google.")

                # Skenario D: Error Lainnya (Internet putus, dll)
                except Exception as e:
                    st.error("Gangguan Sistem")
                    st.write("Terjadi kesalahan yang tidak terduga.")