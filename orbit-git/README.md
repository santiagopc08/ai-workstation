# ORBIT Git

The execution engine for Git operations in the ORBIT ecosystem.

## Overview
ORBIT Git provides a safe, observable, and isolated interface to Git via the `orbit-execution` engine. It implements the Git operations needed without directly invoking `subprocess` or relying on external C-based Git libraries like `pygit2`.

## Sprint 1 Features
- Repository Discovery & Validation
- Git Version Parsing
- Status Parsing (porcelain v2)
