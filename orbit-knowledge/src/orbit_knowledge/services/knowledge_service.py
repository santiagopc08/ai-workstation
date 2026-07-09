import logging
from pathlib import Path
from orbit_knowledge.models import SearchResult
from orbit_knowledge.indexing.storage import SQLiteStorageBackend
from orbit_knowledge.providers.filesystem import resolve_path, safe_read
from orbit_knowledge.planner.query_planner import plan_query
from orbit_knowledge.fingerprints.simhash import hamming_distance
import orbit_knowledge.search.content as search_content_module

logger = logging.getLogger("orbit_knowledge")

def find_document(name: str) -> list[str]:
    """
    Busca documentos cuyo nombre de archivo coincida parcialmente (case-insensitive).
    """
    if not name:
        return []
        
    name_lower = name.lower()
    storage = SQLiteStorageBackend()
    docs = storage.list_documents()
    return sorted([
        d.path for d in docs if name_lower in Path(d.path).name.lower()
    ])

def search_documentation(query: str) -> list[SearchResult]:
    """
    Realiza una búsqueda híbrida utilizando planificación de consultas para enrutamiento.
    """
    plan = plan_query(query)
    logger.info(f"Planificador de Consultas seleccionó estrategia: {plan.strategy} ({plan.reason})")
    
    # El motor híbrido se encarga de ponderar y combinar todas las dimensiones
    return search_content_module.search_content(query)

def detect_near_duplicates(path: str) -> list[str]:
    """
    Analiza la base de datos de huellas digitales de SimHash para detectar archivos
    casi duplicados (Hamming distance <= 3).
    """
    storage = SQLiteStorageBackend()
    target_sh = storage.get_fingerprint(path)
    if not target_sh:
        return []

    all_fps = storage.list_fingerprints()
    duplicates: list[str] = []
    
    for other_path, other_sh in all_fps.items():
        if other_path == path:
            continue
        if hamming_distance(target_sh, other_sh) <= 3:
            duplicates.append(other_path)

    return duplicates

def summarize_document(path: str) -> str:
    """
    Genera un resumen estructurado del documento especificado,
    añadiendo alertas si existen duplicados o copias redundantes en el sistema.
    """
    storage = SQLiteStorageBackend()
    doc = storage.get_document(path)
    duplicates = detect_near_duplicates(path)
    
    dup_warning = ""
    if duplicates:
        dup_warning = "\n\n> [!WARNING]  \n> **Posibles duplicados o documentación redundante detectada:**  \n" + \
                      "\n".join([f"> - `{d}`" for d in duplicates]) + "\n"

    if doc and doc.summary:
        return (
            f"# Resumen de {doc.title}\n\n"
            f"**Ubicación:** `{path}`  \n"
            f"**Tamaño:** {doc.size} bytes  \n"
            f"**Etiquetas:** {', '.join(doc.tags)}  \n\n"
            f"## Resumen Extractor:\n"
            f"{doc.summary}"
            f"{dup_warning}"
        )

    # Fallback si no está indexado en la BD
    resolved_file = resolve_path(path)
    content = safe_read(resolved_file)
    summary_text = content[:500].strip() + "..." if len(content) > 500 else content
    return f"# Resumen de {resolved_file.name}\n\n{summary_text}{dup_warning}"

def related_documents(path: str) -> list[str]:
    """
    Busca documentos relacionados basados en etiquetas y vecindad de grafo.
    """
    storage = SQLiteStorageBackend()
    target_doc = storage.get_document(path)
    if not target_doc:
        return []

    target_tags = set(target_doc.tags)
    if not target_tags:
        return []

    docs = storage.list_documents()
    related_list: list[tuple[str, int]] = []
    
    for d in docs:
        if d.path == path:
            continue
        file_tags = set(d.tags)
        common_tags = target_tags.intersection(file_tags)
        if common_tags:
            related_list.append((d.path, len(common_tags)))

    related_list.sort(key=lambda x: x[1], reverse=True)
    return [r[0] for r in related_list[:5]]
