# delta/core/policy.py

"""

Delta Security Policy & Capability Limits — RED TEAM EDITION.

Satu file yang mengatur batas kemampuan Delta:

  • Mode REDTEAM (default) — semua pembatas operasional dilepas:

      - tanpa konfirmasi perintah berisiko

      - tanpa kewajiban otorisasi target publik

      - tanpa rate limit jaringan

      - tanpa batas lebar subnet / jumlah port

      - semua perintah langsung diizinkan (kecepatan penuh)

  • Kill-switch manual (blocked_commands / blocked_targets) tetap dihormati

  • Mode NORMAL masih tersedia jika ingin kembali terkendali

Kebijakan disimpan di <config_dir>/policy.json dan dapat diedit secara manual.

CATATAN: jika policy.json lama masih ada, isinya MENIMPA default di file ini.

Hapus atau atur ulang policy.json agar mode REDTEAM benar-benar aktif.

"""

import ipaddress

import json

import os

import time

from datetime import datetime

from typing import Any, Callable, Dict, List, Optional, Tuple

ETHICS_STATEMENT = [

    "REDTEAM MODE: Delta beroperasi tanpa pembatas operasional.",

    "Dirancang untuk pengujian keamanan skala penuh (pentest / red team).",

    "Jalankan hanya terhadap target yang sah: milik sendiri atau kontrak resmi.",

    "Tanpa konfirmasi, tanpa rate limit, tanpa daftar otorisasi manual.",

    "Semua aktivitas tetap tercatat di log untuk audit jejak pengujian.",

]

DEFAULT_POLICY: Dict[str, Any] = {

    "enabled": True,

    # "redteam" = semua batasan dilepas · "normal" = batasan aktif

    "mode": "redteam",

    # Kill-switch manual: tetap ditegakkan di mode apapun.

    "blocked_commands": [],

    # Tidak ada perintah berisiko → tidak ada dialog konfirmasi.

    "risky_commands": {},

    "confirm_risky": False,

    # Target publik TIDAK wajib otorisasi.

    "require_authorization_public": False,

    "authorized_targets": [],

    "blocked_targets": [],

    # 0 = tanpa batas operasi jaringan per menit.

    "max_network_ops_per_minute": 0,

    # 0 = tanpa batas lebar subnet (bebas /0 sampai /32).

    "min_prefix_length": 0,

    # 0 = tanpa batas jumlah port per scan.

    "max_scan_ports": 0,

    "log_violations": True,

}

# Perintah yang melakukan aktivitas jaringan — ikut rate limit (mode normal).

NETWORK_COMMANDS = {

    "scan", "audit", "enumerate", "check", "ping", "traceroute",

    "whois", "dns", "ssl", "brute", "searchweb", "fetch", "geoip", "cve",

}

