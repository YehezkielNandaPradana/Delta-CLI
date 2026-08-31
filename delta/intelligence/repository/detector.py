import os
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set

@dataclass
class DetectorResult:
    primary_language: str
    languages: List[str] = field(default_factory=list)
    frameworks: List[str] = field(default_factory=list)
    package_managers: List[str] = field(default_factory=list)
    build_systems: List[str] = field(default_factory=list)
    test_runner: Optional[str] = None
    test_command: Optional[str] = None
    entrypoints: List[str] = field(default_factory=list)
    has_git: bool = False

class RepositoryDetector:
    def __init__(self, root_path: str = "."):
        self.root = Path(root_path).resolve()

    def detect(self) -> DetectorResult:
        languages: Set[str] = set()
        frameworks: Set[str] = set()
        package_managers: Set[str] = set()
        build_systems: Set[str] = set()
        test_runner = None
        test_command = None
        entrypoints: List[str] = []

        has_git = (self.root / ".git").exists()

        # Check Python
        if (self.root / "pyproject.toml").exists() or (self.root / "setup.py").exists() or (self.root / "requirements.txt").exists() or any(self.root.glob("*.py")):
            languages.add("python")
            package_managers.add("pip")
            test_runner = "pytest"
            test_command = "pytest"
            if (self.root / "manage.py").exists():
                frameworks.add("django")
            if (self.root / "app.py").exists():
                entrypoints.append("app.py")
            if (self.root / "main.py").exists():
                entrypoints.append("main.py")

        # Check Node / JS / TS
        pkg_json = self.root / "package.json"
        if pkg_json.exists():
            languages.add("javascript")
            package_managers.add("npm")
            if (self.root / "tsconfig.json").exists() or any(self.root.glob("**/*.ts")):
                languages.add("typescript")
            try:
                with open(pkg_json, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                    if "react" in deps:
                        frameworks.add("react")
                    if "vue" in deps:
                        frameworks.add("vue")
                    if "express" in deps:
                        frameworks.add("express")
                    if "next" in deps:
                        frameworks.add("next.js")
                    scripts = data.get("scripts", {})
                    if "jest" in deps or "jest" in scripts.get("test", ""):
                        test_runner = "jest"
                        test_command = "npm test"
                    elif "vitest" in deps or "vitest" in scripts.get("test", ""):
                        test_runner = "vitest"
                        test_command = "npx vitest run"
                    else:
                        test_runner = "npm test"
                        test_command = "npm test"
            except Exception:
                pass

        # Check PHP / Laravel
        composer_json = self.root / "composer.json"
        if composer_json.exists():
            languages.add("php")
            package_managers.add("composer")
            if (self.root / "artisan").exists():
                frameworks.add("laravel")
                test_runner = "artisan test"
                test_command = "php artisan test"
            elif (self.root / "phpunit.xml").exists() or (self.root / "phpunit.xml.dist").exists():
                test_runner = "phpunit"
                test_command = "./vendor/bin/phpunit"

        # Check Go
        if (self.root / "go.mod").exists():
            languages.add("go")
            test_runner = "go test"
            test_command = "go test ./..."

        # Check Rust
        if (self.root / "Cargo.toml").exists():
            languages.add("rust")
            test_runner = "cargo test"
            test_command = "cargo test"

        # Primary language heuristic
        primary = "unknown"
        if "python" in languages:
            primary = "python"
        elif "typescript" in languages:
            primary = "typescript"
        elif "javascript" in languages:
            primary = "javascript"
        elif "php" in languages:
            primary = "php"
        elif "go" in languages:
            primary = "go"
        elif "rust" in languages:
            primary = "rust"
        elif languages:
            primary = list(languages)[0]

        return DetectorResult(
            primary_language=primary,
            languages=sorted(list(languages)),
            frameworks=sorted(list(frameworks)),
            package_managers=sorted(list(package_managers)),
            build_systems=sorted(list(build_systems)),
            test_runner=test_runner,
            test_command=test_command,
            entrypoints=entrypoints,
            has_git=has_git
        )
