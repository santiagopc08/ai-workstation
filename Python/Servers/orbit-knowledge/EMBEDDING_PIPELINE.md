# EMBEDDING_PIPELINE.md - ORBIT Vector Embeddings Pipeline

Este documento describe la especificación de la tubería de generación, almacenamiento y recuperación de vectores de embeddings del **ORBIT Indexer Engine v1.0**.

---

## 1. Diseño del Pipeline

El cálculo de embeddings es la operación más pesada en términos de cómputo y latencia. Por ello, se implementan tres niveles de protección:

1.  **Indexación incremental por hashes:** Si el archivo no ha cambiado (su hash SHA256 es idéntico al guardado), se omite por completo su lectura y re-procesamiento.
2.  **Caché persistente en Base de Datos:** Los embeddings calculados para cada chunk se guardan en la tabla `embeddings` de `embeddings.db` indexados por `chunk_id`. Si un documento se re-indexa pero un chunk conserva el mismo texto hash, el embedding anterior se reutiliza inmediatamente sin consultar a la API de Inteligencia Artificial.
3.  **Llamadas en lote (Batching):** Los adaptadores HTTP admiten la entrada de múltiples textos en una única solicitud de red.

---

## 2. Especificación de la Interfaz

Cualquier adaptador de cálculo de vectores debe implementar la clase abstracta `EmbeddingProvider`:

```python
class EmbeddingProvider(ABC):
    @abstractmethod
    def generate_embedding(self, text: str) -> list[float]:
        """Genera el vector del texto individual."""
        pass
        
    @abstractmethod
    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Genera embeddings para una lista de textos de forma eficiente."""
        pass
```

---

## 3. Adaptadores HTTP Soportados

- **LM Studio (`LMStudioEmbeddingProvider`):** Contacta con `http://localhost:1234/v1/embeddings` (modelo por defecto: `nomic-embed-text`).
- **Ollama (`OllamaEmbeddingProvider`):** Contacta con `http://localhost:11434/api/embed` (modelo por defecto: `nomic-embed-text`).
- **OpenAI (`OpenAIEmbeddingProvider`):** Contacta con la API oficial de OpenAI (`https://api.openai.com/v1/embeddings`) mediante claves de entorno y modelo `text-embedding-3-small`.
- **Voyage AI (`VoyageEmbeddingProvider`):** Utiliza Voyage AI con modelos de alta densidad.

---

## 4. Proveedor Offline Mock (`MockEmbeddingProvider`)

Para posibilitar el desarrollo local desconectado y asegurar que el set de pruebas unitarias funcione sin dependencias externas:
- Se implementa un generador de vectores determinista.
- Semilla el generador pseudo-aleatorio de Python (`random.Random(hash)`) con el valor MD5 del fragmento de texto a indexar.
- Genera un vector de longitud 384 determinista: el mismo fragmento textual siempre producirá el mismo vector de embedding exacto con un costo computacional menor a un microsegundo.
