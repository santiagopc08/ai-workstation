# ORBIT Execution: Component Architecture

This diagram shows the internal structure of the `orbit-execution` engine and its relationship with `orbit-core`.

```mermaid
graph TD
    %% Consumers
    GitEngine[ORBIT Git Engine]
    DockerEngine[ORBIT Docker Engine]
    
    %% Execution API
    subgraph ORBIT Execution
        ExecutionEngine[ExecutionEngine<br/>Gateway API]
        PolicyEngine[PolicyEngine<br/>Security Validation]
        EnvResolver[EnvironmentResolver<br/>Sandbox & Stripping]
        
        ExecutionEngine --> PolicyEngine
        ExecutionEngine --> EnvResolver
        
        subgraph Providers
            ExecutionProvider[[ExecutionProvider<br/>Protocol]]
            LocalProvider[LocalExecutionProvider<br/>subprocess]
            SSHProvider[SSHProvider<br/>Remote - Future]
            DockerProvider[DockerExecProvider<br/>Future]
            
            ExecutionProvider <|-- LocalProvider
            ExecutionProvider <|-- SSHProvider
            ExecutionProvider <|-- DockerProvider
        end
        
        ExecutionEngine --> ExecutionProvider
        
        subgraph Internals
            ProcessManager[ProcessManager<br/>Lifecycle & Trees]
            StreamingManager[StreamingManager<br/>I/O Pumping Threads]
            CancelManager[CancellationManager<br/>Signals & Timeouts]
            
            LocalProvider --> ProcessManager
            LocalProvider --> StreamingManager
            ProcessManager <--> CancelManager
        end
    end
    
    %% Core Platform
    subgraph ORBIT Core
        EventBus[EventBus]
        Metrics[MetricsCollector]
        Logger[OrbitLogger]
    end
    
    GitEngine --> ExecutionEngine
    DockerEngine --> ExecutionEngine
    
    ExecutionEngine --> EventBus
    ExecutionEngine --> Metrics
    ExecutionEngine --> Logger
    ProcessManager --> Logger
```
