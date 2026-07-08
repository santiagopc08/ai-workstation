# API.md - ORBIT Knowledge Engine API

Este documento contiene la especificación de la interfaz pública (Tools, Resources y Prompts) expuesta por el servidor MCP **ORBIT Knowledge Engine v2.0**.

---

## 1. Herramientas MCP (Tools)

### 1.1 Herramientas de Proyectos

#### `list_projects`
Lista todos los proyectos indexados en la base de conocimiento.
- **Parámetros:** *Ninguno*
- **Retorno:** `list[str]`

#### `project_summary`
Genera un resumen estructurado en Markdown del proyecto dado.
- **Parámetros:** `project` (string)
- **Retorno:** `str` (Markdown)

#### `project_tree`
Genera la estructura de árbol ASCII del proyecto especificado.
- **Parámetros:** `project` (string)
- **Retorno:** `str` (ASCII Tree)

#### `project_documents`
Lista los archivos pertenecientes al proyecto especificado.
- **Parámetros:** `project` (string)
- **Retorno:** `list[str]` (Rutas relativas)

#### `project_metadata`
Devuelve metadatos consolidados del volumen de archivos y tags del proyecto.
- **Parámetros:** `project` (string)
- **Retorno:** `dict[str, Any]`

---

### 1.2 Herramientas de Documentación y Conocimiento

#### `find_document`
Localiza documentos indexados por coincidencia parcial de nombre de archivo.
- **Parámetros:** `name` (string)
- **Retorno:** `list[str]`

#### `search_documentation`
Busca un texto en toda la documentación indexada devolviendo un ranking por relevancia (score).
- **Parámetros:** `query` (string)
- **Retorno:** `list[dict]`
  - Cada elemento contiene: `file` (str), `line` (int), `text` (str), `score` (float: 0.01 a 0.99).

#### `summarize_document`
Devuelve el resumen de metadatos o contenido inicial de un documento indexado.
- **Parámetros:** `path` (string)
- **Retorno:** `str` (Markdown)

#### `related_documents`
Devuelve documentos relacionados que comparten etiquetas (tags) con el archivo dado.
- **Parámetros:** `path` (string)
- **Retorno:** `list[str]`

---

### 1.3 Herramientas de Arquitectura y Stack

#### `get_architecture`
Extrae la arquitectura descrita en los documentos de especificación del proyecto.
- **Parámetros:** `project` (string)
- **Retorno:** `str` (Markdown)

#### `get_stack`
Obtiene la pila de tecnologías deducida a partir del análisis del proyecto.
- **Parámetros:** `project` (string)
- **Retorno:** `list[str]`

#### `get_dependencies`
Lista todas las importaciones y librerías declaradas en el código Python del proyecto.
- **Parámetros:** `project` (string)
- **Retorno:** `list[str]`

#### `get_services`
Lista los servicios definidos en archivos Docker Compose en el proyecto.
- **Parámetros:** `project` (string)
- **Retorno:** `list[str]`

---

### 1.4 Herramientas del Índice

#### `build_index`
Inicia una compilación incremental del índice sincronizando cambios.
- **Parámetros:** *Ninguno*
- **Retorno:** `dict` (Estadísticas del índice)

#### `rebuild_index`
Wipea el índice existente y ejecuta una compilación total en frío.
- **Parámetros:** *Ninguno*
- **Retorno:** `dict` (Estadísticas del índice)

#### `index_status`
Retorna las estadísticas del índice y los proyectos cargados.
- **Parámetros:** *Ninguno*
- **Retorno:** `dict`

#### `refresh_project`
Actualiza de forma exclusiva los archivos que pertenezcan al proyecto especificado.
- **Parámetros:** `project` (string)
- **Retorno:** `dict`

---

### 1.5 Herramientas Legacy (Compatibilidad)

El servidor mantiene total compatibilidad y firma con las siguientes herramientas para no romper Open WebUI:
- `list_files(folder)`
- `read_file(file_path)`
- `search_files(pattern)`
- `search_content(query)`
- `tree(folder)`
- `read_multiple(files)`

---

## 2. Recursos MCP (Resources)

El servidor expone URIs de recursos que los agentes pueden leer de forma directa:

1.  **`knowledge://{file_path}`:** Contenido en caliente de cualquier archivo permitido.
2.  **`orbit://projects`:** Listado de proyectos en Markdown.
3.  **`orbit://architecture`:** Consolidador de la arquitectura de todos los proyectos indexados.
4.  **`orbit://stacks`:** Resumen de las pilas de tecnologías por proyecto.
5.  **`orbit://index`:** Estado y estadísticas del índice en JSON.
6.  **`orbit://config`:** Variables de entorno y configuración del motor.

---

## 3. Prompts MCP (Prompts)

Plantillas de prompts pre-diseñadas y expuestas de manera nativa para guiar a los agentes:

- `SummarizeProject(project)`
- `ExplainArchitecture(project)`
- `ReviewDocumentation(path)`
- `FindConfiguration(project)`
- `LocateService(project, service)`
- `GenerateADR(project, decision)`
- `ReviewMarkdown()`
