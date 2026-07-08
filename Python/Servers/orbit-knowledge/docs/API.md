# ORBIT Knowledge API Reference

La interfaz pública del servidor MCP expone herramientas, recursos y plantillas para agentes inteligentes y sistemas RAG.

## Herramientas MCP (Tools)

- **`list_files` / `read_file` / `search_files`**: Operaciones tradicionales sobre el sistema de archivos local bajo la raíz de conocimiento.
- **`search_documentation` / `summarize_document`**: Búsqueda semántica híbrida y resúmenes automáticos.
- **`get_architecture` / `get_stack` / `get_dependencies` / `get_services`**: Consultas basadas en el grafo relacional de tecnologías.
- **`list_projects` / `project_summary` / `project_metadata`**: Información estructural de los proyectos indexados.

## Recursos MCP (Resources)

- **`projects://summary`**: Resumen del estado de indexación y salud global.
- **`projects://technologies`**: Inventario completo de stacks detectados.

## Prompts MCP

- **`project-onboarding`**: Plantilla estructurada para guiar al modelo en la lectura de dependencias de un nuevo repositorio indexado.
