# ORBIT Knowledge Architecture

ORBIT Knowledge Engine es la capa de gestión de conocimiento semántico y relaciones en grafo integrada en ORBIT.

## Diagrama de Arquitectura de Datos

```text
                   Open WebUI
                        │
                        ▼
               ORBIT Knowledge MCP
                        │
            ┌───────────┴───────────┐
            ▼                       ▼
     Knowledge Index          ChromaDB
            ▲                       ▲
            │                       │
        ORBIT Indexer ──────────────┘
            ▲
            │
      Filesystem Watcher
            ▲
            │
      Knowledge/
```

## Componentes Clave

1. **Query Planner (`knowledge/planner`)**: Determina el modo óptimo de responder a una consulta mediante enrutamiento inteligente (estrategias `HYBRID`, `GRAPH`, `READ_FILE`, `MULTI_STAGE`).
2. **Hybrid Search & Ranking (`knowledge/ranking`)**: Recuperación unificada combinando relevancia léxica (BM25) y semántica (Embeddings vectoriales de ChromaDB) con pesos dinámicos.
3. **Knowledge Graph (`knowledge/graph`)**: Representación de dependencias del proyecto, arquitecturas de software y relaciones conceptuales mediante nodos y aristas persistidos en SQLite.
4. **Automatic Tagging (`knowledge/tagging`)**: Motor basado en reglas para inferir tecnologías y categorías a partir de extensiones y patrones de código.
5. **Fingerprinting (`knowledge/fingerprints`)**: Generación de hashes SimHash y distancias Hamming para detección de duplicación incremental.
