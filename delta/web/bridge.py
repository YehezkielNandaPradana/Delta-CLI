"""Bridge between Delta CLI Engine and Web Interface."""
import io
import json
import os
import re
import sys
import threading
from datetime import datetime
from typing import Any, Dict, Optional, Set, List, Tuple
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
        # Initialize VoiceManager on EventBus
        try:
            from delta.ai.events import event_bus
            from delta.voice.manager import VoiceManager
            self.voice_manager = VoiceManager(config=self.config, event_bus=event_bus)
            self.voice_manager.start()
        except Exception:
            self.voice_manager = None

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

    def delete_history_item(self, history_id: int) -> Dict[str, Any]:
        if not self.engine or not hasattr(self.engine, "database"):
            return {"status": "error", "message": "Database not initialized"}
        try:
            res = self.engine.database.delete_history_item(history_id)
            return {"status": "ok", "deleted": res}
        except Exception as exc:
            return {"status": "error", "message": str(exc)}

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

        # 1. First attempt dynamic query to live 9Router gateway (http://localhost:20128/v1/models)
        try:
            import urllib.request
            req = urllib.request.Request("http://127.0.0.1:20128/v1/models", headers={"User-Agent": "Delta-Workstation/1.0"})
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                if resp.status == 200:
                    raw_data = json.loads(resp.read().decode("utf-8"))
                    router_data = raw_data.get("data", []) if isinstance(raw_data, dict) else []
                    for rm in router_data:
                        m_id = rm.get("id") if isinstance(rm, dict) else str(rm)
                        if m_id:
                            models_list.append({
                                "name": m_id,
                                "description": f"9Router Live Gateway Model ({m_id})",
                                "provider": "9router",
                                "is_current": (m_id == current_model)
                            })
        except Exception:
            pass

        # 2. Add or merge known presets
        seen_names = {m["name"].lower() for m in models_list}
        for name, info in MODEL_PRESETS.items():
            if name.lower() not in seen_names:
                p_name = info.get("provider", "openai")
                models_list.append({
                    "name": name,
                    "description": info.get("description", ""),
                    "provider": p_name,
                    "is_current": (name == current_model or info.get("model") == current_model)
                })
                seen_names.add(name.lower())

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

    def start_router(self) -> Dict[str, Any]:
        from delta.utils.router_manager import is_9router_running, start_9router, wait_for_9router
        if is_9router_running():
            return {
                "status": "ok",
                "running": True,
                "message": "9Router is already running on port 20128"
            }
        try:
            start_9router()
            ready = wait_for_9router(timeout=15.0)
            if ready:
                return {
                    "status": "ok",
                    "running": True,
                    "message": "9Router local gateway started successfully on port 20128"
                }
            return {
                "status": "error",
                "running": False,
                "message": "Failed to start 9Router within 15 seconds"
            }
        except Exception as exc:
            return {
                "status": "error",
                "running": False,
                "message": f"Error starting 9Router: {str(exc)}"
            }

    def get_tunnel_status(self) -> Dict[str, Any]:
        from delta.utils.tunnel_manager import get_tunnel_status, get_tunnel_logs
        st = get_tunnel_status()
        st["recent_logs"] = get_tunnel_logs(limit=25)
        return st

    def get_tunnel_logs(self, limit: int = 100) -> Dict[str, Any]:
        from delta.utils.tunnel_manager import get_tunnel_logs, get_tunnel_status
        return {
            "status": "ok",
            "tunnel": get_tunnel_status(),
            "logs": get_tunnel_logs(limit=limit)
        }

    def start_tunnel(self, port: int = 8080) -> Dict[str, Any]:
        from delta.utils.tunnel_manager import start_cloudflare_tunnel
        return start_cloudflare_tunnel(port=port)

    def stop_tunnel(self) -> Dict[str, Any]:
        from delta.utils.tunnel_manager import stop_cloudflare_tunnel
        stopped = stop_cloudflare_tunnel()
        return {"status": "ok", "stopped": stopped}

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

    def geotrace_analyze(self, target: str, operator: str = "delta-analyst", purpose: str = "OSINT Investigation", consent_mode: bool = False) -> Dict[str, Any]:
        """Run GeoTrace OSINT analysis via Engine."""
        from delta.modules.geotrace import GeoTraceEngine, SafetyGateException
        engine = getattr(self.engine, "geotrace", None) or GeoTraceEngine()
        try:
            res = engine.investigate(
                target=target,
                operator=operator,
                purpose=purpose,
                consent_mode=consent_mode
            )
            return {"status": "ok", "report": engine.reporter.to_json(res)}
        except SafetyGateException as sge:
            return {"status": "rejected", "message": str(sge)}
        except Exception as exc:
            return {"status": "error", "message": str(exc)}

    def geotrace_get_audit(self, limit: int = 50) -> Dict[str, Any]:
        """Fetch recent immutable audit logs from GeoTrace."""
        import sqlite3
        from delta.modules.geotrace import GeoTraceEngine
        engine = getattr(self.engine, "geotrace", None) or GeoTraceEngine()
        try:
            with sqlite3.connect(engine.audit_mgr.db_path) as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT query_id, operator, target, timestamp, purpose, consent_mode, status, reason, record_hash FROM geotrace_audit_log ORDER BY id DESC LIMIT ?",
                    (limit,)
                )
                rows = cur.fetchall()
                logs = []
                for r in rows:
                    logs.append({
                        "query_id": r[0],
                        "operator": r[1],
                        "target": r[2],
                        "timestamp": r[3],
                        "purpose": r[4],
                        "consent_mode": bool(r[5]),
                        "status": r[6],
                        "reason": r[7] or "",
                        "record_hash": r[8]
                    })
                return {"status": "ok", "logs": logs}
        except Exception as exc:
            return {"status": "error", "message": str(exc), "logs": []}

    def geotrace_verify_audit(self) -> Dict[str, Any]:
        """Verify cryptographic hash chain integrity of GeoTrace audit DB."""
        from delta.modules.geotrace import GeoTraceEngine
        engine = getattr(self.engine, "geotrace", None) or GeoTraceEngine()
        try:
            valid, issues = engine.audit_mgr.verify_log_integrity()
            return {"status": "ok", "valid": valid, "issues": issues}
        except Exception as exc:
            return {"status": "error", "message": str(exc), "valid": False, "issues": [str(exc)]}

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

    def inspect_web_target(self, target: str, port: int = 80, fast_mode: bool = False) -> Dict[str, Any]:
        """Run comprehensive web security inspection & audit."""
        from delta.modules.web import WebModule
        import urllib.parse
        import time

        clean_target = target.strip()
        if clean_target.startswith("http://") or clean_target.startswith("https://"):
            parsed = urllib.parse.urlparse(clean_target)
            host = parsed.netloc.split(":")[0]
            port = parsed.port or (443 if parsed.scheme == "https" else 80)
        else:
            host = clean_target.split("/")[0].split(":")[0]

        mod = WebModule()
        start_t = time.time()
        # If specific port provided and non-standard, analyze that url first
        if port not in (80, 443):
            res = mod._analyze_url(f"http://{host}:{port}")
            if not res.status_code:
                res = mod._analyze_url(f"https://{host}:{port}")
        else:
            res = mod.analyze(host, port)
        duration_ms = round((time.time() - start_t) * 1000, 1)

        # Calculate security score & grade
        total_sec_headers = len(res.security_headers)
        passed_sec_headers = sum(1 for v in res.security_headers.values() if v)
        sec_ratio = passed_sec_headers / max(total_sec_headers, 1)

        if sec_ratio >= 0.85:
            grade = "A+"
            grade_color = "emerald"
        elif sec_ratio >= 0.7:
            grade = "A"
            grade_color = "emerald"
        elif sec_ratio >= 0.5:
            grade = "B"
            grade_color = "indigo"
        elif sec_ratio >= 0.3:
            grade = "C"
            grade_color = "amber"
        elif sec_ratio >= 0.15:
            grade = "D"
            grade_color = "orange"
        else:
            grade = "F"
            grade_color = "rose"

        # Additional checks
        cookies = mod.check_cookies(host) if not fast_mode else []
        robots = mod.check_robots_txt(host) if not fast_mode else {"exists": False, "disallowed": [], "sitemaps": []}
        methods = mod.check_http_methods(host) if not fast_mode else []
        sensitive_files = mod.check_common_files(host) if not fast_mode else []

        return {
            "status": "ok",
            "host": host,
            "port": port,
            "url": res.url,
            "status_code": res.status_code,
            "title": res.title or mod.extract_title(host),
            "server": res.server,
            "latency_ms": duration_ms,
            "security_grade": grade,
            "security_grade_color": grade_color,
            "security_headers": res.security_headers,
            "passed_headers_count": passed_sec_headers,
            "total_headers_count": total_sec_headers,
            "technologies": res.technologies,
            "cookies": cookies,
            "robots_txt": robots,
            "http_methods": methods,
            "sensitive_files": sensitive_files,
            "raw_headers": res.headers
        }

    def search_web_intelligence(self, query: str, search_type: str = "search") -> Dict[str, Any]:
        """Search OSINT web intelligence or CVE via DuckDuckGo."""
        from delta.modules.websearch import WebSearchModule
        searcher = WebSearchModule()
        q = query.strip()

        try:
            if search_type == "cve":
                res = searcher.search_cve(q)
                items = [{"title": res.title, "url": res.url, "snippet": res.snippet, "source": "cve"}] if res else []
            elif search_type == "exploit":
                results = searcher.search_exploit(q)
                items = [{"title": r.title, "url": r.url, "snippet": r.snippet, "source": "exploit"} for r in results]
            elif search_type == "news":
                results = searcher.search_security_news(q)
                items = [{"title": r.title, "url": r.url, "snippet": r.snippet, "source": "news"} for r in results]
            else:
                results = searcher.search_duckduckgo(q, max_results=12)
                items = [{"title": r.title, "url": r.url, "snippet": r.snippet, "source": "web"} for r in results]

            return {"status": "ok", "query": q, "search_type": search_type, "results": items, "count": len(items)}
        except Exception as exc:
            return {"status": "error", "message": str(exc), "results": [], "count": 0}

    def fetch_web_page_content(self, url: str) -> Dict[str, Any]:
        """Fetch web page content, headers, and metadata."""
        from delta.modules.websearch import WebSearchModule
        searcher = WebSearchModule()
        info = searcher.fetch_page(url.strip())
        if info.error:
            return {"status": "error", "message": info.error, "url": url}
        return {
            "status": "ok",
            "url": info.url,
            "title": info.title,
            "status_code": info.status_code,
            "content_type": info.content_type,
            "headers": info.headers,
            "content": info.content,
            "content_length": len(info.content)
        }

    def run_network_ping(self, host: str, count: int = 4, timeout: float = 2.0) -> Dict[str, Any]:
        """Run ICMP ping latency check."""
        from delta.modules.network import NetworkModule
        net = NetworkModule()
        res = net.ping(host.strip(), count=count, timeout=timeout)
        return {
            "status": "ok",
            "host": res.host,
            "ip": res.ip,
            "alive": res.alive,
            "rtt_ms": res.rtt_ms,
            "error": res.error
        }

    def run_network_dns(self, domain: str) -> Dict[str, Any]:
        """Run comprehensive DNS record queries & reverse lookups."""
        from delta.modules.dns import DNSModule
        dns_mod = DNSModule()
        clean_d = domain.strip().replace("http://", "").replace("https://", "").split("/")[0].split(":")[0]
        res = dns_mod.get_all_dns(clean_d)
        
        # Try getting TXT records if available via socket/platform
        txt_records = []
        try:
            import subprocess
            import platform
            cmd = ["nslookup", "-type=TXT", clean_d] if platform.system().lower() == "windows" else ["dig", "+short", "TXT", clean_d]
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=4)
            if p.returncode == 0:
                for line in p.stdout.split("\n"):
                    line = line.strip()
                    if line and ("v=spf" in line.lower() or "dmarc" in line.lower() or "google-site" in line.lower() or "domainkey" in line.lower() or '"' in line):
                        clean_txt = line.replace('"', '').strip()
                        if clean_txt:
                            txt_records.append(clean_txt)
        except Exception:
            pass

        return {
            "status": "ok",
            "domain": res.domain,
            "ip": res.ip,
            "a_records": res.a_records or ([res.ip] if res.ip else []),
            "aaaa_records": res.aaaa_records,
            "mx_records": res.mx_records,
            "ns_records": res.ns_records,
            "cname_records": res.cname_records,
            "txt_records": txt_records,
            "reverse_dns": res.reverse_dns
        }

    def run_network_traceroute(self, host: str, max_hops: int = 15) -> Dict[str, Any]:
        """Run traceroute path analysis."""
        from delta.modules.network import NetworkModule
        import platform
        import subprocess
        import re

        clean_h = host.strip().replace("http://", "").replace("https://", "").split("/")[0].split(":")[0]
        hops_list = []

        # Use system tracert / traceroute for fast reliable hops
        try:
            is_win = platform.system().lower() == "windows"
            cmd = ["tracert", "-d", "-h", str(max_hops), "-w", "1000", clean_h] if is_win else ["traceroute", "-n", "-m", str(max_hops), "-w", "1", clean_h]
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
            
            for line in p.stdout.split("\n"):
                line = line.strip()
                if not line:
                    continue
                # Match hop line format
                match = re.search(r"^\s*(\d+)\s+.*?(\d+\.\d+\.\d+\.\d+)", line)
                if match:
                    hop_num = int(match.group(1))
                    ip = match.group(2)
                    
                    # Extract rtt
                    rtt = 0.0
                    rtt_matches = re.findall(r"(\d+(?:\.\d+)?)\s*ms", line)
                    if rtt_matches:
                        rtt = float(rtt_matches[0])
                    
                    hops_list.append({
                        "hop": hop_num,
                        "ip": ip,
                        "hostname": "",
                        "rtt_ms": rtt,
                        "reached": True
                    })
        except Exception:
            pass

        # Fallback to internal module if system traceroute returned empty
        if not hops_list:
            net = NetworkModule()
            raw_hops = net.traceroute(clean_h, max_hops=max_hops, timeout=1.5)
            hops_list = [{
                "hop": h.hop,
                "ip": h.ip,
                "hostname": h.hostname,
                "rtt_ms": round(h.rtt_ms, 1),
                "reached": h.reached
            } for h in raw_hops if h.ip]

        return {
            "status": "ok",
            "target": clean_h,
            "total_hops": len(hops_list),
            "hops": hops_list
        }

    def run_network_geoip(self, host: str) -> Dict[str, Any]:
        """Lookup GeoIP & ASN information."""
        from delta.modules.geoip import GeoIPModule
        import socket

        clean_h = host.strip().replace("http://", "").replace("https://", "").split("/")[0].split(":")[0]
        try:
            ip = socket.gethostbyname(clean_h)
        except Exception:
            ip = clean_h

        mod = GeoIPModule()
        res = mod.lookup(ip)
        return {
            "status": "ok" if res.success else "error",
            "host": clean_h,
            "ip": res.ip,
            "country": res.country,
            "country_code": res.country_code,
            "region": res.region,
            "city": res.city,
            "zip_code": res.zip_code,
            "lat": res.lat,
            "lon": res.lon,
            "timezone": res.timezone,
            "isp": res.isp,
            "org": res.org,
            "as_number": res.as_number,
            "error": res.error
        }

    def run_network_ssl(self, host: str, port: int = 443) -> Dict[str, Any]:
        """Lookup SSL/TLS certificate details."""
        from delta.modules.ssl import SSLModule
        clean_h = host.strip().replace("http://", "").replace("https://", "").split("/")[0].split(":")[0]
        mod = SSLModule()
        res = mod.check(clean_h, port=port)
        return {
            "status": "ok",
            "host": res.host,
            "port": res.port,
            "valid": res.valid,
            "expired": res.expired,
            "days_remaining": res.days_remaining,
            "self_signed": res.self_signed,
            "protocol": res.protocol,
            "algorithm": res.algorithm,
            "serial_number": res.serial_number,
            "not_before": res.not_before,
            "not_after": res.not_after,
            "subject": res.subject,
            "issuer": res.issuer,
            "errors": res.errors
        }

    def run_network_sweep(self, network: str) -> Dict[str, Any]:
        """Sweep subnet to discover alive hosts."""
        from delta.modules.network import NetworkModule
        net = NetworkModule()
        results = net.ping_sweep(network.strip(), timeout=1.0)
        items = [{
            "host": r.host,
            "ip": r.ip,
            "alive": r.alive,
            "rtt_ms": r.rtt_ms
        } for r in results if r.alive]
        return {
            "status": "ok",
            "network": network,
            "count": len(items),
            "hosts": items
        }

    def process_voice_transcript(self, text: str) -> Dict[str, Any]:
        """Process transcribed voice input through the VTuber STT manager and Delta conversational loop."""
        from delta.vtuber.voice.stt.manager import stt_manager
        if not text or not text.strip():
            return {"status": "error", "message": "Empty voice transcript"}

        try:
            if stt_manager.speech_manager and stt_manager.speech_manager.is_speaking:
                import asyncio
                try:
                    asyncio.create_task(stt_manager.speech_manager.stop())
                except Exception:
                    pass

            exec_res = self.execute_command(text.strip())
            from delta.voice.formatter import VoiceFormatter
            raw_resp = ""
            if isinstance(exec_res, dict):
                raw_resp = exec_res.get("response") or exec_res.get("message") or exec_res.get("output", "")
            elif isinstance(exec_res, str):
                raw_resp = exec_res

            speech_text = VoiceFormatter.format_for_speech(raw_resp, style="genz_cute") if raw_resp else ""

            # Output vocal response via voice manager
            if hasattr(self, "voice_manager") and self.voice_manager and speech_text:
                from delta.voice.model import VoicePriority
                self.voice_manager.speak(speech_text, priority=VoicePriority.NORMAL)

            return {"status": "ok", "transcript": text.strip(), "result": exec_res, "speech_text": speech_text}
        except Exception as exc:
            return {"status": "error", "message": str(exc)}

    def get_vtuber_personality_data(self) -> Dict[str, Any]:
        """Fetch current PersonaProfile, MoodState, and stored Long-Term Memories."""
        from delta.vtuber.personality import personality_manager
        from delta.vtuber.memory import memory_manager
        memories = memory_manager.store.retrieve(limit=25)
        return {
            "status": "ok",
            "persona": personality_manager.profile.model_dump(),
            "mood": personality_manager.mood.model_dump(),
            "memories": [m.model_dump() for m in memories],
            "short_term_count": len(memory_manager.short_term.messages),
        }

    def clear_vtuber_memories(self) -> Dict[str, Any]:
        """Clear all stored long-term memories."""
        from delta.vtuber.memory import memory_manager
        memory_manager.store.clear_all()
        memory_manager.short_term.clear()
        return {"status": "ok", "message": "All VTuber memories cleared successfully"}

    def get_vtuber_runtime_data(self) -> Dict[str, Any]:
        """Fetch unified PersonalVTuberRuntime metrics & status."""
        from delta.vtuber.runtime import personal_vtuber_runtime
        return {"status": "ok", "runtime": personal_vtuber_runtime.get_runtime_status()}

    def _get_active_vts_client(self):
        """Helper to retrieve active VTSClient instance from runtime or instantiate configured one."""
        from delta.vtuber.runtime import personal_vtuber_runtime
        from delta.vtuber.avatar.vts_renderer import VTSRenderer
        from delta.vtuber.avatar.vts.client import VTSClient

        avatar_ctrl = personal_vtuber_runtime.avatar
        if avatar_ctrl and hasattr(avatar_ctrl, "renderer") and isinstance(avatar_ctrl.renderer, VTSRenderer):
            return avatar_ctrl.renderer.client

        # If not active renderer, check engine or attach dynamically
        host = getattr(self.engine.config, "vts_host", "127.0.0.1") if self.engine and hasattr(self.engine, "config") else "127.0.0.1"
        port = getattr(self.engine.config, "vts_port", 8001) if self.engine and hasattr(self.engine, "config") else 8001
        auth_token = getattr(self.engine.config, "vts_auth_token", "") if self.engine and hasattr(self.engine, "config") else ""
        
        # Cache client on bridge for testing if renderer is not VTSRenderer
        if not hasattr(self, "_cached_vts_client") or self._cached_vts_client is None:
            self._cached_vts_client = VTSClient(
                host=host,
                port=port,
                auth_token=auth_token or None,
                enabled=True,
            )
        return self._cached_vts_client

    def get_vts_status(self) -> Dict[str, Any]:
        """Fetch VTube Studio integration status and state machine details."""
        client = self._get_active_vts_client()
        return {"status": "ok", "vts": client.get_status_summary()}

    def get_vts_visual_status(self) -> Dict[str, Any]:
        """Fetch VTube Studio visual capture status without leaking tokens."""
        from delta.vtuber.avatar.vts_visual.manager import vts_visual_manager
        mgr = getattr(self, "vts_visual_mgr", None) or vts_visual_manager
        status_obj = mgr.get_status()
        return {"status": "ok", "visual": status_obj.model_dump()}

    async def vts_test_parameter(self, parameter: str, value: float) -> Dict[str, Any]:
        """Inject a single whitelisted parameter into VTube Studio."""
        from delta.vtuber.avatar.vts.protocol import VTS_ALLOWED_PARAMETERS
        if parameter not in VTS_ALLOWED_PARAMETERS:
            return {
                "status": "error",
                "message": f"Parameter '{parameter}' is not whitelisted. Allowed: {sorted(list(VTS_ALLOWED_PARAMETERS))}",
            }

        client = self._get_active_vts_client()
        if not client.is_connected or not client.is_authenticated:
            # Try connecting if not connected
            client.enabled = True
            ok = await client.connect()
            if not ok:
                return {
                    "status": "error",
                    "message": f"VTube Studio not connected or unauthenticated ({client.state.value})",
                    "vts": client.get_status_summary(),
                }

        res = await client.inject_raw_parameters(
            [{"parameter": parameter, "value": float(value)}],
            request_id="DeltaDirectTest",
        )
        if res.get("success"):
            return {
                "status": "ok",
                "message": f"Injected {parameter} = {value}",
                "parameter": parameter,
                "value": value,
                "vts": client.get_status_summary(),
            }
        else:
            return {
                "status": "error",
                "message": res.get("errorMessage") or f"Failed to inject parameter {parameter} ({res.get('reason')})",
                "reason": res.get("reason"),
                "errorID": res.get("errorID"),
                "vts": client.get_status_summary(),
            }

    async def vts_test_expression(self, expression_name: str, intensity: float = 0.8) -> Dict[str, Any]:
        """Test an expression on VTS using Live2DExpressionMapper."""
        import logging
        logger = logging.getLogger(__name__)
        logger.info("VTS_EXPRESSION_TEST_START\nexpression=%s\nintensity=%s", expression_name, intensity)

        from delta.vtuber.emotion.schemas import VTuberExpression
        from delta.vtuber.avatar.live2d_mapper import Live2DExpressionMapper
        from delta.vtuber.avatar.vts.protocol import VTS_ALLOWED_PARAMETERS

        expr_clean = expression_name.lower().strip()
        try:
            matched_expr = VTuberExpression(expr_clean)
        except ValueError:
            valid_exprs = [e.value for e in VTuberExpression]
            logger.info("VTS_EXPRESSION_TEST_RESULT\nstatus=FAIL\nreason=EXPRESSION_NOT_AVAILABLE")
            return {
                "status": "error",
                "message": f"Expression '{expression_name}' unavailable. Valid expressions: {valid_exprs}",
                "reason": "EXPRESSION_NOT_AVAILABLE",
            }

        client = self._get_active_vts_client()
        if not client.is_connected or not client.is_authenticated:
            client.enabled = True
            ok = await client.connect()
            if not ok:
                logger.info("VTS_EXPRESSION_TEST_RESULT\nstatus=FAIL\nreason=VTS_NOT_AUTHENTICATED")
                return {
                    "status": "error",
                    "message": f"VTube Studio not connected or unauthenticated ({client.state.value})",
                    "reason": "VTS_NOT_AUTHENTICATED",
                    "vts": client.get_status_summary(),
                }

        params_dict = Live2DExpressionMapper.get_expression_parameters(matched_expr, intensity=intensity)
        # Filter parameters to only whitelisted ones
        param_list = [
            {"parameter": k, "value": v}
            for k, v in params_dict.items()
            if k in VTS_ALLOWED_PARAMETERS
        ]

        logger.info("VTS_EXPRESSION_REQUEST_SENT")
        res = await client.inject_raw_parameters(param_list, request_id="DeltaExpressionTest")
        logger.info("VTS_EXPRESSION_RESPONSE")
        if res.get("success"):
            logger.info("VTS_EXPRESSION_TEST_RESULT\nstatus=PASS")
            return {
                "status": "ok",
                "message": f"Expression '{matched_expr.value}' applied",
                "expression": matched_expr.value,
                "parameters_applied": params_dict,
                "vts": client.get_status_summary(),
            }
        else:
            logger.info("VTS_EXPRESSION_TEST_RESULT\nstatus=FAIL\nreason=%s", res.get("reason", "UNKNOWN"))
            return {
                "status": "error",
                "message": res.get("errorMessage") or f"Failed to inject expression '{matched_expr.value}'",
                "reason": res.get("reason"),
                "errorID": res.get("errorID"),
                "vts": client.get_status_summary(),
            }

    async def vts_test_lipsync(self) -> Dict[str, Any]:
        """Run predefined amplitude curve lip-sync test (no random / sin-based fake values)."""
        import asyncio

        client = self._get_active_vts_client()
        if not client.is_connected or not client.is_authenticated:
            client.enabled = True
            ok = await client.connect()
            if not ok:
                return {"status": "error", "message": f"VTS not connected ({client.state.value})", "steps": []}

        # Predefined amplitude curve (phoneme-like envelope)
        curve = [0.0, 0.3, 0.7, 1.0, 0.6, 0.2, 0.8, 0.4, 0.9, 0.0]
        steps = []
        for i, amp in enumerate(curve):
            res = await client.inject_raw_parameters(
                [{"parameter": "ParamMouthOpenY", "value": float(amp)}],
                request_id="DeltaLipSyncTest",
            )
            steps.append({
                "step": i + 1,
                "amplitude": amp,
                "status": "PASS" if res.get("success") else "FAIL",
                "reason": res.get("reason"),
            })
            await asyncio.sleep(0.12)

        passed = all(s["status"] == "PASS" for s in steps)
        return {"status": "ok" if passed else "partial_fail", "passed": passed, "steps": steps, "vts": client.get_status_summary()}

    async def vts_test_physics(self) -> Dict[str, Any]:
        """Run head sweep to exercise hair/body physics springs in VTS."""
        import asyncio

        client = self._get_active_vts_client()
        if not client.is_connected or not client.is_authenticated:
            client.enabled = True
            ok = await client.connect()
            if not ok:
                return {"status": "error", "message": f"VTS not connected ({client.state.value})", "steps": []}

        # Head sweep: left -> right -> center (drives hair spring inertia in VTS)
        sweep = [-20.0, -14.0, -6.0, 0.0, 6.0, 14.0, 20.0, 14.0, 6.0, 0.0, -6.0, -14.0, -20.0, 0.0]
        steps = []
        for i, angle in enumerate(sweep):
            payload = [
                {"parameter": "ParamAngleX", "value": float(angle)},
                {"parameter": "ParamAngleZ", "value": round(angle * 0.3, 2)},
            ]
            res = await client.inject_raw_parameters(payload, request_id="DeltaPhysicsTest")
            steps.append({
                "step": i + 1,
                "ParamAngleX": angle,
                "status": "PASS" if res.get("success") else "FAIL",
                "reason": res.get("reason"),
            })
            await asyncio.sleep(0.1)

        passed = all(s["status"] == "PASS" for s in steps)
        return {"status": "ok" if passed else "partial_fail", "passed": passed, "steps": steps, "vts": client.get_status_summary()}

    async def vts_reset_parameters(self) -> Dict[str, Any]:
        """Reset test parameters back to neutral default rest posture."""
        import logging
        logger = logging.getLogger(__name__)
        logger.info("VTS_RESET_START")

        client = self._get_active_vts_client()
        if not client.is_connected or not client.is_authenticated:
            client.enabled = True
            ok = await client.connect()
            if not ok:
                logger.info("VTS_RESET_RESULT\nstatus=FAIL\nreason=VTS_NOT_AUTHENTICATED")
                return {
                    "status": "error",
                    "message": f"VTube Studio not connected ({client.state.value})",
                    "vts": client.get_status_summary(),
                }

        reset_payload = [
            {"parameter": "ParamAngleX", "value": 0.0},
            {"parameter": "ParamAngleY", "value": 0.0},
            {"parameter": "ParamAngleZ", "value": 0.0},
            {"parameter": "ParamBodyAngleX", "value": 0.0},
            {"parameter": "ParamBodyAngleY", "value": 0.0},
            {"parameter": "ParamBodyAngleZ", "value": 0.0},
            {"parameter": "ParamMouthOpenY", "value": 0.0},
            {"parameter": "ParamMouthForm", "value": 0.0},
            {"parameter": "ParamEyeLOpen", "value": 1.0},
            {"parameter": "ParamEyeROpen", "value": 1.0},
            {"parameter": "ParamEyeBallX", "value": 0.0},
            {"parameter": "ParamEyeBallY", "value": 0.0},
            {"parameter": "ParamBreath", "value": 0.5},
        ]

        res = await client.inject_raw_parameters(reset_payload, request_id="DeltaResetInject")
        if res.get("success"):
            logger.info("VTS_RESET_RESULT\nstatus=PASS")
            return {
                "status": "ok",
                "message": "VTube Studio parameters reset to neutral",
                "vts": client.get_status_summary(),
            }
        logger.info("VTS_RESET_RESULT\nstatus=FAIL\nreason=%s", res.get("reason"))
        return {
            "status": "error",
            "message": res.get("errorMessage") or "Failed to reset parameters",
            "reason": res.get("reason"),
            "errorID": res.get("errorID"),
            "vts": client.get_status_summary(),
        }

    async def vts_run_auto_test(self) -> Dict[str, Any]:
        """Run sequential 10-step VTS automated test suite with capability awareness."""
        import asyncio
        import logging
        logger = logging.getLogger(__name__)

        logger.info("VTS_TEST_START")
        client = self._get_active_vts_client()
        if not client.is_connected or not client.is_authenticated:
            client.enabled = True
            ok = await client.connect()
            if not ok:
                return {
                    "status": "error",
                    "message": f"Cannot run auto test: VTube Studio not connected ({client.state.value})",
                    "steps": [],
                }

        steps_results = []

        # 1. getCurrentModel
        try:
            m_data = await client.fetch_current_model()
            has_model = m_data.get("modelLoaded", False)
            steps_results.append({
                "step": 1,
                "name": "getCurrentModel",
                "status": "PASS" if has_model else "FAIL",
                "reason": "OK" if has_model else "NO_MODEL_LOADED",
                "request": "CurrentModelRequest",
                "response": m_data,
                "details": f"Model: {m_data.get('modelName', 'None')}" if has_model else "No model loaded",
            })
        except Exception as exc:
            steps_results.append({
                "step": 1,
                "name": "getCurrentModel",
                "status": "FAIL",
                "reason": "EXCEPTION",
                "error": str(exc),
                "details": str(exc),
            })

        # Helper step runner
        async def _exec_param_step(step_no: int, name: str, param: str, val: float):
            try:
                # Validate capability if model capabilities are populated
                if client.supported_parameters and not client.is_parameter_supported(param):
                    steps_results.append({
                        "step": step_no,
                        "name": name,
                        "status": "FAIL",
                        "reason": "PARAMETER_NOT_SUPPORTED",
                        "request": f"{param} = {val}",
                        "details": f"Parameter {param} not supported by active model",
                    })
                    return

                res = await client.inject_raw_parameters(
                    [{"parameter": param, "value": val}],
                    request_id=f"DeltaAutoTest_{step_no}",
                )
                status_str = "PASS" if res.get("success") else "FAIL"
                step_dict = {
                    "step": step_no,
                    "name": name,
                    "status": status_str,
                    "reason": res.get("reason", "OK" if res.get("success") else "FAILED"),
                    "request": f"{param} = {val}",
                    "details": f"{param} = {val}",
                }
                if not res.get("success"):
                    if res.get("errorID") is not None:
                        step_dict["errorID"] = res.get("errorID")
                    if res.get("errorMessage"):
                        step_dict["errorMessage"] = res.get("errorMessage")
                steps_results.append(step_dict)
            except Exception as e:
                steps_results.append({
                    "step": step_no,
                    "name": name,
                    "status": "FAIL",
                    "reason": "EXCEPTION",
                    "error": str(e),
                    "details": str(e),
                })
            await asyncio.sleep(0.15)

        # 2. ParamAngleX +20
        await _exec_param_step(2, "ParamAngleX +20", "ParamAngleX", 20.0)
        # 3. ParamAngleX -20
        await _exec_param_step(3, "ParamAngleX -20", "ParamAngleX", -20.0)
        # 4. ParamAngleY +15
        await _exec_param_step(4, "ParamAngleY +15", "ParamAngleY", 15.0)
        # 5. ParamAngleY -15
        await _exec_param_step(5, "ParamAngleY -15", "ParamAngleY", -15.0)
        # 6. ParamMouthOpenY 1
        await _exec_param_step(6, "ParamMouthOpenY 1", "ParamMouthOpenY", 1.0)
        # 7. ParamMouthOpenY 0
        await _exec_param_step(7, "ParamMouthOpenY 0", "ParamMouthOpenY", 0.0)

        # 8. expression smile
        try:
            res_smile = await self.vts_test_expression("smile")
            steps_results.append({
                "step": 8,
                "name": "expression smile",
                "status": "PASS" if res_smile.get("status") == "ok" else "FAIL",
                "reason": res_smile.get("reason", "OK" if res_smile.get("status") == "ok" else "EXPRESSION_FAILED"),
                "details": res_smile.get("message", ""),
            })
        except Exception as e:
            steps_results.append({
                "step": 8,
                "name": "expression smile",
                "status": "FAIL",
                "reason": "EXCEPTION",
                "error": str(e),
            })
        await asyncio.sleep(0.15)

        # 9. expression neutral
        try:
            res_neutral = await self.vts_test_expression("neutral")
            steps_results.append({
                "step": 9,
                "name": "expression neutral",
                "status": "PASS" if res_neutral.get("status") == "ok" else "FAIL",
                "reason": res_neutral.get("reason", "OK" if res_neutral.get("status") == "ok" else "EXPRESSION_FAILED"),
                "details": res_neutral.get("message", ""),
            })
        except Exception as e:
            steps_results.append({
                "step": 9,
                "name": "expression neutral",
                "status": "FAIL",
                "reason": "EXCEPTION",
                "error": str(e),
            })
        await asyncio.sleep(0.15)

        # 10. reset
        try:
            res_reset = await self.vts_reset_parameters()
            steps_results.append({
                "step": 10,
                "name": "reset",
                "status": "PASS" if res_reset.get("status") == "ok" else "FAIL",
                "reason": res_reset.get("reason", "OK" if res_reset.get("status") == "ok" else "RESET_FAILED"),
                "details": res_reset.get("message", ""),
            })
        except Exception as e:
            steps_results.append({
                "step": 10,
                "name": "reset",
                "status": "FAIL",
                "reason": "EXCEPTION",
                "error": str(e),
            })

        all_pass = all(s.get("status") == "PASS" for s in steps_results)
        return {
            "status": "ok" if all_pass else "partial_fail",
            "passed": all_pass,
            "total_steps": len(steps_results),
            "passed_steps": sum(1 for s in steps_results if s.get("status") == "PASS"),
            "steps": steps_results,
            "vts": client.get_status_summary(),
        }

    def update_vtuber_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Update VTuber settings across configuration & personality manager."""
        if not settings:
            return {"status": "error", "message": "No settings provided"}

        from delta.vtuber.personality import personality_manager
        if "name" in settings:
            personality_manager.profile.name = str(settings["name"])
        if "formality" in settings:
            personality_manager.profile.formality = float(settings["formality"])
        if "humor" in settings:
            personality_manager.profile.humor = float(settings["humor"])
        if "enthusiasm" in settings:
            personality_manager.profile.enthusiasm = float(settings["enthusiasm"])
        if "technicality" in settings:
            personality_manager.profile.technicality = float(settings["technicality"])

        if self.engine and hasattr(self.engine, "config") and self.engine.config:
            if "avatar_renderer" in settings:
                self.engine.config.avatar_renderer = str(settings["avatar_renderer"])
            if "tts_voice" in settings:
                self.engine.config.tts_voice = str(settings["tts_voice"])
            if "tts_speed" in settings:
                self.engine.config.tts_speed = float(settings["tts_speed"])
            if "stt_language" in settings:
                self.engine.config.stt_language = str(settings["stt_language"])
            if "vad_threshold" in settings:
                self.engine.config.vad_threshold = float(settings["vad_threshold"])

        return {"status": "ok", "message": "VTuber settings updated successfully"}

    @property
    def config(self) -> Any:
        if self.engine and hasattr(self.engine, "config"):
            return self.engine.config
        from delta.core.config import DeltaConfig
        return DeltaConfig()

    def get_voice_status(self) -> Dict[str, Any]:
        """Fetch current voice output subsystem configuration & status."""
        cfg = self.config
        return {
            "enabled": getattr(cfg, "tts_enabled", True),
            "provider": getattr(cfg, "tts_provider", "auto"),
            "profile": getattr(cfg, "tts_profile", "female"),
            "language": getattr(cfg, "tts_language", "id-ID"),
            "speed": getattr(cfg, "tts_speed", 1.0),
            "volume": getattr(cfg, "tts_volume", 1.0),
        }

    def update_voice_config(self, enabled: Optional[bool] = None, profile: Optional[str] = None, provider: Optional[str] = None, language: Optional[str] = None) -> None:
        """Update voice output configuration and persist."""
        cfg = self.config
        if enabled is not None:
            cfg.tts_enabled = enabled
        if profile is not None:
            cfg.tts_profile = profile
        if provider is not None:
            cfg.tts_provider = provider
        if language is not None:
            cfg.tts_language = language
        if hasattr(cfg, "save"):
            cfg.save()

    async def get_desktop_context(self) -> Dict[str, Any]:
        """Fetch on-demand snapshot of desktop context and active window metadata."""
        from delta.vtuber.desktop import desktop_manager
        ctx = await desktop_manager.capture_context(current_cwd=getattr(self.engine, "cwd", None))
        return {"status": "ok", "context": ctx.model_dump()}

    async def capture_screen(self) -> Dict[str, Any]:
        """Capture on-demand ephemeral screenshot."""
        from delta.vtuber.desktop import desktop_manager
        shot = await desktop_manager.capture_ephemeral_screenshot()
        if not shot:
            return {"status": "error", "message": "Screenshot capture unavailable or permission disabled"}
        return {"status": "ok", "screenshot": shot.model_dump()}

    async def read_clipboard(self) -> Dict[str, Any]:
        """Read sanitized clipboard content."""
        from delta.vtuber.desktop import desktop_manager
        clip = await desktop_manager.read_sanitized_clipboard()
        if not clip:
            return {"status": "error", "message": "Clipboard read unavailable or permission disabled"}
        return {"status": "ok", "clipboard": clip.model_dump()}



