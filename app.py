import streamlit as st
from dotenv import load_dotenv
import os
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

prompt_template = """You are a YouTube video summarizer. You will take the transcript text
and summarize the entire video, providing the important points within 250 words.
Please provide the summary in the following language: {language}. Here is the transcript: """

# Function to extract available transcript languages
def get_available_languages(youtube_video_url):
    try:
        # Extract video ID
        if "v=" in youtube_video_url:
            video_id = youtube_video_url.split("v=")[1].split("&")[0]
        elif "youtu.be/" in youtube_video_url:
            video_id = youtube_video_url.split("youtu.be/")[1].split("?")[0]
        else:
            return None, "Invalid YouTube URL format."

        # Get available transcript languages
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        available_languages = {t.language_code: t.language for t in transcript_list}

        return video_id, available_languages, None
    except TranscriptsDisabled:
        return None, None, "Transcripts are disabled for this video."
    except Exception as e:
        return None, None, str(e)

# Function to fetch transcript in the selected language
def extract_transcript(youtube_video_url, selected_language):
    try:
        video_id, available_languages, error = get_available_languages(youtube_video_url)
        if error:
            return None, error

        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript_text = transcript_list.find_transcript([selected_language]).fetch()
        transcript = " ".join([i["text"] for i in transcript_text])

        return transcript, None
    except NoTranscriptFound:
        return None, f"No transcript available in the selected language: {selected_language}"
    except Exception as e:
        return None, str(e)

# Function to generate notes in the selected language
def generate_gemini_content(transcript_text, selected_language):
    try:
        model = genai.GenerativeModel("gemini-pro")
        prompt = prompt_template.format(language=selected_language) + transcript_text
        response = model.generate_content(prompt)
        return response.text, None
    except Exception as e:
        return None, str(e)

# Streamlit UI
st.title("YouTube Video Transcript to Detailed Notes Converter")
youtube_link = st.text_input("Enter YouTube Video Link:")

if youtube_link:
    video_id, available_languages, error = get_available_languages(youtube_link)
    
    if error:
        st.error(error)
    elif available_languages:
        st.image(f"http://img.youtube.com/vi/{video_id}/0.jpg", use_column_width=True)
        st.write("### Available Languages:")
        
        # Display available language options
        language_options = list(available_languages.keys())
        selected_language = st.selectbox("Select a language for detailed notes:", language_options, format_func=lambda x: available_languages[x])

        if st.button("Get Detailed Notes"):
            transcript_text, transcript_error = extract_transcript(youtube_link, selected_language)
            
            if transcript_error:
                st.error(transcript_error)
            else:
                summary, summary_error = generate_gemini_content(transcript_text, selected_language)
                if summary_error:
                    st.error(summary_error)
                else:
                    st.markdown("## Detailed Notes:")
                    st.write(summary)
