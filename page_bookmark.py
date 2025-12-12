from funcs import st, pd, GSheetsConnection, plt

def page_bookmark():
    st.title("Bookmark")
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # Baca data terbaru tanpa cache (ttl=0)
    try:
        data = conn.read(worksheet="bookmarks", ttl=0)
        df = pd.DataFrame(data)
    except Exception:
        st.error("Gagal memuat data bookmark. Pastikan sheet 'bookmarks' ada.")
        return

    # hanya tampilkan visualisasi jika data ada
    if not df.empty and 'book' in df.columns:
        st.write('---')
        with st.expander(label='Distribusi kitab yang dibookmark oleh pengguna Real Bread lainnya'):
            pie, bar = st.columns(2)
            hitung = df['book'].value_counts().to_dict()

            labels = list(hitung.keys())
            values = list(hitung.values())
            
            with pie:
                fig, ax = plt.subplots()
                ax.pie(values, labels=labels, autopct="%1.1f%%")
                ax.axis('equal')
                st.pyplot(fig)

            with bar:
                fig2, ax2 = plt.subplots()
                ax2.bar(labels, values)
                st.pyplot(fig2)

    st.write('---')

    # Filter data user
    if 'username' in df.columns:
        user_df = df[df['username'] == st.session_state['username']]
    else:
        user_df = pd.DataFrame()

    if user_df.empty:
        st.info('Belum ada bookmark di akun ini.')
    else:
        # Loop dengan iterrows() tapi kita butuh index asli untuk menghapus
        for index, row in user_df.iterrows():
            with st.container(border=True):
                c1, c2 = st.columns([0.9, 0.1])
                with c1:
                    st.write(f"### {row['book']} {int(row['chapter'])}:{int(row['verse'])}")
                    st.write(row['content'])
                with c2:
                    # PERUBAHAN 3: Tombol Hapus Bookmark
                    if st.button("🗑️", key=f"del_bm_{index}", help="Hapus Bookmark ini"):
                        # Hapus dari dataframe asli berdasarkan index
                        df_updated = df.drop(index)
                        try:
                            conn.update(data=df_updated, worksheet="bookmarks")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Gagal menghapus: {e}")