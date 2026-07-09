import queue
import threading
from dataclasses import dataclass
from typing import Callable, Optional
from orbit_knowledge.config import settings

@dataclass(slots=True, frozen=True)
class IndexingJob:
    action: str  # "index", "remove", "refresh"
    path: str

class JobQueue:
    """
    Cola de trabajos hilo-segura basada en queue.Queue para procesar la indexación
    en segundo plano de manera no bloqueante.
    """
    def __init__(self, num_workers: int = 2, worker_callback: Optional[Callable[[IndexingJob], None]] = None) -> None:
        self._queue: queue.Queue[Optional[IndexingJob]] = queue.Queue()
        self.num_workers = num_workers
        self.worker_callback = worker_callback
        self.workers: list[threading.Thread] = []
        self.running = False
        
    def start(self) -> None:
        """Inicia el pool de hilos trabajadores."""
        if self.running:
            return
        self.running = True
        for i in range(self.num_workers):
            t = threading.Thread(target=self._worker_loop, daemon=True, name=f"OrbitIndexerWorker-{i}")
            t.start()
            self.workers.append(t)
            
    def stop(self) -> None:
        """Detiene de forma limpia los trabajadores metiendo objetos centinela."""
        if not self.running:
            return
        self.running = False
        # Insertar centinelas para despertar y salir del bucle de hilos
        for _ in range(self.num_workers):
            self._queue.put(None)
        for t in self.workers:
            t.join(timeout=1.0)
        self.workers.clear()

    def add_job(self, job: IndexingJob) -> None:
        """Añade una nueva solicitud de indexación a la cola."""
        self._queue.put(job)
        
    def _worker_loop(self) -> None:
        while self.running:
            try:
                job = self._queue.get()
                if job is None:
                    self._queue.task_done()
                    break
                
                if self.worker_callback:
                    try:
                        self.worker_callback(job)
                    except Exception:
                        pass
                
                self._queue.task_done()
            except Exception:
                continue

# Instancia global única de la cola de indexación
job_queue: JobQueue = JobQueue(num_workers=settings.WORKERS)
