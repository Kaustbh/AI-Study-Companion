import io
import os
import sqlite3
import tempfile

import streamlit as st
import matplotlib.pyplot as plt
import google.generativeai as genai
from fpdf import FPDF
from dotenv import load_dotenv
from wordcloud import WordCloud

from youtube_transcript import extract_transcript

load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


def fetch_transcript(video_id):
    conn = sqlite3.connect('youtube_transcripts.db')
    c = conn.cursor()
    c.execute("SELECT transcript FROM transcripts WHERE video_id = ?", (video_id,))
    transcript_text = c.fetchone()[0]
    conn.close()
    return transcript_text


def generate_notes(transcript_text, subject, custom_prompt=None):
    if custom_prompt:
        prompt = custom_prompt
    else:
        if subject == "Physics":
            prompt = """
                Title: Detailed Physics Notes from YouTube Video Transcript
                [Physics-related detailed prompt goes here]
            """
        elif subject == "Chemistry":
            prompt = """
                Title: Detailed Chemistry Notes from YouTube Video Transcript
                [Chemistry-related detailed prompt goes here]
            """
        elif subject == "Biology":
            prompt = """
                Title: Detailed Biology Notes from YouTube Video Transcript
                [Biology-related detailed prompt goes here]
            """
        elif subject == "Economics":
            prompt = """
                Title: Detailed Economics Notes from YouTube Video Transcript
                [Economics-related detailed prompt goes here]
            """
        elif subject == "Data Science and Statistics":
            prompt = """
                Title: Comprehensive Notes on Data Science and Statistics from YouTube Video Transcript
                [Data Science-related detailed prompt goes here]
            """

    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(prompt + transcript_text)
    return response.text


def summarize_text(text):
    summary_prompt = """
        Summarize the following content briefly:
    """
    model = genai.GenerativeModel('gemini-1.5-flash')
    summary_response = model.generate_content(summary_prompt + text)
    return summary_response.text


def create_wordcloud(text):
    wordcloud = WordCloud(width=800, height=400, background_color="white").generate(
        text
    )
    fig, ax = plt.subplots()
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis("off")
    return fig


def download_text(text, file_name):
    buffer = io.StringIO(text)
    st.download_button(
        label="Download Notes as Text File",
        data=buffer.getvalue(),
        file_name=file_name,
        mime="text/plain",
    )


def download_pdf(text, file_name):
    # Create PDF
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Add text to PDF, splitting by lines to ensure correct formatting
    for line in text.split('\n'):
        pdf.multi_cell(0, 10, line)

    # Save the PDF to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        pdf.output(tmp_file.name)
        pdf_output = io.BytesIO(tmp_file.read())
        tmp_file.close()  # Close the file so it can be deleted

    # Streamlit download button for PDF
    st.download_button(
        label=f"Download {file_name}",
        data=pdf_output,
        file_name=file_name,
        mime="application/pdf",
    )

    # Delete the temporary file
    os.remove(tmp_file.name)


def main():
    st.title("YouTube Transcript to Detailed Notes Converter")

    subjects = [
        "Physics",
        "Chemistry",
        "Mathematics",
        "Data Science and Statistics",
        "Biology",
        "Economics",
        "Custom Prompt",
    ]
    subject = st.selectbox("Select Subject:", subjects)

    youtube_link = st.text_input("Enter YouTube Video Link:")

    custom_prompt = None
    if subject == "Custom Prompt":
        custom_prompt = st.text_area("Enter your custom prompt:")

    if youtube_link:
        video_id = youtube_link.split("=")[-1]
        st.image(f"http://img.youtube.com/vi/{video_id}/0.jpg", use_column_width=True)

    # Initialize session state for detailed notes if it doesn't exist
    if "detailed_notes" not in st.session_state:
        st.session_state.detailed_notes = ""

    if st.button("Get Detailed Notes"):
        transcript_text = extract_transcript(youtube_link)

        if transcript_text:
            st.success("Transcript extracted successfully!")

            st.session_state.detailed_notes = generate_notes(
                transcript_text, subject, custom_prompt
            )
            st.markdown("## Detailed Notes:")
            st.write(st.session_state.detailed_notes)
        else:
            st.error("Failed to extract transcript.")

    # Separate button for summarizing notes
    if st.session_state.detailed_notes and st.button("Summarize Notes"):
        summary = summarize_text(st.session_state.detailed_notes)
        st.session_state.summary = summary  # Store summary in session state
        st.markdown("## Summary:")
        st.write(st.session_state.summary)

    # Show the latest summary if available
    # if "summary" in st.session_state:
    #     st.markdown("## Latest Summary:")
    #     st.write(st.session_state.summary)

    # Separate checkbox for generating word cloud
    if st.session_state.detailed_notes and st.checkbox("Generate Word Cloud"):
        st.markdown("## Word Cloud:")
        f = create_wordcloud(st.session_state.detailed_notes)
        st.pyplot(f)

    # Separate button for downloading the document
    if st.session_state.detailed_notes:
        download_pdf(st.session_state.detailed_notes, "detailed_notes.pdf")


if __name__ == "__main__":
    main()


# https://www.youtube.com/watch?v=dcXqhMqhZUo
