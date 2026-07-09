# CHUNKING_STRATEGY.md - ORBIT Chunks Segmentation Strategy

Este documento describe las reglas y metodologías empleadas por el **ORBIT Chunker Engine** (`knowledge/indexing/chunker.py`) para fragmentar documentos de conocimiento semánticamente sin romper la coherencia del contenido.

---

## 1. Reglas Generales
- **Orientado a Semántica:** No se realizan cortes ciegos por número fijo de caracteres o palabras, excepto como último recurso para evitar pérdida de información.
- **Rastreo de Líneas:** Cada fragmento retiene la propiedad exacta de su rango de líneas de inicio (`start_line`) y fin (`end_line`) para habilitar referencias precisas e inyección de contexto acotado al LLM.

---

## 2. Estrategia de Markdown
El fraccionador de Markdown opera de manera jerárquica:

1.  **Agrupación por H2 (`## `):** El texto se divide por encabezados de segundo nivel. Si la sección completa mide menos de `CHUNK_SIZE` (1000 caracteres por defecto), se guarda como un único chunk.
2.  **Sub-división por H3 (`### `):** Si una sección H2 excede el tamaño, se segmenta por sus encabezados H3.
3.  **Párrafos (`\n\n`):** Si un sub-bloque H3 sigue superando la longitud, se separa a nivel de párrafos.
4.  **Corte por ventana:** Si un único párrafo de texto plano sigue siendo superior a `CHUNK_SIZE`, se rebana secuencialmente con un solapamiento de seguridad (`CHUNK_OVERLAP`).

---

## 3. Estrategia de Código Python
Utiliza el árbol de sintaxis abstracta estándar (`ast` de Python) para extraer fragmentos coherentes:

1.  **Clases completas (`ast.ClassDef`):** Cada clase (incluyendo docstrings, variables de clase y todos sus métodos) se empaqueta como un fragmento unitario de código.
2.  **Funciones y métodos (`ast.FunctionDef`):** Las funciones globales o asíncronas independientes se indexan en sus propios fragmentos de inicio a fin.
3.  **Fallback de Párrafos:** En caso de fallas de sintaxis o archivos rotos, se recurre a la segmentación genérica de bloques de texto.

---

## 4. Estrategia de Datos JSON
1.  **Sub-objetos de primer nivel:** Dado un diccionario JSON en la raíz, se extrae cada par clave-valor, se formatea en JSON estructurado indentado con 2 espacios, y se guarda como un chunk individual (ej: `{"key": "value"}`).
2.  **Elementos de lista de primer nivel:** Si el JSON es una lista, se extrae cada elemento de la lista por separado.
3.  **Fallback Completo:** Si no cumple los criterios anteriores, se indexa el documento JSON completo en crudo.
