import os
from dotenv import load_dotenv
import streamlit as st
import google.generativeai as genai

# Load environment variables from .env file
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize Gemini model if API key is available
gemini_model = None
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel('gemini-pro')
    except Exception as e:
        st.error(f"Failed to configure Gemini: {e}")

st.set_page_config(page_title="Chatbot with Streamlit", page_icon="🤖")
st.title("Your personal AI Chatbot")
st.write("Type a message below and press Enter (or use the Send button).")

if "messages" not in st.session_state:
    # messages is a list of dicts: {"role": "user"|"assistant", "content": str}
    st.session_state.messages = []

# Display existing messages
for msg in st.session_state.messages:
    role = msg.get("role", "assistant")
    content = msg.get("content", "")
    # use chat_message if available (Streamlit >= 1.18), otherwise fall back to write
    try:
        st.chat_message(role).markdown(content)
    except Exception:
        if role == "user":
            st.markdown(f"**You:** {content}")
        else:
            st.markdown(f"**Assistant:** {content}")


def generate_ai_response(user_text: str) -> str:
    """Generate a response using the Gemini API."""
    try:
        if not gemini_model:
            # If no AI model is available, provide guidance
            return (
                f"I heard: {user_text}. "
                "(Set GEMINI_API_KEY in .env to enable AI responses)"
            )

        # For Gemini, we need to adapt the history format from previous messages
        gemini_history = [
            {"role": "user" if msg["role"] == "user" else "model", "parts": [msg["content"]]}
            for msg in st.session_state.messages
        ]
        # Start a chat with the existing history
        chat = gemini_model.start_chat(history=gemini_history)
        # Send the new user message
        response = chat.send_message(user_text)
        return response.text or ""

    except Exception as e:
        return f"(Error generating response: {e})"


# Input area: use chat_input if available, otherwise a text_input + send button
input_col, button_col = st.columns([8, 1])
with input_col:
    try:
        user_input = st.chat_input("Type your message here...")
    except Exception:
        user_input = st.text_input("Type your message here...", key="text_input")
with button_col:
    send = st.button("Send")

# When the user submits text, append it and generate a response
if (user_input and user_input.strip()) or send:
    # If using text_input + send button, grab the text input value
    if not user_input:
        user_input = st.session_state.get("text_input", "").strip()

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        # generate and display assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                ai_text = generate_ai_response(user_input)
                st.markdown(ai_text)
                st.session_state.messages.append({"role": "assistant", "content": ai_text})

        # clear the text_input widget (if present)
        if "text_input" in st.session_state:
            st.session_state["text_input"] = ""
