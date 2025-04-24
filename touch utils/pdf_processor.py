import os
import logging
import tempfile
import re
from typing import Dict, Any, List, Tuple, Optional, Union
import io
import base64

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    import fitz  # PyMuPDF
except ImportError:
    logger.error("PyMuPDF (fitz) não está instalado. Instale com: pip install pymupdf")

try:
    from openai import OpenAI
except ImportError:
    logger.warning("OpenAI não está disponível. Algumas funcionalidades podem não funcionar.")


def extract_text_from_pdf(file_bytes: Union[bytes, io.BytesIO]) -> Dict[str, Any]:
    """
    Extrai texto e metadados de um arquivo PDF
    
    Args:
        file_bytes: Conteúdo do arquivo PDF em bytes ou BytesIO
        
    Returns:
        Dicionário com texto extraído e metadados
    """
    try:
        logger.info("Iniciando extração de texto do PDF")
        
        # Converte para BytesIO se necessário
        if isinstance(file_bytes, bytes):
            file_stream = io.BytesIO(file_bytes)
        else:
            file_stream = file_bytes
        
        # Abre o documento
        doc = fitz.open(stream=file_stream.read(), filetype="pdf")
        
        # Extrai texto página por página
        full_text = ""
        pages_text = []
        for i, page in enumerate(doc):
            text = page.get_text()
            pages_text.append(text)
            full_text += text + "\n\n"
        
        # Extrai metadados do documento
        metadata = doc.metadata
        if not metadata:
            metadata = {}
        
        # Adiciona informações adicionais
        metadata["page_count"] = len(doc)
        
        # Extrai imagens (opcional)
        images_info = []
        try:
            for page_num, page in enumerate(doc):
                image_list = page.get_images(full=True)
                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    if base_image:
                        images_info.append({
                            "page": page_num + 1,
                            "index": img_index,
                            "width": base_image["width"],
                            "height": base_image["height"],
                            "size": len(base_image["image"])
                        })
        except Exception as e:
            logger.warning(f"Não foi possível extrair informações das imagens: {str(e)}")
        
        # Extrai informações de fontes (opcional)
        fonts = set()
        try:
            for page in doc:
                for font in page.get_fonts():
                    if font[3]:  # Nome da fonte
                        fonts.add(font[3])
        except Exception as e:
            logger.warning(f"Não foi possível extrair informações de fontes: {str(e)}")
        
        # Monta resultado completo
        result = {
            "text": full_text,
            "pages": pages_text,
            "metadata": metadata,
            "images_count": len(images_info),
            "fonts": list(fonts),
            "characters_count": len(full_text),
            "words_count": len(re.findall(r'\w+', full_text))
        }
        
        logger.info(f"Extração concluída: {result['words_count']} palavras em {metadata['page_count']} páginas")
        return result
        
    except Exception as e:
        logger.error(f"Erro ao extrair texto do PDF: {str(e)}")
        return {
            "error": str(e),
            "text": "",
            "pages": [],
            "metadata": {}
        }


def extract_images_from_pdf(file_bytes: Union[bytes, io.BytesIO], max_images: int = 5) -> List[Dict[str, Any]]:
    """
    Extrai imagens de um PDF para visualização
    
    Args:
        file_bytes: Conteúdo do arquivo PDF
        max_images: Número máximo de imagens a extrair
        
    Returns:
        Lista de dicionários com informações das imagens
    """
    try:
        # Converte para BytesIO se necessário
        if isinstance(file_bytes, bytes):
            file_stream = io.BytesIO(file_bytes)
        else:
            file_stream = file_bytes
        
        # Abre o documento
        doc = fitz.open(stream=file_stream.read(), filetype="pdf")
        
        # Lista para armazenar resultados
        images = []
        image_count = 0
        
        # Processamento página por página
        for page_num, page in enumerate(doc):
            image_list = page.get_images(full=True)
            
            for img_index, img in enumerate(image_list):
                if image_count >= max_images:
                    break
                    
                xref = img[0]
                base_image = doc.extract_image(xref)
                
                if base_image:
                    # Converte imagem para base64
                    image_data = base_image["image"]
                    image_ext = base_image["ext"]
                    image_base64 = base64.b64encode(image_data).decode('utf-8')
                    
                    images.append({
                        "page": page_num + 1,
                        "index": img_index,
                        "width": base_image["width"],
                        "height": base_image["height"],
                        "format": image_ext,
                        "base64": f"data:image/{image_ext};base64,{image_base64}"
                    })
                    image_count += 1
            
            if image_count >= max_images:
                break
        
        logger.info(f"Extraídas {len(images)} imagens do PDF")
        return images
        
    except Exception as e:
        logger.error(f"Erro ao extrair imagens do PDF: {str(e)}")
        return []


