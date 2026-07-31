# delta/core/policy.py
"""
Delta Security Policy & Capability Limits.

Satu file yang mengatur batas kemampuan Delta:
  • Etika keamanan (ethics) — prinsip penggunaan yang sah & bertanggung jawab
  • Batas perintah (capability limits) — perintah yang diblokir / berisiko
  • Otorisasi target — hanya target yang sah yang boleh dipindai
  • Rate limiting — batas operasi jaringan per menit
  • Persetujuan tindakan berisiko (confirmation)

Kebijakan disimpan di <config_dir>/policy.json dan dapat diedit secara manual.
Semua keputusan dikembalikan sebagai (action, reason, suggestion) dengan
action salah satu dari: "allow", "confirm", "block".
"""

import ipaddress
import json
import os
import time
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple


ETHICS_STATEMENT = [
    "Delta is intended for AUTHORIZED security testing only.",
    "Only scan systems you own or have explicit written permission to test.",
    "Respect privacy, data protection laws, and applicable regulations.",
    "Unauthorized scanning is illegal in most jurisdictions.",
    "Do not use Delta for disruption, extortion, or any malicious purpose.",
    "Report discovered vulnerabilities responsibly to the system owner.",
]


DEFAULT_POLICY: Dict[str, Any] = {
    "enabled": True,
    # Perintah yang sepenuhnya diblokir (bukan bawaan Delta).
    "blocked_commands": [],
    # Perintah berisiko yang selalu butuh konfirmasi ("confirm_risky").
    "risky_commands": {
        "brute": "Password brute force attack",
        "crack": "Password brute force attack (alias)",
        "hydra": "Password brute force attack (alias)",
    },
    "confirm_risky": True,
    # Target publik wajib ada di authorized_targets sebelum boleh dipindai.
    "require_authorization_public": True,
    "authorized_targets": [],
    "blocked_targets": [],
    # Batas operasi jaringan per menit (rate limit).
    "max_network_ops_per_minute": 6,
    # Batas lebar subnet yang dipindai (prefix >= 24 artinya /24.. /32).
    "min_prefix_length": 24,
    # Batas jumlah port per scan.
    "max_scan_ports": 2000,
    "log_violations": True,
}


# Perintah yang melakukan aktivitas jaringan — ikut rate limit.
NETWORK_COMMANDS = {
    "scan", "audit", "enumerate", "check", "ping", "traceroute",
    "whois", "dns", "ssl", "brute", "searchweb", "fetch", "geoip", "cve",
}

# Perintah yang menyerang/menyentuh target — butuh otorisasi target.
TARGET_SCAN_COMMANDS = {
    "scan", "audit", "enumerate", "check", "brute", "ping", "traceroute", "ssl",
}


def _is_private_target(target: str) -> bool:
    """True untuk localhost, link-local, dan range IP privat."""
    host = target.strip().lower()
    host = host.rstrip(".")
    if host in ("localhost", "127.0.0.1", "::1", "0.0.0.0"):
        return True
    if "/" in host:  # CIDR
        try:
            net = ipaddress.ip_network(host, strict=False)
        except ValueError:
            return False
        return net.is_private or net.is_loopback or net.is_link_local
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return False
    return ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast


def _extract_target(cmd: str, args: List[str]) -> Optional[str]:
    """Ambil target dari argumen sesuai bentuk perintah (nilai flag dilewati)."""
    non_flag: List[str] = []
    skip_next = False
    for a in args:
        if skip_next:
            skip_next = False
            continue
        if a.startswith("-"):
            skip_next = True
            continue
        non_flag.append(a.strip())
    if not non_flag:
        return None
    if cmd == "brute":  # brute <service> <target>
        return non_flag[-1]
    return non_flag[0]


