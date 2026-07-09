import threading
import time
from typing import Callable, Optional

class Scheduler:
    """
    Planifica y orquesta escaneos periódicos completos e incrementales.
    Permite delegar la carga de escaneo de E/S de disco a hilos trabajadores de la cola.
    """
    def __init__(self, full_scan_callback: Optional[Callable[[], None]] = None) -> None:
        self.full_scan_callback = full_scan_callback
        self.running = False
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        """Inicia el planificador periódico en segundo plano."""
        self.running = True
        self._thread = threading.Thread(target=self._run, daemon=True, name="OrbitIndexerScheduler")
        self._thread.start()

    def stop(self) -> None:
        """Detiene el planificador."""
        self.running = False
        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None

    def _run(self) -> None:
        # Ejecutar un escaneo completo inicial a los 5 segundos de arrancar
        time.sleep(5.0)
        if self.running and self.full_scan_callback:
            try:
                self.full_scan_callback()
            except Exception:
                pass

        # Bucle de escaneo periódico completo
        # Por defecto cada 600 segundos (10 minutos)
        while self.running:
            try:
                time.sleep(600.0)
                if self.running and self.full_scan_callback:
                    self.full_scan_callback()
            except Exception:
                continue

    def trigger_full_scan(self) -> None:
        """Fuerza la ejecución inmediata de un escaneo completo del disco."""
        if self.full_scan_callback:
            threading.Thread(target=self.full_scan_callback, daemon=True).start()
