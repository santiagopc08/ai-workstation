# ORBIT Knowledge Installation

Instrucciones de instalación y puesta en marcha del motor.

## Requisitos Previos

- **macOS** (Optimizado para Apple Silicon M1/M2/M3)
- **Python >= 3.10**
- **uv** (Gestor de dependencias ultrarrápido recomendado)

## Instalación

### Opción 1: Con gestor `uv` (Recomendado)

Sincroniza y descarga automáticamente el entorno virtual aislado:

```bash
uv sync
```

### Opción 2: Instalación editable tradicional con pip

```bash
pip install -e .
```

## Configuración Inicial

Crea un archivo opcional `settings.yaml` en el directorio de ejecución para sobreescribir los valores por defecto:

```yaml
root: "/Users/usuario/Knowledge"
cache_size: 256
logging_level: "INFO"
```
