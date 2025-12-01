import streamlit as st
from funcs import ask_gemini

def page_ai():
    st.title("Chat Bebas")
    

    if "chat" not in st.session_state: 
        st.session_state.chat = []
    

    for mulaichat in st.session_state.chat: 
        avatar_path = mulaichat.get("avatar") 
        
        st.chat_message(mulaichat["role"], avatar=avatar_path).write(mulaichat["content"])
    
    if userinput := st.chat_input("Tanya tentang Alkitab atau teologi..."):

        user_message = {"role":"user", "avatar":"orang.jpg", "content":userinput}
        st.session_state.chat.append(user_message)
        
        st.chat_message("user", avatar='orang.jpg').write(userinput)
        
        prompt_dgn_constraint = """Instruksi Utama:
1. Jawablah pertanyaan HANYA jika berkaitan dengan: Alkitab, Teologi, Sejarah Gereja, Kehidupan Rohani, Konseling Kristen, atau Etika Kristen dan yang berkaitan dengan agama lain.
2. Jika pengguna bertanya tentang hal di luar topik tersebut, tolaklah dengan sopan. Katakan bahwa kamu didesain khusus untuk membantu studi Alkitab.
3. Jawablah dengan nada yang pastoral, bijaksana, dan berdasarkan prinsip Alkitab.

Riwayat percakapan sejauh ini:
"""

        for message in st.session_state.chat[-10:]: # 
            if message["role"] == "user":
                role = "User"
            else:
                role = "Assistant"

            prompt_dgn_constraint += f"{role}: {message['content']}\n"

        prompt_dgn_constraint += f"User: {userinput}\nAssistant:"


        with st.chat_message("assistant", avatar='logo.png'):
            with st.spinner("Loading, tunggu sebentar"):
                jawaban = ask_gemini(prompt_dgn_constraint) 
                st.write(jawaban)
        
        assistant_message = {"role":"assistant", "avatar":"logo.png", "content":jawaban}
        st.session_state.chat.append(assistant_message)