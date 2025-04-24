import streamlit as st
import sys
import os

# Adiciona o caminho da pasta "touch utils" ao sys.path
sys.path.append(os.path.abspath("touch utils"))

from audio_generator import text_to_audio
from pdf_processor import process_pdf
from youtube_transcriber import transcribe_and_summarize
from formatter import to_markdown

st.set_page_config(page_title="Narrador de Projetos IA", page_icon="🎧", layout="centered")
st.title("🎙️ Narrador de Projetos com IA")
st.markdown("""
Experimente subir um arquivo PDF ou colar o link de um vídeo do YouTube com conteúdo técnico.
A IA vai ler, resumir, gerar insights e transformar tudo em um áudio narrado para você ouvir ou baixar.
""")

tabs = st.tabs(["📄 Upload PDF", "🎥 Link do YouTube", "🔊 Player / Exportação"])

with tabs[0]:
    uploaded_pdf = st.file_uploader("Faça upload do seu documento PDF", type=["pdf"])
    if uploaded_pdf:
        with st.spinner("Lendo e resumindo o conteúdo..."):
            resumo, insights = process_pdf(uploaded_pdf)
            st.success("Resumo gerado com sucesso!")
            st.markdown("### 📌 Resumo do Documento")
            st.markdown(resumo)
            st.markdown("### 🛠️ Pontos Técnicos e Ajustes")
            st.markdown(insights)
            st.session_state["resumo"] = resumo

with tabs[1]:
    video_url = st.text_input("Cole o link do vídeo do YouTube")
    if video_url:
        with st.spinner("Transcrevendo e resumindo o vídeo..."):
            resumo, insights = transcribe_and_summarize(video_url)
            st.success("Transcrição e resumo finalizados!")
            st.markdown("### 🎬 Resumo do Vídeo")
            st.markdown(resumo)
            st.markdown("### 🧩 Pontos Técnicos Extraídos")
            st.markdown(insights)
            st.session_state["resumo"] = resumo

with tabs[2]:
    if "resumo" in st.session_state:
        st.markdown("### 🎧 Ouça o conteúdo narrado")
        audio_bytes = text_to_audio(st.session_state["resumo"])
        st.audio(audio_bytes, format="audio/mp3")

        st.markdown("---")
        st.download_button(
            label="📥 Baixar áudio narrado",
            data=audio_bytes,
            file_name="resumo_narrado.mp3",
            mime="audio/mp3"
        )

        st.markdown("---")
        markdown_text = to_markdown(st.session_state["resumo"])
        st.download_button("📄 Exportar para Markdown", markdown_text, file_name="resumo.md")
    else:
        st.info("Você ainda não carregou um PDF ou link do YouTube.")
