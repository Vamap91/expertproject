import streamlit as st
import sys
import os
import time
import logging
from typing import Tuple, Optional
import openai
from openai import OpenAI

# IMPORTANTE: Configurar a página deve ser a primeira operação do Streamlit
st.set_page_config(
    page_title="🎙️ Narrador de Projetos com IA",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Adiciona a pasta com os utilitários ao sys.path
# Mantém o nome original da pasta com espaço
sys.path.append(os.path.abspath("touch utils"))

# Imports dos módulos auxiliares
try:
    from formatter import to_markdown
    from audio_generator import text_to_audio
    from youtube_transcriber import transcribe_and_summarize
    from pdf_processor import process_pdf_complete
except ImportError as e:
    st.error(f"Erro ao importar módulos: {str(e)}. Verifique se a pasta 'touch utils' existe com todos os arquivos necessários.")
    logger.error(f"Import error: {str(e)}")

# Resto do código...


# Configurações do aplicativo
class AppConfig:
    """Centraliza as configurações do aplicativo"""
    TITLE = "🎙️ Narrador de Projetos com IA"
    SUBTITLE = "Transforme documentos e vídeos em áudio narrado com análise inteligente"
    ICON = "🎧"
    PRIMARY_COLOR = "#1E88E5"
    SECONDARY_COLOR = "#004D40"
    BG_COLOR = "#F5F7F9"
    MODEL_OPTIONS = ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"]
    DEFAULT_MODEL = "gpt-3.5-turbo"
    MAX_PDF_SIZE_MB = 10
    CACHE_TTL = 3600  # 1 hora


# Inicialização da API OpenAI
@st.cache_resource
def get_openai_client():
    """Inicializa e retorna o cliente OpenAI com cache"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("⚠️ OPENAI_API_KEY não encontrada nas variáveis de ambiente.")
        logger.error("OpenAI API key not found")
        return None
    try:
        return OpenAI(api_key=api_key)
    except Exception as e:
        st.error(f"⚠️ Erro ao inicializar cliente OpenAI: {str(e)}")
        logger.error(f"OpenAI client initialization error: {str(e)}")
        return None


# Função de análise via OpenAI com cache
@st.cache_data(ttl=AppConfig.CACHE_TTL)
def summarize_text_openai(text: str, model: str) -> str:
    """
    Analisa o texto usando a API OpenAI com sistema de cache
    
    Args:
        text: Texto a ser analisado
        model: Modelo da OpenAI a ser usado
        
    Returns:
        Resumo e análise do texto
    """
    client = get_openai_client()
    if not client:
        return "Erro ao inicializar cliente OpenAI. Verifique a chave de API."
    
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
        logger.error(f"OpenAI API error: {str(e)}")
        return f"Erro ao processar com OpenAI: {str(e)}"


# Processador de PDF com OpenAI
def process_pdf(file, model: str) -> Tuple[str, str]:
    """
    Processa um arquivo PDF e extrai insights usando IA
    
    Args:
        file: Arquivo PDF carregado
        model: Modelo da OpenAI a ser usado
        
    Returns:
        Tupla (resumo, insights)
    """
    try:
        # Verifica tamanho do arquivo
        file_size_mb = len(file.getvalue()) / (1024 * 1024)
        if file_size_mb > AppConfig.MAX_PDF_SIZE_MB:
            return f"Arquivo muito grande ({file_size_mb:.1f}MB). Limite: {AppConfig.MAX_PDF_SIZE_MB}MB", ""
        
        # Processa o PDF usando a função do módulo pdf_processor
        with st.status("Analisando PDF...", expanded=False) as status:
            summary, stats = process_pdf_complete(file.getvalue(), model)
            status.update(label="Análise concluída!", state="complete", expanded=False)
        
        # Formata insights baseados nas estatísticas retornadas
        insights = f"Documento: {stats.get('title', 'Sem título')} | {stats.get('pages', 0)} páginas | {stats.get('words', 0)} palavras"
        
        return summary, insights
    except Exception as e:
        logger.error(f"PDF processing error: {str(e)}")
        return f"Erro ao processar PDF: {str(e)}", ""


def setup_ui():
    """Configura a interface do usuário"""
    # Configuração de página e tema
    st.set_page_config(
        page_title=AppConfig.TITLE,
        page_icon=AppConfig.ICON,
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # CSS personalizado
    st.markdown(f"""
    <style>
        /* Cores gerais do tema */
        :root {{
            --primary-color: {AppConfig.PRIMARY_COLOR};
            --secondary-color: {AppConfig.SECONDARY_COLOR};
            --background-color: {AppConfig.BG_COLOR};
        }}
        
        /* Cabeçalho */
        .main .block-container {{
            padding-top: 2rem;
            padding-bottom: 2rem;
        }}
        
        /* Estilos gerais */
        h1, h2, h3 {{
            color: var(--primary-color);
        }}
        
        .stTabs [data-baseweb="tab-list"] {{
            gap: 2rem;
        }}
        
        .stTabs [data-baseweb="tab"] {{
            height: 4rem;
            white-space: pre-wrap;
            border-radius: 4px 4px 0px 0px;
            gap: 1rem;
        }}
        
        /* Estilo dos botões */
        .stButton>button {{
            border-radius: 4px;
            padding: 0.5rem 1rem;
            font-weight: 500;
        }}
        
        /* Destaque da escolha do modelo */
        div[data-testid="stSelectbox"] > div:first-child {{
            border-radius: 4px;
            border-color: var(--primary-color);
        }}
        
        /* Container de cartões para resultados */
        .card {{
            border-radius: 10px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            border: 1px solid #e6e6e6;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
            background-color: white;
        }}
    </style>
    """, unsafe_allow_html=True)
    
    # Cabeçalho com animação
    st.markdown(f"""
        <div style="text-align: center; margin-bottom: 2rem;">
            <h1>{AppConfig.TITLE}</h1>
            <p style="font-size: 1.2rem; color: grey;">{AppConfig.SUBTITLE}</p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
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
        
        # Escolha do modelo da OpenAI com explicação
        st.markdown("<h3>Configuração da IA</h3>", unsafe_allow_html=True)
        selected_model = st.selectbox(
            "Escolha o modelo para análise:",
            options=AppConfig.MODEL_OPTIONS,
            index=AppConfig.MODEL_OPTIONS.index(AppConfig.DEFAULT_MODEL),
            help="Modelos mais avançados oferecem análises mais detalhadas, mas podem levar mais tempo"
        )
        
        # Modo avançado
        with st.expander("Configurações avançadas"):
            st.checkbox("Ativar detecção de língua", value=True, 
                      help="Detecta automaticamente o idioma do conteúdo")
            st.slider("Nível de detalhamento", min_value=1, max_value=5, value=3,
                    help="Ajusta o nível de detalhamento da análise")
            st.toggle("Incluir citações", value=True)
    
    # Retorna o modelo selecionado
    return selected_model


def main():
    """Função principal da aplicação"""
    # Configura a UI e obtém o modelo selecionado
    selected_model = setup_ui()
    
    # Inicializa estados da sessão
    if "resumo" not in st.session_state:
        st.session_state["resumo"] = None
    if "status" not in st.session_state:
        st.session_state["status"] = None
    if "insights" not in st.session_state:
        st.session_state["insights"] = None
    
    # Cria as tabs em uma coluna principal
    col1, _ = st.columns([2, 1])
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
                help=f"Tamanho máximo: {AppConfig.MAX_PDF_SIZE_MB}MB"
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
                            st.session_state["status"] = "success"
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
                            st.session_state["status"] = "success"
                            st.success("Análise completa! Vá para a aba 'Áudio e Exportação'.")
                            # Mostra prévia do resultado
                            with st.expander("Prévia do resultado", expanded=True):
                                st.markdown(resumo)
                        except Exception as e:
                            logger.error(f"YouTube processing error: {str(e)}")
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
                            logger.error(f"Audio generation error: {str(e)}")
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
                        logger.error(f"Markdown conversion error: {str(e)}")
                        st.error(f"Erro ao converter para Markdown: {str(e)}")
                    
                    # Outras opções de exportação
                    st.download_button(
                        "📝 Exportar como TXT",
                        st.session_state["resumo"],
                        file_name="resumo.txt",
                        use_container_width=True
                    )
            else:
                st.info("Você ainda não carregou um PDF ou link do YouTube. Por favor, utilize uma das outras abas para gerar conteúdo.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        st.error(f"Ocorreu um erro na aplicação: {str(e)}")
