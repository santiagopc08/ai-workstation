# ORBIT Knowledge FAQ

Preguntas frecuentes acerca del funcionamiento de ORBIT Knowledge.

## 1. ¿Cómo gestiona el motor el indexado incremental?
Genera una firma hash SimHash de cada documento y la compara con la guardada en la base de datos de metadatos. Si la firma difiere, el motor realiza el análisis y chunking; de lo contrario, se salta el archivo ahorrando tiempo.

## 2. ¿Qué pasa si el watcher en vivo está deshabilitado?
El indexado incremental no se ejecuta en caliente. No obstante, puedes reconstruir o actualizar el índice bajo demanda usando `orbit-knowledge rebuild` o invocando las herramientas correspondientes.

## 3. ¿Soporta bases de datos remotas?
No. ORBIT está diseñado para ejecutarse localmente con SQLite embebido para garantizar latencias mínimas y la privacidad completa de tus datos.