def extract_table_data(file_bytes: Union[bytes, io.BytesIO]) -> List[Dict[str, Any]]:
    """
    Tenta extrair tabelas do PDF
    
    Args:
        file_bytes: Conteúdo do arquivo PDF
        
    Returns:
        Lista de tabelas extraídas
    """
    try:
        import pandas as pd
        import tabula
        
        # Salva o PDF em um arquivo temporário
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            if isinstance(file_bytes, io.BytesIO):
                tmp.write(file_bytes.getvalue())
            else:
                tmp.write(file_bytes)
            tmp_path = tmp.name
        
        # Extrai tabelas
        tables = tabula.read_pdf(tmp_path, pages='all', multiple_tables=True)
        
        # Remove o arquivo temporário
        os.unlink(tmp_path)
        
        # Converte para formato mais amigável
        result = []
        for i, table in enumerate(tables):
            if not table.empty:
                result.append({
                    "index": i,
                    "rows": len(table),
                    "columns": len(table.columns),
                    "headers": list(table.columns),
                    "data": table.to_dict(orient='records')
                })
        
        logger.info(f"Extraídas {len(result)} tabelas do PDF")
        return result
        
    except Exception as e:
        logger.error(f"Erro ao extrair tabelas: {str(e)}")
        return []


def analyze_pdf_with_ai(content: Dict[str, Any], model: str) -> str:
    """
    Analisa o conteúdo do PDF usando AI
    
    Args:
        content: Dicionário com texto e metadados do PDF
        model: Modelo da OpenAI a ser usado
        
    Returns:
        Análise do conteúdo em formato markdown
    """
    try:
        logger.info(f"Analisando PDF com IA (modelo: {model})")
        
        # Obtém a chave da API
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("API key da OpenAI não disponível")
            return "Não foi possível analisar o documento: Chave da API não disponível."
        
        client = OpenAI(api_key=api_key)
        
        # Prepara texto para análise (limita tamanho para evitar tokens excessivos)
        text = content.get("text", "")
        if len(text) > 8000:
            analysis_text = text[:8000] + "...\n[Texto truncado devido ao tamanho]"
        else:
            analysis_text = text
        
        # Obtém metadados relevantes
        meta = content.get("metadata", {})
        title = meta.get("title", "Documento sem título")
        author = meta.get("author", "Autor desconhecido")
        page_count = meta.get("page_count", 0)
        
        # Constrói o prompt para a IA
        prompt = f"""
        Analise o seguinte documento PDF:
        
        Título: {title}
        Autor: {author}
        Páginas: {page_count}
        
        CONTEÚDO:
        {analysis_text}
        
        Por favor, forneça:
        1. Um resumo executivo do documento (3-4 parágrafos)
        2. Os pontos principais e conceitos-chave abordados
        3. Recomendações práticas ou insights técnicos baseados no conteúdo
        4. Uma conclusão com os próximos passos sugeridos
        
        Use uma formatação clara em markdown, com títulos e listas onde apropriado.
        """
        
        # Faz a chamada para a API
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Você é um analista técnico especializado em extrair insights valiosos de documentos PDF."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        
        # Extrai a resposta
        analysis = response.choices[0].message.content
        
        logger.info(f"Análise concluída: {len(analysis)} caracteres")
        return analysis
        
    except Exception as e:
        logger.error(f"Erro na análise do PDF com IA: {str(e)}")
        return f"Erro ao analisar o documento: {str(e)}"


