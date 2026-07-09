import threading
from collections import OrderedDict
from typing import Any, Optional

class LRUCache:
    """
    Implementación genérica de Caché LRU (Least Recently Used)
    con soporte multi-hilo mediante bloqueos de exclusión mutua.
    """
    def __init__(self, maxsize: int):
        self.maxsize = maxsize
        self.cache: OrderedDict[Any, Any] = OrderedDict()
        self.lock = threading.Lock()
        
    def get(self, key: Any) -> Optional[Any]:
        """Obtiene un elemento y lo mueve al final de la cola de uso."""
        with self.lock:
            if key not in self.cache:
                return None
            self.cache.move_to_end(key)
            return self.cache[key]
            
    def set(self, key: Any, value: Any) -> None:
        """Inserta o actualiza un elemento, evacuando el menos usado si supera el límite."""
        if self.maxsize <= 0:
            return
        with self.lock:
            if key in self.cache:
                self.cache[key] = value
                self.cache.move_to_end(key)
            else:
                self.cache[key] = value
                if len(self.cache) > self.maxsize:
                    self.cache.popitem(last=False)
                    
    def clear(self) -> None:
        """Vacia por completo la caché."""
        with self.lock:
            self.cache.clear()
