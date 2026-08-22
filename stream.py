import os
from datetime import datetime, timezone

import streamlit as st
from google import genai
from pymongo import MongoClient
from bson import ObjectId


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AI Chatbot",
    page_icon="🤖",
    layout="wide"
)


# ============================================================
# ENVIRONMENT VARIABLES
# ============================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")


# ============================================================
# CHECK ENVIRONMENT VARIABLES
# ============================================================

if not GEMINI_API_KEY:
    st.error("❌ GEMINI_API_KEY is not set.")
    st.stop()

if not MONGO_URI:
    st.error("❌ MONGO_URI is not set.")
    st.stop()


# ============================================================
# GEMINI CONNECTION
# ============================================================

try:

    gemini_client = genai.Client(
        api_key=GEMINI_API_KEY
    )

except Exception as e:

    st.error(f"❌ Gemini initialization failed: {e}")
    st.stop()


# ============================================================
# MONGODB CONNECTION
# ============================================================

try:

    mongo_client = MongoClient(
        MONGO_URI,
        serverSelectionTimeoutMS=10000,
        connectTimeoutMS=10000
    )

    # Test MongoDB connection
    mongo_client.admin.command("ping")

    db = mongo_client["chatbot"]

    # Collection for complete conversations
    chats_collection = db["chats"]

    mongo_connected = True

except Exception as e:

    mongo_connected = False
    mongo_error = str(e)


# ============================================================
# SESSION STATE
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat_id" not in st.session_state:
    st.session_state.chat_id = None


# ============================================================
# FUNCTIONS
# ============================================================

def create_new_chat():
    """
    Start a completely new chat.
    """

    st.session_state.messages = []
    st.session_state.chat_id = None


def load_chat(chat_id):
    """
    Load a previous chat from MongoDB.
    """

    try:

        chat = chats_collection.find_one(
            {"_id": ObjectId(chat_id)}
        )

        if chat:

            st.session_state.chat_id = chat_id

            st.session_state.messages = chat.get(
                "messages",
                []
            )

    except Exception as e:

        st.error(f"❌ Could not load chat: {e}")


def save_chat():

    if not mongo_connected:
        return

    if not st.session_state.messages:
        return

    try:

        now = datetime.now(timezone.utc)

        # Create title from first user message
        first_user_message = next(
            (
                message["content"]
                for message in st.session_state.messages
                if message["role"] == "user"
            ),
            "New Chat"
        )

        title = first_user_message[:40]

        # Existing chat
        if st.session_state.chat_id:

            chats_collection.update_one(
                {
                    "_id": ObjectId(
                        st.session_state.chat_id
                    )
                },
                {
                    "$set": {
                        "messages": st.session_state.messages,
                        "title": title,
                        "updated_at": now
                    }
                }
            )

        # New chat
        else:

            result = chats_collection.insert_one(
                {
                    "title": title,
                    "messages": st.session_state.messages,
                    "created_at": now,
                    "updated_at": now
                }
            )

            st.session_state.chat_id = str(
                result.inserted_id
            )

    except Exception as e:

        st.error(f"❌ Could not save chat: {e}")


def delete_all_chats():

    if not mongo_connected:
        return

    try:

        chats_collection.delete_many({})

        st.session_state.messages = []
        st.session_state.chat_id = None

    except Exception as e:

        st.error(f"❌ Could not clear chats: {e}")


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("⚙️ Settings")

    # MongoDB status
    if mongo_connected:

        st.success("🟢 MongoDB Connected")

    else:

        st.error("🔴 MongoDB Failed")

        with st.expander("MongoDB Error"):
            st.code(mongo_error)

    st.divider()

    # --------------------------------------------------------
    # NEW CHAT
    # --------------------------------------------------------

    if st.button(
        "🆕 New Chat",
        use_container_width=True
    ):

        create_new_chat()
        st.rerun()

    # --------------------------------------------------------
    # CLEAR ALL CHAT HISTORY
    # --------------------------------------------------------

    if st.button(
        "🗑️ Clear Chat History",
        use_container_width=True
    ):

        delete_all_chats()
        st.rerun()

    st.divider()

    # --------------------------------------------------------
    # CHAT HISTORY
    # --------------------------------------------------------

    st.subheader("💬 Chat History")

    if mongo_connected:

        chats = list(
            chats_collection.find(
                {},
                {
                    "title": 1,
                    "updated_at": 1
                }
            ).sort(
                "updated_at",
                -1
            )
        )

        if not chats:

            st.caption(
                "No previous chats"
            )

        else:

            for chat in chats:

                chat_id = str(
                    chat["_id"]
                )

                title = chat.get(
                    "title",
                    "New Chat"
                )

                # Limit title length
                if len(title) > 35:
                    title = title[:35] + "..."

                # Highlight current chat
                if chat_id == st.session_state.chat_id:

                    button_text = f"🟢 {title}"

                else:

                    button_text = f"💬 {title}"

                if st.button(
                    button_text,
                    key=f"chat_{chat_id}",
                    use_container_width=True
                ):

                    load_chat(chat_id)
                    st.rerun()


# ============================================================
# MAIN CHAT AREA
# ============================================================

st.title("🤖 AI Chatbot")

st.caption(
    "Google Gemini + Streamlit + MongoDB Atlas"
)


# ============================================================
# DISPLAY CHAT MESSAGES
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

prompt = st.chat_input(
    "Ask me anything..."
)


if prompt:

    # --------------------------------------------------------
    # USER MESSAGE
    # --------------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt
        }
    )

    with st.chat_message("user"):

        st.markdown(prompt)


    # --------------------------------------------------------
    # GEMINI RESPONSE
    # --------------------------------------------------------

    with st.chat_message("assistant"):

        with st.spinner("Thinking..."):

            try:

                # Create conversation text
                conversation = []

                for message in st.session_state.messages:

                    conversation.append(
                        f"{message['role']}: "
                        f"{message['content']}"
                    )

                conversation_text = "\n".join(
                    conversation
                )

                # Gemini
                response = gemini_client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=conversation_text
                )

                answer = response.text

                st.markdown(answer)

                # Save assistant message
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer
                    }
                )

                # Save entire conversation
                save_chat()

            except Exception as e:

                st.error(
                    f"❌ Gemini error: {e}"
                )