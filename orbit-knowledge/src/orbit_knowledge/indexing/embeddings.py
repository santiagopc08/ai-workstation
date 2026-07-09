import json
import hashlib
import random
import urllib.request
from abc import ABC, abstractmethod
from typing import Any
from orbit_knowledge.config import settings

class EmbeddingProvider(ABC):
    """
    Interfaz abstracta para definir proveedores de embeddings de vectores.
    Asegura desacoplamiento de servicios externos.
    """
    @abstractmethod
    def generate_embedding(self, text: str) -> list[float]:
        """Genera vector de embedding para una cadena de texto."""
        pass
        
    @abstractmethod
    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Genera múltiples vectores en lote."""
        pass


class MockEmbeddingProvider(EmbeddingProvider):
    """
    Proveedor offline mock. Genera vectores deterministas mediante
    hashing del contenido para evitar llamadas de red durante tests o desarrollo local offline.
    """
    def __init__(self, dimension: int = 384) -> None:
        self.dimension = dimension

    def generate_embedding(self, text: str) -> list[float]:
        # Inicializar generador pseudo-aleatorio con el hash de la cadena para hacerlo determinista
        seed = int(hashlib.md5(text.encode("utf-8")).hexdigest(), 16) % (2**32)
        rng = random.Random(seed)
        return [rng.uniform(-1.0, 1.0) for _ in range(self.dimension)]

    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        return [self.generate_embedding(t) for t in texts]


class BaseHttpEmbeddingProvider(EmbeddingProvider):
    """
    Clase base para proveedores HTTP. Utiliza urllib de la librería estándar
    para evitar agregar dependencias externas complejas.
    """
    def __init__(self, url: str, headers: dict[str, str], payload_builder: Any) -> None:
        self.url = url
        self.headers = headers
        self.payload_builder = payload_builder

    def _post(self, payload: dict[str, Any]) -> dict[str, Any]:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(self.url, data=data, headers=self.headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=10.0) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as e:
            raise RuntimeError(f"Error HTTP contactando al proveedor de embeddings ({self.url}): {e}")

    def generate_embedding(self, text: str) -> list[float]:
        results = self.generate_embeddings([text])
        return results[0] if results else []

    @abstractmethod
    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        pass


class LMStudioEmbeddingProvider(BaseHttpEmbeddingProvider):
    """
    Adaptador para embeddings locales servidos por LM Studio.
    """
    def __init__(self, model: str = "nomic-embed-text") -> None:
        headers = {"Content-Type": "application/json"}
        url = "http://localhost:1234/v1/embeddings"
        super().__init__(url, headers, None)
        self.model = model

    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        payload = {
            "model": self.model,
            "input": texts
        }
        res = self._post(payload)
        # Parsear respuesta estándar de OpenAI/LMStudio
        return [item["embedding"] for item in res.get("data", [])]


class OllamaEmbeddingProvider(BaseHttpEmbeddingProvider):
    """
    Adaptador para embeddings locales servidos por Ollama.
    """
    def __init__(self, model: str = "nomic-embed-text") -> None:
        headers = {"Content-Type": "application/json"}
        url = "http://localhost:11434/api/embed"
        super().__init__(url, headers, None)
        self.model = model

    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        payload = {
            "model": self.model,
            "input": texts
        }
        res = self._post(payload)
        return res.get("embeddings", [])


class OpenAIEmbeddingProvider(BaseHttpEmbeddingProvider):
    """
    Adaptador para la API oficial de OpenAI.
    """
    def __init__(self, api_key: str, model: str = "text-embedding-3-small") -> None:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        url = "https://api.openai.com/v1/embeddings"
        super().__init__(url, headers, None)
        self.model = model

    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        payload = {
            "model": self.model,
            "input": texts
        }
        res = self._post(payload)
        return [item["embedding"] for item in res.get("data", [])]


class VoyageEmbeddingProvider(BaseHttpEmbeddingProvider):
    """
    Adaptador para la API de Voyage AI.
    """
    def __init__(self, api_key: str, model: str = "voyage-3") -> None:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        url = "https://api.voyageai.com/v1/embeddings"
        super().__init__(url, headers, None)
        self.model = model

    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        payload = {
            "model": self.model,
            "input": texts
        }
        res = self._post(payload)
        return res.get("embeddings", [])


def get_embedding_provider() -> EmbeddingProvider:
    """
    Fábrica para resolver el proveedor configurado en Settings.
    """
    provider_name = settings.EMBEDDING_PROVIDER.lower()
    
    if provider_name == "lmstudio":
        return LMStudioEmbeddingProvider()
    elif provider_name == "ollama":
        return OllamaEmbeddingProvider()
    elif provider_name == "openai":
        api_key = getattr(settings, "OPENAI_API_KEY", "")
        return OpenAIEmbeddingProvider(api_key)
    elif provider_name == "voyage":
        api_key = getattr(settings, "VOYAGE_API_KEY", "")
        return VoyageEmbeddingProvider(api_key)
    else:
        # Fallback por defecto: Mock offline determinista
        return MockEmbeddingProvider()
