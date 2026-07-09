import hashlib
from orbit_knowledge.models import Chunk

def create_chunks(
    document_path: str,
    project_name: str,
    content: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200
) -> list[Chunk]:
    """
    Fracciona de forma inteligente el contenido de un archivo en bloques (chunks) estructurados.
    Trabaja a nivel de líneas para no cortar oraciones o sentencias lógicas y rastrea
    el rango de líneas exactas (`start_line` y `end_line`) para cada chunk.
    """
    chunks: list[Chunk] = []
    lines = content.splitlines()
    if not lines:
        return []
        
    current_chunk_lines: list[str] = []
    current_len = 0
    start_line = 1
    chunk_idx = 0
    
    i = 0
    while i < len(lines):
        line = lines[i]
        current_chunk_lines.append(line)
        # Sumar longitud de la línea más el retorno de carro
        current_len += len(line) + 1
        
        # Guardar fragmento al alcanzar el tamaño objetivo o al final del archivo
        if current_len >= chunk_size or i == len(lines) - 1:
            text = "\n".join(current_chunk_lines)
            end_line = i + 1
            chunk_id = f"{document_path}#chunk{chunk_idx}"
            chunk_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
            
            chunks.append(Chunk(
                id=chunk_id,
                document=document_path,
                project=project_name,
                start_line=start_line,
                end_line=end_line,
                text=text,
                hash=chunk_hash
            ))
            chunk_idx += 1
            
            # Calcular cuántas líneas retroceder para satisfacer el solape (chunk_overlap)
            overlap_len = 0
            backtrack_count = 0
            for r_line in reversed(current_chunk_lines):
                overlap_len += len(r_line) + 1
                if overlap_len >= chunk_overlap:
                    break
                backtrack_count += 1
                
            # Establecer el punto de partida del siguiente fragmento
            if backtrack_count > 0 and i < len(lines) - 1:
                i = i - backtrack_count + 1
                start_line = i + 1
            else:
                start_line = i + 2
                
            current_chunk_lines = []
            current_len = 0
        i += 1
        
    return chunks
