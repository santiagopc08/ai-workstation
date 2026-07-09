from fastmcp import FastMCP

def register_prompts(mcp: FastMCP) -> None:
    """Registra plantillas de prompts reutilizables en la instancia de FastMCP."""

    @mcp.prompt()
    def SummarizeProject(project: str) -> str:
        """Prompt para generar resúmenes consolidados del proyecto."""
        return (
            f"Actúa como un experto en ingeniería del conocimiento. "
            f"Analiza la documentación disponible para el proyecto '{project}' y crea un resumen de alto nivel que incluya:\n"
            f"1. Objetivo del proyecto y metas clave.\n"
            f"2. Pila tecnológica (stack) y dependencias principales.\n"
            f"3. Resumen funcional de cada documento y archivo indexado.\n"
            f"Usa las herramientas de proyectos (ej. project_summary) para guiar tu recopilación."
        )

    @mcp.prompt()
    def ExplainArchitecture(project: str) -> str:
        """Prompt para auditar y explicar la arquitectura técnica de un proyecto."""
        return (
            f"Analiza y describe la arquitectura de software del proyecto '{project}'. "
            f"Extrae y detalla:\n"
            f"1. Descomposición modular y flujo de control principal.\n"
            f"2. Servicios locales y de red expuestos (ej. Docker Compose).\n"
            f"3. Dependencias de importaciones de código y bibliotecas.\n"
            f"4. Registros de decisión de diseño o arquitectura (ADR) encontrados.\n"
            f"Utiliza las herramientas 'get_architecture', 'get_dependencies' y 'get_services' como entrada."
        )

    @mcp.prompt()
    def ReviewDocumentation(path: str) -> str:
        """Prompt para auditar la documentación técnica de un documento específico."""
        return (
            f"Realiza una revisión técnica y editorial del documento ubicado en '{path}'. "
            f"Evalúa críticamente:\n"
            f"1. Completitud de la información técnica básica.\n"
            f"2. Claridad, coherencia terminológica y estructura general.\n"
            f"3. Calidad del Markdown empleado y validez de bloques de código y referencias."
        )

    @mcp.prompt()
    def FindConfiguration(project: str) -> str:
        """Prompt para auditar las configuraciones dispersas del proyecto."""
        return (
            f"Analiza los archivos de configuración (YAML, JSON, TOML, .env) "
            f"en el proyecto '{project}'. Clasifícalos por entorno de ejecución e identifica las variables clave."
        )

    @mcp.prompt()
    def LocateService(project: str, service: str) -> str:
        """Prompt para rastrear la especificación y despliegue de un contenedor/servicio."""
        return (
            f"Localiza la definición y configuración del servicio '{service}' "
            f"en el proyecto '{project}'. Describe sus puertos, variables de entorno, y volúmenes montados."
        )

    @mcp.prompt()
    def GenerateADR(project: str, decision: str) -> str:
        """Prompt para redactar un Registro de Decisión de Arquitectura (ADR) formal."""
        return (
            f"Redacta un borrador de Registro de Decisión de Arquitectura (ADR) formal para el proyecto '{project}' "
            f"sobre la decisión: '{decision}'. Usa la plantilla estándar (Estatus, Contexto, Decisión, Consecuencias)."
        )

    @mcp.prompt()
    def ReviewMarkdown() -> str:
        """Prompt general para revisar y mejorar el estilo visual y estructural de un documento Markdown."""
        return (
            "Audita el contenido Markdown provisto. Valida que mantenga una jerarquía de títulos limpia (un solo H1), "
            "enlaces y bloques de código válidos, y el uso correcto de alertas informativas (NOTE, WARNING, IMPORTANT)."
        )
