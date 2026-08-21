import os
import requests
import streamlit as st


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AI Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CONFIGURATION
# ============================================================

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

MODELS = {
    "Gemini 2.5 Flash": "google/gemini-2.5-flash",
    "Llama 3.3 70B": "meta-llama/llama-3.3-70b-instruct",
    "Phi-4": "microsoft/phi-4",
}

SYSTEM_PROMPT = """
You are a helpful, friendly, and accurate AI assistant.

Give clear answers that are easy to understand.
If you are unsure about something, say so instead of making up information.
Use markdown when it improves readability.
"""


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>
        .main-title {
            font-size: 2.3rem;
            font-weight: 700;
            margin-bottom: 0.2rem;
        }

        .subtitle {
            color: #777;
            margin-bottom: 1.5rem;
        }

        .model-info {
            padding: 10px;
            border-radius: 8px;
            background-color: rgba(128, 128, 128, 0.1);
            margin-bottom: 15px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SESSION STATE
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "total_requests" not in st.session_state:
    st.session_state.total_requests = 0

if "selected_model" not in st.session_state:
    st.session_state.selected_model = "Gemini 2.5 Flash"


# ============================================================
# API KEY
# ============================================================

def get_api_key():
    """
    Get OpenRouter API key.

    Priority:
    1. Streamlit secrets
    2. Environment variable
    """

    # Streamlit Cloud / .streamlit/secrets.toml
    try:
        if "OPENROUTER_API_KEY" in st.secrets:
            return st.secrets["OPENROUTER_API_KEY"]
    except Exception:
        pass

    # Environment variable
    api_key = os.getenv("OPENROUTER_API_KEY")

    return api_key


# ============================================================
# OPENROUTER API CALL
# ============================================================

def get_ai_response(messages, model_name, api_key):
    """
    Send chat history to OpenRouter and return AI response.
    """

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://streamlit.io",
        "X-Title": "Simple AI Chatbot",
    }

    # Add system message before conversation history
    api_messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        }
    ]

    # Send recent conversation history
    api_messages.extend(messages[-20:])

    payload = {
        "model": model_name,
        "messages": api_messages,
        "temperature": 0.7,
        "max_tokens": 1000,
    }

    try:
        response = requests.post(
            OPENROUTER_URL,
            headers=headers,
            json=payload,
            timeout=60,
        )

        # Handle HTTP errors
        if response.status_code != 200:

            try:
                error_data = response.json()
                error_message = error_data.get("error", {}).get(
                    "message",
                    "Unknown API error"
                )
            except Exception:
                error_message = response.text

            return None, (
                f"OpenRouter API error "
                f"({response.status_code}): {error_message}"
            )

        data = response.json()

        # Validate response
        if "choices" not in data or not data["choices"]:
            return None, "The API returned an empty response."

        message = data["choices"][0].get("message", {})
        content = message.get("content")

        if not content:
            return None, "The AI returned an empty message."

        return content, None

    except requests.exceptions.Timeout:
        return None, (
            "The request timed out. "
            "Please try again."
        )

    except requests.exceptions.ConnectionError:
        return None, (
            "Could not connect to OpenRouter. "
            "Please check your internet connection."
        )

    except requests.exceptions.RequestException as e:
        return None, f"Network error: {str(e)}"

    except Exception as e:
        return None, f"Unexpected error: {str(e)}"


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("⚙️ Settings")

    selected_model = st.selectbox(
        "Choose AI Model",
        options=list(MODELS.keys()),
        index=list(MODELS.keys()).index(
            st.session_state.selected_model
        ),
    )

    st.session_state.selected_model = selected_model

    model_id = MODELS[selected_model]

    st.markdown(
        f"""
        <div class="model-info">
            <b>Selected Model</b><br>
            {selected_model}<br><br>
            <small>{model_id}</small>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    st.subheader("📊 Chat Statistics")

    total_messages = len(st.session_state.messages)
    user_messages = sum(
        1
        for message in st.session_state.messages
        if message["role"] == "user"
    )
    assistant_messages = sum(
        1
        for message in st.session_state.messages
        if message["role"] == "assistant"
    )

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Messages", total_messages)

    with col2:
        st.metric("Requests", st.session_state.total_requests)

    st.metric("Your Questions", user_messages)
    st.metric("AI Answers", assistant_messages)

    st.divider()

    if st.button(
        "🗑️ Clear Chat",
        use_container_width=True,
    ):
        st.session_state.messages = []
        st.session_state.total_requests = 0
        st.rerun()

    st.divider()

    st.caption(
        "Powered by Streamlit + OpenRouter"
    )


# ============================================================
# MAIN UI
# ============================================================

st.markdown(
    '<div class="main-title">🤖 AI Chatbot</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    "Chat with Gemini, Llama, or Phi using OpenRouter."
    "</div>",
    unsafe_allow_html=True,
)


# ============================================================
# API KEY CHECK
# ============================================================

api_key = get_api_key()

if not api_key:

    st.warning(
        "⚠️ OpenRouter API key is not configured."
    )

    st.info(
        """
        ### How to configure the API key

        **For Streamlit Cloud:**

        Add this to your app's Secrets:

        ```toml
        OPENROUTER_API_KEY = "your-api-key-here"
        ```

        **For local testing:**

        Create:

        `.streamlit/secrets.toml`

        and add:

        ```toml
        OPENROUTER_API_KEY = "your-api-key-here"
        ```
        """
    )

    st.stop()


# ============================================================
# DISPLAY CHAT HISTORY
# ============================================================

for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# ============================================================
# CHAT INPUT
# ============================================================

user_input = st.chat_input(
    "Type your message here..."
)


if user_input:

    # --------------------------------------------------------
    # Add user message
    # --------------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_input,
        }
    )

    with st.chat_message("user"):
        st.markdown(user_input)

    # --------------------------------------------------------
    # Generate AI response
    # --------------------------------------------------------

    with st.chat_message("assistant"):

        with st.spinner(
            f"{selected_model} is thinking..."
        ):

            response, error = get_ai_response(
                st.session_state.messages,
                model_id,
                api_key,
            )

        # ----------------------------------------------------
        # Handle error
        # ----------------------------------------------------

        if error:

            st.error(error)

            # Remove user message if request failed
            st.session_state.messages.pop()

        else:

            st.markdown(response)

            # Save assistant response
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": response,
                }
            )

            st.session_state.total_requests += 1