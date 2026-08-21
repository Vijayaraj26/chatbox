import streamlit as st
import requests
import json

st.set_page_config(page_title="My Free AI Chatbot", page_icon="🤖")
st.title("🤖 My Free AI Chatbot")

# Get API key from secrets
try:
    api_key = st.secrets["OPENROUTER_API_KEY"]
except:
    st.error("❌ Please add OPENROUTER_API_KEY in Secrets!")
    st.stop()

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Show messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# User input
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
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "deepseek/deepseek-r1:free",
                        "messages": [
                            {"role": "user", "content": prompt}
                        ]
                    },
                    timeout=30
                )
                
                # Check if request was successful
                if response.status_code == 200:
                    result = response.json()
                    bot_reply = result["choices"][0]["message"]["content"]
                    st.write(bot_reply)
                    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
                else:
                    # Show error details
                    st.error(f"API Error: {response.status_code}")
                    st.write(response.text)
                    
            except requests.exceptions.Timeout:
                st.error("⏰ Request timed out. Please try again.")
            except requests.exceptions.ConnectionError:
                st.error("🔌 Connection error. Check your internet.")
            except KeyError as e:
                st.error(f"❌ Response error: {e}")
                st.write("Full response:", response.json() if 'response' in locals() else "No response")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")