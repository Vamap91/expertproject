# utils/pdf_processor.py

import fitz  # PyMuPDF
from transformers import pipeline

summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

def extract_text_from_pdf(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def summarize_text(text):
    max_chunk = 1024
    chunks = [text[i:i+max_chunk] for i in range(0, len(text), max_chunk)]
    summary = ""
    for chunk in chunks:
        result = summarizer(chunk, max_length=180, min_length=30, do_sample=False)
        summary += result[0]['summary_text'] + " "
    return summary

def process_pdf(file):
    raw_text = extract_text_from_pdf(file)
    resumo = summarize_text(raw_text)
    insights = "🧠 Pontos técnicos serão analisados nas próximas versões com IA específica."
    return resumo, insights
