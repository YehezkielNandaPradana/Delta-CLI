import tempfile
import os
from delta.intelligence.repository.detector import RepositoryDetector

def test_detect_python_pytest_project():
    with tempfile.TemporaryDirectory() as tmp:
        with open(os.path.join(tmp, "pyproject.toml"), "w") as f:
            f.write("[tool.pytest.ini_options]\n")
        with open(os.path.join(tmp, "main.py"), "w") as f:
            f.write("print('hello')\n")

        detector = RepositoryDetector(tmp)
        info = detector.detect()
        assert "python" in info.languages
        assert info.primary_language == "python"
        assert info.test_runner == "pytest"
        assert info.test_command == "pytest"

def test_detect_node_project():
    with tempfile.TemporaryDirectory() as tmp:
        with open(os.path.join(tmp, "package.json"), "w") as f:
            f.write('{"scripts": {"test": "jest"}, "dependencies": {"react": "^18.0.0"}}')

        detector = RepositoryDetector(tmp)
        info = detector.detect()
        assert "javascript" in info.languages or "typescript" in info.languages
        assert "react" in info.frameworks
        assert info.test_runner == "jest"
        assert info.test_command == "npm test"

def test_detect_laravel_project():
    with tempfile.TemporaryDirectory() as tmp:
        with open(os.path.join(tmp, "composer.json"), "w") as f:
            f.write('{"require": {"laravel/framework": "^10.0"}}')
        with open(os.path.join(tmp, "artisan"), "w") as f:
            f.write("<?php")

        detector = RepositoryDetector(tmp)
        info = detector.detect()
        assert "php" in info.languages
        assert "laravel" in info.frameworks
        assert info.test_command == "php artisan test"
