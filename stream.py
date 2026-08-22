import os
import uuid
from datetime import datetime, timezone

import streamlit as st
from google import genai
from pymongo import MongoClient


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Gemini AI Chatbot",
    page_icon="🤖",
    layout="wide"
)


# ============================================================
# GET ENVIRONMENT VARIABLES
# ============================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")


# ============================================================
# CHECK ENVIRONMENT VARIABLES
# ============================================================

if not GEMINI_API_KEY:
    st.error("❌ GEMINI_API_KEY is not configured in Render.")

    st.info(
        "Go to Render → Environment → Add GEMINI_API_KEY"
    )

    st.stop()


if not MONGO_URI:
    st.error("❌ MONGO_URI is not configured in Render.")

    st.info(
        "Go to Render → Environment → Add MONGO_URI"
    )

    st.stop()


# ============================================================
# GEMINI CONNECTION
# ============================================================

@st.cache_resource
def create_gemini_client():

    try:

        client = genai.Client(
            api_key=GEMINI_API_KEY
        )

        return client

    except Exception as e:

        st.error(
            f"Gemini connection failed: {e}"
        )

        return None


# ============================================================
# MONGODB CONNECTION
# ============================================================

@st.cache_resource
def create_mongodb_connection():

    try:

        client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=5000
        )

        # Test connection
        client.admin.command("ping")

        database = client["ai_chatbot"]

        messages = database["messages"]

        return client, database, messages

    except Exception as e:

        st.error(
            f"MongoDB connection failed: {e}"
        )

        return None, None, None


# ============================================================
# CREATE CONNECTIONS
# ============================================================

gemini_client = create_gemini_client()

mongo_client, db, messages_collection = (
    create_mongodb_connection()
)


# ============================================================
# CHECK CONNECTIONS
# ============================================================

if gemini_client is None:
    st.stop()


if messages_collection is None:
    st.stop()


# ============================================================
# SESSION STATE
# ============================================================

if "conversation_id" not in st.session_state:

    st.session_state.conversation_id = str(
        uuid.uuid4()
    )


if "messages" not in st.session_state:

    st.session_state.messages = []


if "loaded" not in st.session_state:

    st.session_state.loaded = False


# ============================================================
# SAVE MESSAGE
# ============================================================

def save_message(
    conversation_id,
    role,
    content
):

    try:

        messages_collection.insert_one(
            {
                "conversation_id": conversation_id,
                "role": role,
                "content": content,
                "created_at": datetime.now(
                    timezone.utc
                )
            }
        )

        return True

    except Exception as e:

        st.error(
            f"Could not save message: {e}"
        )

        return False


# ============================================================
# LOAD CHAT HISTORY
# ============================================================

def load_messages(
    conversation_id
):

    try:

        cursor = messages_collection.find(
            {
                "conversation_id": conversation_id
            }
        ).sort(
            "created_at",
            1
        )

        messages = []

        for document in cursor:

            messages.append(
                {
                    "role": document["role"],
                    "content": document["content"]
                }
            )

        return messages

    except Exception as e:

        st.error(
            f"Could not load chat history: {e}"
        )

        return []


# ============================================================
# DELETE CHAT
# ============================================================

def delete_chat(
    conversation_id
):

    try:

        messages_collection.delete_many(
            {
                "conversation_id": conversation_id
            }
        )

        return True

    except Exception as e:

        st.error(
            f"Could not delete chat: {e}"
        )

        return False


# ============================================================
# ASK GEMINI
# ============================================================

def ask_gemini(
    question
):

    try:

        response = gemini_client.models.generate_content(

            model="gemini-2.5-flash",

            contents=question
        )

        if response.text:

            return response.text

        return "Gemini returned an empty response."

    except Exception as e:

        return f"ERROR: {e}"


# ============================================================
# LOAD DATABASE CHAT HISTORY
# ============================================================

if not st.session_state.loaded:

    st.session_state.messages = load_messages(
        st.session_state.conversation_id
    )

    st.session_state.loaded = True


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("⚙️ Chat Settings")

    st.divider()

    # --------------------------------------------------------
    # DATABASE STATUS
    # --------------------------------------------------------

    st.subheader("Database")

    st.success("🟢 MongoDB Connected")


    # --------------------------------------------------------
    # GEMINI STATUS
    # --------------------------------------------------------

    st.subheader("AI Model")

    st.success("🟢 Gemini Connected")


    st.divider()


    # --------------------------------------------------------
    # STATISTICS
    # --------------------------------------------------------

    st.subheader("📊 Chat Statistics")

    total_messages = len(
        st.session_state.messages
    )

    user_messages = sum(
        1
        for message in st.session_state.messages
        if message["role"] == "user"
    )

    ai_messages = sum(
        1
        for message in st.session_state.messages
        if message["role"] == "assistant"
    )

    st.write(
        f"Total messages: **{total_messages}**"
    )

    st.write(
        f"Your questions: **{user_messages}**"
    )

    st.write(
        f"AI answers: **{ai_messages}**"
    )


    st.divider()


    # --------------------------------------------------------
    # NEW CHAT
    # --------------------------------------------------------

    if st.button(
        "➕ New Chat",
        use_container_width=True
    ):

        st.session_state.conversation_id = str(
            uuid.uuid4()
        )

        st.session_state.messages = []

        st.session_state.loaded = True

        st.rerun()


    # --------------------------------------------------------
    # CLEAR CHAT
    # --------------------------------------------------------

    if st.button(
        "🗑️ Clear Current Chat",
        use_container_width=True
    ):

        delete_chat(
            st.session_state.conversation_id
        )

        st.session_state.messages = []

        st.rerun()


# ============================================================
# MAIN PAGE
# ============================================================

st.title("🤖 Gemini AI Chatbot")

st.caption(
    "Streamlit + Gemini API + MongoDB Atlas + Render"
)


# ============================================================
# DISPLAY CHAT HISTORY
# ============================================================

for message in st.session_state.messages:

    with st.chat_message(
        message["role"]
    ):

        st.markdown(
            message["content"]
        )


# ============================================================
# CHAT INPUT
# ============================================================

user_input = st.chat_input(
    "Ask Gemini something..."
)


# ============================================================
# PROCESS USER QUESTION
# ============================================================

if user_input:

    # --------------------------------------------------------
    # DISPLAY USER MESSAGE
    # --------------------------------------------------------

    with st.chat_message("user"):

        st.markdown(
            user_input
        )


    # --------------------------------------------------------
    # ADD USER MESSAGE TO SESSION
    # --------------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_input
        }
    )


    # --------------------------------------------------------
    # SAVE USER MESSAGE TO MONGODB
    # --------------------------------------------------------

    save_message(
        st.session_state.conversation_id,
        "user",
        user_input
    )


    # --------------------------------------------------------
    # ASK GEMINI
    # --------------------------------------------------------

    with st.chat_message("assistant"):

        with st.spinner(
            "Gemini is thinking..."
        ):

            answer = ask_gemini(
                user_input
            )


        # ----------------------------------------------------
        # CHECK GEMINI ERROR
        # ----------------------------------------------------

        if answer.startswith("ERROR:"):

            st.error(
                answer
            )

        else:

            st.markdown(
                answer
            )


    # --------------------------------------------------------
    # SAVE AI RESPONSE
    # --------------------------------------------------------

    if not answer.startswith("ERROR:"):

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer
            }
        )

        save_message(
            st.session_state.conversation_id,
            "assistant",
            answer
        )
