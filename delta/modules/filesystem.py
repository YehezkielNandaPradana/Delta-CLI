# delta/modules/filesystem.py
"""
File System Module - File/folder operations & directory analysis.

Semua operasi dieksekusi langsung tanpa konfirmasi (auto-approved):
  • mkdir    - buat folder
  • write    - buat/timpa file
  • touch    - buat file kosong
  • edit     - ubah isi file (ganti teks)
  • append   - tambah teks ke akhir file
  • cat      - lihat isi file/dokumen
  • cd       - pindah folder
  • pwd      - tampilkan folder aktif
  • ls       - daftar isi folder
  • tree     - tampilkan struktur folder
  • dirinfo  - analisis folder/direktori
"""

import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


TEXT_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".c", ".cpp", ".h", ".cs",
    ".go", ".rs", ".rb", ".php", ".sh", ".bat", ".ps1", ".html", ".htm",
    ".css", ".scss", ".json", ".xml", ".yaml", ".yml", ".toml", ".ini",
    ".cfg", ".conf", ".md", ".txt", ".log", ".csv", ".sql", ".env", ".gitignore",
    ".dockerfile", ".vue", ".svelte", ".kt", ".swift", ".lua", ".pl", ".r",
    ".ipynb", ".rst", ".tex", ".ini",
}

# Kata pengisi yang diabaikan saat mengekstrak argumen file dari bahasa alami.
FILLER_WORDS = {
    "buat", "buatkan", "bikin", "membuat", "create", "make", "new",
    "file", "folder", "direktori", "directory", "dir", "dokumen", "document",
    "dengan", "berisi", "isi", "content", "yang", "untuk", "di", "pada",
    "ke", "dalam", "menjadi", "jadi", "ubah", "ganti", "edit", "tulis",
    "tambahkan", "tambah", "append", "baca", "lihat", "buka", "tampilkan",
    "daftar", "list", "show", "open", "read", "view", "write", "masuk",
    "pindah", "go", "cd", "pwd", "analisis", "analisa", "analyze", "analyse",
    "analysis", "info", "struktur", "tree", "the", "a", "an", "in", "of",
    "saya", "minta", "tolong", "please", "bantu", "help", "dengan", "sebagai",
}

_PATH_FLAGS = {"-p", "--parents", "-a", "--all", "-l", "--long", "-d", "--depth",
               "-f", "--find", "-r", "--replace", "-n", "--lines"}


def _decode_newlines(text: str) -> str:
    """Ubah escape \\n / \\t literal menjadi karakter aslinya (untuk penulisan kode)."""
    return text.replace("\\n", "\n").replace("\\t", "\t")


def _strip_content_prefix(text: str) -> str:
    """Buang kata pengantar sebelum isi file ('dengan isi', 'berisi', dst)."""
    text = re.sub(r"^(dengan\s+)?(isi|berisi|content|dengan|mengandung)\s*[:=-]?\s*", "", text, flags=re.IGNORECASE).strip()
    return text


