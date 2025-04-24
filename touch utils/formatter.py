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
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Análise de Projeto</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: {bg_color};
            color: {text_color};
            line-height: 1.6;
            padding: 20px;
            max-width: 800px;
            margin: 0 auto;
        }}
        .container {{
            background-color: {bg_color};
            border: 1px solid {border_color};
            border-radius: 8px;
            padding: 25px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1, h2, h3 {{
            color: #1E88E5;
        }}
        .footer {{
            margin-top: 30px;
            font-size: 0.8em;
            text-align: center;
            color: #777;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Análise de Projeto</h1>
        <div class="content">
            {formatted_text}
        </div>
        <div class="footer">
            Gerado pelo Narrador de Projetos com IA em {datetime.now().strftime("%d/%m/%Y %H:%M")}
        </div>
    </div>
</body>
</html>"""
        
        logger.info("Conversão para HTML concluída com sucesso")
        return html_content
        
    except Exception as e:
        logger.error(f"Erro ao converter para HTML: {str(e)}")
        # Retorna texto simples em caso de erro
        return f"<pre>{html.escape(text)}</pre>"="viewport" content="width=device-width, initial-scale=1.0">
    <title>Análise de Projeto</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: {bg_color};
            color: {text_color};
            line-height: 1.6;
            padding: 20px;
            max-width: 800px;
            margin: 0 auto;
        }}
        .container {{
            background-color: {bg_color};
            border: 1px solid {border_color};
            border-radius: 8px;
            padding: 25px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1, h2, h3 {{
            color: #1E88E5;
        }}
        .footer {{
            margin-top: 30px;
            font-size: 0.8em;
            text-align: center;
            color: #777;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Análise de Projeto</h1>
        <div class="content">
            {formatted_text}
        </div>
        <div class="footer">
            Gerado pelo Narrador de Projetos com IA em {datetime.now().strftime("%d/%m/%Y %H:%M")}
        </div>
    </div>
</body>
</html>"""
        
        logger.info("Conversão para HTML concluída com sucesso")
        return html_content
        
    except Exception as e:
        logger.error(f"Erro ao converter para HTML: {str(e)}")
        # Retorna texto simples em caso de erro
        return f"<pre>{html.escape(text)}</pre>"

def to_json(text: str) -> Dict[str, Any]:
    """
    Converte o resumo em um formato JSON estruturado
    
    Args:
        text: Texto a ser convertido para JSON
        
    Returns:
        Dicionário com os dados estruturados
    """
    try:
        logger.info("Convertendo para estrutura JSON")
        
        # Estrutura básica de JSON
        result = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "generator": "Narrador de Projetos com IA",
                "content_length": len(text)
            },
            "content": {
                "raw_text": text,
                "sections": []
            }
        }
        
        # Tenta identificar seções com base em cabeçalhos
        section_pattern = r'#{1,3}\s+(.*?)\n(.*?)(?=#{1,3}|\Z)'
        sections = re.findall(section_pattern, text, re.DOTALL)
        
        if sections:
            for title, content in sections:
                result["content"]["sections"].append({
                    "title": title.strip(),
                    "content": content.strip()
                })
        else:
            # Se não encontrar seções, usa o texto completo
            result["content"]["sections"].append({
                "title": "Resumo Completo",
                "content": text.strip()
            })
            
        logger.info(f"Conversão para JSON concluída com {len(result['content']['sections'])} seções")
        return result
        
    except Exception as e:
        logger.error(f"Erro ao converter para JSON: {str(e)}")
        # Retorna estrutura mínima em caso de erro
        return {
            "error": str(e),
            "raw_text": text
        }

def sanitize_text(text: str) -> str:
    """
    Sanitiza texto para remover caracteres problemáticos
    
    Args:
        text: Texto a ser sanitizado
        
    Returns:
        Texto sanitizado
    """
    # Remove caracteres de controle indesejados
    sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    
    # Normaliza quebras de linha
    sanitized = sanitized.replace('\r\n', '\n').replace('\r', '\n')
    
    # Remove quebras de linha extras
    sanitized = re.sub(r'\n{3,}', '\n\n', sanitized)
    
    return sanitized

def extract_key_points(text: str) -> List[str]:
    """
    Extrai pontos-chave do texto usando heurísticas simples
    
    Args:
        text: Texto para extrair pontos-chave
        
    Returns:
        Lista de pontos-chave
    """
    key_points = []
    
    # Procura por listas (itens começando com - ou *)
    list_items = re.findall(r'^[\s]*[-*][\s]+(.*?), text, re.MULTILINE)
    if list_items:
        key_points.extend(list_items)
    
    # Procura por frases com palavras-chave indicativas
    indicators = [
        'importante', 'fundamental', 'crucial', 'essencial', 'principal',
        'chave', 'destaque', 'relevante', 'significativo', 'crítico'
    ]
    
    for indicator in indicators:
        pattern = r'([^.!?]*\b{}\b[^.!?]*[.!?])'.format(indicator)
        sentences = re.findall(pattern, text, re.IGNORECASE)
        key_points.extend([s.strip() for s in sentences])
    
    # Limita a quantidade de pontos-chave
    return key_points[:10] if len(key_points) > 10 else key_points


if __name__ == "__main__":
    # Teste das funções
    test_text = """# Análise do Projeto XYZ
    
## Resumo Executivo
Este projeto visa implementar um sistema de análise de dados usando IA.

## Pontos Principais
- Integração com APIs externas
- Dashboard interativo
- Processamento em tempo real

## Recomendações
É fundamental melhorar a documentação.
O código precisa de refatoração.
"""
    
    # Testa conversão para markdown
    markdown = to_markdown(test_text)
    print("\n--- MARKDOWN ---")
    print(markdown[:100] + "...")
    
    # Testa conversão para HTML
    html_content = to_html(test_text)
    print("\n--- HTML ---")
    print(html_content[:100] + "...")
    
    # Testa extração de pontos-chave
    key_points = extract_key_points(test_text)
    print("\n--- PONTOS-CHAVE ---")
    for point in key_points:
        print(f"- {point}")
