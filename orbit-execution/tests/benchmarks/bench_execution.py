"""Benchmarks for ORBIT Execution Sprint 1."""

import sys
import time

from orbit_execution import ExecutionEngine, ExecutionRequest


def run_benchmark(count: int) -> None:
    engine = ExecutionEngine()
    request = ExecutionRequest(command=[sys.executable, "-c", "pass"])
    
    print(f"Running {count} synchronous executions...")
    start_time = time.time()
    
    for _ in range(count):
        engine.execute(request)
        
    elapsed = time.time() - start_time
    latency_ms = (elapsed / count) * 1000
    
    print(f"Total time: {elapsed:.2f}s")
    print(f"Average latency per execution: {latency_ms:.2f}ms")


def run() -> None:
    run_benchmark(100)
    print("-" * 40)
    run_benchmark(1000)


if __name__ == "__main__":
    run()
