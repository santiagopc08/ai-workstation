import time
import threading
from abc import ABC, abstractmethod
from typing import Any
from orbit_knowledge.config import settings
from orbit_knowledge.indexing.events import event_bus, DocumentCreated, DocumentUpdated, DocumentDeleted
from orbit_knowledge.indexing.hashes import compute_sha256
from orbit_knowledge.providers.filesystem import iter_allowed_files

class Watcher(ABC):
    @abstractmethod
    def start(self) -> None: pass
    
    @abstractmethod
    def stop(self) -> None: pass


class PollingWatcher(Watcher):
    """
    Monitorizador de archivos mediante sondeo periódico de fecha de modificación e
    hilo demonio. Publica eventos en el EventBus al detectar CREATE, MODIFIED, DELETE.
    """
    def __init__(self, storage_backend: Any = None) -> None:
        self.running = False
        self.thread: threading.Thread | None = None
        self.storage = storage_backend

    def start(self) -> None:
        """Inicia el escaneo en segundo plano si está activado en settings."""
        if not settings.WATCHER_ENABLED:
            return
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True, name="OrbitFileSystemWatcher")
        self.thread.start()

    def stop(self) -> None:
        """Detiene el hilo de escaneo."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
            self.thread = None

    def _run(self) -> None:
        # Resolver dependencia de almacenamiento circular o tardía
        if not self.storage:
            from orbit_knowledge.indexing.storage import SQLiteStorageBackend
            self.storage = SQLiteStorageBackend()

        # Cargar mapa de hashes en disco
        known_files = self.storage.list_hashes()
        
        while self.running:
            try:
                time.sleep(settings.WATCHER_INTERVAL_SECONDS)
                
                # Obtener archivos permitidos en disco
                disk_files = {}
                for path in iter_allowed_files(settings.ROOT):
                    # Ignorar directorios ocultos o la base de datos sqlite que reside en .orbit
                    if ".orbit" in path.parts or ".git" in path.parts:
                        continue
                    rel_path = str(path.relative_to(settings.ROOT))
                    try:
                        stat = path.stat()
                        disk_files[rel_path] = (stat.st_mtime, stat.st_size, path)
                    except OSError:
                        continue

                # 1. Detectar archivos eliminados
                deleted = [p for p in known_files if p not in disk_files]
                for rel_path in deleted:
                    event_bus.publish(DocumentDeleted(rel_path))
                    self.storage.delete_hash(rel_path)
                    del known_files[rel_path]

                # 2. Detectar creados o modificados
                for rel_path, (mtime, size, path) in disk_files.items():
                    if rel_path not in known_files:
                        # CREATE
                        event_bus.publish(DocumentCreated(rel_path))
                        # Guardar hash preliminar para evitar bucles
                        file_hash = compute_sha256(path)
                        self.storage.save_hash(rel_path, file_hash, mtime, size)
                        known_files[rel_path] = {
                            "path": rel_path,
                            "hash": file_hash,
                            "modified": mtime,
                            "size": size
                        }
                    else:
                        known = known_files[rel_path]
                        if mtime != known["modified"] or size != known["size"]:
                            file_hash = compute_sha256(path)
                            if file_hash != known["hash"]:
                                # MODIFIED
                                event_bus.publish(DocumentUpdated(rel_path))
                                self.storage.save_hash(rel_path, file_hash, mtime, size)
                                known_files[rel_path] = {
                                    "path": rel_path,
                                    "hash": file_hash,
                                    "modified": mtime,
                                    "size": size
                                }
                            else:
                                # Solo cambió mtime en el disco
                                self.storage.save_hash(rel_path, file_hash, mtime, size)
                                known_files[rel_path]["modified"] = mtime
            except Exception:
                continue

