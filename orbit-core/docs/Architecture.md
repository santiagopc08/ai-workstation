# ORBIT Core Architecture

`orbit-core` is the foundational library for all ORBIT engines (Knowledge, Git, Terminal, etc.).

## Principles

1. **No Circular Dependencies**: `orbit-core` is at the very bottom of the dependency graph. It imports nothing from other engines.
2. **No Global State**: Registries, containers, and event buses are instantiated per-engine, not globally.
3. **Protocols over Inheritance**: Everything is defined using `typing.Protocol` (structural typing) rather than ABCs (nominal typing). This allows external objects to satisfy ORBIT contracts without explicitly importing or subclassing them.
4. **Zero Dependencies**: Relies exclusively on the Python Standard Library to minimize surface area and conflicts.

## Layers

```
Capabilities / Plugins
        |
    Registry
        |
DI Container / Event Bus
        |
    Interfaces
        |
      Types
        |
    Utilities
```
