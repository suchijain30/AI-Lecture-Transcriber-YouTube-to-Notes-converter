import streamlit as st
import os
import yt_dlp
import whisper
import google.generativeai as genai
from googletrans import Translator
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

translator = Translator()

prompt_template = """You are a YouTube video summarizer. You will take the transcript text
and summarize the entire video, providing the important points within 250 words.
Please provide the summary in the following language: {language}. Here is the transcript: """

# Function to extract available transcript languages
def get_available_transcript(youtube_video_url):
    try:
        if "v=" in youtube_video_url:
            video_id = youtube_video_url.split("v=")[1].split("&")[0]
        elif "youtu.be/" in youtube_video_url:
            video_id = youtube_video_url.split("youtu.be/")[1].split("?")[0]
        else:
            return None, None, "Invalid YouTube URL format."

        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        # Fetch transcript from the first available language
        for transcript in transcript_list:
            transcript_text = transcript.fetch()
            transcript_language = transcript.language
            transcript_code = transcript.language_code
            transcript_content = " ".join([i["text"] for i in transcript_text])
            return transcript_content, transcript_language, transcript_code, None

        return None, None, None, "No transcript found."
    except TranscriptsDisabled:
        return None, None, None, "Transcripts are disabled for this video."
    except Exception as e:
        return None, None, None, str(e)

# Function to download audio if transcript is missing
def download_audio(youtube_url):
    try:
        ydl_opts = {
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192"
            }],
            "outtmpl": "downloaded_audio.mp3"
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])

        return "downloaded_audio.mp3", None
    except Exception as e:
        return None, f"Error downloading audio: {str(e)}"

# Function to transcribe audio using Whisper
def transcribe_audio(audio_path):
    try:
        model = whisper.load_model("base")  # Load Whisper model (base version)
        result = model.transcribe(audio_path)
        return result["text"], None
    except Exception as e:
        return None, f"Error transcribing audio: {str(e)}"

# Function to generate detailed notes using Gemini
def generate_gemini_content(transcript_text, transcript_language):
    try:
        model = genai.GenerativeModel("gemini-pro")
        prompt = prompt_template.format(language=transcript_language) + transcript_text
        response = model.generate_content(prompt)
        return response.text, None
    except Exception as e:
        return None, str(e)

# Function to translate text
def translate_text(text, target_language):
    try:
        translated_text = translator.translate(text, dest=target_language).text
        return translated_text, None
    except Exception as e:
        return None, str(e)

# Streamlit UI
st.title("YouTube Video Transcript & Notes Generator")
youtube_link = st.text_input("Enter YouTube Video Link:")

if youtube_link:
    transcript_text, transcript_language, transcript_code, error = get_available_transcript(youtube_link)

    if error:
        st.warning("No transcript found. Extracting from audio...")

        # Download & Transcribe Audio
        audio_file, audio_error = download_audio(youtube_link)
        if audio_error:
            st.error(audio_error)
        else:
            transcript_text, transcribe_error = transcribe_audio(audio_file)
            if transcribe_error:
                st.error(transcribe_error)
            else:
                transcript_language = "auto-detected"
                transcript_code = "auto"
                st.success("Audio transcription successful!")

    if transcript_text:
        # Generate notes in transcript's language
        summary, summary_error = generate_gemini_content(transcript_text, transcript_language)
        if summary_error:
            st.error(summary_error)
        else:
            st.markdown(f"## Detailed Notes in {transcript_language}:")
            st.write(summary)

            # Allow user to select a different language for the summary
            st.write("### Choose a language to translate the notes:")
            language_options = {
                "en": "English",
                "hi": "Hindi",
                "fr": "French",
                "es": "Spanish",
                "de": "German",
                "zh-cn": "Chinese",
                "ar": "Arabic",
                "ru": "Russian"
            }
            selected_language = st.selectbox("Select language:", list(language_options.keys()), format_func=lambda x: language_options[x])

            if st.button("Translate Notes"):
                translated_summary, translate_error = translate_text(summary, selected_language)
                if translate_error:
                    st.error(translate_error)
                else:
                    st.markdown(f"## Translated Notes in {language_options[selected_language]}:")
                    st.write(translated_summary)
