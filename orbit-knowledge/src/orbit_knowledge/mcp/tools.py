from typing import Any as TypingAny
from fastmcp import FastMCP
from orbit_knowledge.logging_config import log_tool_call
from orbit_knowledge.services import project_service, knowledge_service
from orbit_knowledge.indexing.engine import indexer_engine
from orbit_knowledge.providers import filesystem
import orbit_knowledge.search.content as search_content_module
import orbit_knowledge.search.filename as search_filename_module

def register_tools(mcp: FastMCP) -> None:
    """Registra las herramientas en la instancia de FastMCP."""
    
    # ==========================================
    # --- HERRAMIENTAS LEGACY (Compatibilidad) ---
    # ==========================================

    @mcp.tool()
    @log_tool_call
    def list_files(folder: str = "") -> list[str]:
        """[LEGACY] Lista archivos dentro del sistema de archivos de forma recursiva."""
        return filesystem.list_files(folder)

    @mcp.tool()
    @log_tool_call
    def read_file(file_path: str) -> str:
        """[LEGACY] Lee de forma segura el contenido de un archivo de la base de conocimiento."""
        return filesystem.read_file(file_path)

    @mcp.tool()
    @log_tool_call
    def search_files(pattern: str) -> list[str]:
        """[LEGACY] Busca archivos permitidos por coincidencia parcial de su nombre."""
        return search_filename_module.search_files(pattern)

    @mcp.tool()
    @log_tool_call
    def search_content(query: str) -> list[dict[str, TypingAny]]:
        """[LEGACY] Busca un texto dentro de toda la documentación."""
        results = search_content_module.search_content(query)
        return [r.to_dict() for r in results]

    @mcp.tool()
    @log_tool_call
    def tree(folder: str = "") -> str:
        """[LEGACY] Muestra la estructura de directorios en formato de árbol ASCII."""
        return filesystem.tree(folder)

    @mcp.tool()
    @log_tool_call
    def read_multiple(files: list[str]) -> dict[str, str]:
        """[LEGACY] Lee el contenido de múltiples archivos en lote."""
        return filesystem.read_multiple(files)

    # ==========================================
    # --- HERRAMIENTAS DE PROYECTOS (V2.0) ---
    # ==========================================

    @mcp.tool()
    @log_tool_call
    def list_projects() -> list[str]:
        """Lista todos los proyectos indexados en la base de conocimiento de ORBIT."""
        return project_service.list_projects()

    @mcp.tool()
    @log_tool_call
    def project_summary(project: str) -> str:
        """Genera un resumen consolidado de documentación y archivos de un proyecto."""
        return project_service.project_summary(project)

    @mcp.tool()
    @log_tool_call
    def project_tree(project: str) -> str:
        """Genera el árbol de archivos en formato ASCII del proyecto especificado."""
        return project_service.project_tree(project)

    @mcp.tool()
    @log_tool_call
    def project_documents(project: str) -> list[str]:
        """Lista las rutas relativas de todos los documentos asignados al proyecto."""
        return project_service.project_documents(project)

    @mcp.tool()
    @log_tool_call
    def project_metadata(project: str) -> dict[str, TypingAny]:
        """Devuelve las estadísticas, tags y volumen de archivos del proyecto."""
        return project_service.project_metadata(project)

    # ==========================================
    # --- HERRAMIENTAS DE CONOCIMIENTO (V2.0) ---
    # ==========================================

    @mcp.tool()
    @log_tool_call
    def find_document(name: str) -> list[str]:
        """Busca documentos indexados por coincidencia parcial de su nombre."""
        return knowledge_service.find_document(name)

    @mcp.tool()
    @log_tool_call
    def search_documentation(query: str) -> list[dict[str, TypingAny]]:
        """Busca texto en el conocimiento indexado devolviendo puntuación de relevancia (score)."""
        results = knowledge_service.search_documentation(query)
        return [r.to_dict() for r in results]

    @mcp.tool()
    @log_tool_call
    def summarize_document(path: str) -> str:
        """Genera un resumen extractor estructurado del documento indexado."""
        return knowledge_service.summarize_document(path)

    @mcp.tool()
    @log_tool_call
    def related_documents(path: str) -> list[str]:
        """Encuentra documentos relacionados que comparten etiquetas (tags) con el archivo dado."""
        return knowledge_service.related_documents(path)

    # ==========================================
    # --- HERRAMIENTAS DE ARQUITECTURA (V2.0) ---
    # ==========================================

    @mcp.tool()
    @log_tool_call
    def get_architecture(project: str) -> str:
        """Extrae la información de arquitectura descrita en los documentos del proyecto."""
        docs = project_service.project_documents(project)
        # Buscar archivos candidatos que describan arquitectura
        candidates = [d for d in docs if "arch" in d.lower() or "design" in d.lower() or "readme" in d.lower()]
        if not candidates:
            return f"No se encontró documentación explícita de arquitectura para el proyecto '{project}'."
            
        summary_arch = f"# Arquitectura del proyecto: {project}\n\n"
        for doc in candidates[:3]:
            summary_arch += f"### Extraído de: `{doc}`\n"
            summary_arch += knowledge_service.summarize_document(doc) + "\n\n"
        return summary_arch

    @mcp.tool()
    @log_tool_call
    def get_stack(project: str) -> list[str]:
        """Extrae la pila tecnológica del proyecto de acuerdo con el análisis de tags."""
        meta = project_service.project_metadata(project)
        tags = meta.get("top_tags", [])
        # Filtrar tags genéricas de archivos
        generic = {"md", "txt", "py", "json", "yaml", "yml", "toml", "code", "documento", "datos", "configuracion", "texto", "markdown"}
        return [t for t in tags if t not in generic]

    @mcp.tool()
    @log_tool_call
    def get_dependencies(project: str) -> list[str]:
        """Lista las importaciones y librerías declaradas en los módulos de código del proyecto."""
        docs = project_service.project_documents(project)
        dependencies: list[str] = []
        for d in docs:
            if d.endswith(".py"):
                try:
                    content = filesystem.read_file(d)
                    from orbit_knowledge.indexing.metadata import extract_python_metadata_extended
                    meta = extract_python_metadata_extended(content)
                    dependencies.extend(meta.get("imports", []))
                except Exception:
                    continue
        return sorted(list(set(dependencies)))

    @mcp.tool()
    @log_tool_call
    def get_services(project: str) -> list[str]:
        """Lista los nombres de servicios declarados en archivos Docker Compose del proyecto."""
        docs = project_service.project_documents(project)
        services: list[str] = []
        for d in docs:
            if "compose" in d.lower() or "docker" in d.lower():
                try:
                    content = filesystem.read_file(d)
                    from orbit_knowledge.indexing.metadata import extract_docker_metadata_extended
                    meta = extract_docker_metadata_extended(content)
                    services.extend(meta.get("services", []))
                except Exception:
                    continue
        return sorted(list(set(services)))

    # ==========================================
    # --- HERRAMIENTAS DE ÍNDICE (V2.0) ---
    # ==========================================

    @mcp.tool()
    @log_tool_call
    def build_index() -> dict[str, TypingAny]:
        """Construye o actualiza el índice incremental de conocimiento."""
        return indexer_engine.index_all()

    @mcp.tool()
    @log_tool_call
    def rebuild_index() -> dict[str, TypingAny]:
        """Reconstruye por completo el índice de conocimiento eliminando la base anterior."""
        return indexer_engine.index_all(rebuild=True)

    @mcp.tool()
    @log_tool_call
    def index_status() -> dict[str, TypingAny]:
        """Muestra estadísticas detalladas del índice de conocimiento."""
        return indexer_engine.builder.get_status()

    @mcp.tool()
    @log_tool_call
    def refresh_project(project: str) -> dict[str, TypingAny]:
        """Actualiza el índice exclusivamente para los archivos bajo el proyecto dado."""
        return indexer_engine.refresh_project(project)
