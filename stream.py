import streamlit as st
import requests

st.set_page_config(page_title="My Free AI Chatbot", page_icon="🤖")
st.title("🤖 My Free AI Chatbot")

# Get API key from Streamlit secrets
api_key = st.secrets["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"]

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Show past messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# User input box
if prompt := st.chat_input("Type your message here..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    
    # Get AI response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = requests.post(
                    url="https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                    },
                    json={
                        "model": "deepseek/deepseek-r1:free",  # Free AI model
                        "messages": [{"role": "user", "content": prompt}]
                    }
                )
                bot_reply = response.json()["choices"][0]["message"]["content"]
                st.write(bot_reply)
                st.session_state.messages.append({"role": "assistant", "content": bot_reply})
            except Exception as e:
                st.error(f"Error: {str(e)}")