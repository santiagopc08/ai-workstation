from dataclasses import dataclass, field
from typing import Any

@dataclass(slots=True, frozen=True)
class FileMetadata:
    """Metadatos del sistema de archivos para control de cambios."""
    size_bytes: int
    modified_time: float
    is_symlink: bool

@dataclass(slots=True, frozen=True)
class FileInfo:
    """Representa un documento indexado y estructurado en la base de conocimiento."""
    path: str
    project: str
    extension: str
    title: str
    size: int
    hash: str
    modified: float
    headings: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    summary: str = ""

@dataclass(slots=True, frozen=True)
class Chunk:
    """Fragmento de documento optimizado para inyección de RAG y futuros embeddings."""
    id: str
    document: str
    project: str
    section: str
    title: str
    start_line: int
    end_line: int
    text: str
    hash: str

@dataclass(slots=True, frozen=True)
class SearchResult:
    """Coincidencia estructurada tras búsqueda en el motor de conocimiento."""
    file: str
    line: int
    text: str
    score: float

    def to_dict(self) -> dict[str, Any]:
        """Convierte a diccionario compatible con la API legacy del cliente."""
        return {
            "file": self.file,
            "line": self.line,
            "text": self.text,
            "score": round(self.score, 4)
        }

@dataclass(slots=True, frozen=True)
class TreeNode:
    """Nodo estructurado para representación de árboles ASCII de conocimiento."""
    name: str
    is_dir: bool
    children: list["TreeNode"] = field(default_factory=list)
