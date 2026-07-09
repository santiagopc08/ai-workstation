from pathlib import Path
from typing import Any, Optional
from orbit_knowledge.config import settings
from orbit_knowledge.models import FileInfo
from orbit_knowledge.indexing.storage import SQLiteStorageBackend
from orbit_knowledge.indexing.hashes import compute_sha256
from orbit_knowledge.indexing.metadata import (
    extract_markdown_metadata_extended,
    extract_python_metadata_extended,
    extract_json_metadata_extended,
    extract_docker_metadata_extended,
    extract_yaml_metadata_generic
)
from orbit_knowledge.indexing.chunker import chunk_document
from orbit_knowledge.indexing.embeddings import get_embedding_provider
from orbit_knowledge.indexing.events import event_bus, IndexFinished
from orbit_knowledge.providers.filesystem import resolve_path, safe_read, iter_allowed_files

def get_project_name(relative_path_str: str) -> str:
    path_obj = Path(relative_path_str)
    parts = path_obj.parts
    if not parts or len(parts) == 1:
        return "Global"
    if parts[0] == "Projects" and len(parts) >= 2:
        return f"Projects/{parts[1]}"
    return parts[0]

class IndexBuilder:
    """
    Controla la orquestación e inserción física de metadatos, chunks y embeddings
    dentro de la capa de almacenamiento SQLite y la base de datos de embeddings.
    """
    def __init__(self, storage: Optional[SQLiteStorageBackend] = None) -> None:
        self.storage = storage or SQLiteStorageBackend()
        self.emb_provider = get_embedding_provider()

    def index_document(self, relative_path: str) -> None:
        """
        Indexa completamente un archivo: lee contenido, calcula hash,
        extrae metadata, genera chunks semánticos y calcula embeddings vectoriales.
        """
        abs_path = resolve_path(relative_path)
        if not abs_path.exists() or not abs_path.is_file():
            self.remove_document(relative_path)
            return

        try:
            content = safe_read(abs_path)
            stat = abs_path.stat()
            file_hash = compute_sha256(abs_path)
        except Exception:
            return

        project = get_project_name(relative_path)
        ext = abs_path.suffix.lower()
        
        # 1. Extraer metadatos específicos según extensión
        headings: list[str] = []
        tags = [ext[1:]] if ext else []
        title = abs_path.name
        summary = ""
        
        if ext == ".md":
            meta = extract_markdown_metadata_extended(content)
            title = meta["title"]
            headings = meta["headings"]
            summary = content[:200].strip() + "..." if len(content) > 200 else content
            tags.extend(["markdown", "documento"])
            if meta["code_blocks"]:
                tags.extend(meta["code_blocks"])
        elif ext == ".py":
            meta = extract_python_metadata_extended(content)
            title = f"Módulo Python: {abs_path.name}"
            headings = [f"Class: {c}" for c in meta["classes"]] + [f"Func: {f}" for f in meta["functions"]]
            summary = meta["docstring"] or (content[:200].strip() + "..." if len(content) > 200 else content)
            tags.extend(["python", "codigo"])
            tags.extend(meta["imports"])
        elif ext == ".json":
            meta = extract_json_metadata_extended(content)
            title = f"Datos JSON: {abs_path.name}"
            headings = [f"Key: {k}" for k in meta["keys"][:10]]
            summary = f"JSON esquema: {list(meta['schema'].keys())[:5]}"
            tags.extend(["json", "datos"])
        elif ext in (".yaml", ".yml"):
            is_compose = "compose" in abs_path.name.lower() or "docker" in abs_path.name.lower()
            if is_compose:
                meta = extract_docker_metadata_extended(content)
                title = f"Docker Compose: {abs_path.name}"
                headings = [f"Service: {s}" for s in meta["services"]]
                summary = f"Servicios: {meta['services']}, Puertos: {meta['ports']}"
                tags.extend(["docker", "compose", "yaml"])
            else:
                meta = extract_yaml_metadata_generic(content)
                title = f"Configuración YAML: {abs_path.name}"
                summary = content[:200].strip() + "..." if len(content) > 200 else content
                tags.extend(["yaml", "configuracion"])
                if meta["anchors"]:
                    tags.extend(meta["anchors"])
        else:
            summary = content[:200].strip() + "..." if len(content) > 200 else content
            tags.extend(["texto"])

        # 2. Guardar Info del documento
        doc_info = FileInfo(
            path=relative_path,
            project=project,
            extension=ext,
            title=title,
            size=stat.st_size,
            hash=file_hash,
            modified=stat.st_mtime,
            headings=headings,
            tags=list(set(tags)),
            summary=summary
        )
        self.storage.save_document(doc_info)
        
        # Guardar metadatos en index.db
        self.storage.save_metadata(relative_path, "headings", headings)
        self.storage.save_metadata(relative_path, "tags", list(set(tags)))

        # Calcular y guardar huella digital SimHash
        from orbit_knowledge.fingerprints.simhash import SimHash
        sh = SimHash(content)
        self.storage.save_fingerprint(relative_path, sh.fingerprint)

        # Construir/actualizar Grafo de Conocimiento
        from orbit_knowledge.graph.engine import KnowledgeGraphEngine
        graph_eng = KnowledgeGraphEngine(self.storage)
        graph_eng.build_graph_for_document(relative_path, content)

        # 3. Eliminar chunks anteriores en cascada
        # La BD SQLite de chunks se limpia por path del documento
        with self.storage._get_connection(self.storage.index_db) as conn:
            conn.execute("DELETE FROM chunks WHERE document_path = ?", (relative_path,))
            conn.commit()

        # 4. Generar chunks semánticos nuevos
        chunks = chunk_document(relative_path, project, content, settings.CHUNK_SIZE)
        for chunk in chunks:
            # Guardar chunk físico en SQLite
            self.storage.save_chunk(chunk, chunk.section, chunk.title)
            
            # 5. Generar y guardar embeddings
            try:
                vector = self.emb_provider.generate_embedding(chunk.text)
                if vector:
                    self.storage.save_embedding(
                        chunk.id,
                        settings.EMBEDDING_PROVIDER,
                        getattr(self.emb_provider, "model", "default"),
                        vector
                    )
            except Exception:
                # No bloquear si la API de embeddings falla temporalmente
                continue

        # Guardar hash en el control de cambios
        self.storage.save_hash(relative_path, file_hash, stat.st_mtime, stat.st_size)

    def remove_document(self, relative_path: str) -> None:
        """Elimina por completo un documento, sus chunks, huellas y relaciones del grafo."""
        self.storage.delete_document(relative_path)
        self.storage.delete_hash(relative_path)
        
        # Eliminar del grafo
        self.storage.delete_node(f"doc:{relative_path}")
        
        # Eliminar fingerprint
        with self.storage._get_connection(self.storage.index_db) as conn:
            conn.execute("DELETE FROM fingerprints WHERE document_path = ?", (relative_path,))
            conn.commit()
            
        # Eliminar embeddings asociados
        # Recuperar chunk ids eliminados de embeddings.db
        with self.storage._get_connection(self.storage.embeddings_db) as conn:
            conn.execute("DELETE FROM embeddings WHERE chunk_id LIKE ?", (f"{relative_path}#%",))
            conn.commit()

    def rebuild_all(self) -> dict[str, Any]:
        """Elimina todos los datos en disco y realiza un re-indexado completo en frío."""
        # Wipe databases
        self.storage._init_schemas()
        
        disk_files = []
        for path in iter_allowed_files(settings.ROOT):
            if ".orbit" in path.parts or ".git" in path.parts:
                continue
            rel_path = str(path.relative_to(settings.ROOT))
            disk_files.append(rel_path)

        for rel_path in disk_files:
            self.index_document(rel_path)
            
        stats = self.get_status()
        event_bus.publish(IndexFinished(stats))
        return stats

    def incremental_scan(self) -> dict[str, Any]:
        """Escanéa el disco y procesa únicamente los archivos modificados o creados."""
        known_hashes = self.storage.list_hashes()
        disk_files = {}
        
        for path in iter_allowed_files(settings.ROOT):
            if ".orbit" in path.parts or ".git" in path.parts:
                continue
            rel_path = str(path.relative_to(settings.ROOT))
            try:
                stat = path.stat()
                disk_files[rel_path] = (stat.st_mtime, stat.st_size, path)
            except OSError:
                continue

        # 1. Eliminar huérfanos
        for rel_path in list(known_hashes.keys()):
            if rel_path not in disk_files:
                self.remove_document(rel_path)

        # 2. Indexar modificados o nuevos
        for rel_path, (mtime, size, path) in disk_files.items():
            if rel_path not in known_hashes:
                self.index_document(rel_path)
            else:
                known = known_hashes[rel_path]
                if mtime != known["modified"] or size != known["size"]:
                    file_hash = compute_sha256(path)
                    if file_hash != known["hash"]:
                        self.index_document(rel_path)

        stats = self.get_status()
        event_bus.publish(IndexFinished(stats))
        return stats

    def get_status(self) -> dict[str, Any]:
        """Genera estadísticas consolidadas del estado de indexación en SQLite."""
        docs = self.storage.list_documents()
        
        # Conteo de chunks
        with self.storage._get_connection(self.storage.index_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM chunks")
            total_chunks = cursor.fetchone()[0]

        # Conteo de embeddings
        with self.storage._get_connection(self.storage.embeddings_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM embeddings")
            total_embeddings = cursor.fetchone()[0]

        projects = sorted(list(set(d.project for d in docs)))
        total_size = sum(d.size for d in docs)
        
        return {
            "status": "ready" if docs else "empty",
            "total_files": len(docs),
            "total_chunks": total_chunks,
            "total_embeddings": total_embeddings,
            "total_size_bytes": total_size,
            "projects_count": len(projects),
            "projects": projects
        }
