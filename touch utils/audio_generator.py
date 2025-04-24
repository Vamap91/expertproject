import io
import os
import logging
import tempfile
from typing import Optional, Union, Tuple

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def text_to_audio(text: str, voice: str = "pt", rate: int = 175) -> Union[bytes, None]:
    """
    Converte texto para áudio usando TTS.
    
    Args:
        text: Texto para converter em áudio
        voice: Idioma/voz a ser usada (padrão: 'pt' para português)
        rate: Velocidade da fala (palavras por minuto)
        
    Returns:
        Bytes do arquivo de áudio gerado ou None em caso de erro
    """
    try:
        # Importamos aqui para não afetar o carregamento inicial da aplicação
        import pyttsx3
        
        logger.info(f"Iniciando conversão de texto para áudio: {len(text)} caracteres")
        
        # Preparando engine TTS
        engine = pyttsx3.init()
        engine.setProperty('rate', rate)
        
        # Definindo voz baseada no idioma
        voices = engine.getProperty('voices')
        
        # Tenta encontrar uma voz no idioma especificado
        voice_found = False
        for v in voices:
            if voice.lower() in v.id.lower() or voice.lower() in v.name.lower():
                engine.setProperty('voice', v.id)
                voice_found = True
                logger.info(f"Voz selecionada: {v.name}")
                break
                
        if not voice_found and voices:
            # Usa a primeira voz disponível se não encontrar o idioma específico
            engine.setProperty('voice', voices[0].id)
            logger.warning(f"Voz para '{voice}' não encontrada. Usando voz padrão: {voices[0].name}")
        
        # Criar arquivo temporário para o áudio
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            temp_filename = temp_file.name
        
        # Processar texto em blocos para evitar problemas com textos muito longos
        # (alguns mecanismos TTS têm limites de tamanho de texto)
        chunks = split_text(text, max_chars=800)
        
        # Salvar áudio
        engine.save_to_file(text, temp_filename)
        engine.runAndWait()
        
        # Ler arquivo gerado
        with open(temp_filename, 'rb') as audio_file:
            audio_bytes = audio_file.read()
        
        # Limpar arquivo temporário
        os.unlink(temp_filename)
        
        logger.info(f"Conversão de texto para áudio concluída: {len(audio_bytes)} bytes")
        return audio_bytes
        
    except Exception as e:
        logger.error(f"Erro na conversão de texto para áudio: {str(e)}")
        
        # Fallback para gTTS se pyttsx3 falhar
        try:
            from gtts import gTTS
            from io import BytesIO
            
            logger.info("Tentando fallback para gTTS")
            mp3_fp = BytesIO()
            tts = gTTS(text=text, lang=voice[:2])
            tts.write_to_fp(mp3_fp)
            mp3_fp.seek(0)
            audio_bytes = mp3_fp.read()
            logger.info(f"Fallback para gTTS bem-sucedido: {len(audio_bytes)} bytes")
            return audio_bytes
            
        except Exception as fallback_e:
            logger.error(f"Erro no fallback para gTTS: {str(fallback_e)}")
            return None

def split_text(text: str, max_chars: int = 1000) -> list:
    """
    Divide texto em blocos menores para processamento.
    
    Args:
        text: Texto a ser dividido
        max_chars: Número máximo de caracteres por bloco
        
    Returns:
        Lista de blocos de texto
    """
    # Se o texto for menor que o tamanho máximo, retorna como está
    if len(text) <= max_chars:
        return [text]
    
    chunks = []
    remaining_text = text
    
    while remaining_text:
        # Encontra um bom ponto de quebra (fim de frase ou parágrafo)
        if len(remaining_text) <= max_chars:
            chunks.append(remaining_text)
            break
        
        # Procura por pontos finais, exclamação, interrogação ou quebras de linha
        split_point = max_chars
        
        # Percorre do limite máximo para trás procurando um bom ponto de quebra
        for i in range(max_chars, max_chars // 2, -1):
            if i >= len(remaining_text):
                continue
                
            if remaining_text[i] in ['.', '!', '?', '\n']:
                split_point = i + 1
                break
        
        # Adiciona o chunk atual e remove do texto restante
        chunks.append(remaining_text[:split_point])
        remaining_text = remaining_text[split_point:].strip()
    
    return chunks

# Função para detecção de idioma (opcional, para determinar a voz automaticamente)
def detect_language(text: str) -> str:
    """
    Detecta o idioma do texto para escolher a voz adequada.
    Requer a biblioteca langdetect.
    
    Args:
        text: Texto para detectar o idioma
        
    Returns:
        Código do idioma detectado (ex: 'pt', 'en', 'es')
    """
    try:
        from langdetect import detect
        
        # Usa apenas os primeiros N caracteres para economizar processamento
        sample = text[:min(len(text), 500)]
        lang = detect(sample)
        logger.info(f"Idioma detectado: {lang}")
        return lang
    except Exception as e:
        logger.warning(f"Não foi possível detectar o idioma: {str(e)}")
        return "pt"  # Retorna português como padrão

# Função de conversão avançada com opções adicionais
def text_to_audio_advanced(
    text: str, 
    voice: Optional[str] = None,
    rate: int = 175,
    output_format: str = "mp3",
    auto_detect_language: bool = True
) -> Tuple[Union[bytes, None], dict]:
    """
    Versão avançada da conversão texto-para-fala com mais opções.
    
    Args:
        text: Texto para converter
        voice: Voz/idioma específico (se None, detecta automaticamente)
        rate: Velocidade da fala
        output_format: Formato do áudio (mp3, wav)
        auto_detect_language: Se deve detectar o idioma automaticamente
        
    Returns:
        Tupla (bytes do áudio, metadados)
    """
    metadata = {
        "chars_count": len(text),
        "words_count": len(text.split()),
        "format": output_format
    }
    
    # Detecta o idioma automaticamente se solicitado
    if auto_detect_language and voice is None:
        detected_lang = detect_language(text)
        voice = detected_lang
        metadata["detected_language"] = detected_lang
    elif voice is None:
        voice = "pt"  # Idioma padrão
    
    metadata["voice"] = voice
    metadata["rate"] = rate
    
    # Usa a função principal para gerar o áudio
    audio_data = text_to_audio(text, voice, rate)
    
    if audio_data:
        metadata["success"] = True
        metadata["size_bytes"] = len(audio_data)
    else:
        metadata["success"] = False
    
    return audio_data, metadata


if __name__ == "__main__":
    # Teste simples da função
    test_text = "Este é um teste de conversão de texto para áudio. Verifique se a voz está clara e natural."
    audio = text_to_audio(test_text)
    
    if audio:
        # Salva em um arquivo para teste
        with open("test_audio.mp3", "wb") as f:
            f.write(audio)
        print(f"Arquivo de áudio gerado com sucesso: {len(audio)} bytes")
    else:
        print("Não foi possível gerar o áudio")
