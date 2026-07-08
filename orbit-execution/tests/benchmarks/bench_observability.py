"""Observability Benchmarks for ORBIT Execution (RFC-007)."""

import sys
import time

from orbit_execution import ExecutionEngine, ExecutionRequest


def run_benchmark(count: int) -> None:
    # Everything is enabled by default in Sprint 4
    engine = ExecutionEngine()
    
    code = "import sys; sys.exit(0)"
    request = ExecutionRequest(
        command=[sys.executable, "-c", code],
    )
    
    print(f"Running {count} executions WITH full Observability (Logging, Metrics, Tracing)...")
    
    start_time = time.time()
    for _ in range(count):
        engine.execute(request)
        
    elapsed = time.time() - start_time
    latency_ms = (elapsed / count) * 1000
    
    print(f"Total time: {elapsed:.2f}s")
    print(f"Average latency per execution: {latency_ms:.2f}ms")
    
    health = engine.health_reporter.health()
    print(f"Completed processes verified via Health: {health.dependencies.get('completed_processes')}")


def run() -> None:
    run_benchmark(50)


if __name__ == "__main__":
    run()
