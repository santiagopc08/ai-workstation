import contextvars
import json
import logging
import time
import uuid
from functools import wraps
from typing import Any, Callable

# ContextVar para rastrear el request_id entre hilos
request_id_var = contextvars.ContextVar("request_id", default="")

# Definición del nivel personalizado TRACE (valor 5, menor que DEBUG=10)
logging.TRACE = 5
logging.addLevelName(logging.TRACE, "TRACE")

def trace(self, message, *args, **kws):
    if self.isEnabledFor(logging.TRACE):
        self._log(logging.TRACE, message, args, **kws)
logging.Logger.trace = trace

logger = logging.getLogger("orbit_knowledge")

def setup_logging() -> None:
    """Configura el logger estructurado en formato JSON."""
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # Leer nivel dinámico de configuración
        from orbit_knowledge.config import settings
        lvl_str = settings.LOGGING_LEVEL.upper()
        
        if lvl_str == "TRACE":
            lvl = 5
        elif lvl_str == "DEBUG":
            lvl = logging.DEBUG
        elif lvl_str == "WARNING":
            lvl = logging.WARNING
        elif lvl_str == "ERROR":
            lvl = logging.ERROR
        else:
            lvl = logging.INFO
            
        logger.setLevel(lvl)
        logger.propagate = False


def log_tool_call(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorador para auditar y trazar llamadas a herramientas MCP en formato JSON estructurado.
    Mide la duración de ejecución y evita registrar contenido de archivos de texto.
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.perf_counter()
        
        # Generar identificador único de trazabilidad para esta llamada
        request_id = str(uuid.uuid4())
        token = request_id_var.set(request_id)
        
        start_log = {
            "event": "tool_start",
            "tool": func.__name__,
            "request_id": request_id,
            "args": [str(a) for a in args],
            "kwargs": {k: str(v) for k, v in kwargs.items()}
        }
        logger.info(json.dumps(start_log))
        
        try:
            result = func(*args, **kwargs)
            duration = time.perf_counter() - start_time
            
            # Formatear el resumen de la salida
            result_summary = "None"
            if result is not None:
                if isinstance(result, str):
                    result_summary = f"str(len={len(result)})"
                elif isinstance(result, list):
                    result_summary = f"list(len={len(result)})"
                elif isinstance(result, dict):
                    result_summary = f"dict(len={len(result)})"
                else:
                    result_summary = str(type(result).__name__)

            success_log = {
                "event": "tool_success",
                "tool": func.__name__,
                "request_id": request_id,
                "duration_seconds": round(duration, 6),
                "result_summary": result_summary
            }
            logger.info(json.dumps(success_log))
            return result
        except Exception as e:
            duration = time.perf_counter() - start_time
            error_log = {
                "event": "tool_error",
                "tool": func.__name__,
                "request_id": request_id,
                "duration_seconds": round(duration, 6),
                "error_type": type(e).__name__,
                "error_message": str(e)
            }
            logger.error(json.dumps(error_log))
            raise e
        finally:
            request_id_var.reset(token)
            
    return wrapper

# Configurar logging al importar el módulo
setup_logging()
