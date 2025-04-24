# utils/youtube_transcriber.py

import whisper
import tempfile
import os
import yt_dlp
from transformers import pipeline

summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

def download_audio_from_youtube(url):
    temp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': temp_file.name,
        'quiet': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return temp_file.name

def transcribe_audio(file_path):
    model = whisper.load_model("base")
    result = model.transcribe(file_path)
    return result["text"]

def summarize_text(text):
    chunks = [text[i:i+1024] for i in range(0, len(text), 1024)]
    summary = ""
    for chunk in chunks:
        result = summarizer(chunk, max_length=180, min_length=30, do_sample=False)
        summary += result[0]['summary_text'] + " "
    return summary

def transcribe_and_summarize(url):
    audio_path = download_audio_from_youtube(url)
    transcription = transcribe_audio(audio_path)
    summary = summarize_text(transcription)
    insights = "📌 Este conteúdo foi extraído via transcrição de vídeo do YouTube."
    os.remove(audio_path)
    return summary, insights

