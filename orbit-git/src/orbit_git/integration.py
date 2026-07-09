"""Integration layer between ORBIT Git and ORBIT Knowledge."""

from typing import Any

from orbit_git.engine import GitEngine
from orbit_git.models import Repository

try:
    from orbit_knowledge.services.knowledge_service import (  # type: ignore
        related_documents,
        summarize_document,
    )
    from orbit_knowledge.services.project_service import project_metadata, project_summary  # type: ignore
except Exception:
    # If orbit-knowledge is not installed or raises errors, fallback to stub functions.
    def summarize_document(path: str) -> str: return ""
    def related_documents(path: str) -> list[str]: return []
    def project_summary(project: str) -> str: return ""
    def project_metadata(project: str) -> dict[str, Any]: return {}


class GitKnowledgeService:
    """Service to bridge ORBIT Git and ORBIT Knowledge, producing structured LLM payloads."""

    def __init__(self, git_engine: GitEngine) -> None:
        self._git_engine = git_engine

    def summarize_diff(self, repo: Repository, ref_a: str, ref_b: str) -> str:
        """Summarize a diff between two references, incorporating knowledge context."""
        diff = self._git_engine.diff().diff_between(repo, ref_a, ref_b)
        
        output = [f"# Diff Summary: {ref_a}..{ref_b}", ""]
        output.append(f"**Files changed:** {diff.stats.files_changed}")
        output.append(f"**Insertions:** {diff.stats.insertions}")
        output.append(f"**Deletions:** {diff.stats.deletions}")
        output.append("")
        
        output.append("## Changed Files & Context")
        for f in diff.files:
            output.append(f"### `{f.path}` ({f.status})")
            output.append(f"*(+{f.insertions} / -{f.deletions})*")
            output.append("")
            # Context from orbit_knowledge
            try:
                doc_summary = summarize_document(f.path)
                output.append("**Knowledge Context:**")
                output.append(doc_summary)
            except Exception:
                output.append("**Knowledge Context:** Not available.")
            output.append("")
            
        return "\n".join(output)

    def summarize_commit(self, repo: Repository, commit_hash: str) -> str:
        """Summarize a specific commit."""
        commit, diff = self._git_engine.history().show(repo, commit_hash)
        
        output = [f"# Commit Summary: {commit.hash}", ""]
        output.append(f"**Author:** {commit.author}")
        output.append(f"**Date:** {commit.date}")
        output.append(f"**Message:**\n{commit.message}")
        output.append("")
        
        output.append("## Changed Files & Context")
        for f in diff.files:
            output.append(f"### `{f.path}` ({f.status})")
            try:
                doc_summary = summarize_document(f.path)
                output.append(doc_summary)
            except Exception:
                pass
            output.append("")
            
        return "\n".join(output)

    def summarize_history(self, repo: Repository, limit: int = 5) -> str:
        """Summarize recent repository history."""
        commits = self._git_engine.history().log(repo)[:limit]
        
        output = [f"# History Summary (Last {limit} commits)", ""]
        for c in commits:
            output.append(f"- **{c.hash[:7]}** ({c.author}): {c.message}")
            
        return "\n".join(output)

    def affected_documents(self, repo: Repository, commit_hash: str) -> list[str]:
        """Get documents structurally affected or related to the files modified in a commit."""
        _, diff = self._git_engine.history().show(repo, commit_hash)
        affected: set[str] = set()
        
        for f in diff.files:
            affected.add(f.path)
            try:
                related = related_documents(f.path)
                affected.update(related)
            except Exception:
                pass
                
        return sorted(list(affected))

    def related_knowledge(self, repo: Repository, path: str) -> list[str]:
        """Find knowledge architecture or documentation related to a specific file."""
        try:
            return related_documents(path)  # type: ignore
        except Exception:
            return []

    def repository_summary(self, repo: Repository, project_name: str) -> str:
        """Generate a complete repository and project knowledge summary."""
        output = [f"# Repository Integration Summary: {project_name}", ""]
        
        try:
            p_summary = project_summary(project_name)
            output.append("## Knowledge Architecture")
            output.append(p_summary)
            output.append("")
        except Exception:
            output.append("## Knowledge Architecture\nNot available.\n")
            
        try:
            metadata = project_metadata(project_name)
            output.append("## Metadata")
            for k, v in metadata.items():
                output.append(f"- **{k}:** {v}")
            output.append("")
        except Exception:
            pass
            
        output.append("## Recent Activity")
        try:
            commits = self._git_engine.history().log(repo)[:5]
            for c in commits:
                output.append(f"- {c.hash[:7]}: {c.message}")
        except Exception:
            output.append("No recent activity.")
            
        return "\n".join(output)
