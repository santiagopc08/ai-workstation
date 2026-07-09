from typing import Any
from orbit_knowledge.indexing.storage import SQLiteStorageBackend
from orbit_knowledge.providers.filesystem import tree
from orbit_knowledge.cache.lru import LRUCache

# Caché de resúmenes de proyectos
project_summary_cache: LRUCache = LRUCache(32)

def list_projects() -> list[str]:
    """Lista todos los nombres de proyectos actualmente guardados en SQLite."""
    storage = SQLiteStorageBackend()
    docs = storage.list_documents()
    return sorted(list(set(d.project for d in docs)))

def project_documents(project: str) -> list[str]:
    """Lista todas las rutas de documentos relativas pertenecientes al proyecto."""
    storage = SQLiteStorageBackend()
    docs = storage.get_documents_by_project(project)
    return sorted([d.path for d in docs])

def project_summary(project: str) -> str:
    """
    Genera un resumen Markdown consolidado del proyecto.
    Usa caché LRU de alto rendimiento.
    """
    cached = project_summary_cache.get(project)
    if cached is not None:
        return cached

    storage = SQLiteStorageBackend()
    docs = storage.get_documents_by_project(project)
    if not docs:
        return f"El proyecto '{project}' no tiene archivos indexados o no existe."

    summary = f"# Resumen del Proyecto: {project}\n\n"
    summary += f"- **Cantidad de archivos indexados:** {len(docs)}\n"
    summary += f"- **Tamaño consolidado:** {sum(d.size for d in docs)} bytes\n\n"

    # Buscar README
    readme = None
    for d in docs:
        if "readme" in d.path.lower():
            readme = d
            break
            
    if readme:
        summary += f"## Descripción General (de {readme.path}):\n"
        summary += f"{readme.summary}\n\n"
    else:
        summary += "## Descripción General:\n"
        summary += f"{docs[0].summary}\n\n"

    summary += "## Documentos Principales:\n"
    for d in docs[:15]:
        summary += f"- **{d.title}** (`{d.path}`): {d.summary[:120]}...\n"

    if len(docs) > 15:
        summary += f"- ... y {len(docs) - 15} archivos adicionales.\n"

    project_summary_cache.set(project, summary)
    return summary

def project_tree(project: str) -> str:
    """Genera la estructura ASCII de los archivos del proyecto."""
    return tree(project)

def project_metadata(project: str) -> dict[str, Any]:
    """Devuelve metadatos consolidados del proyecto, incluyendo métricas del Grafo de Conocimiento."""
    storage = SQLiteStorageBackend()
    docs = storage.get_documents_by_project(project)
    
    extensions = sorted(list(set(d.extension for d in docs)))
    tags: list[str] = []
    for d in docs:
        tags.extend(d.tags)

    doc_ids = [f"doc:{d.path}" for d in docs]
    
    # Métricas del Grafo
    graph_technologies: list[str] = []
    graph_connections_count = 0

    if doc_ids:
        with storage._get_connection(storage.index_db) as conn:
            cursor = conn.cursor()
            placeholders = ",".join("?" for _ in doc_ids)
            
            # 1. Extraer tecnologías asociadas a este proyecto en el Grafo
            cursor.execute(f"""
                SELECT DISTINCT target 
                FROM edges 
                WHERE source IN ({placeholders}) AND relation = 'USES' AND target LIKE 'tech:%'
            """, doc_ids)
            graph_technologies = sorted([r["target"].replace("tech:", "") for r in cursor.fetchall()])

            # 2. Contar aristas totales conectadas a archivos de este proyecto
            cursor.execute(f"""
                SELECT COUNT(*) 
                FROM edges 
                WHERE source IN ({placeholders}) OR target IN ({placeholders})
            """, doc_ids + doc_ids)
            graph_connections_count = cursor.fetchone()[0]

    return {
        "project": project,
        "files_count": len(docs),
        "extensions_used": extensions,
        "top_tags": sorted(list(set(tags)))[:20],
        "size_bytes": sum(d.size for d in docs),
        "graph_technologies": graph_technologies,
        "graph_connections_count": graph_connections_count
    }
