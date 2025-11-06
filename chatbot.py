import os
from dotenv import load_dotenv
import streamlit as st

# Try to import the OpenAI client; if unavailable we gracefully fall back
try:
    from openai import OpenAI
except Exception:
    OpenAI = None

# Load environment variables from .env file
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = None
if OPENAI_API_KEY and OpenAI is not None:
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
    except Exception:
        client = None

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
    """Generate a response either via OpenAI (if configured) or a local fallback."""
    if client is None:
        # simple fallback: echo + guidance
        return f"I heard: {user_text} (set OPENAI_API_KEY in .env to enable AI responses)"

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                *st.session_state.messages,
                {"role": "user", "content": user_text},
            ],
        )
        # Extract assistant content (coerce to str to avoid None typing)
        ai_message = response.choices[0].message.content or ""
        return str(ai_message)
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
        # show the user's message immediately
        try:
            st.chat_message("user").markdown(user_input)
        except Exception:
            st.markdown(f"**You:** {user_input}")

        # generate and display assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                ai_text = generate_ai_response(user_input)
                st.markdown(ai_text)
                st.session_state.messages.append({"role": "assistant", "content": ai_text})

        # clear the text_input widget (if present)
        if "text_input" in st.session_state:
            st.session_state["text_input"] = ""



