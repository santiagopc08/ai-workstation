"""Benchmarks for ORBIT Git Sprint 1."""

import subprocess
import tempfile
import time
from pathlib import Path

from orbit_execution import ExecutionEngine

from orbit_git import GitEngine


def run_benchmarks() -> None:
    execution_engine = ExecutionEngine()
    git_engine = GitEngine(execution_engine)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        subprocess.run(["git", "init"], cwd=tmp_path, check=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True)
        
        # Add 100 files
        for i in range(100):
            (tmp_path / f"file_{i}.txt").write_text("hello")
        
        subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, check=True)
        
        repo = git_engine.open(str(tmp_path))
        
        # Benchmark discover
        start = time.time()
        for _ in range(50):
            git_engine.discover(str(tmp_path))
        elapsed_discover = (time.time() - start) / 50 * 1000
        print(f"Average discover() latency: {elapsed_discover:.2f}ms")
        
        # Benchmark open
        start = time.time()
        for _ in range(50):
            git_engine.open(str(tmp_path))
        elapsed_open = (time.time() - start) / 50 * 1000
        print(f"Average open() latency: {elapsed_open:.2f}ms")
        
        # Benchmark status
        start = time.time()
        for _ in range(50):
            git_engine.status(repo)
        elapsed_status = (time.time() - start) / 50 * 1000
        print(f"Average status() latency: {elapsed_status:.2f}ms")


if __name__ == "__main__":
    run_benchmarks()