class FileSystemModule:
    """
    Operasi file & folder. Semua method mengembalikan (ok, message).
    Tidak ada konfirmasi interaktif — perintah langsung dieksekusi.
    """

    def __init__(self, cwd: Optional[str] = None, display: Any = None):
        self.cwd = cwd or os.getcwd()
        self.display = display

    # ------------------------------------------------------------ helpers

    def _resolve(self, path: str = "") -> str:
        if not path or path == ".":
            return os.path.abspath(self.cwd)
        return os.path.abspath(os.path.join(self.cwd, path))

    @staticmethod
    def _human_size(num: float) -> str:
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if num < 1024 or unit == "TB":
                return f"{num:.1f} {unit}" if unit != "B" else f"{int(num)} B"
            num /= 1024
        return f"{num:.1f} TB"

    # ------------------------------------------------------------ folder

    def mkdir(self, path: str, parents: bool = False) -> Tuple[bool, str]:
        """Buat folder. parents=True membuat folder bertingkat sekaligus."""
        if not path:
            return False, "Path folder kosong. Usage: mkdir <folder> [-p]"
        target = self._resolve(path)
        try:
            if os.path.exists(target):
                if os.path.isdir(target):
                    return True, f"Folder sudah ada: {target}"
                return False, f"Tidak bisa membuat folder: '{target}' bukan folder"
            if parents:
                os.makedirs(target, exist_ok=True)
            else:
                os.mkdir(target)
            return True, f"Folder dibuat: {target}"
        except OSError as e:
            return False, f"Gagal membuat folder {target}: {e}"

    # ------------------------------------------------------------ file

    def write(self, path: str, content: str = "") -> Tuple[bool, str]:
        """Buat file baru atau timpa file yang sudah ada (tanpa konfirmasi)."""
        if not path:
            return False, "Path file kosong. Usage: write <file> <isi>"
        target = self._resolve(path)
        try:
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "w", encoding="utf-8") as f:
                f.write(_decode_newlines(content))
            size = os.path.getsize(target)
            return True, f"File ditulis: {target} ({self._human_size(size)})"
        except OSError as e:
            return False, f"Gagal menulis {target}: {e}"

    def touch(self, path: str) -> Tuple[bool, str]:
        """Buat file kosong jika belum ada."""
        if not path:
            return False, "Path file kosong. Usage: touch <file>"
        target = self._resolve(path)
        try:
            if os.path.exists(target):
                os.utime(target)
                return True, f"File sudah ada, timestamp diperbarui: {target}"
            with open(target, "a", encoding="utf-8"):
                pass
            return True, f"File dibuat: {target}"
        except OSError as e:
            return False, f"Gagal membuat {target}: {e}"

    def edit(self, path: str, old: str, new: str = "") -> Tuple[bool, str]:
        """Ganti teks pertama yang cocok di dalam file (tanpa konfirmasi)."""
        if not path or not old:
            return False, "Usage: edit <file> <teks-lama> <teks-baru>"
        target = self._resolve(path)
        if not os.path.isfile(target):
            return False, f"File tidak ditemukan: {target}"
        try:
            with open(target, "r", encoding="utf-8") as f:
                content = f.read()
            if old not in content:
                return False, f"Teks tidak ditemukan di {target}: '{old}'"
            content = content.replace(old, _decode_newlines(new), 1)
            with open(target, "w", encoding="utf-8") as f:
                f.write(content)
            return True, f"File diperbarui: {target}"
        except OSError as e:
            return False, f"Gagal mengedit {target}: {e}"

    def append(self, path: str, text: str) -> Tuple[bool, str]:
        """Tambahkan teks ke akhir file (membuat file jika belum ada)."""
        if not path:
            return False, "Path file kosong. Usage: append <file> <teks>"
        target = self._resolve(path)
        try:
            os.makedirs(os.path.dirname(target), exist_ok=True)
            prefix = ""
            if os.path.exists(target) and os.path.getsize(target) > 0:
                with open(target, "r", encoding="utf-8") as f:
                    existing = f.read()
                if existing and not existing.endswith("\n"):
                    prefix = "\n"
            with open(target, "a", encoding="utf-8") as f:
                f.write(prefix + _decode_newlines(text))
                if text and not text.endswith("\n"):
                    f.write("\n")
            return True, f"Ditambahkan ke: {target}"
        except OSError as e:
            return False, f"Gagal menambah ke {target}: {e}"

    def read(self, path: str, max_lines: Optional[int] = None) -> Tuple[bool, str]:
        """Baca isi file/dokumen. max_lines membatasi jumlah baris yang ditampilkan."""
        if not path:
            return False, "Path file kosong. Usage: cat <file> [jumlah-baris]"
        target = self._resolve(path)
        if not os.path.isfile(target):
            return False, f"File tidak ditemukan: {target}"
        try:
            with open(target, "rb") as f:
                raw = f.read()
            text = raw.decode("utf-8", errors="replace")
            if b"\x00" in raw:
                return True, f"(File biner — {self._human_size(len(raw))}, {os.path.basename(target)})"
            lines = text.splitlines()
            total = len(lines)
            if max_lines and total > max_lines:
                lines = lines[:max_lines]
            body = "\n".join(lines)
            if body and max_lines and total > max_lines:
                body += f"\n... ({total - max_lines} baris lagi)"
            if not body:
                body = "(file kosong)"
            return True, body
        except OSError as e:
            return False, f"Gagal membaca {target}: {e}"

    # ------------------------------------------------------------ navigasi

    def cd(self, path: str) -> Tuple[bool, str, str]:
        """Pindah folder. Mengembalikan (ok, pesan, cwd_baru)."""
        if not path or path == "~":
            target = os.path.expanduser("~")
        else:
            target = self._resolve(path)
        if not os.path.isdir(target):
            return False, f"Folder tidak ditemukan: {target}", self.cwd
        self.cwd = os.path.abspath(target)
        return True, f"Folder aktif: {self.cwd}", self.cwd

    def list_dir(self, path: str = "", all_hidden: bool = False, long: bool = False) -> Tuple[bool, List[Dict[str, Any]]]:
        """Daftar isi folder."""
        target = self._resolve(path)
        if not os.path.isdir(target):
            return False, []
        entries: List[Dict[str, Any]] = []
        try:
            names = sorted(os.listdir(target))
        except OSError:
            return False, []
        for name in names:
            if not all_hidden and name.startswith("."):
                continue
            full = os.path.join(target, name)
            try:
                is_dir = os.path.isdir(full)
                size = 0 if is_dir else os.path.getsize(full)
                mtime = datetime.fromtimestamp(os.path.getmtime(full))
            except OSError:
                is_dir, size, mtime = False, 0, datetime.now()
            entries.append({
                "name": name,
                "is_dir": is_dir,
                "size": size,
                "mtime": mtime,
            })
        return True, entries

    # ------------------------------------------------------------ analisis

    def tree(self, path: str = "", max_depth: int = 2) -> Tuple[bool, str]:
        """Tampilkan struktur folder berjenjang."""
        root = self._resolve(path)
        if not os.path.isdir(root):
            return False, f"Folder tidak ditemukan: {root}"
        lines: List[str] = [os.path.basename(root) or root]

        def walk(dirpath: str, prefix: str, depth: int) -> None:
            if depth > max_depth:
                lines.append(prefix + "  ... (dalam) ...")
                return
            try:
                names = sorted(os.listdir(dirpath))
            except OSError:
                return
            dirs = [n for n in names if os.path.isdir(os.path.join(dirpath, n))]
            files = [n for n in names if not os.path.isdir(os.path.join(dirpath, n))]
            items = [(n, True) for n in dirs] + [(n, False) for n in files]
            for i, (name, is_dir) in enumerate(items):
                last = i == len(items) - 1
                connector = "└── " if last else "├── "
                marker = "/" if is_dir else ""
                lines.append(prefix + connector + name + marker)
                if is_dir:
                    walk(os.path.join(dirpath, name), prefix + ("    " if last else "│   "), depth + 1)

        walk(root, "", 1)
        return True, "\n".join(lines)

    def dirinfo(self, path: str = "") -> Tuple[bool, Dict[str, Any]]:
        """Analisis folder/direktori: jumlah file, ukuran, tipe file, dst."""
        root = self._resolve(path)
        if not os.path.isdir(root):
            return False, {}
        stats = {
            "path": root,
            "files": 0,
            "dirs": 0,
            "hidden": 0,
            "total_size": 0,
            "extensions": {},  # ext -> {"count": n, "size": s}
            "largest": [],     # [(name, size)]
            "recent": [],      # [(name, mtime)]
        }
        for dirpath, dirnames, filenames in os.walk(root):
            for d in dirnames:
                stats["dirs"] += 1
                if d.startswith("."):
                    stats["hidden"] += 1
            for fn in filenames:
                full = os.path.join(dirpath, fn)
                if fn.startswith("."):
                    stats["hidden"] += 1
                try:
                    size = os.path.getsize(full)
                    mtime = os.path.getmtime(full)
                except OSError:
                    continue
                stats["files"] += 1
                stats["total_size"] += size
                ext = os.path.splitext(fn)[1].lower() or "(tanpa ekstensi)"
                ext_info = stats["extensions"].setdefault(ext, {"count": 0, "size": 0})
                ext_info["count"] += 1
                ext_info["size"] += size
                stats["largest"].append((os.path.relpath(full, root), size))
                stats["recent"].append((os.path.relpath(full, root), mtime))
        stats["largest"].sort(key=lambda x: -x[1])
        stats["recent"].sort(key=lambda x: -x[1])
        stats["largest"] = stats["largest"][:5]
        stats["recent"] = stats["recent"][:5]
        stats["extensions"] = dict(
            sorted(stats["extensions"].items(), key=lambda kv: -kv[1]["size"])
        )
        return True, stats
