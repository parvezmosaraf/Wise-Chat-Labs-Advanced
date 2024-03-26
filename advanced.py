import os
import io
import streamlit as st
from streamlit_chat import message
from dotenv import load_dotenv
from gtts import gTTS
from audiorecorder import audiorecorder
from pdfquery import PDFQuery
import whisper
import urllib.request
from urllib.request import urlopen
import ssl
import json

ssl._create_default_https_context = ssl._create_unverified_context

# Load environment variables from .env file
load_dotenv()

st.set_page_config(page_title="Wise Chat Labs", layout="wide")

# Theming
st.markdown(
    """
    <style>
    .stApp {
        background-color: #fafafa;
    }
    .chat-message {
        padding: 10px;
        border-radius: 10px;
    }
    .user-message {
        background-color: #e1f5fe;
    }
    .bot-message {
        background-color: #ede7f6;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

def display_messages():
    st.subheader("Chat with your PDF")
    for i, (msg, is_user) in enumerate(st.session_state["messages"]):
        message_style = "user-message" if is_user else "bot-message"
        st.markdown(
            f"<div class='chat-message {message_style}'>{msg}</div>",
            unsafe_allow_html=True,
        )
    st.session_state["thinking_spinner"] = st.empty()

def generate_tts_audio(text):
    tts = gTTS(text=text, lang='en')
    audio_bytes = io.BytesIO()
    tts.write_to_fp(audio_bytes)
    audio_bytes.seek(0)
    return audio_bytes

def play_audio(audio_bytes):
    audio_bytes.seek(0)
    st.audio(audio_bytes, format='audio/mp3', start_time=0)

def process_input(user_text):
    with st.session_state["thinking_spinner"], st.spinner("Thinking..."):
        query_text = st.session_state["pdfquery"].ask(user_text)
    
    audio_response = generate_tts_audio(query_text)
    play_audio(audio_response)
    
    st.session_state["messages"].append((user_text, True))
    st.session_state["messages"].append((query_text, False))

def load_and_ingest_document():
    file_path = 'osha.pdf'
    if os.path.exists(file_path):
        st.session_state["pdfquery"].ingest(file_path)
    else:
        st.error("PDF file not found. Please ensure 'osha.pdf' is in the root directory.")

def is_openai_api_key_set() -> bool:
    return len(st.session_state.get("OPENAI_API_KEY", "")) > 0

def transcribe_audio_to_text(audio_file_path):
    model = whisper.load_model("base")
    result = model.transcribe(audio_file_path)
    return result["text"]

def main():
    # Set the title of the app
    st.title("Wise Chat Labs - Your Ultimate Chatbot")

    # Initialize the session state for messages if it doesn't exist
    if 'messages' not in st.session_state:
        st.session_state['messages'] = []
    
    # Setup layout: Input on the left (1/3 width) and chat display on the right (2/3 width)
    col1, col2 = st.columns([1, 2])

    with col1:
        st.header("Controls")
        # Text input for user message
        user_input = st.text_input("Type your message here...", key="user_input", on_change=process_input, args=(st.session_state.get("user_input"),))
        
        # Title for voice input section
        st.title("Or speak your message...")

        # Audio recorder for voice input
        audio = audiorecorder("Click to record", "Click to stop recording", key="audio_recorder")
        if audio is not None and hasattr(audio, 'export'):
            # Saving the recorded audio and processing it
            audio_file_path = "user_audio_input.wav"
            audio.export(audio_file_path, format="wav")
            user_text = transcribe_audio_to_text(audio_file_path)
            process_input(user_text)

    with col2:
        st.header("Conversation")
        # Display chat messages
        display_messages()

    # Checks if OpenAI API key is set and initializes PDFQuery
    if 'OPENAI_API_KEY' not in st.session_state:
        st.session_state['OPENAI_API_KEY'] = os.getenv("OPENAI_API_KEY", "")
        if is_openai_api_key_set():
            st.session_state['pdfquery'] = PDFQuery(st.session_state["OPENAI_API_KEY"])
            load_and_ingest_document()
        else:
            st.session_state['pdfquery'] = None
            st.error("OpenAI API key is not set. Please check your .env file.")

def process_input(user_input):
    if user_input:  # Make sure user_input is not empty
        with st.session_state["thinking_spinner"], st.spinner("Thinking..."):
            query_text = st.session_state["pdfquery"].ask(user_input)

        audio_response = generate_tts_audio(query_text)
        play_audio(audio_response)

        # Append both the user's question and the bot's answer to the conversation
        st.session_state["messages"].append((user_input, True))  # True indicates user's message
        st.session_state["messages"].append((query_text, False))  # False indicates bot's response

# Remember to include the rest of your function definitions here as well...

if __name__ == "__main__":
    main()
