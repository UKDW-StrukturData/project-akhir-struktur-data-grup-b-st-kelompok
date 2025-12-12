import streamlit as st
import pandas as pd
import requests
import google.generativeai as genai
from bs4 import BeautifulSoup
from functools import lru_cache
import datetime
import time
import hashlib
import io
import textwrap
import matplotlib.pyplot as plt
from streamlit_gsheets import GSheetsConnection

# --- PERUBAHAN DISINI ---
# Jangan pakai try-except. Kita paksa import biar sistem tahu ini WAJIB.
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
# ------------------------

# -----------------------
# LIST KITAB & CHAPTERS
# -----------------------
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

# -----------------------
# UTIL: HTML CLEANER
# -----------------------
def clean_text_html(text):
    """Bersihkan tag HTML dari string."""
    soup = BeautifulSoup(text or "", "html.parser")
    return soup.get_text(separator="\n")

def cleanText(data):
    """Transform JSON api -> list of lines (judul dan ayat)."""
    hasil = []
    if isinstance(data, list):
        items = data
    else:
        items = [data]
    for item in items:
        if not item:
            continue
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

# -----------------------
# API CALLS (cached)
# -----------------------
API_BASE = "https://api.ayt.co/v1"

@lru_cache(maxsize=512)
def getChapter(book, chapter):
    """
    Ambil full chapter dari API.
    Cached (LRU) sehingga pemanggilan berulang O(1) amortized.
    """
    try:
        url = f"{API_BASE}/bible.php?book={requests.utils.quote(book)}&chapter={chapter}&source=realbread.streamlit.app"
        res = requests.get(url, timeout=8)
        if res.status_code != 200:
            return []
        data = res.json()
        return cleanText(data)
    except Exception:
        return []

def getPassage(book, chapter, passage):
    """
    Jika passage is None -> ambil full pasal via getChapter (cached).
    Jika passage is list -> ambil ayat tertentu via endpoint passage.php.
    """
    try:
        if passage is None or passage == []:
            return getChapter(book, chapter)
        # passage is list of verse numbers or strings
        passage_str = ",".join([str(x) for x in passage])
        url = f"{API_BASE}/passage.php?passage={requests.utils.quote(f'{book} {chapter}:{passage_str}')}&source=realbread.streamlit.app"
        res = requests.get(url, timeout=8)
        if res.status_code != 200:
            return []
        data = res.json()
        return cleanText(data)
    except Exception:
        return []

def getVerseCount(book, chapter):
    verses = getChapter(book, chapter)
    count = 0
    for line in verses:
        if not line.strip().startswith("###"):
            count += 1
    return count

# -----------------------
# ASK GEMINI (AI)
# -----------------------
def ask_gemini(prompt):
    api_key = None
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        api_key = None

    if not api_key or "MASUKKAN" in str(api_key):
        return "Tolong masukkan API Key di secret GEMINI_API_KEY."

    genai.configure(api_key=api_key)

    models_to_try = [
        "gemini-2.5-flash"
    ]

    error_log = []
    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            error_log.append(f"{model_name}: {e}")
            continue

    return f"Maaf, semua model AI gagal diakses. Log: {', '.join(error_log)}"

