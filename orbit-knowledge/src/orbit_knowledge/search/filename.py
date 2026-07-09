from pathlib import Path
from orbit_knowledge.indexing.storage import SQLiteStorageBackend
from orbit_knowledge.config import settings

def search_files(pattern: str) -> list[str]:
    """
    Busca archivos por patrón de nombre consultando directamente
    el almacenamiento SQLite indexado.
    """
    if not pattern:
        return []
        
    pattern_lower = pattern.lower()
    storage = SQLiteStorageBackend()
    docs = storage.list_documents()
    
    results: list[str] = []
    for doc in docs:
        filename = Path(doc.path).name.lower()
        if pattern_lower in filename:
            results.append(doc.path)
            if len(results) >= settings.MAX_LISTED_FILES:
                break
                
    return sorted(results)
