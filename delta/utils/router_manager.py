import os
import socket
import subprocess
import time
import sys

def is_9router_running() -> bool:
    """Check if 9router is running on port 20128."""
    try:
        with socket.create_connection(("localhost", 20128), timeout=1):
            return True
    except (ConnectionRefusedError, socket.timeout):
        return False

def start_9router() -> None:
    """Start 9router in the background listening on all network interfaces (0.0.0.0)."""
    router_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "9router"))

    env = os.environ.copy()
    env["PORT"] = "20128"
    env["HOST"] = "0.0.0.0"
    env["HOSTNAME"] = "0.0.0.0"
    env["NEXT_PUBLIC_BASE_URL"] = "http://localhost:20128"

    if sys.platform == "win32":
        subprocess.Popen(
            ["npm.cmd", "run", "start"],
            cwd=router_path,
            env=env,
            creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
            stdout=open(os.devnull, "w"),
            stderr=open(os.devnull, "w")
        )
    else:
        subprocess.Popen(
            ["npm", "run", "start"],
            cwd=router_path,
            env=env,
            start_new_session=True,
            stdout=open(os.devnull, "w"),
            stderr=open(os.devnull, "w")
        )

def wait_for_9router(timeout: float = 30.0, interval: float = 1.0) -> bool:
    """Wait for 9router to be ready on port 20128.

    Args:
        timeout: Maximum seconds to wait.
        interval: Polling interval in seconds.

    Returns:
        True if 9router is ready, False if it did not become ready in time.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        if is_9router_running():
            return True
        time.sleep(interval)
    return False

def ensure_9router() -> bool:
    """Ensure 9router is running. Start it if not, then wait for readiness.

    Returns:
        True if 9router is running and ready, False otherwise.
    """
    if is_9router_running():
        return True
    start_9router()
    return wait_for_9router(timeout=30.0)
