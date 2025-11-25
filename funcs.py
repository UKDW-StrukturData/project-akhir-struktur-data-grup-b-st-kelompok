import re
import streamlit as st
import requests
import google.generativeai as genai

# lang_map = {
#     'English' : 'en',
#     'Indonesia' : 'id'
# }

# chapters = {
#     # Old Testament
#     "Genesis": 50,
#     "Exodus": 40,
#     "Leviticus": 27,
#     "Numbers": 36,
#     "Deuteronomy": 34,
#     "Joshua": 24,
#     "Judges": 21,
#     "Ruth": 4,
#     "1 Samuel": 31,
#     "2 Samuel": 24,
#     "1 Kings": 22,
#     "2 Kings": 25,
#     "1 Chronicles": 29,
#     "2 Chronicles": 36,
#     "Ezra": 10,
#     "Nehemiah": 13,
#     "Esther": 10,
#     "Job": 42,
#     "Psalms": 150,
#     "Proverbs": 31,
#     "Ecclesiastes": 12,
#     "Song of Solomon": 8,
#     "Isaiah": 66,
#     "Jeremiah": 52,
#     "Lamentations": 5,
#     "Ezekiel": 48,
#     "Daniel": 12,
#     "Hosea": 14,
#     "Joel": 3,
#     "Amos": 9,
#     "Obadiah": 1,
#     "Jonah": 4,
#     "Micah": 7,
#     "Nahum": 3,
#     "Habakkuk": 3,
#     "Zephaniah": 3,
#     "Haggai": 2,
#     "Zechariah": 14,
#     "Malachi": 4,

#     # New Testament
#     "Matthew": 28,
#     "Mark": 16,
#     "Luke": 24,
#     "John": 21,
#     "Acts": 28,
#     "Romans": 16,
#     "1 Corinthians": 16,
#     "2 Corinthians": 13,
#     "Galatians": 6,
#     "Ephesians": 6,
#     "Philippians": 4,
#     "Colossians": 4,
#     "1 Thessalonians": 5,
#     "2 Thessalonians": 3,
#     "1 Timothy": 6,
#     "2 Timothy": 4,
#     "Titus": 3,
#     "Philemon": 1,
#     "Hebrews": 13,
#     "James": 5,
#     "1 Peter": 5,
#     "2 Peter": 3,
#     "1 John": 5,
#     "2 John": 1,
#     "3 John": 1,
#     "Jude": 1,
#     "Revelation": 22
# }

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
                        hasil.append(f"### {title}")
                    hasil.append(f"[{verse}] {text}")
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

def ask_gemini(prompt):
    api_key = None
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except:
        pass
    
    if not api_key:
        api_key = API_KEY_DARURAT

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