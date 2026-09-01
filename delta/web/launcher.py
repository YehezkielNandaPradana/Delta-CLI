"""
Dedicated Browser Window Launcher for Delta Web UI.

Launches Delta in a clean, maximized Chromium desktop app window
(--app=http://127.0.0.1:8000 --start-maximized) using Microsoft Edge,
Google Chrome, Brave, or platform Chromium, falling back to webbrowser.
"""

import os
import sys
import shutil
import subprocess
import threading
import time
from typing import Optional, List


def find_windows_browser() -> Optional[str]:
    """Find available Chromium-based browser executable on Windows."""
    # Standard installation paths for Edge, Chrome, Brave on Windows
    candidate_paths = [
        # Microsoft Edge (built-in on Windows 10/11)
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%LocalAppData%\Microsoft\Edge\Application\msedge.exe"),
        # Google Chrome
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
        # Brave Browser
        os.path.expandvars(r"%ProgramFiles%\BraveSoftware\Brave-Browser\Application\brave.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\BraveSoftware\Brave-Browser\Application\brave.exe"),
        os.path.expandvars(r"%LocalAppData%\BraveSoftware\Brave-Browser\Application\brave.exe"),
    ]

    for p in candidate_paths:
        if os.path.isfile(p):
            return p

    # Fallback to PATH lookup
    for name in ("msedge", "chrome", "google-chrome", "chromium", "brave"):
        found = shutil.which(name)
        if found and os.path.isfile(found):
            return found

    return None


def find_posix_browser() -> Optional[str]:
    """Find available Chromium-based browser on Linux or macOS."""
    if sys.platform == "darwin":
        mac_paths = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
            "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
        ]
        for p in mac_paths:
            if os.path.isfile(p):
                return p

    for name in ("google-chrome", "chrome", "chromium", "chromium-browser", "microsoft-edge", "brave-browser", "brave"):
        found = shutil.which(name)
        if found:
            return found

    return None


def launch_delta_browser(url: str = "http://127.0.0.1:8000", delay: float = 0.25) -> None:
    """
    Launch Delta Web UI in a dedicated maximized application window.

    Spawns in a background daemon thread with a tiny delay to ensure the
    underlying HTTP server is ready to accept connections.
    """
    def _open():
        if delay > 0:
            time.sleep(delay)

        browser_exe: Optional[str] = None
        if sys.platform == "win32":
            browser_exe = find_windows_browser()
        else:
            browser_exe = find_posix_browser()

        if browser_exe:
            # Launch in Chromium App Mode with start-maximized flag
            args: List[str] = [
                browser_exe,
                f"--app={url}",
                "--start-maximized",
                "--window-position=0,0",
            ]
            try:
                if sys.platform == "win32":
                    # DETACHED_PROCESS + CREATE_NEW_PROCESS_GROUP prevents terminal blocking
                    creationflags = 0x00000008 | 0x00000200  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
                    subprocess.Popen(
                        args,
                        creationflags=creationflags,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        close_fds=True,
                    )
                else:
                    subprocess.Popen(
                        args,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        start_new_session=True,
                    )
                return
            except Exception:
                pass

        # Fallback to standard webbrowser module if no chromium binary found
        import webbrowser
        try:
            webbrowser.open(url)
        except Exception:
            pass

    t = threading.Thread(target=_open, daemon=True, name="DeltaBrowserLauncher")
    t.start()
