from unittest.mock import patch, MagicMock
from delta.utils.tunnel_manager import (
    is_cloudflared_available,
    get_tunnel_status,
    start_cloudflare_tunnel,
    stop_cloudflare_tunnel
)

def test_tunnel_status_initial():
    status = get_tunnel_status()
    assert isinstance(status, dict)
    assert "running" in status
    assert "url" in status
    assert "available" in status

def test_is_cloudflared_available():
    with patch("shutil.which", return_value="/usr/local/bin/cloudflared"):
        assert is_cloudflared_available() is True
    with patch("delta.utils.tunnel_manager.find_cloudflared_binary", return_value=None):
        assert is_cloudflared_available() is False

def test_start_cloudflare_tunnel_missing_binary():
    with patch("delta.utils.tunnel_manager.find_cloudflared_binary", return_value=None), \
         patch("delta.utils.tunnel_manager.auto_download_cloudflared", return_value=None):
        res = start_cloudflare_tunnel(port=8080)
        assert res["status"] == "error"
        assert res["running"] is False
        assert "not found" in res["message"].lower()

def test_start_cloudflare_tunnel_success():
    mock_proc = MagicMock()
    mock_proc.poll.return_value = None
    mock_proc.stdout.readline.side_effect = [
        "2026-09-02 INF Starting tunnel...",
        "2026-09-02 INF Your quick Tunnel has been created! Visit https://delta-alpha-bravo.trycloudflare.com",
        ""
    ]

    with patch("delta.utils.tunnel_manager.is_cloudflared_available", return_value=True), \
         patch("subprocess.Popen", return_value=mock_proc):
        res = start_cloudflare_tunnel(port=8080, timeout=1.0)
        assert res["status"] == "ok"
        assert res["running"] is True
        assert res["url"] == "https://delta-alpha-bravo.trycloudflare.com"

        # Check status
        st = get_tunnel_status()
        assert st["running"] is True
        assert st["url"] == "https://delta-alpha-bravo.trycloudflare.com"

        # Stop tunnel
        stopped = stop_cloudflare_tunnel()
        assert stopped is True
        assert get_tunnel_status()["running"] is False
