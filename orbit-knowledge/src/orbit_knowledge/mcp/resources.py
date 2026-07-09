import json
from fastmcp import FastMCP
from orbit_knowledge.config import settings
from orbit_knowledge.services import project_service
from orbit_knowledge.indexing.engine import indexer_engine

def register_resources(mcp: FastMCP) -> None:
    """Registra los recursos MCP en la instancia de FastMCP."""

    @mcp.resource("knowledge://{file_path}")
    def read_knowledge_resource(file_path: str) -> str:
        """Expone y lee de forma directa cualquier archivo de conocimiento como un recurso."""
        from orbit_knowledge.providers import filesystem
        return filesystem.read_file(file_path)

    @mcp.resource("orbit://projects")
    def get_current_projects() -> str:
        """Expone la lista de proyectos en formato Markdown para los agentes."""
        projects = project_service.list_projects()
        if not projects:
            return "No hay proyectos indexados actualmente."
        return "### Proyectos de ORBIT indexados:\n\n" + "\n".join(f"- {p}" for p in projects)

    @mcp.resource("orbit://architecture")
    def get_global_architecture() -> str:
        """Consolida la información de arquitectura de todos los proyectos de ORBIT."""
        projects = project_service.list_projects()
        output = "# Arquitectura Global de ORBIT\n\n"
        if not projects:
            output += "No hay datos de arquitectura indexados."
            return output
            
        for p in projects:
            output += f"## Proyecto: {p}\n"
            output += f"{project_service.project_summary(p)}\n\n"
        return output

    @mcp.resource("orbit://stacks")
    def get_global_stacks() -> str:
        """Mapea un reporte con la pila de tecnologías de los proyectos."""
        projects = project_service.list_projects()
        output = "# Stacks Tecnológicos Consolidados\n\n"
        if not projects:
            output += "Sin datos de tecnologías."
            return output
            
        for p in projects:
            meta = project_service.project_metadata(p)
            tags = meta.get("top_tags", [])
            generic = {"md", "txt", "py", "json", "yaml", "yml", "toml", "code", "documento", "datos", "configuracion", "texto", "markdown"}
            tech = [t for t in tags if t not in generic]
            output += f"- **{p}:** {', '.join(tech) if tech else 'Sin tecnologías deducidas'}\n"
        return output

    @mcp.resource("orbit://index")
    def get_knowledge_index_status() -> str:
        """Expone las estadísticas completas del estado del índice en formato JSON."""
        status = indexer_engine.builder.get_status()
        return json.dumps(status, indent=2, ensure_ascii=False)

    @mcp.resource("orbit://config")
    def get_orbit_config() -> str:
        """Devuelve la configuración e información de entorno del Knowledge Engine."""
        cfg_dict = {
            "root_directory": str(settings.ROOT),
            "allowed_extensions": list(settings.ALLOWED_EXTENSIONS),
            "index_path": str(settings.INDEX_FILE_PATH),
            "max_file_size_mb": settings.MAX_FILE_SIZE_MB,
            "watcher_enabled": settings.WATCHER_ENABLED,
            "chunk_size": settings.CHUNK_SIZE,
            "chunk_overlap": settings.CHUNK_OVERLAP
        }
        return json.dumps(cfg_dict, indent=2, ensure_ascii=False)

    @mcp.resource("orbit://graph")
    def get_knowledge_graph_summary() -> str:
        """Devuelve un resumen estructurado del Grafo de Conocimiento de ORBIT."""
        storage = indexer_engine.builder.storage
        with storage._get_connection(storage.index_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM nodes")
            nodes_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM edges")
            edges_count = cursor.fetchone()[0]
            
            # Listar conteos de tipos de nodo
            cursor.execute("SELECT type, COUNT(*) as c FROM nodes GROUP BY type")
            types = cursor.fetchall()
            type_lines = [f"- **{r['type']}:** {r['c']} nodos" for r in types]
            
            # Listar conteos de relaciones
            cursor.execute("SELECT relation, COUNT(*) as c FROM edges GROUP BY relation")
            relations = cursor.fetchall()
            relation_lines = [f"- **{r['relation']}:** {r['c']} aristas" for r in relations]
            
        md = "# ORBIT Knowledge Graph Summary\n\n"
        md += "El Grafo de Conocimiento tiene actualmente:\n"
        md += f"- **Total Nodos:** {nodes_count}\n"
        md += f"- **Total Relaciones:** {edges_count}\n\n"
        md += "### Distribución por tipo de nodo:\n"
        md += "\n".join(type_lines) + "\n\n"
        md += "### Distribución por tipo de relación:\n"
        md += "\n".join(relation_lines) + "\n"
        return md

    @mcp.resource("orbit://inventory")
    def get_technology_inventory() -> str:
        """Devuelve un inventario consolidado de tecnologías encontradas en el Grafo de Conocimiento."""
        storage = indexer_engine.builder.storage
        with storage._get_connection(storage.index_db) as conn:
            cursor = conn.cursor()
            # Obtener relaciones entre documentos y tecnologías
            cursor.execute("""
                SELECT n.name as tech, e.source as doc
                FROM nodes n
                JOIN edges e ON n.id = e.target
                WHERE n.type = 'Technology' AND e.relation = 'USES'
            """)
            rows = cursor.fetchall()
            
        tech_map = {}
        for r in rows:
            tech = r["tech"]
            doc = r["doc"].replace("doc:", "")
            tech_map.setdefault(tech, []).append(doc)
            
        md = "# ORBIT Technology Inventory\n\n"
        if not tech_map:
            md += "No se han detectado tecnologías específicas todavía.\n"
            return md
            
        for tech, docs in sorted(tech_map.items()):
            md += f"### {tech.upper()}\n"
            for d in sorted(docs):
                md += f"- [{d}](file://{settings.ROOT}/{d})\n"
            md += "\n"
        return md

