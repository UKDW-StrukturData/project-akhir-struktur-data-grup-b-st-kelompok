import streamlit as st
from funcs import ask_gemini

def page_ai(): 
    st.title("Chat Bebas")
    
    if "chat" not in st.session_state:  # Ngecek chat tu ada station state ato ga, streamlit soalnya reset tiap input, pokok biar ngechat sama 
        st.session_state.chat = [] # akan buat list kosong, jamin data chat tetep ada di memori


    if st.session_state.get('pindah_dari_read'): # ngecek ada ga yang tanya di page read
        
        prompt_kiriman = st.session_state.get('paket_prompt')
        judul_user = st.session_state.get('paket_judul', "Analisis Ayat")
        
        # Kita pakai spinner, TAPI JANGAN pakai st.chat_message di sini.
        # Cukup spinner saja biar user tau sedang loading.
        with st.spinner(f"Sedang menganalisis topik: {judul_user}..."):
            jawaban = ask_gemini(prompt_kiriman)
        
        # 1. Simpan Pancingan User ke History
        st.session_state.chat.append({
            "role": "user", 
            "avatar": "user.png", 
            "content": judul_user
        })
        
        # 2. Simpan Jawaban AI ke History
        st.session_state.chat.append({
            "role": "assistant", 
            "avatar": "logo.png", 
            "content": jawaban
        })
        
        # 3. Bersihkan Status
        st.session_state['pindah_dari_read'] = False 
        st.session_state['paket_prompt'] = None 
        
        
        # Ini refresh layar, sehingga kode if ini dilewati,
        # dan langsung masuk ke looping di bawah. Hasilnya teks muncul 1x saja.
        st.rerun()
        
 
  
    # Looping ini yang bertugas menampilkan semua chat (termasuk yang barusan ditambah)
    for pesan in st.session_state.chat: 
        avatar_path = pesan.get("avatar") 
        st.chat_message(pesan["role"], avatar=avatar_path).write(pesan["content"])
    
  
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