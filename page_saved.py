from funcs import st, pd, GSheetsConnection

@st.cache_data(ttl=0, show_spinner=False)
def load_saved_data():
    conn = st.connection("gsheets", type=GSheetsConnection)
    return conn.read(worksheet="saved")

def page_saved():
    st.title("Saved Notes")
    st.write("Catatan studi dan riwayat chat Anda.")

    conn = st.connection("gsheets", type=GSheetsConnection)

    try:
        data = load_saved_data()# Update sheet name
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
                    # Ambil 'title'
                    judul = row.get('title', 'Tanpa Judul')
                    st.subheader(f"{judul}")
                
                with col_del:
                    if st.button("🗑️", key=f"del_note_{index}"):
                        df_updated = df.drop(index)
                        try:
                            conn_update = st.connection("gsheets", type=GSheetsConnection)
                            
                            with st.spinner("Menghapus catatan..."):
                                conn_update.update(data=df_updated, worksheet="saved")
                            st.cache_data.clear() 
                            st.rerun()
                        except Exception as e:
                            st.error(f"Gagal hapus: {e}")

                st.markdown(row.get('content', ''))