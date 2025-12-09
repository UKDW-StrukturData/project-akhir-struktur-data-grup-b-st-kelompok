import streamlit as st
import requests
import google.generativeai as genai
from bs4 import BeautifulSoup

kitab = {
    "Kejadian": 50,
    "Keluaran": 40,
    "Imamat": 27,
    "Bilangan": 36,
    "Ulangan": 34,
    "Yosua": 24,
    "Hakim-hakim": 21,
    "Rut": 4,
    "1 Samuel": 31,
    "2 Samuel": 24,
    "1 Raja-raja": 22,
    "2 Raja-raja": 25,
    "1 Tawarikh": 29,
    "2 Tawarikh": 36,
    "Ezra": 10,
    "Nehemia": 13,
    "Ester": 10,
    "Ayub": 42,
    "Mazmur": 150,
    "Amsal": 31,
    "Pengkhotbah": 12,
    "Kidung Agung": 8,
    "Yesaya": 66,
    "Yeremia": 52,
    "Ratapan": 5,
    "Yehezkiel": 48,
    "Daniel": 12,
    "Hosea": 14,
    "Yoel": 3,
    "Amos": 9,
    "Obaja": 1,
    "Yunus": 4,
    "Mikha": 7,
    "Nahum": 3,
    "Habakuk": 3,
    "Zefanya": 3,
    "Hagai": 2,
    "Zakharia": 14,
    "Maleakhi": 4,
    "Matius": 28,
    "Markus": 16,
    "Lukas": 24,
    "Yohanes": 21,
    "Kisah Para Rasul": 28,
    "Roma": 16,
    "1 Korintus": 16,
    "2 Korintus": 13,
    "Galatia": 6,
    "Efesus": 6,
    "Filipi": 4,
    "Kolose": 4,
    "1 Tesalonika": 5,
    "2 Tesalonika": 3,
    "1 Timotius": 6,
    "2 Timotius": 4,
    "Titus": 3,
    "Filemon": 1,
    "Ibrani": 13,
    "Yakobus": 5,
    "1 Petrus": 5,
    "2 Petrus": 3,
    "1 Yohanes": 5,
    "2 Yohanes": 1,
    "3 Yohanes": 1,
    "Yudas": 1,
    "Wahyu": 22
}

def clean_text_html(text):
    """Bersihkan tag HTML dari string."""
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text(separator="\n")

def cleanText(data):
    hasil = []
    if isinstance(data, list):
        items = data
    else:
        items = [data]
    for item in items:
        if "res" in item:
            item = item["res"]
        for book_id, book_data in item.items():
            chapters = book_data.get("data", {})
            for chapter_num, verses in chapters.items():
                for verse_num, verse_data in verses.items():
                    verse = verse_data.get("verse", "")
                    title = verse_data.get("title", "")
                    text = verse_data.get("text", "")
                    if title:
                        hasil.append(clean_text_html(f"### {title}"))
                    hasil.append(clean_text_html(f"[{verse}] {text}"))
    return hasil

def getChapter(book, chapter):
    try:
        bookREQ = requests.get(f'https://api.ayt.co/v1/bible.php?book={book}&chapter={chapter}&source=realbread.streamlit.app')
        if bookREQ.status_code != 200:
            return []
        data = bookREQ.json()
        return cleanText(data)
    except:
        return []

def getPassage(book, chapter, passage):
    try:
        passage_str = ','.join(passage)
        bookREQ = requests.get(f'https://api.ayt.co/v1/passage.php?passage={book} {chapter}:{passage_str}&source=realbread.streamlit.app')
        if bookREQ.status_code != 200:
            return []
        data = bookREQ.json()
        return cleanText(data)
    except:
        return []
    
def getVerseCount(book, chapter):
    verses = getChapter(book, chapter)  # ambil data pasal lengkap
    count = 0
    for line in verses:
        # abaikan baris yang diawali '###' karena itu judul, bukan ayat
        if not line.strip().startswith("###"):
            count += 1
    return count


def ask_gemini(prompt):
    api_key = None
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except:
        pass

    if "MASUKKAN" in api_key or not api_key:
        return "Tolong masukkan API Key di funcs.py baris 6."

    genai.configure(api_key=api_key)

    models_to_try = [
        'gemini-2.5-flash'
    ]
    
    error_log = []

    # 3. Looping nyobain satu-satu
    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text 
        except Exception as e:
            error_log.append(f"{model_name}: Gagal")
            continue

    # Kalau sampai sini berarti SEMUA gagal
    return f"Maaf, semua model AI gagal diakses. Coba buat API Key baru. Log: {', '.join(error_log)}"

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