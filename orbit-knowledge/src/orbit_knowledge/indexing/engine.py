from typing import Any, Optional
from orbit_knowledge.indexing.storage import SQLiteStorageBackend
from orbit_knowledge.indexing.builder import IndexBuilder
from orbit_knowledge.indexing.watcher import PollingWatcher
from orbit_knowledge.indexing.scheduler import Scheduler
from orbit_knowledge.indexing.queue import job_queue, IndexingJob
from orbit_knowledge.indexing.events import event_bus, DocumentCreated, DocumentUpdated, DocumentDeleted

class IndexerEngine:
    """
    Fachada y motor de indexación reactivo. Enlaza el Bus de Eventos,
    los hilos de trabajo asíncronos y el Watcher para mantener sincronizada la base de datos.
    """
    def __init__(self, storage: Optional[SQLiteStorageBackend] = None) -> None:
        self.storage = storage or SQLiteStorageBackend()
        self.builder = IndexBuilder(self.storage)
        self.watcher = PollingWatcher(self.storage)
        self.scheduler = Scheduler(self.builder.incremental_scan)

        # Suscribirse al Bus de Eventos
        event_bus.subscribe(DocumentCreated, self._on_document_created)
        event_bus.subscribe(DocumentUpdated, self._on_document_updated)
        event_bus.subscribe(DocumentDeleted, self._on_document_deleted)

        # Configurar callback de ejecución de trabajos en la cola
        job_queue.worker_callback = self._process_job

    def start(self) -> None:
        """Enciende la cola de trabajos, el watcher y el scheduler de escaneos."""
        job_queue.start()
        self.watcher.start()
        self.scheduler.start()

    def stop(self) -> None:
        """Detiene de forma limpia todos los hilos."""
        self.watcher.stop()
        self.scheduler.stop()
        job_queue.stop()

    def index_all(self, rebuild: bool = False) -> dict[str, Any]:
        """Fuerza una indexación de toda la base de conocimiento."""
        return self.builder.rebuild_all() if rebuild else self.builder.incremental_scan()

    def index_document(self, path: str) -> None:
        """Añade un trabajo de indexación individual para el archivo dado."""
        job_queue.add_job(IndexingJob(action="index", path=path))

    def remove_document(self, path: str) -> None:
        """Añade un trabajo para eliminar un archivo del índice."""
        job_queue.add_job(IndexingJob(action="remove", path=path))

    def refresh_document(self, path: str) -> None:
        """Fuerza un re-indexado inmediato (sincrónico) de un archivo."""
        self.builder.index_document(path)

    def refresh_project(self, project: str) -> dict[str, Any]:
        """Sincroniza y re-indexa todos los archivos correspondientes a un proyecto."""
        docs = self.builder.incremental_scan()
        return docs

    def _on_document_created(self, event: DocumentCreated) -> None:
        job_queue.add_job(IndexingJob(action="index", path=event.path))

    def _on_document_updated(self, event: DocumentUpdated) -> None:
        job_queue.add_job(IndexingJob(action="index", path=event.path))

    def _on_document_deleted(self, event: DocumentDeleted) -> None:
        job_queue.add_job(IndexingJob(action="remove", path=event.path))

    def _process_job(self, job: IndexingJob) -> None:
        """Ejecutor de callbacks para los workers del JobQueue."""
        if job.action == "index" or job.action == "refresh":
            self.builder.index_document(job.path)
        elif job.action == "remove":
            self.builder.remove_document(job.path)

# Instancia global única del motor del indexador
indexer_engine: IndexerEngine = IndexerEngine()
