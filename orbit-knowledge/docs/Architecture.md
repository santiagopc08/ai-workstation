# ARCHITECTURE.md - ORBIT Knowledge Engine

Este documento detalla el diseño de software y la arquitectura modular del **ORBIT Knowledge Engine v2.0** (`orbit-knowledge`).

---

## 1. Diseño Arquitectónico

ORBIT Knowledge Engine evoluciona de un simple MCP de lectura de archivos a un motor de conocimiento semántico e indexación incremental desacoplado. Su objetivo principal es actuar como la única fuente de verdad documental para el resto de agentes y microservicios de ORBIT.

El sistema se compone de capas estrictamente desacopladas para garantizar el mantenimiento de estado en memoria y prevenir el cuello de botella de E/S de disco.

```text
                               +-----------------------------+
                               |        mcp/server.py        | (Protocol Lifecyle & Entry)
                               +--------------+--------------+
                                              |
                       +----------------------+----------------------+
                       |                                             |
                       v                                             v
         +-------------+-------------+                 +-------------+-------------+
         |     mcp/tools.py          |                 |     mcp/resources.py      | (MCP Wrappers)
         +-------------+-------------+                 +-------------+-------------+
                       |                                             |
                       +----------------------+----------------------+
                                              |
                                              v
                              +---------------+---------------+
                              |       services/               | (Service Decoupling Layer)
                              |  - project_service.py         |
                              |  - knowledge_service.py       |
                              +---------------+---------------+
                                              |
                       +----------------------+----------------------+
                       |                                             |
                       v                                             v
         +-------------+-------------+                 +-------------+-------------+
         |        search/            |                 |        indexing/          | (Core Engine)
         |  - content.py (Scored)    |                 |  - index.py (Incremental) |
         |  - filename.py (Cached)   |                 |  - metadata.py (Parsers)  |
         |  - semantic.py (Chroma)   |                 |  - chunking.py (Lines)    |
         +-------------+-------------+                 +-------------+-------------+
                       |                                             |
                       +----------------------+----------------------+
                                              |
                                              v
                              +---------------+---------------+
                              |         cache/ & providers/   | (E/S & Cache Layer)
                              |  - lru.py                     |
                              |  - index_cache.py             |
                              |  - filesystem.py              |
                              +---------------+---------------+
                                              |
                                              v
                                   [Knowledge directory]
```

---

## 2. Descripción de Componentes

### 2.1 Capa de Proveedores y Caché (`providers/` & `cache/`)
- **`providers/filesystem.py`:** Aísla el acceso al sistema de archivos local en macOS. Se encarga de verificar la lista negra de seguridad (blacklist) y prevenir ataques de Path Traversal resolviendo rutas absolutas mediante `.resolve()`.
- **`cache/lru.py`:** Proporciona una implementación genérica y thread-safe de Caché LRU para agilizar las lecturas repetidas de archivos.
- **`cache/index_cache.py`:** Almacena el árbol estructurado del archivo `knowledge.index` en memoria RAM para responder a consultas de búsqueda instantáneamente con costo de E/S cero.

### 2.2 Capa de Indexación (`indexing/`)
- **`indexing/hashing.py`:** Calcula SHA256 para cada documento para verificar si el contenido cambió antes de re-indexar (indexado incremental).
- **`indexing/metadata.py`:** Parsers especializados para extraer metadatos de Markdown (H1-H3, enlaces, tablas, código), Python (clases, funciones, importaciones vía AST), JSON (esquemas) y Docker Compose (servicios, puertos).
- **`indexing/chunking.py`:** Fragmenta textos en bloques con solape. Es sensible al salto de línea, asegurando que las sentencias y párrafos no se dividan por la mitad.
- **`indexing/index.py`:** Orquesta la carga, compilación incremental y guardado del archivo unificado `knowledge.index`.

### 2.3 Capa de Búsqueda y Clasificación (`search/`)
- **`search/ranking.py`:** Evalúa y puntúa la relevancia de los resultados de búsqueda. Asigna un score de `0.01` a `0.99` combinando:
  - Coincidencia en nombre de archivo (peso de hasta +0.6).
  - Coincidencia en encabezados jerárquicos (peso de hasta +0.2).
  - Densidad del término de búsqueda en la línea y posición exacta.
- **`search/semantic.py`:** Mock arquitectónico diseñado para integrarse directamente con embeddings vectoriales y ChromaDB en la próxima fase (`orbit-indexer`).

### 2.4 Capa de Servicios (`services/`)
- Desacopla la lógica de negocio de los decoradores y el protocolo de red de MCP.
- **`services/project_service.py`:** Administra consultas agregadas de proyectos (`list_projects`, `project_summary`, `project_tree`).
- **`services/knowledge_service.py`:** Administra la localización de documentos, resúmenes y relaciones asociativas (`related_documents`) basadas en la coincidencia de etiquetas (tags).

### 2.5 Monitoreo (`watchers/`)
- **`watchers/filesystem_watcher.py`:** Hilo daemon de sondeo que detecta eventos de creación, modificación o borrado de archivos cada 5 segundos y actualiza únicamente el archivo alterado en el índice en tiempo real, logrando sincronización instantánea sin reconstrucción masiva.
