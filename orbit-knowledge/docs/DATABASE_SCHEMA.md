# DATABASE_SCHEMA.md - ORBIT Indexer Database Schema

Este documento detalla el esquema de tablas y relaciones de las tres bases de datos SQLite persistidas en el directorio `.orbit/` por el **ORBIT Indexer Engine v1.0**.

---

## 1. Diseño General

Para prevenir bloqueos de concurrencia y mantener alta velocidad en Apple Silicon, el almacenamiento se desacopla en tres archivos SQLite independientes:

1.  **`knowledge.db`:** Estructura de proyectos y metadatos base de documentos.
2.  **`index.db`:** Fragmentos textuales (chunks), índices inversos de metadatos y hashes de archivos para control incremental.
3.  **`embeddings.db`:** Vectores numéricos calculados para cada chunk.

---

## 2. Esquema de `knowledge.db`

### Tabla `projects`
Almacena los proyectos de conocimiento descubiertos.
```sql
CREATE TABLE projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    created_at REAL NOT NULL
);
```

### Tabla `documents`
Almacena los documentos permitidos indexados dentro de cada proyecto.
```sql
CREATE TABLE documents (
    path TEXT PRIMARY KEY,
    project TEXT NOT NULL,
    extension TEXT NOT NULL,
    title TEXT NOT NULL,
    size INTEGER NOT NULL,
    hash TEXT NOT NULL,
    modified REAL NOT NULL,
    summary TEXT
);
```

---

## 3. Esquema de `index.db`

### Tabla `chunks`
Almacena los fragmentos textuales semánticos extraídos.
```sql
CREATE TABLE chunks (
    id TEXT PRIMARY KEY,
    document_path TEXT NOT NULL,
    project TEXT NOT NULL,
    section TEXT NOT NULL,
    title TEXT NOT NULL,
    start_line INTEGER NOT NULL,
    end_line INTEGER NOT NULL,
    hash TEXT NOT NULL,
    text TEXT NOT NULL
);
```
*   **Índice recomendado:** `CREATE INDEX idx_chunks_doc ON chunks(document_path);`

### Tabla `metadata`
Almacena atributos clave-valor adicionales (tags, headings) en formato JSON.
```sql
CREATE TABLE metadata (
    document_path TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    PRIMARY KEY (document_path, key)
);
```

### Tabla `hashes`
Almacena el estado de modificación rápida de los archivos para permitir escaneos incrementales ultrarrápidos.
```sql
CREATE TABLE hashes (
    path TEXT PRIMARY KEY,
    hash TEXT NOT NULL,
    modified REAL NOT NULL,
    size INTEGER NOT NULL
);
```

### Tabla `nodes`
Representa los nodos en el Grafo de Conocimiento (Document, Project, Class, Function, DockerService, Technology, etc.).
```sql
CREATE TABLE nodes (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    name TEXT NOT NULL,
    properties_json TEXT NOT NULL
);
```

### Tabla `edges`
Representa las relaciones dirigidas en el Grafo de Conocimiento (`USES`, `IMPORTS`, `DEPENDS_ON`, `REFERENCES`, `BELONGS_TO`, etc.).
```sql
CREATE TABLE edges (
    source TEXT NOT NULL,
    target TEXT NOT NULL,
    relation TEXT NOT NULL,
    weight REAL NOT NULL,
    PRIMARY KEY (source, target, relation)
);
```

### Tabla `fingerprints`
Almacena la huella digital SimHash de 64 bits para cada documento con el fin de detectar duplicados cercanos.
```sql
CREATE TABLE fingerprints (
    document_path TEXT PRIMARY KEY,
    simhash TEXT NOT NULL
);
```

---


## 4. Esquema de `embeddings.db`

### Tabla `embeddings`
Almacena los vectores calculados por el proveedor seleccionado.
```sql
CREATE TABLE embeddings (
    chunk_id TEXT PRIMARY KEY,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    vector_json TEXT NOT NULL
);
```

---

## 5. Optimizaciones del Motor SQLite
- **Modo WAL (Write-Ahead Logging):** Configurado en el arranque para posibilitar lecturas sin bloqueo concurrentemente con escrituras en segundo plano.
- **Timeout extendido (30s):** Previene errores de bloqueo temporal (`database is locked`) bajo alta carga.
