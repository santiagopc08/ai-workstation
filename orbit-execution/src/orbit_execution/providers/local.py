"""Local execution provider."""

import os
import signal
import subprocess
import time

from orbit_execution.exceptions import ExecutionError
from orbit_execution.interfaces import ExecutionProvider
from orbit_execution.types import ProcessHandle, RunningProcess


class LocalExecutionProvider(ExecutionProvider):
    """Executes processes locally using the Python standard library."""

    def spawn(self, handle: ProcessHandle) -> RunningProcess:
        """Spawn a new process."""
        request = handle.request
        
        # Merge env
        env: dict[str, str] = {**dict(os.environ), **request.env}

        try:
            # We don't use shell=True to prevent injection vulnerabilities
            process = subprocess.Popen(
                request.command,
                cwd=request.cwd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT if request.options.merge_stderr else subprocess.PIPE,
            )
        except OSError as e:
            raise ExecutionError(f"Failed to spawn process: {e}") from e

        return RunningProcess(
            handle=handle,
            pid=process.pid,
            start_time=time.time(),
            _internal_process=process,
        )

    def kill(self, pid: int) -> None:
        """Terminate the process."""
        try:
            if os.name == "nt":
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], check=False)
            else:
                os.kill(pid, signal.SIGKILL)
        except OSError:
            pass  # Process may already be dead

    def wait(self, process: RunningProcess, timeout: float | None = None) -> int:
        """Wait for the process to exit and return its exit code."""
        internal: subprocess.Popen[bytes] = process._internal_process
        try:
            return internal.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            # Re-raise as standard exception if needed, or let caller handle
            raise
