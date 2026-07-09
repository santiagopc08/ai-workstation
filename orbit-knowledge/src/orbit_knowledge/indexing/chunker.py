import ast
import hashlib
import json
import re
from pathlib import Path
from orbit_knowledge.models import Chunk

def chunk_markdown(document: str, project: str, content: str, chunk_size: int) -> list[Chunk]:
    """
    Fracciona un archivo Markdown semánticamente por títulos H2 y H3.
    Si una sección supera el tamaño máximo, se fragmenta por párrafos.
    """
    chunks: list[Chunk] = []
    lines = content.splitlines()
    
    def get_lines_range(subtext: str) -> tuple[int, int]:
        sublines = subtext.strip().splitlines()
        if not sublines:
            return 1, 1
        first_line = sublines[0].strip()
        last_line = sublines[-1].strip()
        
        start = 1
        end = 1
        for idx, line in enumerate(lines, 1):
            if first_line in line:
                start = idx
                break
        for idx, line in enumerate(lines, start):
            if last_line in line:
                end = idx
        return start, end

    # Separar por títulos H2
    h2_sections = re.split(r"(^##\s+.*$)", content, flags=re.MULTILINE)
    sections: list[tuple[str, str]] = []
    
    if h2_sections[0].strip():
        sections.append(("", h2_sections[0]))
        
    i = 1
    while i < len(h2_sections):
        heading = h2_sections[i]
        body = h2_sections[i+1] if i + 1 < len(h2_sections) else ""
        sections.append((heading, body))
        i += 2

    chunk_idx = 0
    for heading, body in sections:
        section_text = f"{heading}\n{body}".strip()
        
        if len(section_text) <= chunk_size:
            start, end = get_lines_range(section_text)
            chunks.append(Chunk(
                id=f"{document}#chunk{chunk_idx}",
                document=document,
                project=project,
                section=heading or "Intro",
                title=heading.strip("# ").strip() if heading else "Intro",
                start_line=start,
                end_line=end,
                text=section_text,
                hash=hashlib.sha256(section_text.encode("utf-8")).hexdigest()
            ))
            chunk_idx += 1
        else:
            # Dividir por títulos H3
            h3_sections = re.split(r"(^###\s+.*$)", section_text, flags=re.MULTILINE)
            h3_blocks: list[tuple[str, str]] = []
            if h3_sections[0].strip():
                h3_blocks.append((heading or "Header", h3_sections[0]))
            
            idx = 1
            while idx < len(h3_sections):
                h3_heading = h3_sections[idx]
                h3_body = h3_sections[idx+1] if idx + 1 < len(h3_sections) else ""
                h3_blocks.append((h3_heading, h3_body))
                idx += 2
                
            for h3_head, h3_body in h3_blocks:
                h3_text = f"{h3_head}\n{h3_body}".strip()
                if len(h3_text) <= chunk_size:
                    start, end = get_lines_range(h3_text)
                    chunks.append(Chunk(
                        id=f"{document}#chunk{chunk_idx}",
                        document=document,
                        project=project,
                        section=h3_head or heading or "Header",
                        title=h3_head.strip("# ").strip() if h3_head else "Sub-section",
                        start_line=start,
                        end_line=end,
                        text=h3_text,
                        hash=hashlib.sha256(h3_text.encode("utf-8")).hexdigest()
                    ))
                    chunk_idx += 1
                else:
                    # Dividir por párrafos (\n\n)
                    paragraphs = h3_text.split("\n\n")
                    for p in paragraphs:
                        p_stripped = p.strip()
                        if not p_stripped:
                            continue
                        # Si el párrafo sigue superando el tamaño, segmentar a nivel caracteres
                        if len(p_stripped) > chunk_size:
                            sub_chunks = [p_stripped[k:k+chunk_size] for k in range(0, len(p_stripped), max(chunk_size - 100, 1))]
                            for sc in sub_chunks:
                                start, end = get_lines_range(sc)
                                chunks.append(Chunk(
                                    id=f"{document}#chunk{chunk_idx}",
                                    document=document,
                                    project=project,
                                    section=h3_head or heading or "Header",
                                    title="Párrafo Largo",
                                    start_line=start,
                                    end_line=end,
                                    text=sc,
                                    hash=hashlib.sha256(sc.encode("utf-8")).hexdigest()
                                ))
                                chunk_idx += 1
                        else:
                            start, end = get_lines_range(p_stripped)
                            chunks.append(Chunk(
                                id=f"{document}#chunk{chunk_idx}",
                                document=document,
                                project=project,
                                section=h3_head or heading or "Header",
                                title="Párrafo",
                                start_line=start,
                                end_line=end,
                                text=p_stripped,
                                hash=hashlib.sha256(p_stripped.encode("utf-8")).hexdigest()
                            ))
                            chunk_idx += 1
                            
    return chunks

