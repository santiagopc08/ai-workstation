import json
import sqlite3
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional
from orbit_knowledge.config import settings
from orbit_knowledge.models import FileInfo, Chunk

class StorageBackend(ABC):
    """
    Interface para abstraer el almacenamiento del Knowledge Engine.
    Permite desacoplar la lógica de persistencia (SQLite, Postgres, DuckDB, etc.).
    """
    @abstractmethod
    def save_document(self, doc: FileInfo) -> None: pass
    
    @abstractmethod
    def get_document(self, path: str) -> Optional[FileInfo]: pass
    
    @abstractmethod
    def delete_document(self, path: str) -> None: pass
    
    @abstractmethod
    def list_documents(self) -> list[FileInfo]: pass
    
    @abstractmethod
    def get_documents_by_project(self, project: str) -> list[FileInfo]: pass
    
    @abstractmethod
    def save_chunk(self, chunk: Chunk, section: str, title: str) -> None: pass
    
    @abstractmethod
    def get_chunks_for_document(self, path: str) -> list[Chunk]: pass
    
    @abstractmethod
    def get_all_chunks(self) -> list[Chunk]: pass
    
    @abstractmethod
    def save_metadata(self, doc_path: str, key: str, value: Any) -> None: pass
    
    @abstractmethod
    def get_metadata(self, doc_path: str, key: str) -> Optional[Any]: pass
    
    @abstractmethod
    def save_embedding(self, chunk_id: str, provider: str, model: str, vector: list[float]) -> None: pass
    
    @abstractmethod
    def get_embedding(self, chunk_id: str) -> Optional[list[float]]: pass
    
    @abstractmethod
    def save_hash(self, path: str, file_hash: str, modified: float, size: int) -> None: pass
    
    @abstractmethod
    def get_hash(self, path: str) -> Optional[dict[str, Any]]: pass
    
    @abstractmethod
    def delete_hash(self, path: str) -> None: pass
    
    @abstractmethod
    def list_hashes(self) -> dict[str, dict[str, Any]]: pass

    @abstractmethod
    def save_node(self, node_id: str, node_type: str, name: str, properties: dict[str, Any]) -> None: pass
    
    @abstractmethod
    def delete_node(self, node_id: str) -> None: pass
    
    @abstractmethod
    def save_edge(self, source: str, target: str, relation: str, weight: float = 1.0) -> None: pass
    
    @abstractmethod
    def get_nodes_by_type(self, node_type: str) -> list[dict[str, Any]]: pass
    
    @abstractmethod
    def get_all_edges(self) -> list[dict[str, Any]]: pass
    
    @abstractmethod
    def save_fingerprint(self, path: str, simhash: str) -> None: pass
    
    @abstractmethod
    def get_fingerprint(self, path: str) -> Optional[str]: pass
    
    @abstractmethod
    def list_fingerprints(self) -> dict[str, str]: pass



