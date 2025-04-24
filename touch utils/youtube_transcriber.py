import os
import logging
import tempfile
import re
from typing import Tuple, Optional, Dict, Any, List
import requests
from pytube import YouTube
from urllib.error import URLError

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Importamos a função de resumo do aplicativo principal
# Isso requer que a função seja acessível em um módulo separado
# ou que seja importada corretamente
try:
    from openai import OpenAI
except ImportError:
    logger.warning("OpenAI não está disponível. Algumas funcionalidades podem não funcionar.")

# Cache para armazenar transcrições já processadas
# Chave: URL do vídeo, Valor: Texto transcrito
TRANSCRIPTION_CACHE = {}


def validate_youtube_url(url: str) -> bool:
    """
    Valida se a URL é do YouTube
    
    Args:
        url: URL a ser validada
        
    Returns:
        Boolean indicando se é uma URL válida do YouTube
    """
    youtube_regex = (
        r'(https?://)?(www\.)?'
        r'(youtube|youtu|youtube-nocookie)\.(com|be)/'
        r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
    )
    
    match = re.match(youtube_regex, url)
    return match is not None


def extract_video_id(url: str) -> Optional[str]:
    """
    Extrai o ID do vídeo a partir da URL do YouTube
    
    Args:
        url: URL do YouTube
        
    Returns:
        ID do vídeo ou None se não for possível extrair
    """
    youtube_regex = (
        r'(https?://)?(www\.)?'
        r'(youtube|youtu|youtube-nocookie)\.(com|be)/'
        r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
    )
    
    match = re.match(youtube_regex, url)
    if match:
        return match.group(6)
    return None


def get_video_info(url: str) -> Dict[str, Any]:
    """
    Obtém informações sobre o vídeo do YouTube
    
    Args:
        url: URL do vídeo do YouTube
        
    Returns:
        Dicionário com informações do vídeo
    """
    try:
        yt = YouTube(url)
        
        return {
            "title": yt.title,
            "author": yt.author,
            "length": yt.length,
            "publish_date": yt.publish_date.strftime("%Y-%m-%d") if yt.publish_date else None,
            "views": yt.views,
            "description": yt.description,
            "thumbnail_url": yt.thumbnail_url,
            "keywords": yt.keywords,
            "video_id": yt.video_id,
        }
    except Exception as e:
        logger.error(f"Erro ao obter informações do vídeo: {str(e)}")
        return {
            "error": str(e),
            "message": "Não foi possível obter informações do vídeo."
        }


def download_audio(url: str) -> Optional[str]:
    """
    Baixa o áudio de um vídeo do YouTube
    
    Args:
        url: URL do vídeo
        
    Returns:
        Caminho para o arquivo de áudio baixado ou None em caso de erro
    """
    try:
        logger.info(f"Baixando áudio de: {url}")
        
        # Cria um diretório temporário
        temp_dir = tempfile.mkdtemp()
        
        # Baixa apenas a faixa de áudio
        yt = YouTube(url)
        audio_stream = yt.streams.filter(only_audio=True).first()
        
        if not audio_stream:
            logger.error("Nenhum stream de áudio encontrado para o vídeo")
            return None
        
        # Baixa o áudio para o diretório temporário
        audio_file = audio_stream.download(output_path=temp_dir)
        
        logger.info(f"Áudio baixado com sucesso: {audio_file}")
        return audio_file
        
    except Exception as e:
        logger.error(f"Erro ao baixar áudio: {str(e)}")
        return None


def transcribe_audio(audio_file: str, language: str = "pt") -> Optional[str]:
    """
    Transcreve o áudio usando o OpenAI Whisper
    
    Args:
        audio_file: Caminho para o arquivo de áudio
        language: Código do idioma para otimizar a transcrição
        
    Returns:
        Texto transcrito ou None em caso de erro
    """
    try:
        logger.info(f"Transcrevendo áudio: {audio_file}")
        
        # Tenta usar a OpenAI para transcrição
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            logger.error("API key da OpenAI não disponível")
            return None
        
        client = OpenAI(api_key=api_key)
        
        with open(audio_file, "rb") as audio:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio,
                language=language
            )
        
        logger.info(f"Transcrição concluída: {len(transcript.text)} caracteres")
        return transcript.text
        
    except Exception as e:
        logger.error(f"Erro na transcrição: {str(e)}")
        
        # Tenta usar um serviço alternativo em caso de falha
        try:
            logger.info("Tentando serviço alternativo de transcrição")
            # Aqui poderia ser implementado um serviço alternativo
            # como AssemblyAI, Google Speech-to-Text, etc.
            return None
        except Exception as fallback_e:
            logger.error(f"Erro no serviço alternativo: {str(fallback_e)}")
            return None


