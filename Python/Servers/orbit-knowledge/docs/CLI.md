# ORBIT Knowledge CLI

El comando CLI principal `orbit-knowledge` centraliza la administración y diagnósticos del motor.

## Subcomandos Disponibles

### 1. `orbit-knowledge serve`
Inicia el servidor MCP utilizando el puerto y transporte configurados (por defecto http/stdio).
- **Opciones:**
  - `--root <path>`: Sobrescribe el directorio base de conocimiento.
  - `--watcher`: Activa el watcher incremental en caliente.
  - `--log-level <DEBUG|INFO|WARNING|ERROR|TRACE>`: Define el nivel de verbosidad del logger.

### 2. `orbit-knowledge benchmark`
Ejecuta la suite interna de tests de estrés para evaluar el retardo de indexación de 100 a 100K documentos sobre hardware local.

### 3. `orbit-knowledge evaluate`
Ejecuta la suite de pruebas de contratos y métricas de recuperación (Recall, Precision, F1, Hallucination) a partir del set de 150 preguntas.

### 4. `orbit-knowledge rebuild`
Inicia un reindexado de todos los documentos ignorando firmas existentes (cold index rebuild).

### 5. `orbit-knowledge doctor`
Ejecuta diagnósticos rápidos del estado de Python, SQLite WAL, rutas de almacenamiento, permisos y conectividad de puertos locales (ChromaDB, Open WebUI, LM Studio).

### 6. `orbit-knowledge version`
Muestra la versión semántica actual instalada en el sistema.
