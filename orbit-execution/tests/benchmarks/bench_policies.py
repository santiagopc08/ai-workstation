"""Policy Benchmarks for ORBIT Execution (RFC-006)."""

import os
import sys
import time

from orbit_execution import ExecutionEngine, ExecutionPolicy, ExecutionRequest


def run_benchmark(count: int, with_complex_policy: bool) -> None:
    if with_complex_policy:
        global_policy = ExecutionPolicy(
            timeout_sec=10.0,
            max_memory_mb=1024,
            allowed_cwds=[os.getcwd(), "/tmp"],
            blocked_cwds=["/etc", "/var"],
            env_whitelist=["FOO", "BAR", "PATH", "PYTHONPATH"],
            env_blacklist=["AWS_SECRET_ACCESS_KEY"],
            command_whitelist=[sys.executable, "ls", "echo"],
            command_blacklist=["rm", "sudo"],
            interactive_allowed=False,
            allow_shell=False
        )
    else:
        global_policy = None

    engine = ExecutionEngine(global_policy=global_policy)
    
    code = "import sys; sys.exit(0)"
    
    request = ExecutionRequest(
        command=[sys.executable, "-c", code],
        env={"FOO": "1", "BAR": "2"}
    )
    
    label = "WITH complex policy" if with_complex_policy else "WITHOUT complex policy"
    print(f"Running {count} executions {label}...")
    
    start_time = time.time()
    for _ in range(count):
        engine.execute(request)
        
    elapsed = time.time() - start_time
    latency_ms = (elapsed / count) * 1000
    
    print(f"Total time: {elapsed:.2f}s")
    print(f"Average latency per execution: {latency_ms:.2f}ms")


def run() -> None:
    # 50 executions is enough
    run_benchmark(50, with_complex_policy=False)
    print("-" * 40)
    run_benchmark(50, with_complex_policy=True)


if __name__ == "__main__":
    run()
