import os
from dataclasses import dataclass, field
from pathlib import Path

@dataclass(slots=True)
class Settings:
    """
    Configuración unificada para el ORBIT Knowledge Engine e Indexer Engine.
    """
    # Directorio raíz de la base de conocimiento de ORBIT
    ROOT: Path = field(
        default_factory=lambda: Path(__file__).resolve().parents[4] / "Knowledge"
    )

    # Configuración de Caché
    CACHE_SIZE: int = 128

    # Seguridad y Archivos Permitidos
    ALLOWED_EXTENSIONS: set[str] = field(
        default_factory=lambda: {
            ".md",
            ".txt",
            ".py",
            ".json",
            ".yaml",
            ".yml",
            ".toml"
        }
    )
    DANGEROUS_PATTERNS: set[str] = field(
        default_factory=lambda: {
            ".env",
            ".env.*",
            "id_rsa",
            "id_ed25519",
            "*.pem",
            "*.key",
            "*.crt",
            "*.db",
            "*.sqlite"
        }
    )
    MAX_FILE_SIZE_MB: int = 5
    MAX_LISTED_FILES: int = 5000
    MAX_TREE_DEPTH: int = 5

    # Configuración de Indexación
    INDEX_FILE_PATH: Path = field(
        default_factory=lambda: Path(__file__).resolve().parents[4] / "Knowledge" / "knowledge.index"
    )

    # Watcher en segundo plano para monitorear el sistema de archivos
    WATCHER_ENABLED: bool = False
    WATCHER_INTERVAL_SECONDS: float = 5.0

    # Configuración de Búsqueda
    MAX_RESULTS: int = 30
    MAX_SEARCH_DEPTH: int = 10

    # Configuración del Motor de Chunking
    CHUNK_SIZE: int = 1000       # Caracteres por fragmento
    CHUNK_OVERLAP: int = 200      # Caracteres de solape entre fragmentos

    # --- NUEVOS PARÁMETROS DEL INDEXER ENGINE v1.0 ---
    WORKERS: int = 2
    BATCH_SIZE: int = 100
    EMBEDDING_PROVIDER: str = "mock"
    SQLITE_TIMEOUT: float = 30.0
    LOGGING_LEVEL: str = "INFO"

    # --- PARÁMETROS DEL RANKING ENGINE v3.0 ---
    RANKING_WEIGHT_BM25: float = 0.3
    RANKING_WEIGHT_SEMANTIC: float = 0.3
    RANKING_WEIGHT_GRAPH: float = 0.1
    RANKING_WEIGHT_RECENCY: float = 0.1
    RANKING_WEIGHT_PROJECT: float = 0.1
    RANKING_WEIGHT_EXACT: float = 0.05
    RANKING_WEIGHT_TAG: float = 0.05

    def load(self, cli_args: dict = None) -> None:
        """
        Carga la configuración siguiendo la prioridad de origen:
        CLI -> ENV -> YAML -> Defaults.
        """
        import yaml
        
        # 1. Cargar desde YAML si existe
        yaml_path = Path("settings.yaml")
        yaml_config = {}
        if yaml_path.exists():
            try:
                with open(yaml_path, "r", encoding="utf-8") as f:
                    yaml_config = yaml.safe_load(f) or {}
            except Exception as e:
                print(f"Error cargando settings.yaml: {e}")
                
        # 2. Mapear y aplicar variables
        fields_to_check = {
            "ROOT": ("ORBIT_ROOT", Path),
            "CACHE_SIZE": ("ORBIT_CACHE_SIZE", int),
            "MAX_FILE_SIZE_MB": ("ORBIT_MAX_FILE_SIZE_MB", int),
            "MAX_LISTED_FILES": ("ORBIT_MAX_LISTED_FILES", int),
            "MAX_TREE_DEPTH": ("ORBIT_MAX_TREE_DEPTH", int),
            "INDEX_FILE_PATH": ("ORBIT_INDEX_FILE_PATH", Path),
            "WATCHER_ENABLED": ("ORBIT_WATCHER_ENABLED", lambda x: str(x).lower() in ("true", "1", "yes")),
            "WATCHER_INTERVAL_SECONDS": ("ORBIT_WATCHER_INTERVAL_SECONDS", float),
            "CHUNK_SIZE": ("ORBIT_CHUNK_SIZE", int),
            "CHUNK_OVERLAP": ("ORBIT_CHUNK_OVERLAP", int),
            "MAX_RESULTS": ("ORBIT_MAX_RESULTS", int),
            "WORKERS": ("ORBIT_WORKERS", int),
            "BATCH_SIZE": ("ORBIT_BATCH_SIZE", int),
            "EMBEDDING_PROVIDER": ("ORBIT_EMBEDDING_PROVIDER", str),
            "SQLITE_TIMEOUT": ("ORBIT_SQLITE_TIMEOUT", float),
            "LOGGING_LEVEL": ("ORBIT_LOGGING_LEVEL", str),
            "RANKING_WEIGHT_BM25": ("ORBIT_RANKING_WEIGHT_BM25", float),
            "RANKING_WEIGHT_SEMANTIC": ("ORBIT_RANKING_WEIGHT_SEMANTIC", float),
            "RANKING_WEIGHT_GRAPH": ("ORBIT_RANKING_WEIGHT_GRAPH", float),
            "RANKING_WEIGHT_RECENCY": ("ORBIT_RANKING_WEIGHT_RECENCY", float),
            "RANKING_WEIGHT_PROJECT": ("ORBIT_RANKING_WEIGHT_PROJECT", float),
            "RANKING_WEIGHT_EXACT": ("ORBIT_RANKING_WEIGHT_EXACT", float),
            "RANKING_WEIGHT_TAG": ("ORBIT_RANKING_WEIGHT_TAG", float),
        }
        
        for field_name, (env_var, cast_fn) in fields_to_check.items():
            val = None
            
            # A. Valor de CLI (Prioridad 1)
            if cli_args and cli_args.get(field_name.lower()) is not None:
                val = cast_fn(cli_args[field_name.lower()])
                
            # B. Valor de ENV (Prioridad 2)
            elif env_var in os.environ:
                val = cast_fn(os.environ[env_var])
                
            # C. Valor de YAML (Prioridad 3)
            elif field_name.lower() in yaml_config:
                val = cast_fn(yaml_config[field_name.lower()])
                
            # D. Aplicar si se encontró valor
            if val is not None:
                if field_name in ("ROOT", "INDEX_FILE_PATH"):
                    val = Path(val)
                object.__setattr__(self, field_name, val)


# Instancia global de configuración
settings: Settings = Settings()
settings.load()

