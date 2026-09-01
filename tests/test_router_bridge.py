import pytest
from unittest.mock import patch
from delta.web.bridge import EngineBridge

def test_bridge_start_router_already_running():
    bridge = EngineBridge(engine=None)
    with patch("delta.utils.router_manager.is_9router_running", return_value=True):
        res = bridge.start_router()
        assert res["status"] == "ok"
        assert res["running"] is True
        assert "already running" in res["message"]

def test_bridge_start_router_success():
    bridge = EngineBridge(engine=None)
    with patch("delta.utils.router_manager.is_9router_running", return_value=False), \
         patch("delta.utils.router_manager.start_9router") as mock_start, \
         patch("delta.utils.router_manager.wait_for_9router", return_value=True):
        res = bridge.start_router()
        assert res["status"] == "ok"
        assert res["running"] is True
        mock_start.assert_called_once()

def test_bridge_start_router_timeout():
    bridge = EngineBridge(engine=None)
    with patch("delta.utils.router_manager.is_9router_running", return_value=False), \
         patch("delta.utils.router_manager.start_9router"), \
         patch("delta.utils.router_manager.wait_for_9router", return_value=False):
        res = bridge.start_router()
        assert res["status"] == "error"
        assert res["running"] is False
        assert "Failed to start" in res["message"]
