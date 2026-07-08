"""Sandboxing Benchmarks for ORBIT Execution (RFC-008)."""

import os
import sys
import time

from orbit_execution import ExecutionEngine, ExecutionPolicy, ExecutionRequest


def run_benchmark(count: int) -> None:
    # Use policies that trigger sandbox checking (e.g., allowed_cwds)
    engine = ExecutionEngine(
        global_policy=ExecutionPolicy(
            allowed_cwds=[os.getcwd()],
            allow_shell=False,
            command_whitelist=[sys.executable, "python", "python3"]
        )
    )
    
    code = "import sys; sys.exit(0)"
    request = ExecutionRequest(
        command=[sys.executable, "-c", code],
        cwd=os.getcwd()
    )
    
    print(f"Running {count} executions WITH full Sandboxing (realpath, which, os.access)...")
    
    start_time = time.time()
    for _ in range(count):
        engine.execute(request)
        
    elapsed = time.time() - start_time
    latency_ms = (elapsed / count) * 1000
    
    print(f"Total time: {elapsed:.2f}s")
    print(f"Average latency per execution: {latency_ms:.2f}ms")


def run() -> None:
    run_benchmark(50)


if __name__ == "__main__":
    run()
