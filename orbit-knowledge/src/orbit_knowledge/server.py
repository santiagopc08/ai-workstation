# ruff: noqa: E402
import sys
from pathlib import Path

# Agregar el directorio actual y su contenedor a sys.path para importaciones absolutas
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

project_root = current_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from fastmcp import FastMCP
from orbit_knowledge.mcp.tools import register_tools
from orbit_knowledge.mcp.resources import register_resources
from orbit_knowledge.mcp.prompts import register_prompts
from orbit_knowledge.indexing.engine import indexer_engine
from orbit_knowledge.config import settings

mcp = FastMCP("ORBIT Knowledge Engine")

# Registrar Componentes MCP
register_tools(mcp)
register_resources(mcp)
register_prompts(mcp)

# Verificar estado de la BD de SQLite al arrancar y construir si está vacía
try:
    status = indexer_engine.builder.get_status()
    if status["total_files"] == 0:
        print("Base de datos de conocimiento vacía. Ejecutando indexación inicial...")
        # Indexado completo sincrónico inicial
        indexer_engine.builder.rebuild_all()
except Exception as e:
    print(f"Error inicializando el índice de conocimiento: {e}")

@mcp.on_startup()
def on_startup() -> None:
    """Acción de arranque para iniciar el motor del indexador (watcher, cola, scheduler)."""
    indexer_engine.start()

@mcp.on_shutdown()
def on_shutdown() -> None:
    """Acción de apagado para detener limpiamente todos los hilos del motor."""
    indexer_engine.stop()

from starlette.requests import Request
from starlette.responses import JSONResponse
import time

start_time = time.time()

@mcp.custom_route("/health", methods=["GET"])
async def health_endpoint(request: Request) -> JSONResponse:
    """Endpoint de observabilidad opcional."""
    from orbit_knowledge.indexing.engine import indexer_engine
    try:
        status = indexer_engine.builder.get_status()
        docs_count = status.get("total_files", 0)
        projects_count = len(indexer_engine.builder.storage.list_projects())
    except Exception:
        docs_count = 0
        projects_count = 0
        
    uptime = time.time() - start_time
    
    return JSONResponse({
        "status": "healthy",
        "version": "3.0.0",
        "documents": docs_count,
        "projects": projects_count,
        "cache": {
            "size": settings.CACHE_SIZE
        },
        "uptime": round(uptime, 2)
    })

if __name__ == "__main__":

    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=8001
    )
