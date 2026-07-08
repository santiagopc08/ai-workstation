# ROADMAP.md - ORBIT Knowledge Engine Roadmap

Este documento detalla el plan de evolución del **ORBIT Knowledge Engine** y su integración en el ecosistema de IA local ORBIT en macOS.

---

## Estado Actual (v2.0)
- **Desacoplamiento Completo:** La capa MCP solo actúa como transporte. Toda la lógica del sistema reside en servicios.
- **Indexación Incremental:** Implementación de `knowledge.index` con verificación de hashes SHA256 para evitar lecturas de disco redundantes.
- **Metadata Parsers:** Extracción estructurada para Markdown, Python, JSON y Docker Compose.
- **Seguridad Robustecida:** Validación exhaustiva contra Path Traversal, symlink escapes y blacklist de secretos.
- **Watcher Integrado:** Monitoreo en segundo plano por sondeo para sincronizar archivos individuales.

---

## Fase 1: Integración con ChromaDB (`orbit-indexer`)
El siguiente componente que consumirá este motor de conocimiento será **`orbit-indexer`**. 

```text
+-----------------------------+
|    orbit-knowledge MCP      | (Única fuente de verdad de archivos)
+--------------+--------------+
               |
               v (Lee Chunks e Index)
+--------------+--------------+
|       orbit-indexer         | (Genera Embeddings localmente vía Ollama/LM Studio)
+--------------+--------------+
               |
               v (Sincroniza)
+--------------+--------------+
|         ChromaDB            | (Base de datos vectorial local)
+-----------------------------+
```

### Hitos de la Fase 1:
- Desarrollo de un microservicio `orbit-indexer` que lea los fragmentos (`chunks`) de `orbit-knowledge`.
- Integración de embeddings vectoriales locales mediante modelos de embedding ligeros ejecutados en LM Studio u Ollama (ej: `nomic-embed-text` o `bge-large-es`).
- Carga y sincronización periódica en la base de datos de ChromaDB (corriendo en el contenedor Docker local en el puerto 8000).

---

## Fase 2: Búsqueda Semántica Híbrida
- Reemplazar el mock de `search/semantic.py` con una consulta a la base de datos de ChromaDB.
- Implementar algoritmos de búsqueda híbrida combinando:
  - **Búsqueda Léxica (BM25):** Para nombres de archivo y coincidencias exactas de términos de código.
  - **Búsqueda Semántica (Vectores):** Para preguntas conceptuales o consultas en lenguaje natural formuladas en Open WebUI.
  - **Recalificación (Reranking):** Combinación de scores léxicos y semánticos utilizando un modelo cross-encoder local.

---

## Fase 3: Watcher Reactivo del Kernel
- Opcionalmente reemplazar el bucle de sondeo (polling watcher) por un watcher reactivo que consuma las APIs de `FSEvents` de macOS (mediante ctypes o librerías nativas) para eliminar el intervalo de 5 segundos y reaccionar de forma instantánea a nivel del kernel de Apple Silicon.

---

## Fase 4: Integración del Ecosistema de Agentes ORBIT
- Permitir que el resto de servidores MCP de ORBIT (Git, Docker, System) utilicen `orbit-knowledge` como único canal para buscar y comprender el contexto del repositorio antes de proponer cambios, reduciendo el tamaño del contexto inyectado y mejorando la precisión de la IA.
