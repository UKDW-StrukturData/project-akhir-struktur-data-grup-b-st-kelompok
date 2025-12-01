import streamlit as st
from funcs import ask_gemini

def page_ai(): 
    st.title("Chat Bebas")
    
    if "chat" not in st.session_state: # Ngecek chat tu ada station state ato ga, streamlit soalnya reset tiap input, pokok biar ngechat sama 
        st.session_state.chat = [] # akan buat list kosong, jamin data chat tetep ada di memori
    

    for mulaichat in st.session_state.chat: 
        avatar_path = mulaichat.get("avatar") 
        
        st.chat_message(mulaichat["role"], avatar=avatar_path).write(mulaichat["content"])
    
    if userinput := st.chat_input("Tanya tentang Alkitab atau teologi..."):

        user_message = {"role":"user", "avatar":"orang.jpg", "content":userinput}
        st.session_state.chat.append(user_message)
        
        st.chat_message("user", avatar='orang.jpg').write(userinput) # variabel ini yang ditampilkan di streamlitnya (UI)
        
        prompt_dgn_constraint = """Instruksi Utama:
1. Jawablah pertanyaan HANYA jika berkaitan dengan: Alkitab, Teologi, Sejarah Gereja, Kehidupan Rohani, Konseling Kristen, atau Etika Kristen dan yang berkaitan dengan agama lain.
2. Jika pengguna bertanya tentang hal di luar topik tersebut, tolaklah dengan sopan. Katakan bahwa kamu didesain khusus untuk membantu studi Alkitab.
3. Jawablah dengan nada yang pastoral, bijaksana, dan berdasarkan prinsip Alkitab.

Riwayat percakapan sejauh ini:
"""

        for message in st.session_state.chat[-10:]: # looping 10 kali History chat terakhir nya maks (10) di prompt
            if message["role"] == "user": 
                role = "User"
            else:
                role = "Assistant"
                # di atas ini buat nyamain format aja dengan prompt

            prompt_dgn_constraint += f"{role}: {message['content']}\n" # buat AI bisa menjawab berkaitan dengan pertanyaan sebelumnya

        prompt_dgn_constraint += f"User: {userinput}\nAssistant:" # biar si Assistant / AI nya tau bisa jawabnya kapan 


        with st.chat_message("assistant", avatar='logo.png'): # buat bubble baru untuk AI nya
            with st.spinner("Loading, tunggu sebentar"):
                jawaban = ask_gemini(prompt_dgn_constraint) 
                st.write(jawaban) # Nampilin Jawaban AInya 
                
        assistant_message = {"role":"assistant", "avatar":"logo.png", "content":jawaban}
        st.session_state.chat.append(assistant_message) # sama kayak user massage tadi
        