import math
import time
from orbit_knowledge.config import settings

def calculate_advanced_score(
    bm25_score: float,
    vector_score: float,
    graph_distance: float,
    modified_time: float,
    is_exact_match: bool,
    tag_matches_count: int,
    project_boost: float = 0.0
) -> float:
    """
    Fórmula de scoring híbrida paramétrica configurable:
    Combina BM25, similitud conceptual (vector), distancia en grafo,
    recencia de modificación, coincidencia exacta y tags compartidos.
    Acota los resultados de salida entre 0.01 y 0.99.
    """
    # 1. Normalizar BM25 (asumiendo que puntuaciones mayores a 15 son extremadamente relevantes)
    normalized_bm25 = min(bm25_score / 15.0, 1.0)

    # 2. Recencia de archivo
    age_seconds = max(time.time() - modified_time, 0.0)
    # Decaimiento exponencial con vida media de 30 días
    recency_score = math.exp(-age_seconds / 2592000.0)

    # 3. Exact match
    exact_score = 1.0 if is_exact_match else 0.0

    # 4. Coincidencia de etiquetas
    tag_score = min(tag_matches_count * 0.2, 1.0)

    # 5. Distancia en Grafo de conocimiento
    # Si la distancia es 0 o positiva, la similitud es inversamente proporcional
    if graph_distance >= 0.0:
        graph_score = 1.0 / (1.0 + graph_distance)
    else:
        graph_score = 0.0

    # 6. Suma de pesos paramétricos configurables
    final_score = (
        (normalized_bm25 * settings.RANKING_WEIGHT_BM25) +
        (vector_score * settings.RANKING_WEIGHT_SEMANTIC) +
        (graph_score * settings.RANKING_WEIGHT_GRAPH) +
        (recency_score * settings.RANKING_WEIGHT_RECENCY) +
        (project_boost * settings.RANKING_WEIGHT_PROJECT) +
        (exact_score * settings.RANKING_WEIGHT_EXACT) +
        (tag_score * settings.RANKING_WEIGHT_TAG)
    )

    return min(max(final_score, 0.01), 0.99)
