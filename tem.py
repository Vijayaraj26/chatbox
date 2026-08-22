import streamlit as st

st.title("Package Test")

try:
    import google.genai

    st.success("google-genai is installed")

    from google import genai

    st.success("Gemini import works!")

except Exception as e:
    st.error(f"Gemini import failed: {type(e).__name__}: {e}")
