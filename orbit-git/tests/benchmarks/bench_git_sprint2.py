"""Benchmarks for ORBIT Git Sprint 2 (Branches & Commits)."""

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
        
        repo = git_engine.open(str(tmp_path))
        commits = git_engine.commits()
        branches = git_engine.branches()
        
        f = tmp_path / "file.txt"
        f.write_text("init")
        commits.add_all(repo)
        commits.create(repo, "init")
        
        # Benchmark commit creation
        start = time.time()
        for i in range(50):
            f.write_text(f"content {i}")
            commits.add_all(repo)
            commits.create(repo, f"commit {i}")
        elapsed_commit = (time.time() - start) / 50 * 1000
        print(f"Average commit.create() latency: {elapsed_commit:.2f}ms")
        
        # Benchmark checkout
        branches.create(repo, "feature")
        start = time.time()
        for i in range(50):
            target = "feature" if i % 2 == 0 else "master"
            branches.checkout(repo, target)
        elapsed_checkout = (time.time() - start) / 50 * 1000
        print(f"Average branch.checkout() latency: {elapsed_checkout:.2f}ms")
        
        # Benchmark merge
        branches.checkout(repo, "master")
        branches.create(repo, "merge-test")
        
        # Create a branch off the first commit to force merge
        branches.checkout(repo, "merge-test")
        f2 = tmp_path / "file2.txt"
        
        merge_latencies = []
        for i in range(20):
            branches.checkout(repo, "merge-test")
            branches.create(repo, f"feature-{i}")
            branches.checkout(repo, f"feature-{i}")
            f2.write_text(f"update {i}")
            commits.add_all(repo)
            commits.create(repo, f"feature commit {i}")
            
            branches.checkout(repo, "merge-test")
            
            start = time.time()
            branches.merge(repo, f"feature-{i}")
            merge_latencies.append(time.time() - start)
            
        elapsed_merge = (sum(merge_latencies) / len(merge_latencies)) * 1000
        print(f"Average branch.merge() latency: {elapsed_merge:.2f}ms")


if __name__ == "__main__":
    run_benchmarks()
