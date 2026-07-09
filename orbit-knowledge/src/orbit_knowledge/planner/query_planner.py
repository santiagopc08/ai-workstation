import json
import logging

logger = logging.getLogger("orbit_knowledge")

class QueryPlan:
    """Representa el plan de ejecución y enrutado de una consulta."""
    def __init__(self, strategy: str, reason: str) -> None:
        self.strategy = strategy
        self.reason = reason

    def to_dict(self) -> dict[str, str]:
        return {
            "strategy": self.strategy,
            "reason": self.reason
        }

def plan_query(query: str) -> QueryPlan:
    """
    Analiza la consulta sin consumir APIs de Inteligencia Artificial para determinar
    el motor de búsqueda óptimo: READ_FILE, GRAPH, BM25, MULTI_STAGE o HYBRID.
    """
    query_lower = query.lower().strip()

    # 1. READ_FILE
    if query_lower.startswith("read ") or query_lower.startswith("cat ") or (query_lower.endswith(".md") or query_lower.endswith(".py")):
        plan = QueryPlan("READ_FILE", "La consulta coincide con lectura de un archivo o comando explícito.")
    # 2. GRAPH
    elif any(w in query_lower for w in ["depends", "imports", "uses", "references", "relations", "graph", "architecture", "stack", "servicios", "relacion", "depend", "arquitect", "import", "grafo", "config"]):
        plan = QueryPlan("GRAPH", "La consulta involucra dependencias, arquitectura o relaciones en el grafo.")

    # 3. BM25 (Búsqueda léxica directa para códigos puntuales)
    elif len(query_lower.split()) <= 2 and any(t in query_lower for t in ["class", "def", "function", "todo", "error"]):
        plan = QueryPlan("BM25", "Búsqueda léxica puntual orientada a código de programación.")
    # 4. MULTI_STAGE (Preguntas largas)
    elif len(query_lower.split()) > 10 or "?" in query_lower:
        plan = QueryPlan("MULTI_STAGE", "La consulta representa una frase larga/pregunta conceptual en lenguaje natural.")
    # 5. HYBRID (Caso general por defecto)
    else:
        plan = QueryPlan("HYBRID", "Estrategia por defecto combinando similitud conceptual y concordancia de palabras.")

    # Registro de la decisión en el log JSON estructurado
    log_entry = {
        "event": "query_planning_decision",
        "query": query,
        "strategy": plan.strategy,
        "reason": plan.reason
    }
    logger.info(json.dumps(log_entry))

    return plan