def analyze_transcript(transcript: str, model: str) -> str:
    """
    Analisa a transcrição usando OpenAI para extrair insights
    
    Args:
        transcript: Texto transcrito
        model: Modelo da OpenAI a usar
        
    Returns:
        Análise do conteúdo da transcrição
    """
    try:
        logger.info(f"Analisando transcrição: {len(transcript)} caracteres")
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("API key da OpenAI não disponível")
            return "Não foi possível analisar a transcrição: Chave da API não disponível."
        
        client = OpenAI(api_key=api_key)
        
        prompt = f"""
        Analise a transcrição abaixo e extraia os principais insights, pontos técnicos e recomendações:
        
        {transcript[:4000]}...
        
        Forneça uma análise estruturada com:
        1. Resumo dos principais tópicos discutidos
        2. Pontos técnicos importantes mencionados
        3. Recomendações ou sugestões mencionadas
        4. Conclusões gerais
        
        Use markdown para formatar a resposta.
        """
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Você é um analista especializado em extrair insights valiosos de transcrições de vídeos."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        
        analysis = response.choices[0].message.content
        logger.info(f"Análise concluída: {len(analysis)} caracteres")
        return analysis
        
    except Exception as e:
        logger.error(f"Erro na análise da transcrição: {str(e)}")
        return f"Erro ao analisar transcrição: {str(e)}"


def transcribe_and_summarize(url: str, model: str = "gpt-3.5-turbo") -> Tuple[str, str]:
    """
    Processo completo: baixa vídeo, transcreve e analisa
    
    Args:
        url: URL do vídeo do YouTube
        model: Modelo da OpenAI a ser usado na análise
        
    Returns:
        Tupla (resumo, insights)
    """
    try:
        # Valida URL
        if not validate_youtube_url(url):
            raise ValueError("URL inválida do YouTube")
        
        video_id = extract_video_id(url)
        
        # Verifica se já temos no cache
        if video_id in TRANSCRIPTION_CACHE:
            logger.info(f"Usando transcrição em cache para: {video_id}")
            transcript = TRANSCRIPTION_CACHE[video_id]
        else:
            # Baixa áudio
            audio_file = download_audio(url)
            if not audio_file:
                raise ValueError("Não foi possível baixar o áudio do vídeo")
            
            # Transcreve
            transcript = transcribe_audio(audio_file)
            if not transcript:
                raise ValueError("Falha na transcrição do áudio")
            
            # Limpa arquivo temporário
            os.remove(audio_file)
            
            # Salva no cache
            TRANSCRIPTION_CACHE[video_id] = transcript
        
        # Analisa a transcrição
        analysis = analyze_transcript(transcript, model)
        
        # Obtém informações do vídeo para enriquecer o resumo
        video_info = get_video_info(url)
        
        # Formata o resumo com informações do vídeo
        resumo = f"""# Análise do vídeo: {video_info.get('title', 'Sem título')}

{analysis}

---

*Análise baseada na transcrição do vídeo [#{video_id}](https://youtube.com/watch?v={video_id}) de {video_info.get('author', 'Autor desconhecido')}*
"""
        
        insights = f"Vídeo analisado: {video_info.get('title', 'Sem título')} por {video_info.get('author', 'Autor desconhecido')}"
        
        return resumo, insights
        
    except Exception as e:
        logger.error(f"Erro no processo de transcrição e resumo: {str(e)}")
        return f"Erro: {str(e)}", "Não foi possível processar o vídeo"


def batch_process_videos(urls: List[str], model: str = "gpt-3.5-turbo") -> Dict[str, Dict[str, Any]]:
    """
    Processa múltiplos vídeos em lote
    
    Args:
        urls: Lista de URLs do YouTube
        model: Modelo da OpenAI a ser usado
        
    Returns:
        Dicionário com resultados para cada URL
    """
    results = {}
    
    for url in urls:
        video_id = extract_video_id(url)
        if not video_id:
            results[url] = {
                "success": False,
                "error": "URL inválida do YouTube"
            }
            continue
        
        try:
            resumo, insights = transcribe_and_summarize(url, model)
            results[video_id] = {
                "success": True,
                "resumo": resumo,
                "insights": insights,
                "url": url
            }
        except Exception as e:
            results[video_id] = {
                "success": False,
                "error": str(e),
                "url": url
            }
    
    return results


if __name__ == "__main__":
    # Teste simples
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Vídeo de exemplo
    
    print(f"Testando transcrição para: {test_url}")
    try:
        resumo, insights = transcribe_and_summarize(test_url)
        print("\n--- RESUMO ---")
        print(resumo[:300] + "..." if len(resumo) > 300 else resumo)
        print("\n--- INSIGHTS ---")
        print(insights)
    except Exception as e:
        print(f"Erro no teste: {str(e)}")
