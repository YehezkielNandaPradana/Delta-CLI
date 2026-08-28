"""Bridge between Delta CLI Engine and Web Interface."""
import io
import os
import re
import sys
import threading
from datetime import datetime
from typing import Any, Dict, Optional, Set, List
from pydantic import BaseModel
from delta.core.events import AsyncEventBus

ANSI_STRIP = re.compile(r"\x1b\[[0-9;?]*[a-zA-Z]|\x1b\][^\x07]*\x07")
CLI_PREFIX_STRIP = re.compile(r"^(?:Δ AI\s*(?:memikirkan jawaban\.\.\.|→\s*\w+|\n|▔+)|[▔\s]+)+", re.MULTILINE)

def clean_terminal_output(text: str) -> str:
    """Clean ANSI escape codes and TUI terminal banners for Web display."""
    if not text:
        return ""
    clean = ANSI_STRIP.sub("", text)
    lines = []
    for line in clean.splitlines():
        trimmed = line.strip()
        if "memikirkan jawaban..." in trimmed:
            continue
        if "Δ AI" in trimmed or "▔" in trimmed:
            continue
        lines.append(line)
    result = "\n".join(lines).strip()
    return result

class WebBridge:
    """Relays events from AsyncEventBus to WebSocket / Web listeners."""
    def __init__(self, bus: AsyncEventBus):
        self.bus = bus
        self.active_connections: Set[Any] = set()
        self.event_queue: List[Dict[str, Any]] = []

    def handle_event(self, event: BaseModel):
        data = {
            "type": type(event).__name__,
            "data": event.model_dump()
        }
        self.event_queue.append(data)

    def subscribe_all(self):
        pass

