import streamlit as st
from funcs import ask_gemini

def page_ai(): 
    st.title("Chat Bebas")
    
    if "chat" not in st.session_state: # Ngecek chat tu ada station state ato ga, streamlit soalnya reset tiap input, pokok biar ngechat sama 
        st.session_state.chat = [] # akan buat list kosong, jamin data chat tetep ada di memori


    if st.session_state.get('pindah_dari_read'): # ngecek ada ga yang tanya di page read
        
        
        st.session_state['pindah_dari_read'] = False #biar ga looping
        
        
        prompt_kiriman = st.session_state.get('paket_prompt')
        judul_user = st.session_state.get('paket_judul', "Analisis Ayat") # ngambil isinya
        
        
        st.session_state.chat.append({"role":"user", "avatar":"orang.jpg", "content": judul_user}) # untuk ngelanjutin tadi yang udah di get, content nya ngambil dari judul_user tadi
        
        
        with st.chat_message("user", avatar='orang.jpg'):
            st.write(judul_user) # proses ke AI nya 

        with st.chat_message("assistant", avatar='logo.png'):
            with st.spinner("Sedang menganalisis ayat kiriman..."):
                jawaban = ask_gemini(prompt_kiriman)
                st.write(jawaban) # analisis ayat dari page read ke page Ai
        
        
        st.session_state.chat.append({"role":"assistant", "avatar":"logo.png", "content":jawaban}) # nyimpen jawaban AI ke history
        
        st.session_state['paket_prompt'] = None # Hapus Paketnya
    
    for pesan in st.session_state.chat: 
        avatar_path = pesan.get("avatar") 
        st.chat_message(pesan["role"], avatar=avatar_path).write(pesan["content"])
    # looping ini biar ga ilang chat sebelumnya
 
    userinput = st.chat_input("Tanya tentang Alkitab atau teologi...")
    
    if userinput:
        user_message = {"role":"user", "avatar":"orang.jpg", "content":userinput} # saat user input jadi punya role, dan content nya apa 
        st.session_state.chat.append(user_message) # nanti bakal disimpan disini, user_massage masukin ke station state chat yang dimana tadi list kosong
        st.chat_message("user", avatar='orang.jpg').write(userinput) # ini untuk nampilin UI nya aja di stremalit
        
      
        prompt_dgn_constraint = """Instruksi Utama:
1. Jawablah pertanyaan HANYA jika berkaitan dengan: Alkitab, Teologi, Sejarah Gereja, Kehidupan Rohani.
2. Tolak topik lain dengan sopan.
3. Jawablah dengan nada pastoral.

Riwayat percakapan:
"""
       
        for message in st.session_state.chat[-10:]: # looping 10 kali History chat terakhir nya maks (10) di prompt biar ga kebanyakan aj
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
        

       