def chunk_python(document: str, project: str, content: str) -> list[Chunk]:
    """
    Fracciona código Python por bloques semánticos de clases y funciones/métodos del AST.
    """
    chunks: list[Chunk] = []
    lines = content.splitlines()
    chunk_idx = 0
    
    try:
        tree = ast.parse(content)
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                start_line = node.lineno
                end_line = getattr(node, "end_lineno", start_line + len(node.body))
                class_lines = lines[start_line - 1:end_line]
                class_text = "\n".join(class_lines)
                
                chunks.append(Chunk(
                    id=f"{document}#chunk{chunk_idx}",
                    document=document,
                    project=project,
                    section="Clase",
                    title=f"class {node.name}",
                    start_line=start_line,
                    end_line=end_line,
                    text=class_text,
                    hash=hashlib.sha256(class_text.encode("utf-8")).hexdigest()
                ))
                chunk_idx += 1
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                start_line = node.lineno
                end_line = getattr(node, "end_lineno", start_line + len(node.body))
                func_lines = lines[start_line - 1:end_line]
                func_text = "\n".join(func_lines)
                
                chunks.append(Chunk(
                    id=f"{document}#chunk{chunk_idx}",
                    document=document,
                    project=project,
                    section="Función",
                    title=f"def {node.name}",
                    start_line=start_line,
                    end_line=end_line,
                    text=func_text,
                    hash=hashlib.sha256(func_text.encode("utf-8")).hexdigest()
                ))
                chunk_idx += 1
    except Exception:
        pass
        
    if not chunks:
        # Fallback si falla el parseo sintáctico (ej. archivos con errores de sintaxis)
        chunks = chunk_text_generic(document, project, content, 1500)
        
    return chunks

def chunk_json(document: str, project: str, content: str) -> list[Chunk]:
    """
    Fracciona archivos JSON dividiéndolos en sub-objetos de primer nivel.
    """
    chunks: list[Chunk] = []
    chunk_idx = 0
    
    try:
        data = json.loads(content)
        if isinstance(data, dict):
            for k, v in data.items():
                chunk_text = json.dumps({k: v}, indent=2, ensure_ascii=False)
                chunks.append(Chunk(
                    id=f"{document}#chunk{chunk_idx}",
                    document=document,
                    project=project,
                    section="JSON Key",
                    title=f"Key: {k}",
                    start_line=1,
                    end_line=1,
                    text=chunk_text,
                    hash=hashlib.sha256(chunk_text.encode("utf-8")).hexdigest()
                ))
                chunk_idx += 1
        elif isinstance(data, list):
            for idx, item in enumerate(data):
                chunk_text = json.dumps(item, indent=2, ensure_ascii=False)
                chunks.append(Chunk(
                    id=f"{document}#chunk{chunk_idx}",
                    document=document,
                    project=project,
                    section="JSON Array Index",
                    title=f"Index: {idx}",
                    start_line=1,
                    end_line=1,
                    text=chunk_text,
                    hash=hashlib.sha256(chunk_text.encode("utf-8")).hexdigest()
                ))
                chunk_idx += 1
    except Exception:
        pass
        
    if not chunks:
        chunks.append(Chunk(
            id=f"{document}#chunk{chunk_idx}",
            document=document,
            project=project,
            section="JSON Raw",
            title="Raw Content",
            start_line=1,
            end_line=1,
            text=content,
            hash=hashlib.sha256(content.encode("utf-8")).hexdigest()
        ))
        
    return chunks

def chunk_text_generic(document: str, project: str, content: str, chunk_size: int) -> list[Chunk]:
    """
    Fraccionador de texto plano genérico sensible a párrafos e intervalos de línea.
    """
    chunks: list[Chunk] = []
    lines = content.splitlines()
    
    def get_lines_range(subtext: str) -> tuple[int, int]:
        sublines = subtext.strip().splitlines()
        if not sublines:
            return 1, 1
        first_line = sublines[0].strip()
        last_line = sublines[-1].strip()
        
        start = 1
        end = 1
        for idx, line in enumerate(lines, 1):
            if first_line in line:
                start = idx
                break
        for idx, line in enumerate(lines, start):
            if last_line in line:
                end = idx
        return start, end

    paragraphs = content.split("\n\n")
    chunk_idx = 0
    current_paragraphs: list[str] = []
    current_len = 0
    
    for p in paragraphs:
        p_stripped = p.strip()
        if not p_stripped:
            continue
        current_paragraphs.append(p_stripped)
        current_len += len(p_stripped) + 2
        
        if current_len >= chunk_size:
            text = "\n\n".join(current_paragraphs)
            start, end = get_lines_range(text)
            chunks.append(Chunk(
                id=f"{document}#chunk{chunk_idx}",
                document=document,
                project=project,
                section="Texto",
                title=f"Bloque {chunk_idx}",
                start_line=start,
                end_line=end,
                text=text,
                hash=hashlib.sha256(text.encode("utf-8")).hexdigest()
            ))
            chunk_idx += 1
            current_paragraphs = []
            current_len = 0
            
    if current_paragraphs:
        text = "\n\n".join(current_paragraphs)
        start, end = get_lines_range(text)
        chunks.append(Chunk(
            id=f"{document}#chunk{chunk_idx}",
            document=document,
            project=project,
            section="Texto",
            title=f"Bloque {chunk_idx}",
            start_line=start,
            end_line=end,
            text=text,
            hash=hashlib.sha256(text.encode("utf-8")).hexdigest()
        ))
        
    return chunks

def chunk_document(path: str, project: str, content: str, chunk_size: int) -> list[Chunk]:
    """
    Despachador que selecciona el motor de fraccionamiento semántico basado
    en la extensión del archivo.
    """
    ext = Path(path).suffix.lower()
    if ext == ".md":
        return chunk_markdown(path, project, content, chunk_size)
    elif ext == ".py":
        return chunk_python(path, project, content)
    elif ext in (".json", ".jsonld"):
        return chunk_json(path, project, content)
    else:
        return chunk_text_generic(path, project, content, chunk_size)
