# ORBIT Doctor

The `orbit doctor` command (or executing the health check manually) is the primary way to diagnose configuration and environmental issues within the ORBIT platform.

When you run `orbit-core` health checks or the bootstrap initialization, the `HealthChecker` aggregates the status of all registered engines.

## What it Verifies

1. **Git Installation & Execution (`orbit-git`)**
   - Verifies that the `git` executable is available on the system `PATH`.
   - Checks that the underlying `ExecutionEngine` can successfully spawn and capture the output of `git --version`.

2. **Event Bus Health (`orbit-core`)**
   - Verifies the internal synchronous event dispatcher is ready to receive and publish events.

3. **LLM Connectivity (`orbit-skills`)**
   - Attempts a lightweight connection to the configured OpenAI-compatible endpoint (default: `http://localhost:1234/v1`).
   - Ensures the server is reachable and responds within the configured timeout.

4. **Knowledge Engine (`orbit-knowledge`)**
   - Verifies access to local filesystem indexing services.

## Common Errors & Solutions

### 1. `ExecutionError: git executable not found`
**Cause:** The `orbit-execution` engine cannot locate Git on your system.
**Solution:**
- Install Git for your operating system.
- Ensure the directory containing the `git` binary is added to your system `PATH`.
- Restart your terminal.

### 2. `ConnectionError: Failed to reach http://localhost:1234/v1`
**Cause:** The Skill Executor cannot connect to the local LLM inference server.
**Solution:**
- Open LM Studio (or your chosen inference server).
- Ensure the **Local Server** feature is turned ON.
- Check that the port is exactly `1234` (or update the `LLMConfig` in `orbit-skills` to match your custom port).

### 3. `Capability_Unavailable: <capability_id>`
**Cause:** You are attempting to run an ORBIT Skill, but the required engine was not registered during bootstrap.
**Solution:**
- If you wrote a custom bootstrap script, ensure you are registering all necessary capabilities into the `CapabilityRegistry`.
- Standard capabilities include: `git.repository.read`, `git.history.read`, `git.diff.read`, `knowledge.summary`, `knowledge.search`, and `llm.complete`.

### 4. `ModuleNotFoundError: No module named 'orbit_core'`
**Cause:** The Python environment does not have the local ORBIT packages installed.
**Solution:**
- ORBIT relies on local editable installs for its sub-packages.
- Run `uv sync` in the directory you are trying to execute, or run `./scripts/bootstrap.sh` from the root to sync all workspaces globally.
