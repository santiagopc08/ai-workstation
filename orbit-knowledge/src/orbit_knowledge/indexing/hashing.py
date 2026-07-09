import hashlib
from pathlib import Path

def compute_sha256(path: Path) -> str:
    """
    Calcula el hash SHA256 de un archivo en disco de manera eficiente en memoria
    utilizando lectura por bloques de 4KB.
    """
    sha256 = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256.update(byte_block)
        return sha256.hexdigest()
    except OSError:
        return ""
