import fnmatch
from pathlib import Path
from typing import Iterator
from orbit_knowledge.config import settings
from orbit_knowledge.cache.lru import LRUCache

# Instancia global de caché de contenido de archivos (guardando tuplas de contenido y mtime)
file_cache: LRUCache = LRUCache(settings.CACHE_SIZE)

def resolve_path(relative_path: str) -> Path:
    """
    Resuelve una ruta con respecto a settings.ROOT.
    Valida y previene ataques de Path Traversal asegurando que el destino final
    permanezca bajo el subárbol de ROOT.
    """
    resolved_root = settings.ROOT.resolve()
    
    if not relative_path:
        return resolved_root

    path_obj = Path(relative_path)
    
    # Combinar y resolver la ruta absoluta
    resolved_target = (resolved_root / path_obj).resolve()
    
    try:
        resolved_target.relative_to(resolved_root)
    except ValueError:
        raise ValueError("Acceso denegado. Intento de path traversal o escape de raíz detectado.")
        
    return resolved_target

def is_dangerous_file(path: Path) -> bool:
    """
    Verifica si un archivo coincide con los patrones de la lista negra de seguridad.
    """
    name_lower = path.name.lower()
    for pattern in settings.DANGEROUS_PATTERNS:
        if fnmatch.fnmatch(name_lower, pattern.lower()):
            return True
    return False

def is_allowed_file(path: Path) -> bool:
    """
    Determina si un archivo cumple con los requisitos de tamaño, extensión y seguridad.
    """
    try:
        if not path.is_file():
            return False
        if is_dangerous_file(path):
            return False
        if path.suffix.lower() not in settings.ALLOWED_EXTENSIONS:
            return False
        
        # Validar tamaño máximo
        size_mb = path.stat().st_size / (1024 * 1024)
        if size_mb > settings.MAX_FILE_SIZE_MB:
            return False
    except OSError:
        return False
    return True

def safe_read(path: Path) -> str:
    """
    Lee el contenido del archivo de disco validando seguridad y aplicando fallback de codificación.
    """
    if not path.exists():
        raise FileNotFoundError(f"El archivo no existe: {path}")
    if not path.is_file():
        raise ValueError(f"La ruta no apunta a un archivo válido: {path}")
    if is_dangerous_file(path):
        raise PermissionError(f"Acceso denegado a archivo protegido por políticas de seguridad: {path.name}")
        
    try:
        size_mb = path.stat().st_size / (1024 * 1024)
    except OSError as e:
        raise ValueError(f"No se pudo determinar el tamaño del archivo: {e}")
        
    if size_mb > settings.MAX_FILE_SIZE_MB:
        raise ValueError(f"El archivo supera el tamaño máximo permitido de {settings.MAX_FILE_SIZE_MB}MB.")
        
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # Fallback seguro a UTF-8 resiliente
        return path.read_text(encoding="utf-8", errors="replace")

def iter_allowed_files(directory: Path) -> Iterator[Path]:
    """
    Genera de forma diferida (Lazy Iteration) los archivos permitidos dentro de un directorio.
    """
    if not directory.exists() or not directory.is_dir():
        return
    for path in directory.rglob("*"):
        try:
            if path.is_file() and is_allowed_file(path):
                yield path
        except OSError:
            continue

# --- Funciones Públicas Legacy ---

def list_files(folder: str = "") -> list[str]:
    """
    Lista archivos permitidos (relativos a ROOT) aplicando límites DoS.
    """
    path = resolve_path(folder)
    if not path.exists() or not path.is_dir():
        return []

    files_list: list[str] = []
    for f in path.rglob("*"):
        try:
            if f.is_file() and is_allowed_file(f):
                files_list.append(str(f.relative_to(settings.ROOT)))
                if len(files_list) >= settings.MAX_LISTED_FILES:
                    break
        except OSError:
            continue
            
    return sorted(files_list)

def read_file(file_path: str) -> str:
    """
    Lee un archivo utilizando caché LRU y validando fecha de modificación.
    """
    path = resolve_path(file_path)
    
    try:
        current_mtime = path.stat().st_mtime
    except OSError as e:
        raise FileNotFoundError(f"El archivo no existe o no se puede acceder: {e}")

    # Verificar coincidencia en caché
    cached = file_cache.get(str(path))
    if cached is not None:
        content, cached_mtime = cached
        if cached_mtime == current_mtime:
            return content

    # Cargar y guardar en caché
    content = safe_read(path)
    file_cache.set(str(path), (content, current_mtime))
    return content

def read_multiple(files: list[str]) -> dict[str, str]:
    """
    Lee múltiples archivos de forma segura por lote.
    """
    if len(files) > settings.MAX_RESULTS:
        raise ValueError(f"Excedido el límite máximo de lectura por lote de {settings.MAX_RESULTS} archivos.")
        
    results: dict[str, str] = {}
    for f in files:
        results[f] = read_file(f)
    return results

def build_tree_lines(path: Path, prefix: str = "", depth: int = 1) -> list[str]:
    """
    Genera de forma recursiva las líneas del árbol ASCII para la ruta especificada.
    """
    if depth > settings.MAX_TREE_DEPTH:
        return [f"{prefix}└── ... (límite de profundidad de árbol alcanzado)"]

    lines: list[str] = []
    try:
        children = sorted(
            list(path.iterdir()),
            key=lambda x: (x.is_dir(), x.name.lower())
        )
    except OSError:
        return []

    original_count = len(children)
    max_children = 200
    if original_count > max_children:
        children = children[:max_children]

    count = len(children)
    for i, child in enumerate(children):
        is_last = (i == count - 1) and (original_count == count)
        connector = "└── " if is_last else "├── "
        lines.append(f"{prefix}{connector}{child.name}")
        
        if child.is_dir():
            new_prefix = prefix + ("    " if is_last else "│   ")
            lines.extend(build_tree_lines(child, new_prefix, depth + 1))

    if original_count > count:
        lines.append(f"{prefix}└── ... (truncado, mostrando {count} de {original_count} elementos)")
            
    return lines

def tree(folder: str = "") -> str:
    """
    Genera la estructura en formato de árbol ASCII del directorio especificado.
    """
    path = resolve_path(folder)
    if not path.exists():
        raise ValueError("El directorio no existe.")
    if not path.is_dir():
        raise ValueError("La ruta especificada no es un directorio.")
        
    lines = [path.name or str(path)]
    lines.extend(build_tree_lines(path))
    return "\n".join(lines)
