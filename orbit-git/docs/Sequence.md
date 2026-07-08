# ORBIT Git: Sequence Diagrams

This document illustrates the key execution flows through the ORBIT Git architecture.

---

## 1. Open Repository

```mermaid
sequenceDiagram
    autonumber

    actor Caller as Consumer
    participant Engine as GitEngine
    participant Validator as GitValidator
    participant Runner as GitCommandRunner
    participant Exec as ExecutionEngine
    participant Bus as EventBus

    Caller->>Engine: open("/path/to/repo")

    activate Engine
    Engine->>Validator: validate_path("/path/to/repo")
    Validator->>Validator: os.path.realpath()
    Validator->>Validator: check .git/ exists
    Validator->>Validator: check HEAD, objects/, refs/
    Validator-->>Engine: ValidationResult (valid, is_bare, state)

    Engine->>Runner: run("rev-parse", "--git-dir")
    Runner->>Exec: execute(ExecutionRequest)
    Exec-->>Runner: ExecutionResult
    Runner-->>Engine: GitResult

    Engine->>Bus: publish(RepositoryOpened)
    Engine-->>Caller: Repository(path, real_path, is_bare, state)
    deactivate Engine
```

---

## 2. Commit Workflow (add + commit)

```mermaid
sequenceDiagram
    autonumber

    actor Caller as Consumer
    participant Engine as GitEngine
    participant CM as CommitManager
    participant Runner as GitCommandRunner
    participant Exec as ExecutionEngine
    participant Bus as EventBus

    Caller->>Engine: commits(repo).add_all()

    activate Engine
    Engine->>CM: add_all()
    CM->>Runner: run("add", "--all")
    Runner->>Exec: execute(ExecutionRequest[cwd=repo.path])
    Exec-->>Runner: ExecutionResult
    Runner-->>CM: GitResult
    CM-->>Engine: void
    deactivate Engine

    Caller->>Engine: commits(repo).create("feat: add feature")

    activate Engine
    Engine->>CM: create("feat: add feature")
    CM->>Runner: run("commit", "-m", "feat: add feature")
    Runner->>Exec: execute(ExecutionRequest)
    Exec-->>Runner: ExecutionResult (stdout with hash)
    Runner-->>CM: GitResult

    CM->>CM: parse commit hash from stdout
    CM-->>Engine: Commit(hash, message, ...)
    Engine->>Bus: publish(CommitCreated)
    Engine-->>Caller: Commit
    deactivate Engine
```

---

## 3. Fetch + Pull

```mermaid
sequenceDiagram
    autonumber

    actor Caller as Consumer
    participant Engine as GitEngine
    participant RM as RemoteManager
    participant Runner as GitCommandRunner
    participant Exec as ExecutionEngine
    participant Bus as EventBus

    Caller->>Engine: remotes(repo).fetch("origin")

    activate Engine
    Engine->>RM: fetch("origin")
    RM->>Runner: run("fetch", "origin", "--prune")
    Runner->>Exec: execute(ExecutionRequest)
    Exec-->>Runner: ExecutionResult
    Runner-->>RM: GitResult
    Engine->>Bus: publish(FetchCompleted)
    RM-->>Engine: void
    deactivate Engine

    Caller->>Engine: remotes(repo).pull("origin", "main")

    activate Engine
    Engine->>RM: pull("origin", "main")
    RM->>Runner: run("pull", "origin", "main")
    Runner->>Exec: execute(ExecutionRequest)
    Exec-->>Runner: ExecutionResult
    Runner-->>RM: GitResult
    Engine->>Bus: publish(PullCompleted)
    RM-->>Engine: void
    deactivate Engine
```

---

## 4. Branch + Merge with Conflict

```mermaid
sequenceDiagram
    autonumber

    actor Caller as Consumer
    participant Engine as GitEngine
    participant BM as BranchManager
    participant Runner as GitCommandRunner
    participant Exec as ExecutionEngine
    participant Bus as EventBus

    Caller->>Engine: branches(repo).create("feature/x")

    activate Engine
    Engine->>BM: create("feature/x")
    BM->>Runner: run("branch", "feature/x")
    Runner->>Exec: execute(ExecutionRequest)
    Exec-->>Runner: ExecutionResult
    Runner-->>BM: GitResult
    Engine->>Bus: publish(BranchCreated)
    BM-->>Engine: Branch
    deactivate Engine

    Note over Caller: ... work on feature/x ...

    Caller->>Engine: branches(repo).merge("feature/x")

    activate Engine
    Engine->>BM: merge("feature/x")
    BM->>Runner: run("merge", "feature/x")
    Runner->>Exec: execute(ExecutionRequest)
    Exec-->>Runner: ExecutionResult (exit_code=1, conflicts)
    Runner-->>BM: GitResult (success=false)

    BM->>BM: parse conflict file list from stderr
    BM-->>Engine: MergeResult(success=false, conflicts=["file.txt"])
    Engine->>Bus: publish(MergeCompleted[success=false])
    Engine-->>Caller: MergeResult
    deactivate Engine
```

---

## 5. Status + Diff

```mermaid
sequenceDiagram
    autonumber

    actor Caller as Consumer
    participant Engine as GitEngine
    participant Runner as GitCommandRunner
    participant Exec as ExecutionEngine

    Caller->>Engine: status(repo)

    activate Engine
    Engine->>Runner: run("status", "--porcelain=v2", "--branch")
    Runner->>Exec: execute(ExecutionRequest)
    Exec-->>Runner: ExecutionResult
    Runner-->>Engine: GitResult

    Engine->>Engine: parse porcelain v2 output
    Engine-->>Caller: Status(staged, unstaged, untracked, branch, ahead, behind)
    deactivate Engine

    Caller->>Engine: diff(repo, staged=True)

    activate Engine
    Engine->>Runner: run("diff", "--cached", "--numstat")
    Runner->>Exec: execute(ExecutionRequest)
    Exec-->>Runner: ExecutionResult
    Runner-->>Engine: GitResult

    Engine->>Engine: parse numstat output
    Engine-->>Caller: Diff(files, stats)
    deactivate Engine
```

---

## 6. Push with Policy Rejection

```mermaid
sequenceDiagram
    autonumber

    actor Caller as Consumer
    participant Engine as GitEngine
    participant RM as RemoteManager
    participant Runner as GitCommandRunner
    participant Exec as ExecutionEngine
    participant Policy as PolicyManager
    participant Sandbox as SandboxManager

    Caller->>Engine: remotes(repo).push("origin", "main")

    activate Engine
    Engine->>RM: push("origin", "main")
    RM->>Runner: run("push", "origin", "main")
    Runner->>Exec: execute(ExecutionRequest)

    activate Exec
    Exec->>Policy: resolve_and_validate(request)
    Policy-->>Exec: resolved policy
    Exec->>Sandbox: enforce(request, policy)
    Sandbox-->>Exec: raise SandboxViolationError

    Exec-->>Runner: SandboxViolationError
    deactivate Exec

    Runner-->>RM: GitCommandError (wraps SandboxViolationError)
    RM-->>Engine: GitCommandError
    Engine-->>Caller: GitCommandError
    deactivate Engine
```