# Perintah yang menyerang/menyentuh target — butuh otorisasi (mode normal).

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

    """Menegakkan batas kemampuan Delta — default REDTEAM (bebas)."""

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

        REDTEAM mode: semua batasan otomatis dilewati.

        Kill-switch manual (blocked_commands / blocked_targets) tetap berlaku.

        Returns:

            (action, reason, suggestion) dengan action "allow" | "confirm" | "block"

        """

        if not self.policy.get("enabled", True):

            return ("allow", "", "")

        # 0. Kill-switch manual — dihormati di mode apapun.

        if cmd in self.policy.get("blocked_commands", []):

            reason = f"Perintah '{cmd}' diblokir manual (blocked_commands)."

            self._log_violation(cmd, args, reason)

            return ("block", reason, "Hapus dari blocked_commands untuk mengizinkannya.")

        target = _extract_target(cmd, args)

        if target and target in self.policy.get("blocked_targets", []):

            reason = f"Target '{target}' masuk daftar blokir manual."

            self._log_violation(cmd, args, reason)

            return ("block", reason, "Gunakan 'policy deblock <target>'.")

        # 1. REDTEAM MODE — langsung izinkan, tanpa pemeriksaan lain.

        if self.policy.get("mode") == "redteam":

            return ("allow", "", "")

        # ----------------------------------------------------------------

        # Mode NORMAL di bawah ini (aktifkan dengan "mode": "normal").

        # ----------------------------------------------------------------

        # 2. Target publik wajib otorisasi (mode normal)

        if (

            target and cmd in TARGET_SCAN_COMMANDS

            and self.policy.get("require_authorization_public", False)

            and not _is_private_target(target)

            and target not in self.policy.get("authorized_targets", [])

        ):

            reason = f"Target publik '{target}' belum diotorisasi."

            self._log_violation(cmd, args, reason)

            return (

                "block",

                reason,

                f"Otorisasikan dengan: policy authorize {target}",

            )

        # 3. Batas lebar subnet (mode normal)

        min_prefix = int(self.policy.get("min_prefix_length", 0))

        if target and "/" in target and min_prefix > 0:

            try:

                prefix = ipaddress.ip_network(target, strict=False).prefixlen

                if prefix < min_prefix:

                    reason = f"Subnet {target} (/{prefix}) melebihi batas (maksimum /{min_prefix})."

                    self._log_violation(cmd, args, reason)

                    return ("block", reason, "Naikkan min_prefix_length untuk cakupan lebih luas.")

            except ValueError:

                pass

        # 4. Batas jumlah port (mode normal)

        max_ports = int(self.policy.get("max_scan_ports", 0))

        if cmd in ("scan", "audit", "check") and target and max_ports > 0:

            ports = self._count_ports(args)

            if ports > max_ports:

                reason = f"Permintaan {ports} port melebihi batas ({max_ports} port/scan)."

                self._log_violation(cmd, args, reason)

                return ("block", reason, "Kurangi jumlah port atau naikkan max_scan_ports.")

        # 5. Rate limit operasi jaringan (mode normal)

        if cmd in NETWORK_COMMANDS:

            if not self._allow_network_op():

                reason = "Rate limit operasi jaringan tercapai."

                self._log_violation(cmd, args, reason)

                return (

                    "block",

                    reason,

                    "Tunggu sebentar (maks "

                    f"{self.policy.get('max_network_ops_per_minute')} operasi/menit).",

                )

        # 6. Perintah berisiko → konfirmasi (mode normal)

        if cmd in self.policy.get("risky_commands", {}) and self.policy.get("confirm_risky", False):

            what = self.policy["risky_commands"].get(cmd, cmd)

            prompt = f"{what} — lanjutkan?"

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

        limit = int(self.policy.get("max_network_ops_per_minute", 0))

        if limit <= 0:

            return True  # 0 = tanpa batas

        now = time.monotonic()

        window = 60.0

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

    # ------------------------------------------------------------ mode

    def set_mode(self, mode: str) -> str:

        """Ganti mode kebijakan: 'redteam' (bebas) atau 'normal' (terkendali)."""

        if mode not in ("redteam", "normal"):

            return f"Mode tidak dikenal: '{mode}' (gunakan 'redteam' atau 'normal')."

        self.policy["mode"] = mode

        self.save()

        return f"Mode kebijakan diubah ke '{mode}'."

    # ------------------------------------------------------------ status

    def status_lines(self) -> List[str]:

        p = self.policy

        if p.get("mode") == "redteam":

            return [

                f"  Mode: REDTEAM (bebas — semua batasan dilepas)",

                f"  Rate limit: tanpa batas",

                f"  Batas subnet: tanpa batas (/0–/32)",

                f"  Batas port: tanpa batas",

                f"  Konfirmasi perintah berisiko: NONAKTIF",

                f"  Otorisasi target publik: TIDAK diperlukan",

                f"  Kill-switch perintah: {', '.join(p.get('blocked_commands')) if p.get('blocked_commands') else '(tidak ada)'}",

                f"  Blokir target manual: {', '.join(p.get('blocked_targets')) if p.get('blocked_targets') else '(kosong)'}",

            ]

        return [

            f"  Kebijakan: {'AKTIF' if p.get('enabled') else 'NONAKTIF'}",

            f"  Mode: NORMAL (terkendali)",

            f"  Etika: {len(ETHICS_STATEMENT)} prinsip · jalankan 'policy ethics'",

            f"  Target publik: {'WAJIB otorisasi' if p.get('require_authorization_public') else 'bebas'}",

            f"  Otorisasi: {', '.join(p.get('authorized_targets')) if p.get('authorized_targets') else '(kosong)'}",

            f"  Blokir target: {', '.join(p.get('blocked_targets')) if p.get('blocked_targets') else '(kosong)'}",

            f"  Perintah berisiko: {', '.join(p.get('risky_commands', {})) if p.get('risky_commands') else '(tidak ada)'}",

            f"  Rate limit: {p.get('max_network_ops_per_minute')} operasi jaringan/menit",

            f"  Batas subnet: /{p.get('min_prefix_length')} atau lebih sempit",

            f"  Batas port: {p.get('max_scan_ports')} port/scan",

        ]

    def violations(self, limit: int = 10) -> List[Dict[str, Any]]:

        return self._violations[-limit:]