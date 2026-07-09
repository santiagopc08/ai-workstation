# QUICKSTART

Go from an empty terminal to running your first AI-assisted repository summary in **under 5 minutes**.

## Prerequisites
Ensure you have successfully completed the steps in [INSTALL.md](INSTALL.md) (you should have `uv`, Git, Python, and the repository cloned).

## Step 1: Start LM Studio (Optional but Recommended)
ORBIT uses a local LLM to perform advanced analysis.

1. Open **LM Studio**.
2. Load a fast local model (e.g., Llama 3 or Mistral).
3. Start the **Local Server**. Ensure it's running on `http://localhost:1234/v1`.

*(Note: If you don't have LM Studio, you can configure ORBIT to point to OpenAI or another compatible provider via environment variables, but LM Studio is the default zero-config option).*

## Step 2: Run Your First Skill

ORBIT's orchestration layer (`orbit-skills`) comes with several pre-built examples. Let's run the **Repository Summary** skill, which combines Git history, Git status, Knowledge extraction, and LLM analysis to produce a comprehensive Markdown report of any local repository.

From the root of the ORBIT repository, run the example script:

```bash
uv run examples/repository_summary.py .
```

*(The `.` tells the script to analyze the current ORBIT repository itself. You can point it to any other Git repository on your machine by providing an absolute path instead of `.`).*

## Step 3: View the Output

Within seconds, you should see ORBIT:
1. Bootstrapping the runtime (Execution, Git, and Knowledge engines).
2. Extracting recent commits and the current working tree status.
3. Sending the context to the LLM.
4. Outputting a rich, structured Markdown summary of the repository directly in your terminal.

## What's Next?

Try out the other built-in examples!

- Review the changes between your current branch and `main`:
  ```bash
  uv run examples/review_changes.py . main
  ```

- Search the project knowledge base for specific terms:
  ```bash
  uv run examples/search_project.py . "GitEngine"
  ```
