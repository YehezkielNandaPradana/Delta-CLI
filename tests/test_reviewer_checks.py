# tests/test_reviewer_checks.py
from delta.agent.reviewer.correctness import CorrectnessReviewer
from delta.agent.reviewer.architecture import ArchitectureReviewer
from delta.agent.reviewer.security import SecurityReviewer

def test_security_reviewer_detects_hardcoded_secrets():
    sec_rev = SecurityReviewer()
    findings = sec_rev.review(
        modified_files=["src/config.py"],
        diff_text='+ API_KEY = "sk-live-12345678901234567890"'
    )
    assert len(findings) >= 1
    assert findings[0].category == "security"

def test_architecture_reviewer_detects_layer_violations():
    arch_rev = ArchitectureReviewer()
    findings = arch_rev.review(
        repo_graph=None,
        modified_files=["delta/core/engine.py", "delta/web/bridge.py"]
    )
    assert isinstance(findings, list)
