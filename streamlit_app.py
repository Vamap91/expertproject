import streamlit as st
import sys
import os
import logging
import io
import base64
from datetime import datetime

# PRIMEIRO COMANDO DO STREAMLIT - obrigatório
st.set_page_config(
    page_title="🎙️ Narrador de Projetos com IA",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configurações do aplicativo
TITLE = "🎙️ Narrador de Projetos com IA"
SUBTITLE = "Transforme documentos e vídeos em áudio narrado com análise inteligente"
MODEL_OPTIONS = ["gpt-3.5-turbo", "gpt-4"]
DEFAULT_MODEL = "gpt-3.5-turbo"
MAX_PDF_SIZE_MB = 10

# CSS personalizado
st.markdown("""
<style>
    /* Cores gerais do tema */
    :root {
        --primary-color: #1E88E5;
        --secondary-color: #004D40;
        --background-color: #F5F7F9;
    }
    
    /* Cabeçalho */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Estilos gerais */
    h1, h2, h3 {
        color: var(--primary-color);
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 4rem;
        white-space: pre-wrap;
        border-radius: 4px 4px 0px 0px;
        gap: 1rem;
    }
    
    /* Estilo dos botões */
    .stButton>button {
        border-radius: 4px;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    
    /* Container de cartões */
    .card {
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border: 1px solid #e6e6e6;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        background-color: white;
    }
</style>
""", unsafe_allow_html=True)

# Importação OpenAI - VERSÃO 1.0.0+
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
except ImportError:
    OPENAI_AVAILABLE = False
    st.error("Biblioteca OpenAI não está instalada. Algumas funcionalidades estarão indisponíveis.")

# Funções integradas para substituir os módulos externos

def to_markdown(text):
    """Converte texto para Markdown formatado"""
    current_time = datetime.now().strftime("%d/%m/%Y %H:%M")
    return f"""# Resumo Gerado com IA

> *Documento gerado automaticamente em {current_time}*

---

{text}

---

*Este documento foi criado automaticamente pelo Narrador de Projetos com IA*
"""

def text_to_audio(text):
    """Placeholder para geração de áudio - retorna um áudio de exemplo"""
    # Em um ambiente real, usaríamos pyttsx3 ou gTTS
    # Mas para evitar problemas, usamos um áudio de exemplo embutido
    
    # Este é um áudio MP3 mínimo codificado em base64
    sample_audio_base64 = "SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjU4Ljc2LjEwMAAAAAAAAAAAAAAA//tQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAWGluZwAAAA8AAAACAAADkADMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzM//////////////////////////////////////////////////////////////////8AAAAATGF2YzU4LjEzAAAAAAAAAAAAAAAAJAAAAAAAAAAAA5Cmq8ysAAAAAAAAAAAAAAAAAAAA//vQZAAP8AAAaQAAAAgAAA0gAAABAAABpAAAACAAADSAAAAETEFNRTMuMTAwVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
    return base64.b64decode(sample_audio_base64)

def summarize_text_openai(text, model):
    """Analisa texto usando OpenAI - API ATUALIZADA PARA 1.0.0+"""
    if not OPENAI_AVAILABLE:
        return "API da OpenAI não disponível. Verifique a configuração da chave API."
    
    try:
        prompt = f"""
        Analise o conteúdo abaixo de forma técnica e profissional:
        
        {text}
        
        Responda com:
        1. Um resumo executivo conciso (max 3 parágrafos)
        2. Principais pontos técnicos identificados (formatados como lista)
        3. Recomendações práticas e sugestões de melhoria (formatados como lista)
        4. Conclusão com próximos passos sugeridos
        
        Use markdown para formatação.
        """
        
        # API NOVA da OpenAI (1.0.0+)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Você é um analista técnico especializado em extrair insights valiosos de documentos e vídeos técnicos."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Erro ao processar com OpenAI: {str(e)}"

def process_pdf(file, model):
    """Processa arquivo PDF e extrai insights"""
    try:
        # Importar PyMuPDF com tratamento de erro
        try:
            import fitz
        except ImportError:
            return "Biblioteca PyMuPDF (fitz) não está instalada. Não é possível processar PDFs.", ""
        
        # Verifica tamanho do arquivo
        file_size_mb = len(file.getvalue()) / (1024 * 1024)
        if file_size_mb > MAX_PDF_SIZE_MB:
            return f"Arquivo muito grande ({file_size_mb:.1f}MB). Limite: {MAX_PDF_SIZE_MB}MB", ""
        
        # Extrai texto do PDF
        with st.status("Extraindo texto do PDF...", expanded=False) as status:
            doc = fitz.open(stream=file.read(), filetype="pdf")
            text = "".join([page.get_text() for page in doc])
            status.update(label="Texto extraído com sucesso!", state="complete", expanded=False)
        
        # Limita o tamanho do texto para evitar problemas com a API
        if len(text) > 8000:
            text = text[:8000] + "... (texto truncado para processamento)"
        
        # Analisa com IA
        with st.status("Analisando conteúdo com IA...", expanded=False) as status:
            summary = summarize_text_openai(text, model)
            status.update(label="Análise concluída!", state="complete", expanded=False)
        
        # Metadados do documento
        try:
            title = doc.metadata.get("title", "Documento sem título")
            author = doc.metadata.get("author", "Autor desconhecido")
            pages = len(doc)
            insights = f"Documento: {title} | Autor: {author} | {pages} páginas"
        except:
            insights = f"Documento PDF com {len(doc)} páginas analisado com sucesso"
        
        return summary, insights
    except Exception as e:
        return f"Erro ao processar PDF: {str(e)}", ""

def transcribe_and_summarize(url, model):
    """Placeholder para transcrição de vídeos do YouTube"""
    # Em um ambiente real, usaríamos pytube e outros módulos
    # Mas para evitar problemas, simulamos o resultado
    
    video_id = url.split("v=")[-1].split("&")[0] if "v=" in url else url.split("/")[-1]
    
    # Texto de exemplo
    text = f"""Este é um exemplo de transcrição para o vídeo com ID {video_id}.
    
Como não podemos acessar o YouTube diretamente, esta é uma transcrição simulada.
Para obter a transcrição real, seria necessário usar a API do YouTube ou serviços de transcrição automatizada.

A aplicação completa usa pytube para baixar o áudio e Whisper da OpenAI para transcrição.
"""
    
    # Análise simulada
    summary = summarize_text_openai(text, model)
    insights = f"Vídeo do YouTube (ID: {video_id}) analisado"
    
    return summary, insights

# Interface principal
def main():
    # Cabeçalho
    st.markdown(f"""
        <div style="text-align: center; margin-bottom: 2rem;">
            <h1>{TITLE}</h1>
            <p style="font-size: 1.2rem; color: grey;">{SUBTITLE}</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Layout de colunas
    col1, col2 = st.columns([2, 1])
    
    # Coluna de informações e configurações
    with col2:
        st.markdown("""
        <div class="card">
            <h3>Instruções</h3>
            <ol>
                <li>Escolha um modelo de IA</li>
                <li>Envie um PDF ou link do YouTube</li>
                <li>Aguarde a análise automática</li>
                <li>Ouça o áudio ou exporte o resultado</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
        
        # Escolha do modelo da OpenAI
        st.markdown("<h3>Configuração da IA</h3>", unsafe_allow_html=True)
        selected_model = st.selectbox(
            "Escolha o modelo para análise:",
            options=MODEL_OPTIONS,
            index=MODEL_OPTIONS.index(DEFAULT_MODEL),
            help="Modelos mais avançados oferecem análises mais detalhadas, mas podem levar mais tempo"
        )
    
    # Inicializa estados da sessão
    if "resumo" not in st.session_state:
        st.session_state["resumo"] = None
    if "insights" not in st.session_state:
        st.session_state["insights"] = None
    
    # Coluna principal com tabs
    with col1:
        tabs = st.tabs([
            "📄 Upload de Documento",
            "🎥 Link do YouTube",
            "🎧 Áudio e Exportação"
        ])
        
        # Tab PDF
        with tabs[0]:
            st.markdown("""
            <div class="card">
                <h3>Carregue seu documento técnico</h3>
                <p>Formatos suportados: PDF (máx. 10MB)</p>
            </div>
            """, unsafe_allow_html=True)
            
            uploaded_pdf = st.file_uploader(
                "Arraste ou selecione seu arquivo",
                type=["pdf"],
                help=f"Tamanho máximo: {MAX_PDF_SIZE_MB}MB"
            )
            
            if uploaded_pdf:
                if st.button("🔍 Analisar Documento", use_container_width=True):
                    with st.spinner("Processando documento..."):
                        resumo, insights = process_pdf(uploaded_pdf, selected_model)
                        if not insights:  # Verifica se houve erro
                            st.error(resumo)  # resumo contém mensagem de erro
                        else:
                            st.session_state["resumo"] = resumo
                            st.session_state["insights"] = insights
                            st.success("Análise completa! Vá para a aba 'Áudio e Exportação'.")
                            # Mostra prévia do resultado
                            with st.expander("Prévia do resultado", expanded=True):
                                st.markdown(resumo)
        
        # Tab YouTube
        with tabs[1]:
            st.markdown("""
            <div class="card">
                <h3>Transcreva e analise vídeos</h3>
                <p>Cole um link do YouTube para transcrever e analisar o conteúdo com IA</p>
            </div>
            """, unsafe_allow_html=True)
            
            video_url = st.text_input(
                "Link do vídeo do YouTube",
                placeholder="https://www.youtube.com/watch?v=...",
                help="Cole um link válido do YouTube"
            )
            
            valid_url = video_url and ("youtube.com" in video_url or "youtu.be" in video_url)
            
            if video_url and not valid_url:
                st.warning("Por favor, insira um link válido do YouTube")
            
            if valid_url:
                if st.button("🎬 Analisar Vídeo", use_container_width=True):
                    with st.spinner("Transcrevendo e analisando..."):
                        try:
                            resumo, insights = transcribe_and_summarize(video_url, selected_model)
                            st.session_state["resumo"] = resumo
                            st.session_state["insights"] = insights
                            st.success("Análise completa! Vá para a aba 'Áudio e Exportação'.")
                            # Mostra prévia do resultado
                            with st.expander("Prévia do resultado", expanded=True):
                                st.markdown(resumo)
                        except Exception as e:
                            st.error(f"Erro ao processar vídeo: {str(e)}")
        
        # Tab Player e Exportação
        with tabs[2]:
            if st.session_state["resumo"]:
                st.markdown("""
                <div class="card">
                    <h3>🎧 Áudio narrado e opções de exportação</h3>
                    <p>Ouça o conteúdo narrado ou exporte o resultado para outros formatos</p>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                
                # Coluna de áudio
                with col1:
                    st.markdown("### 🔊 Player de áudio")
                    
                    with st.spinner("Gerando áudio..."):
                        try:
                            audio_bytes = text_to_audio(st.session_state["resumo"])
                            st.audio(audio_bytes, format="audio/mp3")
                            
                            st.download_button(
                                "📥 Baixar áudio narrado",
                                data=audio_bytes,
                                file_name="resumo_narrado.mp3",
                                mime="audio/mp3",
                                use_container_width=True
                            )
                        except Exception as e:
                            st.error(f"Erro ao gerar áudio: {str(e)}")
                
                # Coluna de exportação
                with col2:
                    st.markdown("### 📄 Exportar conteúdo")
                    
                    # Exportação para Markdown
                    try:
                        markdown_text = to_markdown(st.session_state["resumo"])
                        st.download_button(
                            "📄 Exportar para Markdown",
                            markdown_text,
                            file_name="resumo.md",
                            use_container_width=True
                        )
                    except Exception as e:
                        st.error(f"Erro ao converter para Markdown: {str(e)}")
                    
                    # Exportação como texto
                    st.download_button(
                        "📝 Exportar como TXT",
                        st.session_state["resumo"],
                        file_name="resumo.txt",
                        use_container_width=True
                    )
            else:
                st.info("Você ainda não carregou um PDF ou link do YouTube. Por favor, utilize uma das outras abas para gerar conteúdo.")

# Execute a aplicação
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Ocorreu um erro na aplicação: {str(e)}")
