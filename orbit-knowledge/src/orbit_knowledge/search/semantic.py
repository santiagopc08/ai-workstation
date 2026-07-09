import json
import math
from orbit_knowledge.models import SearchResult
from orbit_knowledge.config import settings
from orbit_knowledge.indexing.storage import SQLiteStorageBackend
from orbit_knowledge.indexing.embeddings import get_embedding_provider

def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Calcula la similitud de coseno entre dos vectores numéricos."""
    if len(v1) != len(v2) or not v1:
        return 0.0
    dot_product = sum(a * b for a, b in zip(v1, v2))
    norm_a = math.sqrt(sum(a * a for a in v1))
    norm_b = math.sqrt(sum(b * b for b in v2))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot_product / (norm_a * norm_b)

def semantic_search(query: str) -> list[SearchResult]:
    """
    Busca coincidencias conceptuales calculando la similitud del coseno
    del embedding de la consulta contra todos los embeddings almacenados en SQLite.
    Emula el comportamiento de indexación y búsqueda semántica de ChromaDB.
    """
    provider = get_embedding_provider()
    try:
        query_vector = provider.generate_embedding(query)
    except Exception:
        return []

    if not query_vector:
        return []

    storage = SQLiteStorageBackend()
    
    # Recuperar todos los vectores guardados en la BD de embeddings
    rows = []
    try:
        with storage._get_connection(storage.embeddings_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT chunk_id, vector_json FROM embeddings")
            rows = cursor.fetchall()
    except Exception:
        return []

    results: list[SearchResult] = []
    for row in rows:
        chunk_id = row["chunk_id"]
        try:
            vector = json.loads(row["vector_json"])
        except Exception:
            continue
            
        similarity = cosine_similarity(query_vector, vector)
        
        # Filtro de similitud básica para evitar ruido (se reduce en modo mock)
        threshold = -1.0 if settings.EMBEDDING_PROVIDER == "mock" else 0.3
        if similarity > threshold:
            results.append(SearchResult(
                file=chunk_id,  # Se retorna el chunk_id como referencia
                line=1,
                text="",
                score=similarity
            ))

    # Ordenar por puntaje decreciente de similitud semántica
    results.sort(key=lambda x: x.score, reverse=True)
    return results[:15]
