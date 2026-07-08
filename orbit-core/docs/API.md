# ORBIT Core API

## Types

Immutable `dataclass` models (`frozen=True`, `slots=True`):
- `Document`, `Chunk`, `SearchResult`, `Embedding`, `Project`
- `CapabilityInfo`, `HealthStatus`, `ProviderInfo`, `EngineInfo`, `ToolInfo`

## Interfaces (`Protocol`)

- **`Engine`**: Top-level contract (`initialize()`, `shutdown()`, `health()`)
- **`Provider`**: Base backend contract.
- **`StorageProvider`, `EmbeddingProvider`, `SearchProvider`, `CacheProvider`, `TerminalProvider`, `GitProvider`**
- **`Registry`**, **`EventBus`**, **`ConfigLoader`**, **`Logger`**, **`HealthCheck`**

## DI Container

- `Container.register_instance(interface, instance)`
- `Container.register_factory(interface, factory)`
- `Container.resolve(interface)`

## Event Bus

- `EventBus.subscribe(event_type, callback)`
- `EventBus.publish(event)`
- `EventBus.unsubscribe(event_type, callback)`

## Configuration

- `SettingsManager.load_dict(dict)`
- `SettingsManager.load_env_prefix(prefix)`
- `SettingsManager.load_yaml(path)`
- `SettingsManager.get(key, default)`

## Utilities

- `@retry(max_attempts=3, backoff=0.1)`
- `with Timer() as t: ...`
- `safe_join(base, *parts)` (prevents directory traversal)
- `sha256(data)`, `md5(data)`
- `LazyLoader(factory)`
