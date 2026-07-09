import re
from typing import Any

def extract_markdown_metadata(content: str) -> dict[str, Any]:
    """
    Parsea de manera nativa y rápida el contenido Markdown para extraer metadatos estructurados.
    Detecta H1-H6, enlaces, imágenes, tablas y bloques de código.
    """
    title = ""
    headings: list[str] = []
    code_blocks: list[str] = []
    links: list[str] = []
    images: list[str] = []
    tables_count = 0
    
    lines = content.splitlines()
    in_code_block = False
    
    for line in lines:
        stripped = line.strip()
        
        # Bloques de código
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            if in_code_block:
                lang = stripped[3:].strip()
                if lang:
                    code_blocks.append(lang)
            continue
            
        if in_code_block:
            continue
            
        # Encabezados (H1-H6)
        if stripped.startswith("#"):
            match = re.match(r"^(#{1,6})\s+(.*)$", stripped)
            if match:
                level = len(match.group(1))
                text = match.group(2).strip()
                headings.append(f"H{level}: {text}")
                if level == 1 and not title:
                    title = text
                    
        # Imágenes: ![caption](url)
        for img_match in re.finditer(r"!\[(.*?)\]\((.*?)\)", line):
            caption = img_match.group(1) or img_match.group(2)
            images.append(caption)
            
        # Enlaces: [text](url) - Removiendo primero imágenes para evitar falsos positivos
        line_no_images = re.sub(r"!\[.*?\]\(.*?\)", "", line)
        for link_match in re.finditer(r"\[(.*?)\]\((.*?)\)", line_no_images):
            label = link_match.group(1) or link_match.group(2)
            links.append(label)
            
        # Tablas: detectar separadores de tablas en Markdown
        if stripped.startswith("|") and stripped.endswith("|") and "-" in stripped:
            tables_count += 1
            
    return {
        "title": title or "Documento sin Título",
        "headings": headings,
        "code_blocks": code_blocks,
        "links": links,
        "images": images,
        "tables_count": tables_count
    }
