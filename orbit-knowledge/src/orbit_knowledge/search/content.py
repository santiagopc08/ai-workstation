import re
from typing import Optional
from orbit_knowledge.models import SearchResult
from orbit_knowledge.indexing.storage import SQLiteStorageBackend
from orbit_knowledge.search.ranking import BM25
from orbit_knowledge.ranking.engine import calculate_advanced_score
from orbit_knowledge.graph.engine import KnowledgeGraphEngine
from orbit_knowledge.search.semantic import semantic_search
from orbit_knowledge.config import settings

def search_content(query: str, project_filter: Optional[str] = None) -> list[SearchResult]:
    """
    Realiza una búsqueda avanzada híbrida combinando BM25, similitud conceptual (embeddings),
    distancia en el Grafo de Conocimiento, recencia, coincidencia exacta y tags compartidos.
    """
    if not query:
        return []

    storage = SQLiteStorageBackend()
    chunks = storage.get_all_chunks()
    
    if not chunks:
        # Pre-indexación en caliente
        from orbit_knowledge.indexing.builder import IndexBuilder
        builder = IndexBuilder(storage)
        builder.incremental_scan()
        chunks = storage.get_all_chunks()
        if not chunks:
            return []

    if project_filter:
        chunks = [c for c in chunks if c.project == project_filter]

    if not chunks:
        return []

    # 1. Modelo BM25
    corpus = [c.text for c in chunks]
    bm25 = BM25(corpus)
    query_tokens = re.findall(r"\w+", query.lower())

    # 2. Búsqueda vectorial
    vector_scores: dict[str, float] = {}
    try:
        semantic_results = semantic_search(query)
        for r in semantic_results:
            vector_scores[r.file] = r.score
    except Exception:
        pass

    # 3. Inicializar motor de Grafo para calcular distancias relacionales
    graph_eng = KnowledgeGraphEngine(storage)

    results: list[SearchResult] = []

    for idx, chunk in enumerate(chunks):
        bm_score = bm25.score(query_tokens, idx)
        vec_score = vector_scores.get(chunk.id, 0.0)

        # Omitir fragmentos sin relevancia léxica ni semántica
        if bm_score <= 0.0 and vec_score <= 0.0:
            continue

        doc = storage.get_document(chunk.document)
        if not doc:
            continue

        # Distancia en el Grafo
        # Buscamos la distancia mínima del documento del chunk al término buscado
        # (Si está directamente conectado, distancia = 1.0; indirecto = 2.0+; inconexo = -1.0)
        graph_dist = graph_eng.calculate_graph_distance(chunk.document, query)

        # Coincidencia exacta de la consulta en el fragmento
        is_exact = query.lower() in chunk.text.lower()

        # Intersección de etiquetas
        tag_matches = len(set(query_tokens).intersection(doc.tags))

        # Project boost
        proj_boost = 0.1 if project_filter and chunk.project == project_filter else 0.0

        # Calcular Score Avanzado Paramétrico
        final_rank = calculate_advanced_score(
            bm25_score=bm_score,
            vector_score=vec_score,
            graph_distance=graph_dist,
            modified_time=doc.modified,
            is_exact_match=is_exact,
            tag_matches_count=tag_matches,
            project_boost=proj_boost
        )

        # Extraer snippet de línea
        snippet = chunk.text
        for line in chunk.text.splitlines():
            if query.lower() in line.lower():
                snippet = line.strip()
                break

        results.append(SearchResult(
            file=chunk.document,
            line=chunk.start_line,
            text=snippet,
            score=final_rank
        ))

    # Ordenar por puntaje híbrido decreciente
    results.sort(key=lambda x: x.score, reverse=True)
    return results[:settings.MAX_RESULTS]
