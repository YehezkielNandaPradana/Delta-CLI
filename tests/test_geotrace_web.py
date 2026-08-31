from delta.web.bridge import EngineBridge

def test_bridge_geotrace_analyze():
    bridge = EngineBridge()
    res = bridge.geotrace_analyze(
        target="@johndoe_surabaya",
        operator="test-analyst",
        purpose="KYC Security Check",
        consent_mode=False
    )
    assert res["status"] in ("ok", "rejected")
    if res["status"] == "ok":
        assert "report" in res
        assert res["report"]["target"] == "johndoe_surabaya"

def test_bridge_geotrace_audit_and_verify():
    bridge = EngineBridge()
    audit_res = bridge.geotrace_get_audit(limit=10)
    assert audit_res["status"] == "ok"
    assert isinstance(audit_res["logs"], list)

    verify_res = bridge.geotrace_verify_audit()
    assert verify_res["status"] == "ok"
    assert verify_res["valid"] is True