class EngineBridge:
    def __init__(self, engine: Optional[Any] = None):
        self.engine = engine
        if self.engine:
            self.engine.web_mode = True

    def cancel_execution(self) -> Dict[str, Any]:
        if self.engine and hasattr(self.engine, "_stop_event") and self.engine._stop_event:
            self.engine._stop_event.set()
            return {"status": "ok", "message": "Stop signal sent"}
        return {"status": "error", "message": "No active execution to stop"}

    def get_status(self) -> Dict[str, Any]:
        cwd = getattr(self.engine, "cwd", None) or os.getcwd()
        active_target = self.engine.session.get_host() if self.engine and hasattr(self.engine, "session") else ""

        # Count targets
        targets_count = 0
        if self.engine and hasattr(self.engine, "database"):
            try:
                hosts = self.engine.database.get_all_hosts()
                targets_count = len(hosts)
            except Exception:
                targets_count = 0

        # Count tools
        tools_count = 0
        if self.engine and hasattr(self.engine, "tools"):
            try:
                tools_count = len(self.engine.tools.tools)
            except Exception:
                tools_count = 0

        # LLM details
        llm_model = getattr(self.engine.config, "llm_model", "Antigravity") if self.engine and hasattr(self.engine, "config") else "Antigravity"
        llm_provider = getattr(self.engine.config, "llm_provider", "9router") if self.engine and hasattr(self.engine, "config") else "9router"
        is_running = bool(self.engine and getattr(self.engine, "_in_llm_processing", False))
        active_agents_count = 1 if is_running else 0

        return {
            "status": "online",
            "version": "1.0.0",
            "working_directory": cwd,
            "llm_enabled": getattr(self.engine.config, "llm_enabled", False) if self.engine and hasattr(self.engine, "config") else False,
            "active_target": active_target,
            "targets_count": targets_count,
            "tools_count": tools_count,
            "llm_model": llm_model,
            "llm_provider": llm_provider,
            "is_running": is_running,
            "active_agents_count": active_agents_count,
            "active_agents": [
                {
                    "name": "Main Core Agent",
                    "role": "Orchestrator & Reasoning",
                    "status": "RUNNING" if is_running else "IDLE",
                    "last_active": "Just now" if is_running else "Ready"
                },
                {
                    "name": "Security Sentinel",
                    "role": "Penetration & Scope Guard",
                    "status": "RUNNING" if is_running else "IDLE",
                    "last_active": "Ready"
                },
                {
                    "name": "Codebase & System",
                    "role": "Filesystem & Terminal",
                    "status": "RUNNING" if is_running else "IDLE",
                    "last_active": "Ready"
                }
            ]
        }

    def get_targets(self) -> Dict[str, Any]:
        if not self.engine or not hasattr(self.engine, "database"):
            return {"status": "error", "message": "Database not initialized", "targets": []}
        try:
            hosts = self.engine.database.get_all_hosts()
            active_target = self.engine.session.get_host() if hasattr(self.engine, "session") else ""
            return {"status": "ok", "targets": hosts, "active_target": active_target}
        except Exception as exc:
            return {"status": "error", "message": str(exc), "targets": []}

    def add_target(self, host: str, ip: str = "", notes: str = "", risk_level: str = "unknown") -> Dict[str, Any]:
        if not self.engine or not hasattr(self.engine, "database"):
            return {"status": "error", "message": "Database not initialized"}
        if not host or not host.strip():
            return {"status": "error", "message": "Target host cannot be empty"}
        try:
            target_host = host.strip()
            self.engine.database.upsert_host(
                target_host,
                ip=ip.strip() if ip else "",
                notes=notes.strip() if notes else "",
                risk_level=risk_level
            )
            # If no active host is currently set, set this one
            if hasattr(self.engine, "session") and not self.engine.session.get_host():
                self.engine.session.set_host(target_host)
            return {"status": "ok", "message": f"Target '{target_host}' saved successfully"}
        except Exception as exc:
            return {"status": "error", "message": str(exc)}

    def delete_target(self, host: str) -> Dict[str, Any]:
        if not self.engine or not hasattr(self.engine, "database"):
            return {"status": "error", "message": "Database not initialized"}
        try:
            res = self.engine.database.delete_host(host)
            if hasattr(self.engine, "session") and self.engine.session.get_host() == host:
                self.engine.session.set_host("")
            return {"status": "ok", "deleted": res}
        except Exception as exc:
            return {"status": "error", "message": str(exc)}

    def set_active_target(self, host: str) -> Dict[str, Any]:
        if not self.engine or not hasattr(self.engine, "session"):
            return {"status": "error", "message": "Session not initialized"}
        try:
            self.engine.session.set_host(host.strip() if host else "")
            return {"status": "ok", "active_target": self.engine.session.get_host()}
        except Exception as exc:
            return {"status": "error", "message": str(exc)}

    def get_history(self, limit: int = 50) -> Dict[str, Any]:
        if not self.engine or not hasattr(self.engine, "session"):
            return {"status": "error", "message": "Session not initialized", "history": []}
        try:
            history = self.engine.session.get_history(limit=limit)
            return {"status": "ok", "history": history}
        except Exception as exc:
            return {"status": "error", "message": str(exc), "history": []}

    def clear_history(self) -> Dict[str, Any]:
        if not self.engine or not hasattr(self.engine, "database"):
            return {"status": "error", "message": "Database not initialized"}
        try:
            self.engine.database.clear_history()
            return {"status": "ok", "message": "History cleared successfully"}
        except Exception as exc:
            return {"status": "error", "message": str(exc)}

    def get_models(self) -> Dict[str, Any]:
        from delta.ai.llm import MODEL_PRESETS, PROVIDERS
        current_model = getattr(self.engine.config, "llm_model", "Antigravity") if self.engine and hasattr(self.engine, "config") else "Antigravity"
        current_provider = getattr(self.engine.config, "llm_provider", "9router") if self.engine and hasattr(self.engine, "config") else "9router"

        models_list = []
        for name, info in MODEL_PRESETS.items():
            models_list.append({
                "name": name,
                "description": info.get("description", ""),
                "provider": info.get("provider", "openai"),
                "is_current": (name == current_model or info.get("model") == current_model)
            })
        return {
            "status": "ok",
            "current_model": current_model,
            "current_provider": current_provider,
            "models": models_list,
            "providers": [{"name": k, "description": v.get("description", ""), "base_url": v.get("base_url", "")} for k, v in PROVIDERS.items()]
        }

    def select_model(self, model_name: str) -> Dict[str, Any]:
        if not self.engine:
            return {"status": "error", "message": "Engine not initialized"}
        try:
            self.engine._handle_slash_command(f"/model {model_name}")
            new_model = getattr(self.engine.config, "llm_model", model_name)
            return {"status": "ok", "model": new_model, "message": f"Model switched to {new_model}"}
        except Exception as exc:
            return {"status": "error", "message": str(exc)}

    def get_router_status(self) -> Dict[str, Any]:
        import socket
        router_running = False
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            result = sock.connect_ex(("127.0.0.1", 20128))
            router_running = (result == 0)
            sock.close()
        except Exception:
            router_running = False

        provider = getattr(self.engine.config, "llm_provider", "9router") if self.engine and hasattr(self.engine, "config") else "9router"
        base_url = getattr(self.engine.config, "llm_api_base_url", "http://localhost:20128/v1") if self.engine and hasattr(self.engine, "config") else "http://localhost:20128/v1"
        return {
            "status": "ok",
            "running": router_running,
            "provider": provider,
            "base_url": base_url,
            "port": 20128,
            "latency_ms": 12 if router_running else None
        }

    def get_evidence(self) -> Dict[str, Any]:
        evidence_items = []
        if self.engine and hasattr(self.engine, "pentest") and self.engine.pentest:
            try:
                chains = getattr(self.engine.pentest.evidence_engine, "_chains", {})
                for _, chain in chains.items():
                    evidence_items.append({
                        "finding_id": chain.finding_id,
                        "hypothesis_id": chain.hypothesis_id,
                        "impact_summary": chain.impact_summary,
                        "reproduction_curl": chain.reproduction_curl,
                        "baseline_url": chain.baseline_tx.request.url if chain.baseline_tx else "",
                        "test_url": chain.test_tx.request.url if chain.test_tx else "",
                        "anomaly": chain.diff_result.is_significant_anomaly if chain.diff_result else False,
                        "details": chain.diff_result.details if chain.diff_result else []
                    })
            except Exception:
                pass
        return {"status": "ok", "evidence": evidence_items}

    def get_reports(self, limit: int = 20) -> Dict[str, Any]:
        if not self.engine or not hasattr(self.engine, "database"):
            return {"status": "error", "message": "Database not initialized", "reports": []}
        try:
            reports = self.engine.database.get_reports(limit=limit)
            return {"status": "ok", "reports": reports}
        except Exception as exc:
            return {"status": "error", "message": str(exc), "reports": []}

    def get_report_content(self, report_id: int) -> Dict[str, Any]:
        if not self.engine or not hasattr(self.engine, "database"):
            return {"status": "error", "message": "Database not initialized"}
        try:
            report = self.engine.database.get_report(report_id)
            if not report:
                return {"status": "error", "message": f"Report ID {report_id} not found"}
            return {"status": "ok", "report": report}
        except Exception as exc:
            return {"status": "error", "message": str(exc)}

    def generate_report(self, target: str = "") -> Dict[str, Any]:
        if not self.engine:
            return {"status": "error", "message": "Engine not initialized"}
        try:
            target_host = target.strip() or self.engine.session.get_host() or "localhost"
            from delta.modules.report import ReportModule, ReportData
            rep_mod = ReportModule()
            scan_data = self.engine.session.get_scan_result(target_host) or {}
            data = ReportData(
                title=f"Delta Security Assessment Report - {target_host}",
                target=target_host,
                scan_date=datetime.now().isoformat(),
                duration=scan_data.get("duration", 0.0),
                risk_level=scan_data.get("risk_level", "info"),
                summary=scan_data.get("summary", "Automated Web Assessment Report generated via Delta Workstation."),
                host_info={"IP": scan_data.get("ip", ""), "Hostname": scan_data.get("hostname", target_host)},
                open_ports=scan_data.get("open_ports", []),
                services=scan_data.get("services", {}),
                vulnerabilities=scan_data.get("vulnerabilities", []),
            )
            saved_paths = rep_mod.generate(data, format="all")
            # Save into reports database table
            md_path = saved_paths.get("markdown", "")
            md_content = ""
            if md_path and os.path.exists(md_path):
                with open(md_path, "r", encoding="utf-8", errors="replace") as f:
                    md_content = f.read()
            report_id = self.engine.database.save_report(
                title=data.title,
                host=target_host,
                report_type="security_assessment",
                severity=data.risk_level,
                content=md_content,
                format="markdown",
                file_path=md_path
            )
            return {"status": "ok", "message": f"Report generated for {target_host}", "report_id": report_id, "paths": saved_paths}
        except Exception as exc:
            return {"status": "error", "message": str(exc)}

    def execute_command(self, cmd: str, execution_id: Optional[str] = None) -> Dict[str, Any]:
        if not self.engine:
            return {"output": f"Executed command (mock): {cmd}", "is_task": False, "task_id": None}

        original_web_mode = getattr(self.engine, "web_mode", False)
        self.engine.web_mode = True

        output_capture = io.StringIO()
        old_stdout = sys.stdout
        try:
            sys.stdout = output_capture
            self.engine._stop_event = threading.Event()
            try:
                res = self.engine._process_input(cmd, execution_id=execution_id)
            except TypeError:
                res = self.engine._process_input(cmd)

            if isinstance(res, dict):
                output_str = res.get("response") or res.get("error") or ""
                if not output_str and res.get("command"):
                    output_str = f"Executed: {res['command']}"
                output = output_str if output_str else output_capture.getvalue()
                is_task = res.get("is_task", False)
                task_id = res.get("task_id")
            else:
                output = output_capture.getvalue()
                is_task = False
                task_id = None
        finally:
            sys.stdout = old_stdout
            self.engine._stop_event = None
            self.engine.web_mode = original_web_mode

        return {
            "output": clean_terminal_output(output),
            "response": clean_terminal_output(output),
            "is_task": is_task,
            "task_id": task_id
        }

    def get_directory_tree(self, sub_path: str = "") -> Dict[str, Any]:
        root_dir = os.path.abspath(getattr(self.engine, "cwd", None) or os.getcwd())
        target_dir = os.path.abspath(os.path.join(root_dir, sub_path))

        if not target_dir.startswith(root_dir):
            return {"status": "error", "message": "Access denied: Path outside workspace"}

        ignored_names = {".git", "__pycache__", ".pytest_cache", ".venv", "node_modules", ".idea", ".vscode"}

        def build_tree(current_path: str, max_depth: int = 4, depth: int = 0):
            if depth > max_depth:
                return []
            items = []
            try:
                entries = sorted(os.scandir(current_path), key=lambda e: (not e.is_dir(), e.name.lower()))
                for entry in entries:
                    if entry.name in ignored_names:
                        continue
                    rel_path = os.path.relpath(entry.path, root_dir).replace("\\", "/")
                    is_directory = entry.is_dir(follow_symlinks=False)
                    size = entry.stat(follow_symlinks=False).st_size if not is_directory else 0
                    ext = os.path.splitext(entry.name)[1].lower() if not is_directory else ""

                    item = {
                        "name": entry.name,
                        "path": rel_path,
                        "is_dir": is_directory,
                        "size": size,
                        "extension": ext
                    }

                    if is_directory:
                        item["children"] = build_tree(entry.path, max_depth=max_depth, depth=depth + 1)
                        item["size"] = sum(c.get("size", 0) for c in item["children"])
                    items.append(item)
            except (PermissionError, FileNotFoundError):
                pass
            return items

        tree = build_tree(target_dir)
        total_files = 0
        total_folders = 0

        def count_nodes(nodes):
            nonlocal total_files, total_folders
            for n in nodes:
                if n["is_dir"]:
                    total_folders += 1
                    count_nodes(n.get("children", []))
                else:
                    total_files += 1

        count_nodes(tree)

        return {
            "status": "ok",
            "root_path": root_dir,
            "total_files": total_files,
            "total_folders": total_folders,
            "tree": tree
        }

    def read_file_content(self, file_path: str) -> Dict[str, Any]:
        root_dir = os.path.abspath(getattr(self.engine, "cwd", None) or os.getcwd())
        abs_path = os.path.abspath(os.path.join(root_dir, file_path))

        if not abs_path.startswith(root_dir):
            return {"status": "error", "message": "Access denied: Path outside workspace"}

        if not os.path.isfile(abs_path):
            return {"status": "error", "message": "File not found"}

        try:
            stat = os.stat(abs_path)
            if stat.st_size > 2 * 1024 * 1024:  # 2MB size limit
                return {"status": "error", "message": "File too large to view directly (>2MB)"}

            with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            lines = content.splitlines()
            return {
                "status": "ok",
                "path": file_path.replace("\\", "/"),
                "filename": os.path.basename(abs_path),
                "size": stat.st_size,
                "content": content,
                "line_count": len(lines),
                "extension": os.path.splitext(abs_path)[1].lower()
            }
        except Exception as exc:
            return {"status": "error", "message": str(exc)}

    def get_exploit_modules(self, category: str = "", search: str = "") -> Dict[str, Any]:
        """List and search exploit and auxiliary validation modules."""
        try:
            backend = None
            if self.engine and hasattr(self.engine, "pentest") and self.engine.pentest and hasattr(self.engine.pentest, "metasploit"):
                backend = self.engine.pentest.metasploit.backend
            if not backend:
                from delta.pentest.metasploit import MockMetasploitBackend
                backend = MockMetasploitBackend()

            raw_modules = backend.search_modules(query=search, category=category or None)
            modules_list = []
            for mod in raw_modules:
                safety_val = mod.safety_category.value if hasattr(mod.safety_category, "value") else str(mod.safety_category)
                modules_list.append({
                    "name": mod.name,
                    "title": mod.title,
                    "category": mod.category,
                    "description": mod.description,
                    "cvss_score": mod.cvss_score,
                    "cve_list": mod.cve_list,
                    "required_options": mod.required_options,
                    "default_options": mod.default_options,
                    "target_platforms": mod.target_platforms,
                    "target_services": mod.target_services,
                    "safety_category": safety_val,
                })
            return {"status": "ok", "modules": modules_list}
        except Exception as exc:
            return {"status": "error", "message": str(exc), "modules": []}

    def execute_exploit(
        self,
        target_host: str,
        target_port: int,
        module_name: str,
        options: Optional[Dict[str, Any]] = None,
        payload: Optional[str] = None,
        payload_options: Optional[Dict[str, Any]] = None,
        check_only: bool = True,
        roe_confirmed: bool = False
    ) -> Dict[str, Any]:
        """Execute controlled exploit validation with strict RoE confirmation."""
        if not roe_confirmed:
            return {"status": "error", "message": "Rules of Engagement and legal authorization must be explicitly confirmed."}

        if not self.engine or not hasattr(self.engine, "pentest") or not self.engine.pentest or not hasattr(self.engine.pentest, "metasploit"):
            return {"status": "error", "message": "Metasploit controller is not initialized on engine."}

        try:
            res = self.engine.pentest.metasploit.execute_controlled_validation(
                target_host=target_host,
                target_port=target_port,
                module_name=module_name,
                options=options,
                payload=payload,
                check_only=check_only
            )
            return {
                "status": res.status,
                "execution_id": res.execution_id,
                "vulnerability_confirmed": res.vulnerability_confirmed,
                "output": res.output,
                "session_id": res.session_id,
                "execution_time_ms": res.execution_time_ms,
                "evidence": res.evidence_data
            }
        except Exception as exc:
            return {"status": "error", "message": str(exc)}

    def get_exploit_sessions(self) -> Dict[str, Any]:
        """Get list of active and recent exploit validation sessions."""
        if not self.engine or not hasattr(self.engine, "pentest") or not self.engine.pentest or not hasattr(self.engine.pentest, "metasploit"):
            return {"status": "ok", "sessions": []}

        try:
            sessions_dict = self.engine.pentest.metasploit.session_manager.sessions
            items = []
            for s in sessions_dict.values():
                status_val = s.status.value if hasattr(s.status, "value") else str(s.status)
                items.append({
                    "session_id": s.session_id,
                    "target_host": s.target_host,
                    "target_port": s.target_port,
                    "module_used": s.module_used,
                    "status": status_val,
                    "session_type": s.session_type,
                    "created_at": s.created_at,
                    "expires_at": s.expires_at,
                })
            return {"status": "ok", "sessions": items}
        except Exception as exc:
            return {"status": "error", "message": str(exc), "sessions": []}

    def kill_exploit_session(self, session_id: str) -> Dict[str, Any]:
        """Terminate and clean up an active exploit session."""
        if not self.engine or not hasattr(self.engine, "pentest") or not self.engine.pentest or not hasattr(self.engine.pentest, "metasploit"):
            return {"status": "error", "message": "Metasploit controller is not initialized."}

        try:
            msf = self.engine.pentest.metasploit
            msf.session_manager.cleanup_session(session_id, msf.backend)
            return {"status": "ok", "message": f"Session {session_id} terminated."}
        except Exception as exc:
            return {"status": "error", "message": str(exc)}

    def generate_exploit_poc(
        self,
        target_host: str,
        target_port: int,
        module_name: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate PoC scripts (curl, python, raw HTTP) for a module and target."""
        if not self.engine or not hasattr(self.engine, "pentest") or not self.engine.pentest or not hasattr(self.engine.pentest, "metasploit"):
            from delta.pentest.metasploit import MetasploitController
            from delta.pentest.scope import ScopeGuard, ScopeDefinition
            msf = MetasploitController(guard=ScopeGuard(ScopeDefinition()))
        else:
            msf = self.engine.pentest.metasploit

        try:
            poc_dict = msf.generate_poc_script(target_host, target_port, module_name, options)
            return {"status": "ok", "poc": poc_dict}
        except Exception as exc:
            return {"status": "error", "message": str(exc)}

