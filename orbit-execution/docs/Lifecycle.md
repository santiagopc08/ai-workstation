# ORBIT Execution: State Lifecycle

The API enforces strict, one-way state transitions.

## 1. Synchronous Path: `execute()`

The synchronous path handles the entire lifecycle internally, blocking until completion.

```text
[ START ]
   |
   | caller invokes execute(request)
   v
( Policy Validation )
   |
   | policy passed
   v
( OS Process Spawned ) ---> emit ProcessStarted
   |
   | wait for exit
   v
( OS Process Exits ) -----> emit ProcessFinished / ProcessFailed
   |
   v
[ RETURN ExecutionResult ]
```

## 2. Asynchronous Path: `execute_async()`

The asynchronous path decouples initialization from waiting. It allows interactive streaming, background execution, and explicit cancellation.

```text
[ START ]
   |
   | caller invokes execute_async(request)
   v
( Policy Validation )
   |
   | policy passed
   v
( OS Process Spawned ) ---> emit ProcessStarted
   |
   | return ProcessHandle (non-blocking)
   v
[ ASYNC IDLE ]
```

From `[ ASYNC IDLE ]`, the caller can take three paths:

### Path 2A: Stream Subscriptions
1. Caller subscribes to EventBus for `StdoutChunk`, `StderrChunk`.
2. Caller can invoke `RunningProcess.send_stdin()` on the underlying handle.
3. Process exits naturally.
4. Engine emits `ProcessFinished` or `ProcessFailed`.

### Path 2B: Wait
1. Caller invokes `wait(handle)`.
2. Blocks until the process terminates naturally or via policy (e.g. timeout).
3. Returns `ExecutionResult`.

### Path 2C: Cancellation
1. Caller invokes `cancel(handle, token)`.
2. Engine sends cooperative termination signal (e.g., `SIGTERM`).
3. If `token.force_kill` is True, sends `SIGKILL` instead.
4. Process dies.
5. Engine emits `ProcessCancelled`.
6. Subsequent calls to `wait()` will raise `ExecutionError` / return a failed `ExecutionResult`.
