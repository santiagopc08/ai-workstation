# ORBIT Filesystem MCP Server v1.2

Servidor de Protocolo de Contexto de Modelo (MCP) de calidad de producción para interactuar con la base de conocimiento local de ORBIT de forma segura. Optimizado para entornos locales sobre macOS (Apple Silicon).

---

## 1. Arquitectura del Proyecto

El servidor se ha estructurado bajo los principios de separación de responsabilidades (SRP) y diseño modular:

```text
               +----------------------------------------+
               |               server.py                | (MCP Entry & Routing)
               +-------------------+--------------------+
                                   |
                     +-------------+-------------+
                     |                           |
                     v                           v
         +-----------+-----------+   +-----------+-----------+
         |     filesystem.py     |   |       search.py       | (Business Logic)
         +-----------+-----------+   +-----------+-----------+
                     |                           |
                     +-------------+-------------+
                                   |
                                   v
                       +-----------+-----------+
                       |       utils.py        | (Security & Cache Layer)
                       +-----------+-----------+
                                   |
                     +-------------+-------------+
                     |                           |
                     v                           v
         +-----------+-----------+   +-----------+-----------+
         |       models.py       |   |       config.py       | (Structures & Settings)
         +-----------------------+   +-----------------------+
```

---

## 2. Flujo de Control MCP

El procesamiento de una solicitud sigue el siguiente flujo secuencial de capas:

```text
Open WebUI (MCP Client)
      ↓
Tool Call / Resource Request (HTTP Port 8001 /mcp)
      ↓
FastMCP (Protocol Deserialization & Route Dispatching)
      ↓
logging_config.py (@log_tool_call decorador que inyecta request_id)
      ↓
Filesystem Layer (filesystem.py / search.py / tree.py)
      ↓
Security Layer (utils.resolve_path / blacklist check / LRU Cache)
      ↓
Knowledge (Local Directory)
```

---

## 3. Decisiones Técnicas y Rationale

*   **¿Por qué `pathlib`?**
    Proporciona abstracciones orientadas a objetos seguras y consistentes para interactuar con el sistema de archivos de macOS. Facilita la resolución absoluta mediante `.resolve()` e impide el Path Traversal de forma más legible y robusta que la manipulación manual de strings con `os.path`.
*   **¿Por qué `@dataclass(slots=True, frozen=True)`?**
    La inmutabilidad (`frozen=True`) evita modificaciones accidentales de datos en memoria entre hilos. Los `slots` eliminan el diccionario dinámico interno de atributos (`__dict__`), reduciendo drásticamente la latencia y la memoria ocupada por instancia (clave para el rendimiento sobre Apple Silicon).
*   **¿Por qué Caché LRU personalizado con validación de modificación?**
    Las lecturas constantes a disco son costosas. Se implementó un Caché LRU thread-safe con exclusión mutua que guarda pares de `(contenido, mtime)`. Si el archivo en disco cambia, el caché detecta que el `mtime` actual difiere y recarga el contenido de forma transparente, eliminando datos stale con latencia cero en lecturas concurrentes.
*   **¿Por qué límites de DoS estrictos?**
    Un modelo de lenguaje podría solicitar involuntariamente el escaneo de miles de carpetas o la generación de árboles ASCII masivos. Se definieron límites máximos en recursión (`MAX_TREE_DEPTH`), en archivos listados (`MAX_LISTED_FILES`), en tamaño (`MAX_FILE_SIZE_MB = 5`) y truncado por nivel en el árbol para evitar agotar la CPU y memoria del sistema anfitrión.

---

## 4. MCP Best Practices

### Recursos expuestos (`@mcp.resource`)
El servidor expone el esquema URI `knowledge://{file_path}` como un recurso nativo de lectura. Esto permite a los clientes MCP consultar archivos directamente de la base de conocimiento sin invocar una herramienta.

### Prompts de diseño (Planificados)
Se han diseñado los siguientes prompts reutilizables para guiar el análisis documental (documentados para su futura activación):
1.  **`ReviewDocument`:** Prepara al modelo para realizar una auditoría de código, ortografía, estructura y estilo del documento especificado.
2.  **`SummarizeProject`:** Insta al modelo a buscar archivos clave en la base de conocimiento y estructurar un resumen de alto nivel de las metas, dependencias y estado del proyecto.
3.  **`FindArchitecture`:** Diseñado para escanear archivos `.md` y `.py` buscando diagramas, imports y definiciones estructurales a fin de mapear la arquitectura del software.

---

## 5. Ejecución de Pruebas y Benchmarks

### Tests Unitarios
Para correr las pruebas unitarias que validan la seguridad y resiliencia:
```bash
python -m unittest discover -s Python/Servers/orbit-filesystem/tests
```

### Benchmark de Carga
Para medir latencias bajo bases de conocimiento simuladas de 100, 1,000 y 10,000 archivos:
```bash
python Python/Servers/orbit-filesystem/tests/benchmark.py
```
El benchmark generará automáticamente el archivo [PERFORMANCE_REPORT.md](file:///Users/santi/AI/ai-workstation/Python/Servers/orbit-filesystem/PERFORMANCE_REPORT.md).
