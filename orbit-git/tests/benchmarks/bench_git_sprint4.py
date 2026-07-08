"""Benchmarks for ORBIT Git Sprint 4 (Diff & History)."""

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
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        
        subprocess.run(["git", "init"], cwd=repo_path, check=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo_path, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path, check=True)
        
        repo = git_engine.open(str(repo_path))
        commits = git_engine.commits()
        hist_mgr = git_engine.history()
        diff_mgr = git_engine.diff()
        
        f = repo_path / "file.txt"
        
        # Setup repository with 100 commits
        print("Setting up repository with 100 commits...")
        for i in range(100):
            with open(f, "a") as file:
                file.write(f"line {i}\n")
            commits.add_all(repo)
            commits.create(repo, f"commit {i}")
            
        print("Running benchmarks...")
        
        # Benchmark diff_working_tree
        diff_latencies = []
        for _ in range(20):
            with open(f, "a") as file:
                file.write("new line\n")
            
            start = time.time()
            diff_mgr.diff_working_tree(repo)
            diff_latencies.append(time.time() - start)
            
            # Revert change for consistency
            subprocess.run(["git", "checkout", "--", "file.txt"], cwd=repo_path, check=True)
            
        elapsed_diff = (sum(diff_latencies) / len(diff_latencies)) * 1000
        print(f"Average diff.diff_working_tree() latency: {elapsed_diff:.2f}ms")
        
        # Benchmark log
        log_latencies = []
        for _ in range(20):
            start = time.time()
            hist_mgr.log(repo)
            log_latencies.append(time.time() - start)
            
        elapsed_log = (sum(log_latencies) / len(log_latencies)) * 1000
        print(f"Average history.log() latency: {elapsed_log:.2f}ms")
        
        # Benchmark blame
        blame_latencies = []
        for _ in range(20):
            start = time.time()
            hist_mgr.blame(repo, "file.txt")
            blame_latencies.append(time.time() - start)
            
        elapsed_blame = (sum(blame_latencies) / len(blame_latencies)) * 1000
        print(f"Average history.blame() latency: {elapsed_blame:.2f}ms")
        
        # Benchmark parse_commits directly (parser speed)
        from orbit_git.parser import GitOutputParser
        result = git_engine._runner.run(repo, ["log", '--format=%H|%an|%s|%aI'])
        raw_log_output = result.stdout
        
        parser_latencies = []
        for _ in range(100):
            start = time.time()
            GitOutputParser.parse_commits(raw_log_output)
            parser_latencies.append(time.time() - start)
            
        elapsed_parser = (sum(parser_latencies) / len(parser_latencies)) * 1000
        print(f"Average parse_commits() (100 commits) latency: {elapsed_parser:.2f}ms")


if __name__ == "__main__":
    run_benchmarks()
