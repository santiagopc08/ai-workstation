# ORBIT Git: Component Architecture

This diagram shows the internal structure of the `orbit-git` engine, its relationship with `orbit-execution` and `orbit-core`, and the future extensibility points.

```mermaid
graph TD
    %% External Consumers
    Orchestrator["ORBIT Orchestrator"]
    MCP["ORBIT MCP Tools"]
    GitHubAdapter["orbit-github (Future)"]

    %% Git Engine
    subgraph orbit-git
        GitEngine["GitEngine<br/>Facade / Public Entry Point"]
        GitValidator["GitValidator<br/>Pre-flight Checks"]

        subgraph Managers
            RepoManager["RepositoryManager<br/>Open / Close / Discover"]
            BranchManager["BranchManager<br/>Create / Delete / Merge / Rebase"]
            CommitManager["CommitManager<br/>Create / Amend / Cherry-pick"]
            RemoteManager["RemoteManager<br/>Fetch / Pull / Push"]
            TagManager["TagManager<br/>Create / Delete / List"]
            WorktreeManager["WorktreeManager<br/>Add / Remove / List"]
            SubmoduleManager["SubmoduleManager<br/>Init / Update / Sync"]
            ConfigManager["GitConfigManager<br/>Get / Set / Unset"]
        end

        subgraph Providers
            GitProvider[["GitProvider<br/>Protocol"]]
            LocalGitProvider["LocalGitProvider<br/>CLI via ExecutionEngine"]
            FutureProvider["LibGit2Provider<br/>Future"]

            GitProvider <|-- LocalGitProvider
            GitProvider <|-- FutureProvider
        end

        GitCommandRunner["GitCommandRunner<br/>Request Builder & Output Parser"]

        GitEngine --> GitValidator
        GitEngine --> RepoManager
        GitEngine --> BranchManager
        GitEngine --> CommitManager
        GitEngine --> RemoteManager
        GitEngine --> TagManager
        GitEngine --> WorktreeManager
        GitEngine --> SubmoduleManager
        GitEngine --> ConfigManager

        RepoManager --> GitCommandRunner
        BranchManager --> GitCommandRunner
        CommitManager --> GitCommandRunner
        RemoteManager --> GitCommandRunner
        TagManager --> GitCommandRunner
        WorktreeManager --> GitCommandRunner
        SubmoduleManager --> GitCommandRunner
        ConfigManager --> GitCommandRunner

        GitCommandRunner --> LocalGitProvider
    end

    %% Execution Layer
    subgraph orbit-execution
        ExecutionEngine["ExecutionEngine"]
        PolicyManager["PolicyManager"]
        SandboxManager["SandboxManager"]
    end

    LocalGitProvider --> ExecutionEngine

    %% Core Platform
    subgraph orbit-core
        EventBus["EventBus"]
        Logger["OrbitLogger"]
        Metrics["MetricsCollector"]
        Health["HealthCheck"]
        Registry["ComponentRegistry"]
    end

    %% Connections
    Orchestrator --> GitEngine
    MCP --> GitEngine
    GitHubAdapter --> GitEngine

    GitEngine --> EventBus
    GitEngine --> Logger
    GitEngine --> Metrics
    GitEngine --> Health
    GitEngine --> Registry
```

## Component Responsibilities

| Component | Role |
|---|---|
| **GitEngine** | Public facade. Delegates to managers. Coordinates observability. |
| **GitValidator** | Validates repository integrity, path safety, Git binary availability. |
| **GitCommandRunner** | Translates domain calls into `ExecutionRequest` payloads. Parses `ExecutionResult` output. |
| **LocalGitProvider** | Executes Git commands via the local `git` binary through `ExecutionEngine`. |
| **RepositoryManager** | Discovers, opens, closes, and validates repository handles. |
| **BranchManager** | CRUD operations on branches. Merge and rebase orchestration. |
| **CommitManager** | Commit creation, amending, cherry-picking, staging. |
| **RemoteManager** | Remote CRUD. Fetch, pull, push orchestration. |
| **TagManager** | Tag CRUD operations. |
| **WorktreeManager** | Worktree lifecycle management. |
| **SubmoduleManager** | Submodule initialization, updating, and synchronization. |
| **GitConfigManager** | Read/write Git configuration at local, global, or system scope. |

## Dependency Flow

```
orbit-git  →  orbit-execution  →  orbit-core
                    ↓
              Operating System (git binary)
```

Every Git command follows this chain:
1. `GitEngine` → Manager → `GitCommandRunner` (builds args)
2. `GitCommandRunner` → `LocalGitProvider` → `ExecutionEngine` (validates + spawns)
3. `ExecutionEngine` → `PolicyManager` → `SandboxManager` → OS `subprocess`
4. Result bubbles back through `ExecutionResult` → `GitResult` → typed model
