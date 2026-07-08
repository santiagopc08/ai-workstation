"""Benchmarks for ORBIT Git Sprint 3 (Remotes)."""

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
        bare_path = tmp_path / "bare.git"
        bare_path.mkdir()
        subprocess.run(["git", "init", "--bare"], cwd=bare_path, check=True)
        
        # Benchmark clone
        clone_latencies = []
        for i in range(10):
            clone_path = tmp_path / f"clone_{i}"
            c_start = time.time()
            git_engine.clone(str(bare_path), str(clone_path))
            clone_latencies.append(time.time() - c_start)
        
        elapsed_clone = (sum(clone_latencies) / len(clone_latencies)) * 1000
        print(f"Average engine.clone() latency: {elapsed_clone:.2f}ms")
        
        # Setup for push/fetch/pull benchmark
        repo_path = tmp_path / "clone_0"
        repo = git_engine.open(str(repo_path))
        
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo_path, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path, check=True)
        
        commits = git_engine.commits()
        remotes = git_engine.remotes()
        f = repo_path / "file.txt"
        
        push_latencies = []
        for i in range(20):
            f.write_text(f"content {i}")
            commits.add_all(repo)
            commits.create(repo, f"commit {i}")
            
            p_start = time.time()
            remotes.push(repo, "origin", "master")
            push_latencies.append(time.time() - p_start)
            
        elapsed_push = (sum(push_latencies) / len(push_latencies)) * 1000
        print(f"Average remotes.push() latency: {elapsed_push:.2f}ms")
        
        # Setup clone_1 for fetch/pull
        repo2_path = tmp_path / "clone_1"
        repo2 = git_engine.open(str(repo2_path))
        
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo2_path, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo2_path, check=True)
        
        fetch_latencies = []
        pull_latencies = []
        
        for i in range(20):
            # push from repo1
            f.write_text(f"content pull {i}")
            commits.add_all(repo)
            commits.create(repo, f"pull update {i}")
            remotes.push(repo, "origin", "master")
            
            # fetch in repo2
            f_start = time.time()
            remotes.fetch(repo2, "origin")
            fetch_latencies.append(time.time() - f_start)
            
            # pull in repo2
            pl_start = time.time()
            remotes.pull(repo2, "origin", "master")
            pull_latencies.append(time.time() - pl_start)
            
        elapsed_fetch = (sum(fetch_latencies) / len(fetch_latencies)) * 1000
        elapsed_pull = (sum(pull_latencies) / len(pull_latencies)) * 1000
        
        print(f"Average remotes.fetch() latency: {elapsed_fetch:.2f}ms")
        print(f"Average remotes.pull() latency: {elapsed_pull:.2f}ms")
        
        # Benchmark ls-remote
        ls_latencies = []
        for _ in range(20):
            ls_start = time.time()
            remotes.ls_remote(str(bare_path))
            ls_latencies.append(time.time() - ls_start)
            
        elapsed_ls = (sum(ls_latencies) / len(ls_latencies)) * 1000
        print(f"Average remotes.ls_remote() latency: {elapsed_ls:.2f}ms")


if __name__ == "__main__":
    run_benchmarks()