# ============================
#  GET NEIGHBOR (O(1), safe)
# ============================
def getNeighborRef(book, chapter, offset):
    """
    Mengembalikan (book, chapter) baru berdasarkan offset (bisa lebih dari 1).
    Jika melewati batas akhir/awal, kembalikan ujung yang valid.
    """
    books = list(kitab.keys())
    try:
        idx = books.index(book)
    except ValueError:
        # fallback kalau book tidak valid
        return book, chapter

    new_ch = chapter + offset
    new_book = book

    # quick path: still inside same book
    if 1 <= new_ch <= kitab[book]:
        return new_book, new_ch

    if offset > 0:
        # move forward across books
        while True:
            # remaining chapters in current book
            remaining = kitab[new_book] - chapter
            if new_ch <= kitab[new_book]:
                return new_book, new_ch
            # compute across books by moving index forward
            idx += 1
            if idx >= len(books):
                # at very end: return last book last chapter
                last_book = books[-1]
                return last_book, kitab[last_book]
            # subtract chapters of current book and continue
            new_ch -= kitab[new_book]
            new_book = books[idx]
            # loop until new_ch fits into new_book

    if offset < 0:
        # move backward across books
        while True:
            if new_ch >= 1:
                return new_book, new_ch
            idx -= 1
            if idx < 0:
                # at very beginning
                first_book = books[0]
                return first_book, 1
            new_book = books[idx]
            new_ch += kitab[new_book]

    return book, chapter

# =======================
#  LINKED LIST CACHE
# =======================
class CacheNode:
    def __init__(self, book, chapter, verses, ref):
        self.book = book
        self.chapter = chapter
        self.verses = verses
        self.ref = ref
        self.prev = None
        self.next = None

def createNode(book, chapter):
    """Buat node untuk full chapter (pakai getChapter yang cached)."""
    verses = getChapter(book, chapter)
    ref = f"{book} {chapter}"
    return CacheNode(book, chapter, verses, ref)

def safeCreateNode(ref_tuple):
    """Helper: jika ref_tuple None atau invalid -> return None"""
    if not ref_tuple:
        return None
    b, c = ref_tuple
    if b is None or c is None:
        return None
    return createNode(b, c)

def initCache(book, chapter):
    """
    Inisialisasi window 5-node:
    prev2 <-> prev1 <-> curr <-> next1 <-> next2
    Node yang tidak ada (edge) diset None.
    Return pointer ke node current (middle).
    """
    # middle
    curr = createNode(book, chapter)

    # prev1, prev2
    p1_ref = getNeighborRef(book, chapter, -1)
    p2_ref = getNeighborRef(book, chapter, -2)
    prev1 = safeCreateNode(p1_ref)
    prev2 = safeCreateNode(p2_ref)

    # next1, next2
    n1_ref = getNeighborRef(book, chapter, 1)
    n2_ref = getNeighborRef(book, chapter, 2)
    next1 = safeCreateNode(n1_ref)
    next2 = safeCreateNode(n2_ref)

    # link them carefully (check for None)
    if prev2 and prev1:
        prev2.next = prev1
        prev1.prev = prev2

    if prev1:
        prev1.next = curr
        curr.prev = prev1

    if next1:
        curr.next = next1
        next1.prev = curr

    if next1 and next2:
        next1.next = next2
        next2.prev = next1

    return curr

def shiftCache(currentNode, direction):
    """
    Geser window 1 langkah.
    direction: "next" atau "prev"
    Return: (newCurrentNode, success)
    """
    if not currentNode:
        return None, False

    if direction == "next":
        # can't move if there's no next (we're at very end)
        if not currentNode.next:
            return currentNode, False

        newCurr = currentNode.next

        # ensure right side has two nodes (newCurr.next and newCurr.next.next)
        if not newCurr.next:
            # create one to the right if possible
            nb2 = getNeighborRef(newCurr.book, newCurr.chapter, 1)
            right = safeCreateNode(nb2)
            if right:
                newCurr.next = right
                right.prev = newCurr

        # Optionally we can drop far-left node to keep memory small:
        # find leftmost from newCurr and prune if >3 nodes on left side.
        # (Not strictly necessary; python GC handles unreferenced nodes.)
        return newCurr, True

    elif direction == "prev":
        if not currentNode.prev:
            return currentNode, False

        newCurr = currentNode.prev

        if not newCurr.prev:
            pb2 = getNeighborRef(newCurr.book, newCurr.chapter, -1)
            left = safeCreateNode(pb2)
            if left:
                newCurr.prev = left
                left.next = newCurr

        return newCurr, True

    return currentNode, False