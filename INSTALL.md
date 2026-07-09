# Installation Guide

This document outlines how to perform a clean installation of the ORBIT platform from scratch.

## Prerequisites

ORBIT requires the following tools to be installed on your system:

1. **Git** (>= 2.30)
2. **Python** (>= 3.10)
3. **uv** (The extremely fast Python package installer and resolver written in Rust).
   - If you don't have `uv` installed, run:
     ```bash
     curl -LsSf https://astral.sh/uv/install.sh | sh
     ```
     *(Or visit the [uv documentation](https://github.com/astral-sh/uv) for other installation methods like Homebrew).*
4. **LM Studio** (Optional, but highly recommended for local LLM inference).
   - Download and install [LM Studio](https://lmstudio.ai/).
   - Start the local server so it listens on `http://localhost:1234/v1`.

## Step-by-Step Clean Installation

### 1. Clone the Repository

Clone the entire ORBIT monorepo to your local machine:

```bash
git clone <your-repo-url>/ai-workstation.git orbit
cd orbit
```

### 2. Run the Bootstrap Script

We provide automated bootstrap scripts for both Unix and Windows systems. These scripts will automatically set up the virtual environments and sync the local packages (`orbit-core`, `orbit-git`, `orbit-execution`, `orbit-knowledge`, `orbit-skills`).

**For macOS / Linux:**
```bash
./scripts/bootstrap.sh
```

**For Windows (PowerShell):**
```powershell
.\scripts\bootstrap.ps1
```

### 3. Verify the Installation

To verify that the engines are wired correctly and dependencies are satisfied, run the developer check script:

```bash
./scripts/dev.sh
```

This will run `ruff`, `mypy`, and `pytest` across all ORBIT components, ensuring your environment is perfectly configured.

## Troubleshooting

If you encounter issues during installation, please refer to [DOCTOR.md](DOCTOR.md) to diagnose and fix common environmental problems.
