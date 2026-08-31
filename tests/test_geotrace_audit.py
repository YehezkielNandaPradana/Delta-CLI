from delta.modules.geotrace.audit import GeoTraceAuditManager

def test_audit_log_hash_chain_integrity(tmp_path):
    db_file = str(tmp_path / "test_audit.db")
    mgr = GeoTraceAuditManager(db_path=db_file)

    mgr.log_query("analyst_1", "@target1", "KYC check", False, "COMPLETED")
    mgr.log_query("analyst_2", "@target2", "Incident response", True, "COMPLETED")
    mgr.log_query("analyst_1", "@target3", "Threat intelligence", False, "ALLOWED")

    valid, issues = mgr.verify_log_integrity()
    assert valid is True
    assert len(issues) == 0

def test_audit_safety_gate_minor_refusal(tmp_path):
    db_file = str(tmp_path / "test_audit.db")
    mgr = GeoTraceAuditManager(db_path=db_file)

    allowed, status, reason = mgr.evaluate_target_safety({
        "is_private": False,
        "bio": "SMP Negeri 1 Jakarta | Student 14yo",
        "username": "junior_kid"
    })
    assert allowed is False
    assert status == "REJECTED_MINOR"
    assert "minor" in reason.lower()

def test_audit_safety_gate_private_refusal(tmp_path):
    db_file = str(tmp_path / "test_audit.db")
    mgr = GeoTraceAuditManager(db_path=db_file)

    allowed, status, reason = mgr.evaluate_target_safety({
        "is_private": True,
        "bio": "Private photographer profile",
        "username": "secret_guy"
    })
    assert allowed is False
    assert status == "REJECTED_PRIVATE"
    assert "private" in reason.lower()
