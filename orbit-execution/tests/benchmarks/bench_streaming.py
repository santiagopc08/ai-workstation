"""Streaming Benchmarks for ORBIT Execution (RFC-005)."""

import sys
import time

from orbit_core.events.bus import EventBus

from orbit_execution import ExecutionEngine, ExecutionOptions, ExecutionRequest, StdoutChunk


def run_benchmark(count: int, publish_streams: bool) -> None:
    bus = EventBus()
    
    # We add a dummy subscriber just to measure overhead of event bus
    chunks_received = 0
    def on_chunk(e: StdoutChunk) -> None:
        nonlocal chunks_received
        chunks_received += 1
        
    bus.subscribe(StdoutChunk, on_chunk)
    
    engine = ExecutionEngine(event_bus=bus)
    
    # Process prints 10 times with small delay to simulate real streaming
    code = """
import sys
import time
for i in range(10):
    sys.stdout.write(f'line {i}\\n')
    sys.stdout.flush()
"""
    
    request = ExecutionRequest(
        command=[sys.executable, "-c", code],
        options=ExecutionOptions(publish_streams=publish_streams)
    )
    
    label = "WITH streaming" if publish_streams else "WITHOUT streaming"
    print(f"Running {count} executions {label}...")
    
    start_time = time.time()
    for _ in range(count):
        engine.execute(request)
        
    elapsed = time.time() - start_time
    latency_ms = (elapsed / count) * 1000
    
    print(f"Total time: {elapsed:.2f}s")
    print(f"Average latency per execution: {latency_ms:.2f}ms")
    print(f"Total chunks received: {chunks_received}")


def run() -> None:
    # 50 executions is enough given the python loop overhead
    run_benchmark(50, publish_streams=False)
    print("-" * 40)
    run_benchmark(50, publish_streams=True)


if __name__ == "__main__":
    run()
