import streamlit as st
import sys
import os
import openai

# Configuração do caminho da pasta com os utilitários
sys.path.append(os.path.abspath("touch utils"))

from audio_generator import text_to_audio
from youtube_transcriber import transcribe_and_summarize
from formatter import to_markdown

# Configuração da chave da OpenAI via ambiente (ou st.secrets)
openai.api_key = os.getenv("OPENAI_API_KEY")

# Função de sumarização com opção de troca de modelo
def summarize_text_openai(text, model):
    prompt = f"Resuma o conteúdo abaixo de forma técnica, destacando os principais pontos e sugestões de melhoria:\n\n{text}"
    response = openai.ChatCompletion.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# Processamento de PDF
def process_pdf(file, model):
    import fitz  # PyMuPDF
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = "".join([page.get_text() for page in doc])
    summary = summarize_text_openai(text, model)
    insights = "🧠 Análise técnica realizada via OpenAI API."
    return summary, insights

# Configuração da página Streamlit
st.set_page_config(page_title="Narrador de Projetos IA", page_icon="🎧", layout="centered")
st.title("🎙️ Narrador de Projetos com IA")
st.markdown("""
Envie um PDF ou link do YouTube. A IA irá analisar, resumir e transformar o conteúdo em áudio narrado.
""")

# Escolha do modelo da OpenAI
model_options = ["gpt-3.5-turbo", "gpt-4"]
selected_model = st.selectbox("Escolha o modelo da OpenAI para análise:", model_options)

# Abas para funcionalidades
tabs = st.tabs(["📄 Upload PDF", "🎥 Link do YouTube", "🔊 Player / Exportação"])

with tabs[0]:
    uploaded_pdf = st.file_uploader("Faça upload do seu documento PDF", type=["pdf"])
    if uploaded_pdf:
        with st.spinner("Analisando o conteúdo do PDF com IA..."):
            resumo, insights = process_pdf(uploaded_pdf, selected_model)
            st.success("Análise concluída!")
            st.markdown("### 📌 Resumo do Documento")
            st.markdown(resumo)
            st.markdown("### 🛠️ Pontos Técnicos e Ajustes")
            st.markdown(insights)
            st.session_state["resumo"] = resumo

with tabs[1]:
    video_url = st.text_input("Cole o link do vídeo do YouTube")
    if video_url:
        with st.spinner("Transcrevendo e resumindo o vídeo com IA..."):
            resumo, insights = transcribe_and_summarize(video_url, selected_model)
            st.success("Transcrição e análise concluídas!")
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