class PolicyManager:
    """Menegakkan etika keamanan dan batas kemampuan Delta."""

    def __init__(self, config: Any, display: Any = None):
        self.config = config
        self.display = display
        self.policy: Dict[str, Any] = dict(DEFAULT_POLICY)
        self._violations: List[Dict[str, Any]] = []
        self._network_ops: List[float] = []
        self._load()

    # ------------------------------------------------------------ persisten

    @property
    def _policy_path(self) -> str:
        return os.path.join(self.config.config_dir or self.config.data_dir, "policy.json")

    def _load(self) -> None:
        try:
            if os.path.exists(self._policy_path):
                with open(self._policy_path, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                if isinstance(saved, dict):
                    for k, v in saved.items():
                        if k in self.policy:
                            self.policy[k] = v
        except (json.JSONDecodeError, IOError):
            pass

    def save(self) -> None:
        os.makedirs(os.path.dirname(self._policy_path), exist_ok=True)
        with open(self._policy_path, "w", encoding="utf-8") as f:
            json.dump(self.policy, f, indent=2, ensure_ascii=False)

    # -------------------------------------------------------------- helpers

    def _log_violation(self, cmd: str, args: List[str], reason: str) -> None:
        if not self.policy.get("log_violations", True):
            return
        self._violations.append({
            "time": datetime.now().isoformat(timespec="seconds"),
            "command": f"{cmd} {' '.join(args)}".strip(),
            "reason": reason,
        })

    def _warn(self, text: str) -> None:
        if self.display:
            self.display.warning(text)

    def _error(self, text: str) -> None:
        if self.display:
            self.display.error(text)

    # -------------------------------------------------------------- etika

    def ethics(self) -> str:
        return "\n".join(f"  • {line}" for line in ETHICS_STATEMENT)

    # ------------------------------------------------------------- batas

    def check(
        self,
        cmd: str,
        args: List[str],
        confirm: Optional[Callable[[str], bool]] = None,
    ) -> Tuple[str, str, str]:
        """
        Evaluasi perintah terhadap kebijakan.

        Returns:
            (action, reason, suggestion) dengan action "allow" | "confirm" | "block"
        """
        if not self.policy.get("enabled", True):
            return ("allow", "", "")

        # 1. Perintah diblokir total
        if cmd in self.policy.get("blocked_commands", []):
            reason = f"Perintah '{cmd}' diblokir oleh kebijakan Delta."
            self._log_violation(cmd, args, reason)
            return ("block", reason, "Edit blocked_commands di policy.json untuk mengizinkannya.")

        target = _extract_target(cmd, args)

        # 2. Target diblokir
        if target and target in self.policy.get("blocked_targets", []):
            reason = f"Target '{target}' masuk daftar blokir kebijakan."
            self._log_violation(cmd, args, reason)
            return ("block", reason, "Gunakan 'policy deblock <target>' atau hapus dari blocked_targets.")

        # 3. Otorisasi target publik
        if (
            target and cmd in TARGET_SCAN_COMMANDS
            and self.policy.get("require_authorization_public", True)
            and not _is_private_target(target)
            and target not in self.policy.get("authorized_targets", [])
        ):
            reason = (
                f"Target publik '{target}' belum diotorisasi. "
                "Delta hanya mengizinkan target lokal/privat secara default."
            )
            self._log_violation(cmd, args, reason)
            return (
                "block",
                reason,
                f"Jika Anda pemilik/penanggung jawab target, otorisasikan dengan: policy authorize {target}",
            )

        # 4. Batas lebar subnet
        if target and "/" in target:
            try:
                prefix = ipaddress.ip_network(target, strict=False).prefixlen
                min_prefix = int(self.policy.get("min_prefix_length", 24))
                if prefix < min_prefix:
                    reason = (
                        f"Subnet {target} (/{prefix}) melebihi batas Delta (maksimum /{min_prefix})."
                    )
                    self._log_violation(cmd, args, reason)
                    return (
                        "block",
                        reason,
                        f"Naikkan min_prefix_length di policy.json untuk mengizinkan cakupan lebih luas.",
                    )
            except ValueError:
                pass

        # 5. Batas jumlah port
        if cmd in ("scan", "audit", "check") and target:
            ports = self._count_ports(args)
            max_ports = int(self.policy.get("max_scan_ports", 2000))
            if ports > max_ports:
                reason = f"Permintaan {ports} port melebihi batas Delta ({max_ports} port per scan)."
                self._log_violation(cmd, args, reason)
                return ("block", reason, "Kurangi jumlah port atau naikkan max_scan_ports di policy.json.")

        # 6. Rate limit operasi jaringan
        if cmd in NETWORK_COMMANDS:
            if not self._allow_network_op():
                reason = "Batas kecepatan operasi jaringan tercapai (rate limit)."
                self._log_violation(cmd, args, reason)
                return (
                    "block",
                    reason,
                    f"Tunggu sebentar (maks {self.policy.get('max_network_ops_per_minute')} operasi/menit).",
                )

        # 7. Perintah berisiko → konfirmasi
        if cmd in self.policy.get("risky_commands", {}) and self.policy.get("confirm_risky", True):
            what = self.policy["risky_commands"].get(cmd, cmd)
            prompt = f"{what} — lanjutkan? Hanya untuk sistem yang Anda miliki/berizin."
            ok = confirm(prompt) if confirm else True
            if not ok:
                return ("block", f"Tindakan '{cmd}' dibatalkan oleh pengguna.", "Gunakan 'policy' untuk melihat batas Delta.")
            return ("allow", "", "")

        return ("allow", "", "")

    @staticmethod
    def _count_ports(args: List[str]) -> int:
        """Hitung jumlah port dari argumen -p/--ports/--top-ports."""
        count = 0
        i = 0
        while i < len(args):
            a = args[i]
            if a in ("-p", "--ports", "--top-ports") and i + 1 < len(args):
                spec = args[i + 1]
                if a == "--top-ports":
                    try:
                        count = max(count, int(spec))
                    except ValueError:
                        pass
                else:
                    for part in spec.split(","):
                        part = part.strip()
                        if not part:
                            continue
                        if "-" in part:
                            try:
                                lo, hi = part.split("-", 1)
                                count += max(int(hi) - int(lo) + 1, 1)
                            except ValueError:
                                count += 1
                        else:
                            count += 1
                i += 1
            i += 1
        return count

    # -------------------------------------------------------- rate limit

    def _allow_network_op(self) -> bool:
        now = time.monotonic()
        window = 60.0
        limit = int(self.policy.get("max_network_ops_per_minute", 6))
        self._network_ops = [t for t in self._network_ops if now - t < window]
        if len(self._network_ops) >= limit:
            return False
        self._network_ops.append(now)
        return True

    # -------------------------------------------------------- otorisasi

    def authorize(self, host: str) -> str:
        if host in self.policy["authorized_targets"]:
            return f"'{host}' sudah diotorisasi."
        self.policy["authorized_targets"].append(host)
        self.save()
        return f"'{host}' diotorisasi. Semua perintah jaringan ke target ini diizinkan."

    def deauthorize(self, host: str) -> str:
        if host in self.policy["authorized_targets"]:
            self.policy["authorized_targets"].remove(host)
            self.save()
            return f"Otorisasi '{host}' dicabut."
        return f"'{host}' tidak ada dalam daftar otorisasi."

    def block_target(self, host: str) -> str:
        if host not in self.policy["blocked_targets"]:
            self.policy["blocked_targets"].append(host)
            self.save()
        return f"'{host}' diblokir."

    def deblock_target(self, host: str) -> str:
        if host in self.policy["blocked_targets"]:
            self.policy["blocked_targets"].remove(host)
            self.save()
            return f"Blokir '{host}' dicabut."
        return f"'{host}' tidak ada dalam daftar blokir."

    # ------------------------------------------------------------ status

    def status_lines(self) -> List[str]:
        p = self.policy
        lines = [
            f"  Kebijakan: {'AKTIF' if p.get('enabled') else 'NONAKTIF'}",
            f"  Etika: {len(ETHICS_STATEMENT)} prinsip · jalankan 'policy ethics'",
            f"  Target publik: {'WAJIB otorisasi' if p.get('require_authorization_public') else 'bebas'}",
            f"  Otorisasi: {', '.join(p.get('authorized_targets')) if p.get('authorized_targets') else '(kosong)'}",
            f"  Blokir target: {', '.join(p.get('blocked_targets')) if p.get('blocked_targets') else '(kosong)'}",
            f"  Perintah berisiko: {', '.join(p.get('risky_commands', {})) if p.get('risky_commands') else '(tidak ada)'}",
            f"  Rate limit: {p.get('max_network_ops_per_minute')} operasi jaringan/menit",
            f"  Batas subnet: /{p.get('min_prefix_length')} atau lebih sempit",
            f"  Batas port: {p.get('max_scan_ports')} port/scan",
        ]
        if p.get("blocked_commands"):
            lines.append(f"  Perintah diblokir: {', '.join(p['blocked_commands'])}")
        return lines

    def violations(self, limit: int = 10) -> List[Dict[str, Any]]:
        return self._violations[-limit:]
