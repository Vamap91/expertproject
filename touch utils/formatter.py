import logging
import re
import html
from typing import Union, Dict, Any, List
from datetime import datetime

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def to_markdown(text: str) -> str:
    """
    Converte texto para formato Markdown aprimorado
    
    Args:
        text: Texto a ser formatado para Markdown
        
    Returns:
        String formatada em Markdown 
    """
    try:
        logger.info(f"Convertendo para Markdown: {len(text)} caracteres")
        
        # Sanitiza o texto primeiro
        sanitized = sanitize_text(text)
        
        # Adiciona cabeçalho com metadados
        current_time = datetime.now().strftime("%d/%m/%Y %H:%M")
        markdown = f"""# Resumo Gerado com IA

> *Documento gerado automaticamente em {current_time} pelo Narrador de Projetos com IA*

---

{sanitized}

---

*Este documento foi criado automaticamente a partir de uma análise de IA e pode ser editado conforme necessário.*
"""
        logger.info("Conversão para Markdown concluída com sucesso")
        return markdown
    
    except Exception as e:
        logger.error(f"Erro ao converter para Markdown: {str(e)}")
        # Retorna o texto original em caso de erro
        return text

def to_html(text: str, theme: str = "light") -> str:
    """
    Converte texto para HTML com estilo aplicado
    
    Args:
        text: Texto a ser convertido para HTML
        theme: Tema de cores (light ou dark)
        
    Returns:
        String HTML formatada
    """
    try:
        logger.info(f"Convertendo para HTML com tema '{theme}'")
        
        # Escapa caracteres HTML
        escaped_text = html.escape(text)
        
        # Substitui quebras de linha por <br>
        formatted_text = escaped_text.replace('\n', '<br>')
        
        # Define cores baseadas no tema
        if theme.lower() == "dark":
            bg_color = "#2d2d2d"
            text_color = "#e0e0e0"
            border_color = "#444444"
        else:  # light
            bg_color = "#ffffff"
            text_color = "#333333"
            border_color = "#dddddd"
        
        # Cria o HTML com CSS embutido
        html_content = f"""<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name
