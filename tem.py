import streamlit as st
from google import genai

st.title("Gemini Test")

try:
    client = genai.Client(
        api_key=st.secrets["GEMINI_API_KEY"]
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="Say hello in one sentence."
    )

    st.success("Gemini connection works!")
    st.write(response.text)

except Exception as e:
    st.error(f"Error: {e}")