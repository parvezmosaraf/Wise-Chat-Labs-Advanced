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

st.set_page_config(page_title="Wise Chat Labs")

def display_messages():
    st.subheader("Chat with your PDF")
    for i, (msg, is_user) in enumerate(st.session_state["messages"]):
        message(msg, is_user=is_user, key=str(i))
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
    if 'messages' not in st.session_state:
        st.session_state['messages'] = []
    
    st.header("Wise Chat Labs - Your Ultimate Chatbot")
    display_messages()

    if 'OPENAI_API_KEY' not in st.session_state:
        st.session_state['OPENAI_API_KEY'] = os.getenv("OPENAI_API_KEY", "")
        if is_openai_api_key_set():
            st.session_state['pdfquery'] = PDFQuery(st.session_state["OPENAI_API_KEY"])
            load_and_ingest_document()
        else:
            st.session_state['pdfquery'] = None
            st.error("OpenAI API key is not set. Please check your .env file.")

    user_input = st.text_input("Type your message here...", key="user_input")
    if user_input:
        process_input(user_input)

    st.title("Or speak your message...")
    audio = audiorecorder("Start Talking", "Click to stop", key="audio_recorder")
    if audio is not None and hasattr(audio, 'export'):
        audio_file_path = "user_audio_input.wav"
        audio.export(audio_file_path, format="wav")
        user_text = transcribe_audio_to_text(audio_file_path)
        process_input(user_text)

if __name__ == "__main__":
    main()
