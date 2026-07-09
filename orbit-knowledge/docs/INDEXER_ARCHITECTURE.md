# INDEXER_ARCHITECTURE.md - ORBIT Indexer Engine Architecture

Este documento detalla la arquitectura de procesamiento asíncrono, flujo de eventos y concurrencia del **ORBIT Indexer Engine v1.0**.

---

## 1. Flujo de Datos Event-Driven

El indexador de ORBIT utiliza una arquitectura reactiva basada en un bus de eventos en memoria (`EventBus`). Ningún proceso de indexación se realiza directamente; en su lugar, se delega a trabajos desacoplados.

```text
                  [Sistema de Archivos]
                           │
                           ▼
                    PollingWatcher
                           │
                  (Emite Eventos)
                           │
                           v
  [DocumentCreated] [DocumentUpdated] [DocumentDeleted]
                           │
                           ▼
                        EventBus
                           │
                  (Enruta a la Cola)
                           │
                           ▼
                        JobQueue
                           │
                  (Workers de Hilos)
                           │
                           ▼
                      IndexBuilder
                           │
            ┌──────────────┼──────────────┐
            ▼              ▼              ▼
       [knowledge.db]  [index.db]  [embeddings.db]
```

---

## 2. Cola de Trabajos y Pool de Hilos (Queue & Workers)

Para evitar bloqueos del servidor MCP principal y picos de uso en la CPU de Apple Silicon:
- **`JobQueue`:** Cola de prioridad hilo-segura (`queue.Queue`) que recibe instancias de `IndexingJob` ("index", "remove", "refresh").
- **Hilos Daemon:** El sistema levanta por defecto `WORKERS=2` daemon threads. Estos hilos procesan trabajos en segundo plano en caliente.
- **Protección DoS:** El indexador procesa y fragmenta de forma concurrente, asegurando que Open WebUI responda a consultas en menos de 5 milisegundos incluso bajo re-indexado masivo.

---

## 3. Interfaces vs Implementaciones (Regla de Oro)

Para habilitar la máxima extensibilidad futura, los subsistemas principales están desacoplados mediante clases abstractas (`abc.ABC`):

1.  **`Watcher`:** Abstrae la detección física. El sondeo actual (`PollingWatcher`) puede migrar a notificaciones reactivas de kernel (`FSEvents` de macOS) sin alterar el resto del sistema.
2.  **`StorageBackend`:** Abstrae el guardado de datos. El motor actual (`SQLiteStorageBackend`) puede migrar a DuckDB o bases de datos cliente-servidor Postgres.
3.  **`EmbeddingProvider`:** Aísla el cálculo de vectores. Admite APIs locales (`LM Studio`, `Ollama`), remotas (`OpenAI`, `Voyage AI`), y un modelo local determinista para tests (`MockEmbeddingProvider`).
4.  **`SearchEngine`:** Abstrae la lógica de recuperación de información para combinar BM25, coincidencia exacta y vectores.

---

## 4. Grafo de Conocimiento y SimHash (v3.0)

En la versión v3.0, el indexador extrae automáticamente relaciones semánticas y sintácticas para alimentar el **Grafo de Conocimiento (Knowledge Graph)**:

### Construcción del Grafo
Cada vez que un archivo se añade o modifica:
1.  **Detección de Archivo y Proyecto:** Se registran nodos de tipo `Document` y `Project`, con una relación `PART_OF` entre ellos.
2.  **Análisis AST de Python:** Para archivos `.py`, se parsea la estructura sintáctica abstracta para añadir nodos de tipo `Class` (`BELONGS_TO` Document) y `Function` (`PART_OF` Class o `BELONGS_TO` Document). También se registran las importaciones como `PythonModule` (`IMPORTS`).
3.  **Análisis Docker Compose:** Para archivos YAML de Docker, se leen los servicios (`DockerService`, relación `GENERATED_FROM`) y los puertos expuestos (`API`, relación `EXPOSES`).
4.  **Etiquetas Automáticas:** El etiquetador asigna tecnologías (`Technology`, relación `USES`).
5.  **Referencias Cruzadas:** Se buscan menciones a otros archivos o tecnologías en los textos para trazar relaciones del tipo `REFERENCES`.

### Huellas SimHash para Duplicados
Se calcula una huella digital SimHash de 64 bits por documento. Comparando las distancias de Hamming entre huellas, el motor detecta near-duplicates (distancia $\le 3$), advirtiendo al usuario en los resúmenes si existen READMEs redundantes u obsoletos.