def process_pdf_complete(file: Union[bytes, io.BytesIO], model: str = "gpt-3.5-turbo") -> Tuple[str, Dict[str, Any]]:
    """
    Função principal para processamento completo de PDFs
    
    Args:
        file: Conteúdo do arquivo PDF (bytes ou BytesIO)
        model: Modelo da OpenAI a ser usado
        
    Returns:
        Tupla (análise formatada, metadados e estatísticas)
    """
    try:
        # Extrai texto e metadados
        content = extract_text_from_pdf(file)
        
        if "error" in content and content["error"]:
            return f"Erro ao processar PDF: {content['error']}", {}
        
        # Analisa com IA
        analysis = analyze_pdf_with_ai(content, model)
        
        # Prepara metadados para retorno
        meta = content.get("metadata", {})
        stats = {
            "title": meta.get("title", "Documento sem título"),
            "author": meta.get("author", "Autor desconhecido"),
            "pages": meta.get("page_count", 0),
            "words": content.get("words_count", 0),
            "characters": content.get("characters_count", 0),
            "images": content.get("images_count", 0),
            "creation_date": meta.get("creationDate", "Data desconhecida"),
            "modification_date": meta.get("modDate", "Data desconhecida")
        }
        
        return analysis, stats
        
    except Exception as e:
        logger.error(f"Erro no processamento completo do PDF: {str(e)}")
        return f"Erro ao processar o documento: {str(e)}", {}


def check_pdf_security(file_bytes: Union[bytes, io.BytesIO]) -> Dict[str, Any]:
    """
    Verifica características de segurança do PDF
    
    Args:
        file_bytes: Conteúdo do arquivo PDF
        
    Returns:
        Dicionário com informações de segurança
    """
    try:
        # Converte para BytesIO se necessário
        if isinstance(file_bytes, bytes):
            file_stream = io.BytesIO(file_bytes)
        else:
            file_stream = file_bytes
        
        # Abre o documento
        doc = fitz.open(stream=file_stream.read(), filetype="pdf")
        
        security = {
            "encrypted": doc.is_encrypted,
            "permissions": None,
            "can_print": None,
            "can_copy": None,
            "can_modify": None,
            "has_password": None
        }
        
        if doc.is_encrypted:
            # Tenta obter informações de permissões
            try:
                security["permissions"] = doc.permissions
                security["can_print"] = doc.permissions & fitz.PDF_PERM_PRINT > 0
                security["can_copy"] = doc.permissions & fitz.PDF_PERM_COPY > 0
                security["can_modify"] = doc.permissions & fitz.PDF_PERM_MODIFY > 0
                security["has_password"] = True
            except:
                security["has_password"] = True
        else:
            security["can_print"] = True
            security["can_copy"] = True
            security["can_modify"] = True
            security["has_password"] = False
        
        return security
        
    except Exception as e:
        logger.error(f"Erro ao verificar segurança do PDF: {str(e)}")
        return {
            "error": str(e),
            "encrypted": None,
            "can_print": None,
            "can_copy": None,
            "can_modify": None,
            "has_password": None
        }


if __name__ == "__main__":
    # Teste simples
    test_file = "sample.pdf"
    if os.path.exists(test_file):
        with open(test_file, "rb") as f:
            pdf_bytes = f.read()
            
        print("Testando processamento de PDF...")
        analysis, stats = process_pdf_complete(pdf_bytes)
        
        print("\n--- ANÁLISE ---")
        print(analysis[:500] + "..." if len(analysis) > 500 else analysis)
        
        print("\n--- ESTATÍSTICAS ---")
        for key, value in stats.items():
            print(f"{key}: {value}")
    else:
        print(f"Arquivo de teste '{test_file}' não encontrado.")
