import streamlit as st
from dotenv import load_dotenv
import os
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled

# Load environment variables
load_dotenv()

# Configure Google Gemini AI
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Define the prompt for summarization
prompt = """You are a YouTube video summarizer. You will be taking the transcript text
and summarizing the entire video, providing key points within 250 words.
Please provide the summary of the text given here: """

# Function to extract transcript from a YouTube video
def extract_transcript_details(youtube_video_url):
    try:
        # Extract video ID from URL
        if "v=" in youtube_video_url:
            video_id = youtube_video_url.split("v=")[1].split("&")[0]
        elif "youtu.be/" in youtube_video_url:
            video_id = youtube_video_url.split("youtu.be/")[1].split("?")[0]
        else:
            return None, "Invalid YouTube URL format."

        # Fetch transcript
        transcript_text = YouTubeTranscriptApi.get_transcript(video_id)
        transcript = " ".join([i["text"] for i in transcript_text])

        return transcript, None

    except TranscriptsDisabled:
        return None, "Transcripts are disabled for this video."
    except Exception as e:
        return None, str(e)

# Function to generate summary using Google Gemini Pro
def generate_gemini_content(transcript_text, prompt):
    try:
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt + transcript_text)
        return response.text, None
    except Exception as e:
        return None, str(e)

# Streamlit App Interface
st.title("YouTube Transcript to Notes Converter")
youtube_link = st.text_input("Enter YouTube Video Link:")

if youtube_link:
    # Extract video ID and display thumbnail
    if "v=" in youtube_link:
        video_id = youtube_link.split("v=")[1].split("&")[0]
    elif "youtu.be/" in youtube_link:
        video_id = youtube_link.split("youtu.be/")[1].split("?")[0]
    else:
        video_id = None

    if video_id:
        st.image(f"http://img.youtube.com/vi/{video_id}/0.jpg", use_container_width=True)

# Button to get transcript and summary
if st.button("Get Detailed Notes"):
    if not youtube_link:
        st.error("Please enter a valid YouTube link.")
    else:
        transcript_text, transcript_error = extract_transcript_details(youtube_link)

        if transcript_error:
            st.error(f"Error fetching transcript: {transcript_error}")
        elif transcript_text:
            summary, summary_error = generate_gemini_content(transcript_text, prompt)
            
            if summary_error:
                st.error(f"Error generating summary: {summary_error}")
            else:
                st.markdown("## Detailed Notes:")
                st.write(summary)
