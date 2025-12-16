from funcs import st, pd, GSheetsConnection
import time

# --- [BAGIAN 1: LOAD DATA YANG KEBAL LIMIT] ---
@st.cache_data(ttl=0, show_spinner=False)
def load_saved_data_safe():
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # Retry Loop (Mencoba 5 kali dengan jeda makin lama)
    max_retries = 5
    for i in range(max_retries):
        try:
            return conn.read(worksheet="saved")
        except Exception as e:
            # Cek apakah errornya karena Limit (429)
            if "429" in str(e) or "Quota exceeded" in str(e):
                wait_time = (i + 1) * 2  # Backoff: 2s, 4s, 6s, 8s, 10s
                time.sleep(wait_time)
                continue # Coba lagi
            else:
                # Kalau error lain (misal sheet gak ada), lempar keluar
                raise e
            
    # Percobaan terakhir
    return conn.read(worksheet="saved")

# --- [BAGIAN 2: HALAMAN UTAMA] ---
def page_saved():
    st.title("Saved Notes")
    st.write("Catatan studi dan riwayat chat Anda.")

    try:
        data = load_saved_data_safe()
        df = pd.DataFrame(data)
    except Exception:
        st.info("Belum ada catatan (Worksheet 'saved' tidak ditemukan).")
        return

    # Filter data user
    if df.empty or 'username' not in df.columns:
        st.info("Belum ada catatan.")
        return

    user_notes = df[df['username'] == st.session_state['username']]

    if user_notes.empty:
        st.info("Anda belum menyimpan catatan apapun.")
    else:
        # Tampilkan urut dari yang terbaru
        for index, row in user_notes.iloc[::-1].iterrows():
            with st.container(border=True):
                col_head, col_del = st.columns([0.9, 0.1])
                
                with col_head:
                    judul = row.get('title', 'Tanpa Judul')
                    st.subheader(f"{judul}")
                
                with col_del:
                    # --- TOMBOL HAPUS DENGAN RETRY LOGIC (VERSI KUAT) ---
                    if st.button("🗑️", key=f"del_note_{index}"):
                        # Hapus dari dataframe lokal dulu
                        df_updated = df.drop(index)
                        
                        try:
                            # Buat koneksi baru
                            conn_update = st.connection("gsheets", type=GSheetsConnection)
                            
                            with st.spinner("Menghapus... (Tunggu jika loading lama)"):
                                # Loop maksimal 5 kali (Anti-Spam)
                                max_retries = 5
                                for i in range(max_retries):
                                    try:
                                        conn_update.update(data=df_updated, worksheet="saved")
                                        break # Sukses -> Keluar loop
                                    
                                    except Exception as e:
                                        # DETEKSI ERROR LIMIT DARI TEKS ERRORNYA
                                        if "429" in str(e) or "Quota exceeded" in str(e):
                                            # Jeda "Backoff" (Makin lama makin panjang)
                                            # Biar Google gak marah kalau dispam
                                            wait_time = (i + 1) * 2 # 2s, 4s, 6s...
                                            time.sleep(wait_time) 
                                            
                                            # Kasih tanda ke user kalau lagi nunggu
                                          
                                        else:
                                            raise e # Kalau error lain, lempar aja
                            
                            # Jika berhasil update
                            st.cache_data.clear() 
                            st.rerun()
                            
                        except Exception as e:
                            # Tangkap sisa error (hanya jika sudah retry 5x gagal)
                            if "429" in str(e):
                                st.error("⚠️ Sistem sedang sangat sibuk. Mohon tunggu 1 menit sebelum menghapus lagi.", icon="🚫")
                            else:
                                st.error(f"Gagal hapus: {e}")
                
                st.markdown(row.get('content', ''))