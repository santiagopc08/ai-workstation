"""Benchmarks for ORBIT Git Integration."""

import subprocess
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

from orbit_core.events import EventBus
from orbit_execution import ExecutionEngine

from orbit_git import GitEngine
from orbit_git.integration import GitKnowledgeService


def run_benchmarks() -> None:
    print("Setting up repository with 100 commits...")
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir) / "repo"
        tmp_path.mkdir()
        
        subprocess.run(["git", "init"], cwd=tmp_path, check=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True)
        
        engine = GitEngine(ExecutionEngine(), EventBus())
        repo = engine.open(str(tmp_path))
        
        # Create 100 commits
        for i in range(100):
            f = tmp_path / f"file_{i}.txt"
            f.write_text(f"content {i}\n")
            engine.commits().add_all(repo)
            engine.commits().create(repo, f"commit {i}")
            
        svc = GitKnowledgeService(engine)
        history = engine.history().log(repo)
        ref_a = history[-1].hash
        ref_b = history[0].hash
        
        print("Running benchmarks...")
        
        with patch("orbit_git.integration.summarize_document") as mock_summarize:
            mock_summarize.return_value = "Mock doc summary"
            
            # 1. summarize_diff
            iterations = 50
            start = time.time()
            for _ in range(iterations):
                svc.summarize_diff(repo, ref_a, ref_b)
            avg_ms = ((time.time() - start) / iterations) * 1000
            print(f"Average summarize_diff (100 files) latency: {avg_ms:.2f}ms")
            
            # 2. summarize_history
            start = time.time()
            for _ in range(iterations):
                svc.summarize_history(repo, limit=50)
            avg_ms = ((time.time() - start) / iterations) * 1000
            print(f"Average summarize_history (50 commits) latency: {avg_ms:.2f}ms")

if __name__ == "__main__":
    run_benchmarks()
