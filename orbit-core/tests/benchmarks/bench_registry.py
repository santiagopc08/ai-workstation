"""Benchmarks for Registry."""

from orbit_core.registry.registry import ComponentRegistry
from orbit_core.utils.timing import Timer


def run():
    registry = ComponentRegistry()
    
    print(f"Running registry benchmark (100k items)...")
    
    with Timer() as t1:
        for i in range(100_000):
            registry.register(f"item_{i}", i)
            
    print(f"Register Elapsed: {t1.elapsed_ms:.2f}ms")
    
    with Timer() as t2:
        for i in range(100_000):
            _ = registry.resolve(f"item_{i}")
            
    print(f"Resolve Elapsed: {t2.elapsed_ms:.2f}ms")


if __name__ == "__main__":
    run()
