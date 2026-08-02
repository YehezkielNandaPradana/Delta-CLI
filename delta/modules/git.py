# delta/modules/git.py

"""Git operations module — Delta's built-in git workflow.

Supports: init, status, add, commit, push, pull, branch, log, remote, diff, clone.

All operations run directly via subprocess (no confirmation needed).
"""

import os
import shutil
import subprocess
from typing import Any, Dict, List, Optional, Tuple


def _git_root(cwd: str) -> Optional[str]:
    """Return the git repository root directory, or None if not inside a repo."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=cwd, capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:
        pass
    return None


def _run_git(args: List[str], cwd: str = ".", timeout: int = 60) -> Tuple[bool, str, str]:
    """Run a git command and return (success, stdout, stderr)."""
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd, capture_output=True, text=True, timeout=timeout,
        )
        return result.returncode == 0, result.stdout, result.stderr
    except FileNotFoundError:
        return False, "", "git command not found"
    except subprocess.TimeoutExpired:
        return False, "", "git command timed out"
    except Exception as e:
        return False, "", str(e)


class GitModule:
    """Git workflow operations — run git commands directly without confirmation."""

    def __init__(self, cwd: Optional[str] = None, display: Any = None):
        self.cwd = cwd or os.getcwd()
        self.display = display

    # ------------------------------------------------------------ init

    def init(self) -> Tuple[bool, str]:
        """Initialize a new git repository in the current directory."""
        root = _git_root(self.cwd)
        if root:
            return True, f"Already a git repo at {root}"
        ok, out, err = _run_git(["init"], self.cwd)
        if ok:
            return True, f"Git repository initialized in {self.cwd}"
        return False, f"git init failed: {err or out}"

    # ------------------------------------------------------------ status

    def status(self) -> Tuple[bool, str]:
        """Show working tree status."""
        root = _git_root(self.cwd)
        if not root:
            return False, "Not inside a git repository. Run 'git init' first."
        ok, out, err = _run_git(["status", "-sb"], self.cwd)
        if not ok:
            return False, err or out or "git status failed"
        if not out.strip():
            return True, "Nothing to commit, working tree clean"
        return True, out.strip()

    # ------------------------------------------------------------ add

    def add(self, paths: List[str] = None, all_files: bool = False) -> Tuple[bool, str]:
        """Stage files for commit."""
        root = _git_root(self.cwd)
        if not root:
            return False, "Not inside a git repository. Run 'git init' first."
        if all_files:
            ok, out, err = _run_git(["add", "-A"], self.cwd)
        elif paths:
            ok, out, err = _run_git(["add"] + paths, self.cwd)
        else:
            ok, out, err = _run_git(["add", "."], self.cwd)
        if ok:
            return True, f"Staged {'all files' if all_files else ', '.join(paths) or '.'}"
        return False, f"git add failed: {err or out}"

    # ------------------------------------------------------------ commit

    def commit(self, message: str = "") -> Tuple[bool, str]:
        """Commit staged changes."""
        root = _git_root(self.cwd)
        if not root:
            return False, "Not inside a git repository. Run 'git init' first."
        if not message:
            return False, "Commit message required. Usage: git commit <message>"
        ok, out, err = _run_git(["commit", "-m", message], self.cwd)
        if ok:
            return True, f"Committed: {message}"
        if "nothing to commit" in (err + out).lower():
            return True, "Nothing to commit (working tree clean)"
        return False, f"git commit failed: {err or out}"

    # ------------------------------------------------------------ push

    def push(self, remote: str = "origin", branch: str = "") -> Tuple[bool, str]:
        """Push commits to remote."""
        root = _git_root(self.cwd)
        if not root:
            return False, "Not inside a git repository. Run 'git init' first."
        args = ["push"]
        if remote:
            args.append(remote)
        if branch:
            args.append(branch)
        ok, out, err = _run_git(args, self.cwd)
        if ok:
            return True, f"Pushed to {remote}" + (f"/{branch}" if branch else "")
        return False, f"git push failed: {err or out}"

    # ------------------------------------------------------------ pull

    def pull(self, remote: str = "origin", branch: str = "") -> Tuple[bool, str]:
        """Pull changes from remote."""
        root = _git_root(self.cwd)
        if not root:
            return False, "Not inside a git repository. Run 'git init' first."
        args = ["pull"]
        if remote:
            args.append(remote)
        if branch:
            args.append(branch)
        ok, out, err = _run_git(args, self.cwd)
        if ok:
            return True, f"Pulled from {remote}" + (f"/{branch}" if branch else "")
        return False, f"git pull failed: {err or out}"

    # ------------------------------------------------------------ branch

    def branch(self, name: str = "", create: bool = False, list_branches: bool = False) -> Tuple[bool, str]:
        """List, create, or show current branch."""
        root = _git_root(self.cwd)
        if not root:
            return False, "Not inside a git repository. Run 'git init' first."
        if list_branches or (not name and not create):
            ok, out, err = _run_git(["branch", "-a"], self.cwd)
            if ok:
                return True, out.strip() or "No branches"
            return False, f"git branch failed: {err or out}"
        if create:
            ok, out, err = _run_git(["branch", name], self.cwd)
            if ok:
                return True, f"Branch '{name}' created"
            return False, f"git branch create failed: {err or out}"
        if name:
            ok, out, err = _run_git(["branch", name], self.cwd)
            if ok:
                return True, f"Branch '{name}' created"
            return False, f"git branch failed: {err or out}"
        ok, out, err = _run_git(["branch", "--show-current"], self.cwd)
        if ok and out.strip():
            return True, f"Current branch: {out.strip()}"
        return True, "No branch (detached HEAD)"

    # ------------------------------------------------------------ log

    def log(self, count: int = 10) -> Tuple[bool, str]:
        """Show commit history."""
        root = _git_root(self.cwd)
        if not root:
            return False, "Not inside a git repository. Run 'git init' first."
        ok, out, err = _run_git(
            ["log", f"-{count}", "--oneline", "--decorate"],
            self.cwd,
        )
        if ok:
            return True, out.strip() or "No commits yet"
        return False, f"git log failed: {err or out}"

    # ------------------------------------------------------------ remote

    def remote(self, action: str = "list", name: str = "", url: str = "") -> Tuple[bool, str]:
        """Manage git remotes."""
        root = _git_root(self.cwd)
        if not root:
            return False, "Not inside a git repository. Run 'git init' first."
        if action == "list":
            ok, out, err = _run_git(["remote", "-v"], self.cwd)
            if ok:
                return True, out.strip() or "No remotes configured"
            return False, f"git remote failed: {err or out}"
        if action == "add" and name and url:
            ok, out, err = _run_git(["remote", "add", name, url], self.cwd)
            if ok:
                return True, f"Remote '{name}' added: {url}"
            return False, f"git remote add failed: {err or out}"
        if action == "remove" and name:
            ok, out, err = _run_git(["remote", "remove", name], self.cwd)
            if ok:
                return True, f"Remote '{name}' removed"
            return False, f"git remote remove failed: {err or out}"
        return False, "Usage: git remote <list|add|remove> [name] [url]"

    # ------------------------------------------------------------ diff

    def diff(self, staged: bool = False, path: str = "") -> Tuple[bool, str]:
        """Show changes."""
        root = _git_root(self.cwd)
        if not root:
            return False, "Not inside a git repository. Run 'git init' first."
        args = ["diff"]
        if staged:
            args.append("--staged")
        if path:
            args.append(path)
        ok, out, err = _run_git(args, self.cwd)
        if ok:
            if not out.strip():
                return True, "No changes"
            return True, out.strip()
        return False, f"git diff failed: {err or out}"

    # ------------------------------------------------------------ clone

    def clone(self, repo_url: str, dest: str = "") -> Tuple[bool, str]:
        """Clone a repository."""
        if not repo_url:
            return False, "Usage: git clone <url> [destination]"
        target = dest or os.path.basename(repo_url).replace(".git", "")
        ok, out, err = _run_git(["clone", repo_url, target] if dest else ["clone", repo_url], self.cwd)
        if ok:
            return True, f"Cloned into '{target}'"
        return False, f"git clone failed: {err or out}"

    # ------------------------------------------------------------ full workflow

    def workflow_init_and_commit(
        self,
        message: str = "Initial commit",
        remote_url: str = "",
        branch: str = "main",
    ) -> Dict[str, Any]:
        """Full workflow: init -> add all -> commit -> optionally set remote and push."""
        results: Dict[str, Any] = {"steps": [], "success": True}

        # 1. Init
        ok, msg = self.init()
        results["steps"].append({"step": "git init", "ok": ok, "msg": msg})
        if not ok:
            results["success"] = False
            return results

        # 2. Add all
        ok, msg = self.add(all_files=True)
        results["steps"].append({"step": "git add .", "ok": ok, "msg": msg})
        if not ok:
            results["success"] = False

        # 3. Commit
        ok, msg = self.commit(message)
        results["steps"].append({"step": f"git commit -m \"{message}\"", "ok": ok, "msg": msg})
        if not ok:
            results["success"] = False

        # 4. Set default branch name
        if branch and branch != "master":
            _run_git(["branch", "-M", branch], self.cwd)

        # 5. Add remote if provided
        if remote_url:
            ok, msg = self.remote("add", "origin", remote_url)
            results["steps"].append({"step": f"git remote add origin {remote_url}", "ok": ok, "msg": msg})
            if not ok:
                results["success"] = False

        # 6. Push
        ok, msg = self.push("origin", branch)
        results["steps"].append({"step": f"git push origin {branch}", "ok": ok, "msg": msg})
        if not ok:
            results["success"] = False

        return results

    # ------------------------------------------------------------ helpers

    @staticmethod
    def is_git_repo(cwd: str = ".") -> bool:
        """Check if the given directory is inside a git repository."""
        return _git_root(cwd) is not None

    @staticmethod
    def find_git_executable() -> Optional[str]:
        """Find the git executable path, or None if not installed."""
        return shutil.which("git")