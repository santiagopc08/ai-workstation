# ORBIT Knowledge Troubleshooting

Soluciones a problemas comunes encontrados durante el despliegue de ORBIT Knowledge.

## 1. Conflicto de namespaces (ModuleNotFoundError: No module named 'mcp.tools')

### Causa:
El paquete local de utilidades MCP `knowledge/mcp/` colisiona con la librería oficial del SDK de MCP (`mcp`) instalada en site-packages.

### Solución:
Hemos solucionado este problema agregando `__init__.py` al subdirectorio local `mcp/` y estructurando la importación a nivel de paquete como `knowledge.mcp` en lugar de `mcp` de nivel superior. Evita añadir el subdirectorio `knowledge/` de manera directa a los primeros lugares de `sys.path`.

## 2. SQLite base de datos bloqueada (Database locked)

### Solución:
Asegúrate de que no existan múltiples procesos escribiendo al mismo archivo SQLite. El motor activa el modo WAL (Write-Ahead Logging) y un timeout de 30 segundos por defecto para evitar colisiones de concurrencia en SQLite. Puedes aumentarlo mediante la variable de entorno `ORBIT_SQLITE_TIMEOUT`.

## 3. ChromaDB o LM Studio Inalcanzable

### Solución:
Ejecuta `orbit-knowledge doctor` para validar que los puertos locales correspondientes (8000 para Chroma, 1234 para LM Studio) están en escucha y que tus servicios externos están iniciados.
