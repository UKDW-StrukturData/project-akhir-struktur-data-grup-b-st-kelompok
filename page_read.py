import streamlit as st
import pandas as pd
import time
from funcs import kitab, getPassage, ask_gemini, getVerseCount
from funcs import initCache, shiftCache  # versi linked list
from streamlit_gsheets import GSheetsConnection


def navCallback(direction):
    """Navigasi prev/next menggunakan linked list."""
    curr = st.session_state.get("cacheNode")

    if not curr:
        return

    newCurr, success = shiftCache(curr, direction)

    if success:
        st.session_state["cacheNode"] = newCurr
        st.session_state["book"] = newCurr.book
        st.session_state["chapter"] = newCurr.chapter
        st.session_state["verses"] = newCurr.verses
        st.session_state["ref"] = newCurr.ref
        st.session_state["show_result"] = True
        st.session_state["ai_result"] = None


def page_read():
    st.title("Baca Alkitab & Analisis AI")

    # State dasar
    if "show_result" not in st.session_state:
        st.session_state["show_result"] = False
    if "ref" not in st.session_state:
        st.session_state["ref"] = ""
    if "verses" not in st.session_state:
        st.session_state["verses"] = []

    # State kitab & pasal
    if "book" not in st.session_state:
        st.session_state["book"] = list(kitab.keys())[0]
    if "chapter" not in st.session_state:
        st.session_state["chapter"] = 1

    # State linked list cache
    if "cacheNode" not in st.session_state:
        st.session_state["cacheNode"] = None

    list_kitab = list(kitab.keys())

    # ==========================
    # SINKRONISASI CACHE
    # ==========================
    currentCache = st.session_state.get("cacheNode")

    cacheValid = False
    if currentCache:
        if (
            currentCache.book == st.session_state["book"]
            and currentCache.chapter == st.session_state["chapter"]
        ):
            cacheValid = True

    if not cacheValid and st.session_state.get("show_result"):
        st.session_state["cacheNode"] = initCache(
            st.session_state["book"], st.session_state["chapter"]
        )
        currentCache = st.session_state["cacheNode"]

        st.session_state["verses"] = currentCache.verses
        st.session_state["ref"] = currentCache.ref

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

            chapter = st.number_input(
                "Pasal:", min_value=1, max_value=max_ch, key="chapter"
            )

        # Mode ayat/pasal
        with c3:
            mode = st.selectbox("Mode:", ["Pasal", "Ayat"], key="mode")

        passage = None
        passage_options = [str(x) for x in range(1, getVerseCount(book, chapter) + 1)]

        # Jika pilih ayat
        if mode == "Ayat":
            with c4:
                passage = st.multiselect("Ayat:", passage_options, key="passage")

        # Tombol tampilkan ayat
        if st.button("Tampilkan Ayat", use_container_width=True, type="primary"):
            st.session_state["show_result"] = True

            if mode == "Ayat":
                if passage:
                    st.session_state["ref"] = f"{book} {chapter}: {', '.join(passage)}"
                    st.session_state["verses"] = getPassage(book, chapter, passage)
                else:
                    st.warning("Pilih ayat dulu.")
            else:
                # Mode pasal → biarkan logic sinkronisasi cache meng-handle
                pass

    st.write("---")

    with st.expander(label='Pilih Ayat/Pasal', expanded=True):
        pilih = st.multiselect('Pilih Ayat', passage_options)
        if st.button('Bookmark', type='primary', use_container_width=True):
            conn = st.connection("gsheets", type=GSheetsConnection)
            data = conn.read(worksheet="bookmarks", ttl=0)
            df = pd.DataFrame(data)
            for verse in pilih:
                content = getPassage(book, chapter, verse)
                new_user = pd.DataFrame({
                    'book': [book],
                    'chapter': [chapter],
                    'verse' : [verse],
                    'content' : content,
                    'username' : [st.session_state['username']]
                })

                updated_df = pd.concat([df, new_user], ignore_index=True)

                try:
                    conn.update(data=updated_df, worksheet="bookmarks")
                except Exception as e:
                    st.error(f"Gagal menulis ke Google Sheets: {e}")

                with st.status("Bookmarking...", expanded=False) as s:
                    time.sleep(1)
                    s.update(label=f"Bookmarked {book} {chapter}: {verse}.", state="complete")
                    time.sleep(1)

    st.write("---")

    # ==========================
    # TAMPILAN HASIL AYAT
    # ==========================
    if st.session_state.get("show_result") and st.session_state.get("verses"):
        st.subheader(f"{st.session_state.get('ref')}")

        text_for_ai = "\n".join(st.session_state["verses"])

        with st.container(height=600, border=True):
            for v in st.session_state["verses"]:
                st.write(v)

        col1, col2, col3, col4 = st.columns(4)
        can_nav = mode == "Pasal"

        # Tombol Navigasi
        with col1:
            if book == 'Kejadian' and chapter == 1:
                st.button(
                    "Sebelumnya",
                    use_container_width=True,
                    type="primary",
                    disabled=True,
                )
            else:
                st.button(
                    "Sebelumnya",
                    use_container_width=True,
                    type="primary",
                    on_click=navCallback,
                    args=("prev",),
                    disabled=not can_nav,
                )

        # Tombol Tanya AI
        with col2:
            ask_ai = st.button("Tanya AI (Disini)", use_container_width=True)

        # Tombol pindah ke chat
        with col3:
            if st.button("Diskusi Lanjut (Chat)", use_container_width=True):
                prompt_pindah = f"""
                Kamu adalah asisten studi Alkitab.
                Jelaskan arti yang penting dari bahasa asli untuk setiap kata yang penting.
                Berikan cross referencenya juga.

                Ayat yang Anda pilih:
                {text_for_ai}
                """

                st.session_state["paket_prompt"] = prompt_pindah
                st.session_state["paket_judul"] = (
                    f"Diskusi Ayat: {st.session_state['ref']}"
                )
                st.session_state["pindah_dari_read"] = True
                st.switch_page(st.session_state["objek_halaman_ai"])

        with col4:
            if book == 'Wahyu' and chapter == 22:
                st.button(
                    "Setelahnya",
                    use_container_width=True,
                    type="primary",
                    disabled=True,
                )
            else:
                st.button(
                    "Setelahnya",
                    use_container_width=True,
                    type="primary",
                    on_click=navCallback,
                    args=("next",),
                    disabled=not can_nav,
                )

        st.write("---")

        # ==========================
        # ANALISIS AI
        # ==========================
        if ask_ai and st.session_state["verses"]:
            prompt = f"""
            Kamu adalah asisten studi Alkitab.
            Jelaskan arti yang penting dari bahasa asli untuk setiap kata yang penting.
            Berikan cross referencenya juga.

            Ayat yang Anda pilih:
            {text_for_ai}
            """

            with st.spinner(f"AI sedang menganalisis {st.session_state['ref']}..."):
                hasil_ai = ask_gemini(prompt)
                st.session_state["ai_result"] = hasil_ai
                st.session_state["ai_ref"] = st.session_state["ref"]
                st.rerun()

    # ==========================
    # TAMPILKAN HASIL AI
    # ==========================
    if (
        st.session_state.get("ai_result")
        and st.session_state.get("ai_ref") == st.session_state.get("ref")
    ):
        st.subheader("Ringkasan & Makna (AI)")
        st.markdown(st.session_state["ai_result"])

        if st.button("Sembunyikan Hasil AI"):
            st.session_state["ai_result"] = None
            st.rerun()
