"""Cloudflare Quick Tunnel Process Manager for Delta with Auto-Download & Log Streaming."""
import os
import re
import sys
import shutil
import platform
import subprocess
import threading
import time
import urllib.request
from typing import Any, Dict, List, Optional
from collections import deque

_tunnel_process: Optional[subprocess.Popen] = None
_tunnel_url: Optional[str] = None
_tunnel_start_time: Optional[float] = None
_tunnel_lock = threading.Lock()
_tunnel_logs: deque = deque(maxlen=500)
_reader_thread: Optional[threading.Thread] = None

TRY_CLOUDFLARE_REGEX = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")

def _add_log(text: str, level: str = "INFO"):
    timestamp = time.strftime("%H:%M:%S")
    _tunnel_logs.append({
        "timestamp": timestamp,
        "time": time.time(),
        "level": level,
        "message": text.strip()
    })

def find_cloudflared_binary() -> Optional[str]:
    """Find cloudflared executable in PATH, User Home, or Delta Bin directory."""
    # 1. System PATH
    found = shutil.which("cloudflared")
    if found:
        return found

    # 2. User Home / Profile directory
    home_dir = os.path.expanduser("~")
    candidates = [
        os.path.join(home_dir, "cloudflared.exe"),
        os.path.join(home_dir, "cloudflared"),
        os.path.join(home_dir, ".delta", "bin", "cloudflared.exe"),
        os.path.join(home_dir, ".delta", "bin", "cloudflared"),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "bin", "cloudflared.exe"),
        r"C:\Users\ThinkPad\cloudflared.exe",
        r"C:\Program Files\cloudflared\cloudflared.exe",
    ]
    for c in candidates:
        if os.path.exists(c) and os.path.isfile(c):
            return os.path.abspath(c)

    return None

def is_cloudflared_available() -> bool:
    """Check if cloudflared binary is accessible."""
    return find_cloudflared_binary() is not None

def auto_download_cloudflared() -> Optional[str]:
    """Automatically download official cloudflared binary for current OS architecture."""
    system = platform.system().lower()
    machine = platform.machine().lower()

    delta_bin_dir = os.path.join(os.path.expanduser("~"), ".delta", "bin")
    os.makedirs(delta_bin_dir, exist_ok=True)

    if system == "windows":
        filename = "cloudflared.exe"
        download_url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
    elif system == "darwin":
        filename = "cloudflared"
        download_url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-amd64" if "arm" not in machine else "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-arm64"
    else:  # Linux / Android Termux
        filename = "cloudflared"
        if "aarch64" in machine or "arm64" in machine:
            download_url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64"
        elif "arm" in machine:
            download_url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm"
        else:
            download_url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"

    target_path = os.path.join(delta_bin_dir, filename)

    try:
        _add_log(f"Downloading cloudflared from {download_url}...", level="INFO")
        req = urllib.request.Request(
            download_url,
            headers={"User-Agent": "Delta-Workstation/1.0"}
        )
        with urllib.request.urlopen(req, timeout=60) as resp, open(target_path, "wb") as out_f:
            shutil.copyfileobj(resp, out_f)

        # Make executable on Unix
        if system != "windows":
            os.chmod(target_path, 0o755)

        _add_log(f"Successfully installed cloudflared to {target_path}", level="SUCCESS")
        return target_path
    except Exception as e:
        _add_log(f"Failed to auto-download cloudflared: {e}", level="ERROR")
        return None

def _read_output(proc: subprocess.Popen):
    """Background reader thread to continuously capture stdout/stderr logs."""
    global _tunnel_url
    if not proc.stdout:
        return
    try:
        for raw_line in iter(proc.stdout.readline, ""):
            if not raw_line:
                break
            line = raw_line.strip()
            if not line:
                continue

            match = TRY_CLOUDFLARE_REGEX.search(line)
            if match:
                _tunnel_url = match.group(0)
                _add_log(f"QUICK TUNNEL ACTIVE: {_tunnel_url}", level="SUCCESS")

            _add_log(line, level="DEBUG" if "DBG" in line else ("WARN" if "WRN" in line else "INFO"))
    except Exception as exc:
        _add_log(f"Output reader stopped: {exc}", level="WARN")

