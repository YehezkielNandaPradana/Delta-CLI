"""
Project Context Resolution Provider for Delta VTuber.
"""

import os
from typing import Optional
from delta.vtuber.desktop.schemas import ProjectContext


class ProjectContextProvider:
    """
    Extracts high-level workspace metadata using Delta's single source of truth.
    """

    @classmethod
    def resolve_context(cls, current_cwd: Optional[str] = None) -> ProjectContext:
        cwd = os.path.abspath(current_cwd or os.getcwd())
        proj_name = os.path.basename(cwd)

        # Detect primary language & git branch
        lang = "Unknown"
        framework = "None"
        branch = None

        if os.path.exists(os.path.join(cwd, "pyproject.toml")) or os.path.exists(os.path.join(cwd, "requirements.txt")):
            lang = "Python"
        elif os.path.exists(os.path.join(cwd, "package.json")):
            lang = "TypeScript/JavaScript"
            framework = "Node.js"
        elif os.path.exists(os.path.join(cwd, "go.mod")):
            lang = "Go"
        elif os.path.exists(os.path.join(cwd, "Cargo.toml")):
            lang = "Rust"

        # Check git branch if .git directory exists
        git_head = os.path.join(cwd, ".git", "HEAD")
        if os.path.isfile(git_head):
            try:
                with open(git_head, "r", encoding="utf-8") as f:
                    ref = f.read().strip()
                    if ref.startswith("ref: refs/heads/"):
                        branch = ref.replace("ref: refs/heads/", "")
            except Exception:
                pass

        return ProjectContext(
            project_name=proj_name,
            project_path=cwd,
            language=lang,
            framework=framework,
            git_branch=branch,
        )