class SQLiteStorageBackend(StorageBackend):
    """
    Implementación en SQLite con tres bases de datos desacopladas en .orbit/
    con soporte multi-hilo mediante WAL (Write-Ahead Logging) y locks optimizados.
    """
    def __init__(self) -> None:
        # Directorio de persistencia de ORBIT
        self.orbit_dir = settings.ROOT.parent / ".orbit"
        self.orbit_dir.mkdir(parents=True, exist_ok=True)
        
        self.knowledge_db = self.orbit_dir / "knowledge.db"
        self.index_db = self.orbit_dir / "index.db"
        self.embeddings_db = self.orbit_dir / "embeddings.db"
        
        self._init_schemas()

    def _get_connection(self, db_path: Path) -> sqlite3.Connection:
        conn = sqlite3.connect(db_path, timeout=30.0)
        # Habilitar modo WAL para permitir lecturas concurrentes y escrituras seguras
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schemas(self) -> None:
        # 1. Base de datos: knowledge.db (Proyectos y documentos)
        with self._get_connection(self.knowledge_db) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    created_at REAL NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    path TEXT PRIMARY KEY,
                    project TEXT NOT NULL,
                    extension TEXT NOT NULL,
                    title TEXT NOT NULL,
                    size INTEGER NOT NULL,
                    hash TEXT NOT NULL,
                    modified REAL NOT NULL,
                    summary TEXT
                )
            """)
            conn.commit()

        # 2. Base de datos: index.db (Chunks, metadatos y hashes)
        with self._get_connection(self.index_db) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    id TEXT PRIMARY KEY,
                    document_path TEXT NOT NULL,
                    project TEXT NOT NULL,
                    section TEXT NOT NULL,
                    title TEXT NOT NULL,
                    start_line INTEGER NOT NULL,
                    end_line INTEGER NOT NULL,
                    hash TEXT NOT NULL,
                    text TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS metadata (
                    document_path TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    PRIMARY KEY (document_path, key)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS hashes (
                    path TEXT PRIMARY KEY,
                    hash TEXT NOT NULL,
                    modified REAL NOT NULL,
                    size INTEGER NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS nodes (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    properties_json TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS edges (
                    source TEXT NOT NULL,
                    target TEXT NOT NULL,
                    relation TEXT NOT NULL,
                    weight REAL NOT NULL,
                    PRIMARY KEY (source, target, relation)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS fingerprints (
                    document_path TEXT PRIMARY KEY,
                    simhash TEXT NOT NULL
                )
            """)
            conn.commit()


        # 3. Base de datos: embeddings.db (Vectores calculados)
        with self._get_connection(self.embeddings_db) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS embeddings (
                    chunk_id TEXT PRIMARY KEY,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    vector_json TEXT NOT NULL
                )
            """)
            conn.commit()

    # --- Implementación Documentos (knowledge.db) ---
    
    def save_document(self, doc: FileInfo) -> None:
        with self._get_connection(self.knowledge_db) as conn:
            # Asegurar la existencia del proyecto
            conn.execute(
                "INSERT OR IGNORE INTO projects (name, created_at) VALUES (?, strftime('%s', 'now'))",
                (doc.project,)
            )
            # Guardar documento
            conn.execute(
                """INSERT OR REPLACE INTO documents (path, project, extension, title, size, hash, modified, summary)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (doc.path, doc.project, doc.extension, doc.title, doc.size, doc.hash, doc.modified, doc.summary)
            )
            conn.commit()

    def get_document(self, path: str) -> Optional[FileInfo]:
        with self._get_connection(self.knowledge_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM documents WHERE path = ?", (path,))
            row = cursor.fetchone()
            if not row:
                return None
            
            # Recuperar headings y tags desde index.db
            headings = self.get_metadata(path, "headings") or []
            tags = self.get_metadata(path, "tags") or []
            
            return FileInfo(
                path=row["path"],
                project=row["project"],
                extension=row["extension"],
                title=row["title"],
                size=row["size"],
                hash=row["hash"],
                modified=row["modified"],
                headings=headings,
                tags=tags,
                summary=row["summary"] or ""
            )

    def delete_document(self, path: str) -> None:
        with self._get_connection(self.knowledge_db) as conn:
            conn.execute("DELETE FROM documents WHERE path = ?", (path,))
            conn.commit()
            
        # Limpiar metadatos y chunks asociados de index.db
        with self._get_connection(self.index_db) as conn:
            conn.execute("DELETE FROM chunks WHERE document_path = ?", (path,))
            conn.execute("DELETE FROM metadata WHERE document_path = ?", (path,))
            conn.commit()

    def list_documents(self) -> list[FileInfo]:
        with self._get_connection(self.knowledge_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT path FROM documents")
            paths = [row["path"] for row in cursor.fetchall()]
            
        docs: list[FileInfo] = []
        for p in paths:
            doc = self.get_document(p)
            if doc:
                docs.append(doc)
        return docs

    def get_documents_by_project(self, project: str) -> list[FileInfo]:
        with self._get_connection(self.knowledge_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT path FROM documents WHERE project = ?", (project,))
            paths = [row["path"] for row in cursor.fetchall()]
            
        docs: list[FileInfo] = []
        for p in paths:
            doc = self.get_document(p)
            if doc:
                docs.append(doc)
        return docs

    # --- Implementación Chunks y Metadatos (index.db) ---

    def save_chunk(self, chunk: Chunk, section: str, title: str) -> None:
        with self._get_connection(self.index_db) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO chunks (id, document_path, project, section, title, start_line, end_line, hash, text)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (chunk.id, chunk.document, chunk.project, section, title, chunk.start_line, chunk.end_line, chunk.hash, chunk.text)
            )
            conn.commit()

    def get_chunks_for_document(self, path: str) -> list[Chunk]:
        with self._get_connection(self.index_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM chunks WHERE document_path = ?", (path,))
            rows = cursor.fetchall()
            return [
                Chunk(
                    id=r["id"],
                    document=r["document_path"],
                    project=r["project"],
                    section=r["section"],
                    title=r["title"],
                    start_line=r["start_line"],
                    end_line=r["end_line"],
                    text=r["text"],
                    hash=r["hash"]
                ) for r in rows
            ]

    def get_all_chunks(self) -> list[Chunk]:
        with self._get_connection(self.index_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM chunks")
            rows = cursor.fetchall()
            return [
                Chunk(
                    id=r["id"],
                    document=r["document_path"],
                    project=r["project"],
                    section=r["section"],
                    title=r["title"],
                    start_line=r["start_line"],
                    end_line=r["end_line"],
                    text=r["text"],
                    hash=r["hash"]
                ) for r in rows
            ]

    def save_metadata(self, doc_path: str, key: str, value: Any) -> None:
        with self._get_connection(self.index_db) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO metadata (document_path, key, value) VALUES (?, ?, ?)",
                (doc_path, key, json.dumps(value))
            )
            conn.commit()

    def get_metadata(self, doc_path: str, key: str) -> Optional[Any]:
        with self._get_connection(self.index_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM metadata WHERE document_path = ? AND key = ?", (doc_path, key))
            row = cursor.fetchone()
            if not row:
                return None
            try:
                return json.loads(row["value"])
            except Exception:
                return None

    # --- Implementación Embeddings (embeddings.db) ---

    def save_embedding(self, chunk_id: str, provider: str, model: str, vector: list[float]) -> None:
        with self._get_connection(self.embeddings_db) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO embeddings (chunk_id, provider, model, vector_json) VALUES (?, ?, ?, ?)",
                (chunk_id, provider, model, json.dumps(vector))
            )
            conn.commit()

    def get_embedding(self, chunk_id: str) -> Optional[list[float]]:
        with self._get_connection(self.embeddings_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT vector_json FROM embeddings WHERE chunk_id = ?", (chunk_id,))
            row = cursor.fetchone()
            if not row:
                return None
            try:
                return json.loads(row["vector_json"])
            except Exception:
                return None

    # --- Implementación Control de Hashes (index.db) ---

    def save_hash(self, path: str, file_hash: str, modified: float, size: int) -> None:
        with self._get_connection(self.index_db) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO hashes (path, hash, modified, size) VALUES (?, ?, ?, ?)",
                (path, file_hash, modified, size)
            )
            conn.commit()

    def get_hash(self, path: str) -> Optional[dict[str, Any]]:
        with self._get_connection(self.index_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM hashes WHERE path = ?", (path,))
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "path": row["path"],
                "hash": row["hash"],
                "modified": row["modified"],
                "size": row["size"]
            }

    def delete_hash(self, path: str) -> None:
        with self._get_connection(self.index_db) as conn:
            conn.execute("DELETE FROM hashes WHERE path = ?", (path,))
            conn.commit()

    def list_hashes(self) -> dict[str, dict[str, Any]]:
        with self._get_connection(self.index_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM hashes")
            rows = cursor.fetchall()
            return {
                r["path"]: {
                    "path": r["path"],
                    "hash": r["hash"],
                    "modified": r["modified"],
                    "size": r["size"]
                } for r in rows
            }

    # --- Grafo y Fingerprints (index.db) ---
    
    def save_node(self, node_id: str, node_type: str, name: str, properties: dict[str, Any]) -> None:
        with self._get_connection(self.index_db) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO nodes (id, type, name, properties_json) VALUES (?, ?, ?, ?)",
                (node_id, node_type, name, json.dumps(properties))
            )
            conn.commit()
            
    def delete_node(self, node_id: str) -> None:
        with self._get_connection(self.index_db) as conn:
            conn.execute("DELETE FROM nodes WHERE id = ?", (node_id,))
            conn.execute("DELETE FROM edges WHERE source = ? OR target = ?", (node_id, node_id))
            conn.commit()
            
    def save_edge(self, source: str, target: str, relation: str, weight: float = 1.0) -> None:
        with self._get_connection(self.index_db) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO edges (source, target, relation, weight) VALUES (?, ?, ?, ?)",
                (source, target, relation, weight)
            )
            conn.commit()
            
    def get_nodes_by_type(self, node_type: str) -> list[dict[str, Any]]:
        with self._get_connection(self.index_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM nodes WHERE type = ?", (node_type,))
            rows = cursor.fetchall()
            return [
                {
                    "id": r["id"],
                    "type": r["type"],
                    "name": r["name"],
                    "properties": json.loads(r["properties_json"]) if r["properties_json"] else {}
                } for r in rows
            ]
            
    def get_all_edges(self) -> list[dict[str, Any]]:
        with self._get_connection(self.index_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM edges")
            rows = cursor.fetchall()
            return [
                {
                    "source": r["source"],
                    "target": r["target"],
                    "relation": r["relation"],
                    "weight": r["weight"]
                } for r in rows
            ]
            
    def save_fingerprint(self, path: str, simhash: str) -> None:
        with self._get_connection(self.index_db) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO fingerprints (document_path, simhash) VALUES (?, ?)",
                (path, simhash)
            )
            conn.commit()
            
    def get_fingerprint(self, path: str) -> Optional[str]:
        with self._get_connection(self.index_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT simhash FROM fingerprints WHERE document_path = ?", (path,))
            row = cursor.fetchone()
            return row["simhash"] if row else None
            
    def list_fingerprints(self) -> dict[str, str]:
        with self._get_connection(self.index_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM fingerprints")
            rows = cursor.fetchall()
            return {r["document_path"]: r["simhash"] for r in rows}

