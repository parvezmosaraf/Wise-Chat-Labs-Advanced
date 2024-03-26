import os
import streamlit as st
from streamlit_chat import message
from pdfquery import PDFQuery
from dotenv import load_dotenv
from gtts import gTTS
import io

# Load environment variables from .env file
load_dotenv()

st.set_page_config(page_title="Wise Chat Labs")

def display_messages():
    st.subheader("Chat with your pdf")
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
    audio_bytes.seek(0)  # Ensure the pointer is at the beginning of the IO stream
    st.audio(audio_bytes, format='audio/mp3', start_time=0)

def process_input():
    if st.session_state["user_input"] and len(st.session_state["user_input"].strip()) > 0:
        user_text = st.session_state["user_input"].strip()
        with st.session_state["thinking_spinner"], st.spinner("Thinking..."):
            query_text = st.session_state["pdfquery"].ask(user_text)
        
        audio_response = generate_tts_audio(query_text)
        play_audio(audio_response)
        
        st.session_state["messages"].append((user_text, True))
        st.session_state["messages"].append((query_text, False))

def load_and_ingest_document():
    file_path = 'osha.pdf'  # PDF file is assumed to be in the same directory as this script
    if os.path.exists(file_path):
        st.session_state["pdfquery"].ingest(file_path)
    else:
        st.error("PDF file not found. Please ensure 'data.pdf' is in the root directory.")

def is_openai_api_key_set() -> bool:
    return len(st.session_state["OPENAI_API_KEY"]) > 0

def main():
    if len(st.session_state) == 0:
        st.session_state["messages"] = []
        st.session_state["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")
        if is_openai_api_key_set():
            st.session_state["pdfquery"] = PDFQuery(st.session_state["OPENAI_API_KEY"])
            load_and_ingest_document()
        else:
            st.session_state["pdfquery"] = None

    st.header("Wise Chat Labs - Your Ultimate Chatbot")

    display_messages()
    st.text_input("Message", key="user_input", disabled=not is_openai_api_key_set(), on_change=process_input)

if __name__ == "__main__":
    main()
