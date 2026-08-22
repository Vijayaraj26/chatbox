import streamlit as st
from google import genai
from pymongo import MongoClient
from datetime import datetime, timezone
import uuid


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Gemini AI Chatbot",
    page_icon="🤖",
    layout="wide"
)


# ============================================================
# GEMINI CONNECTION
# ============================================================

@st.cache_resource
def get_gemini_client():

    api_key = st.secrets["GEMINI_API_KEY"]

    client = genai.Client(
        api_key=api_key
    )

    return client


# ============================================================
# MONGODB CONNECTION
# ============================================================

@st.cache_resource
def get_mongodb():

    mongo_uri = st.secrets["MONGO_URI"]

    client = MongoClient(
        mongo_uri
    )

    # Test MongoDB connection
    client.admin.command("ping")

    database = client["ai_chatbot"]

    return database


# ============================================================
# CONNECT
# ============================================================

try:

    gemini_client = get_gemini_client()

    db = get_mongodb()

    messages_collection = db["messages"]

    connection_status = True

except Exception as e:

    connection_status = False

    st.error(
        f"Database/API connection error: {e}"
    )


# ============================================================
# SESSION STATE
# ============================================================

if "conversation_id" not in st.session_state:

    st.session_state.conversation_id = str(
        uuid.uuid4()
    )


if "messages" not in st.session_state:

    st.session_state.messages = []


# ============================================================
# SAVE MESSAGE TO MONGODB
# ============================================================

def save_message(
    conversation_id,
    role,
    message
):

    messages_collection.insert_one(
        {
            "conversation_id": conversation_id,
            "role": role,
            "message": message,
            "created_at": datetime.now(
                timezone.utc
            )
        }
    )


# ============================================================
# LOAD CHAT HISTORY
# ============================================================

def load_messages(
    conversation_id
):

    messages = []

    cursor = messages_collection.find(
        {
            "conversation_id": conversation_id
        }
    ).sort(
        "created_at",
        1
    )

    for document in cursor:

        messages.append(
            {
                "role": document["role"],
                "content": document["message"]
            }
        )

    return messages


# ============================================================
# GEMINI RESPONSE
# ============================================================

def ask_gemini(question):

    response = gemini_client.models.generate_content(

        model="gemini-2.5-flash",

        contents=question
    )

    return response.text


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("⚙️ Settings")

    st.write("### Database")

    if connection_status:

        st.success(
            "MongoDB Connected"
        )

    else:

        st.error(
            "MongoDB Not Connected"
        )

    st.divider()

    st.write("### Chat Statistics")

    st.write(
        f"Messages: {len(st.session_state.messages)}"
    )

    user_count = sum(
        1
        for message in st.session_state.messages
        if message["role"] == "user"
    )

    assistant_count = sum(
        1
        for message in st.session_state.messages
        if message["role"] == "assistant"
    )

    st.write(
        f"Your Questions: {user_count}"
    )

    st.write(
        f"AI Answers: {assistant_count}"
    )

    st.divider()

    # New chat
    if st.button(
        "➕ New Chat",
        use_container_width=True
    ):

        st.session_state.conversation_id = str(
            uuid.uuid4()
        )

        st.session_state.messages = []

        st.rerun()

    # Clear current chat
    if st.button(
        "🗑️ Clear Chat",
        use_container_width=True
    ):

        messages_collection.delete_many(
            {
                "conversation_id":
                st.session_state.conversation_id
            }
        )

        st.session_state.messages = []

        st.rerun()


# ============================================================
# MAIN PAGE
# ============================================================

st.title("🤖 Gemini AI Chatbot")

st.write(
    "Simple Streamlit chatbot with Gemini API and MongoDB."
)


# ============================================================
# LOAD EXISTING CHAT FROM DATABASE
# ============================================================

if len(st.session_state.messages) == 0:

    try:

        database_messages = load_messages(
            st.session_state.conversation_id
        )

        st.session_state.messages = database_messages

    except Exception as e:

        st.error(
            f"Could not load chat history: {e}"
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
# PROCESS USER MESSAGE
# ============================================================

if user_input:

    # --------------------------------------------------------
    # Display user message
    # --------------------------------------------------------

    with st.chat_message("user"):

        st.markdown(
            user_input
        )


    # --------------------------------------------------------
    # Add to session
    # --------------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_input
        }
    )


    # --------------------------------------------------------
    # Save user message to MongoDB
    # --------------------------------------------------------

    try:

        save_message(
            st.session_state.conversation_id,
            "user",
            user_input
        )

    except Exception as e:

        st.error(
            f"Could not save user message: {e}"
        )


    # --------------------------------------------------------
    # Ask Gemini
    # --------------------------------------------------------

    with st.chat_message("assistant"):

        with st.spinner(
            "Gemini is thinking..."
        ):

            try:

                answer = ask_gemini(
                    user_input
                )

                st.markdown(
                    answer
                )

            except Exception as e:

                answer = None

                st.error(
                    f"Gemini error: {e}"
                )


    # --------------------------------------------------------
    # Save Gemini response
    # --------------------------------------------------------

    if answer:

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer
            }
        )

        try:

            save_message(
                st.session_state.conversation_id,
                "assistant",
                answer
            )

        except Exception as e:

            st.error(
                f"Could not save AI response: {e}"
            )