def get_tunnel_status() -> Dict[str, Any]:
    """Retrieve current status and metrics of the active Cloudflare Quick Tunnel."""
    global _tunnel_process, _tunnel_url, _tunnel_start_time
    running = _tunnel_process is not None and _tunnel_process.poll() is None
    uptime = round(time.time() - _tunnel_start_time, 1) if running and _tunnel_start_time else 0

    return {
        "status": "ok",
        "running": running,
        "url": _tunnel_url if running else None,
        "available": is_cloudflared_available(),
        "binary_path": find_cloudflared_binary(),
        "uptime_seconds": uptime,
        "logs_count": len(_tunnel_logs)
    }

def get_tunnel_logs(limit: int = 100) -> List[Dict[str, Any]]:
    """Retrieve recent log entries from the Cloudflare tunnel process."""
    logs_list = list(_tunnel_logs)
    if limit and limit > 0:
        return logs_list[-limit:]
    return logs_list

def start_cloudflare_tunnel(port: int = 8080, timeout: float = 30.0) -> Dict[str, Any]:
    """Launch a Cloudflare Quick Tunnel forwarding to local port."""
    global _tunnel_process, _tunnel_url, _tunnel_start_time, _reader_thread
    with _tunnel_lock:
        if _tunnel_process is not None and _tunnel_process.poll() is None and _tunnel_url:
            return {
                "status": "ok",
                "running": True,
                "url": _tunnel_url,
                "message": f"Tunnel already running at {_tunnel_url}"
            }

        bin_path = find_cloudflared_binary()
        if not bin_path:
            _add_log("Binary not found locally, attempting auto-download...", level="INFO")
            bin_path = auto_download_cloudflared()

        if not bin_path:
            return {
                "status": "error",
                "running": False,
                "url": None,
                "message": "cloudflared binary not found and download failed. Please install cloudflared manually."
            }

        # Clean old state
        if _tunnel_process:
            try:
                _tunnel_process.terminate()
            except Exception:
                pass

        _tunnel_url = None
        _tunnel_start_time = time.time()
        _add_log(f"Starting cloudflared tunnel forwarding to 127.0.0.1:{port}...", level="INFO")

        cmd = [bin_path, "tunnel", "--url", f"http://127.0.0.1:{port}"]

        creationflags = 0
        if sys.platform == "win32":
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)

        _tunnel_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            creationflags=creationflags
        )

        _reader_thread = threading.Thread(target=_read_output, args=(_tunnel_process,), daemon=True)
        _reader_thread.start()

        deadline = time.time() + timeout
        while time.time() < deadline:
            if _tunnel_process.poll() is not None:
                _add_log(f"Process terminated prematurely with exit code {_tunnel_process.poll()}", level="ERROR")
                break
            if _tunnel_url:
                break
            time.sleep(0.2)

        if _tunnel_url:
            return {
                "status": "ok",
                "running": True,
                "url": _tunnel_url,
                "message": f"Cloudflare Quick Tunnel established: {_tunnel_url}"
            }

        return {
            "status": "error",
            "running": False,
            "url": None,
            "message": "Timed out waiting for trycloudflare.com URL"
        }

def stop_cloudflare_tunnel() -> bool:
    """Terminate any active Cloudflare tunnel process."""
    global _tunnel_process, _tunnel_url, _tunnel_start_time
    with _tunnel_lock:
        if _tunnel_process and _tunnel_process.poll() is None:
            _add_log("Stopping Cloudflare tunnel process...", level="INFO")
            _tunnel_process.terminate()
            try:
                _tunnel_process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                _tunnel_process.kill()
            _tunnel_process = None
            _tunnel_url = None
            _tunnel_start_time = None
            _add_log("Cloudflare tunnel stopped.", level="INFO")
            return True
        _tunnel_process = None
        _tunnel_url = None
        _tunnel_start_time = None
        return False
