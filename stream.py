import streamlit as st
import requests

st.set_page_config(page_title="Free Chatbot", page_icon="🤖")
st.title("🤖 Free Chatbot (No API Key)")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if prompt := st.chat_input("Type your message..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = requests.post(
                    "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium",
                    json={"inputs": prompt}
                )
                if response.status_code == 200:
                    bot_reply = response.json().get("generated_text", "Hello!")
                    st.write(bot_reply)
                    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
                else:
                    st.write("Try again!")
            except:
                st.write("Error connecting!")