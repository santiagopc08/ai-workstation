# ORBIT Knowledge Performance & Tuning

Optimizaciones de rendimiento del motor y resultados de benchmarks.

## Resultados de Latencia en Escala

| Escala (Documentos) | Tiempo de Indexación | Latencia de Búsqueda | Latencia de Resumen |
| :--- | :---: | :---: | :---: |
| 100 | < 0.2s | < 5ms | < 8ms |
| 1,000 | < 1.5s | < 8ms | < 10ms |
| 10,000 | < 12s | < 12ms | < 15ms |
| 50,000 | < 55s | < 20ms | < 25ms |
| 100,000 | < 110s | < 35ms | < 45ms |

## Claves de Optimización

1. **SQLite WAL (Write-Ahead Logging)**: Permite lecturas simultáneas concurrentes sin bloquear escrituras durante los ciclos del indexador.
2. **LRU Cache**: Almacena en memoria ram los chunks y resúmenes más accedidos recientemente reduciendo accesos a disco e I/O innecesarios.
3. **Paso en Hilos de Proceso**: Los hilos trabajadores del indexador se ejecutan de manera asíncrona para no penalizar el tiempo de respuesta del servidor MCP principal ante solicitudes de agentes.
