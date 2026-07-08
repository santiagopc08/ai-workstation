# ORBIT Core

Shared contracts, types, and infrastructure for the ORBIT platform.

## Install

```bash
uv sync
```

## Usage

```python
import orbit_core
print(orbit_core.__version__)
```

## Development

```bash
uv sync --extra dev
uv run ruff check src/ tests/
uv run mypy src/orbit_core/
uv run pytest tests/ -v
```
