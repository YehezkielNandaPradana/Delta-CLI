# Refactor: filesystem ops
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

from functools import lru_cache

from typing import Any, Dict, List, Optional, Tuple

TEXT_EXTENSIONS = frozenset({

    ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".c", ".cpp", ".h", ".cs",

    ".go", ".rs", ".rb", ".php", ".sh", ".bat", ".ps1", ".html", ".htm",

    ".css", ".scss", ".json", ".xml", ".yaml", ".yml", ".toml", ".ini",

    ".cfg", ".conf", ".md", ".txt", ".log", ".csv", ".sql", ".env", ".gitignore",

    ".dockerfile", ".vue", ".svelte", ".kt", ".swift", ".lua", ".pl", ".r",

    ".ipynb", ".rst", ".tex", ".ini",

})

# Kata pengisi diabaikan saat mengekstrak argumen file dari bahasa alami.

_PATH_FLAGS = frozenset({"-p", "--parents", "-a", "--all", "-l", "--long", "-d", "--depth",

               "-f", "--find", "-r", "--replace", "-n", "--lines"})

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

        # Allow absolute paths on any drive (Windows C:\, D:\ or Unix /...)
        if os.path.isabs(path):

            return os.path.abspath(path)

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

        """Ganti teks yang cocok di dalam file (menggunakan fuzzy line matching jika presisi)."""

        return self.smart_edit(path, old, new)

    def smart_edit(self, path: str, old: str, new: str = "") -> Tuple[bool, str]:

        """Smart file editor supporting exact match, fuzzy block matching, and syntax checking."""

        if not path or not old:

            return False, "Usage: edit <file> <teks-lama> <teks-baru>"

        target = self._resolve(path)

        if not os.path.isfile(target):

            return False, f"File tidak ditemukan: {target}"

        try:

            with open(target, "r", encoding="utf-8", errors="replace") as f:

                content = f.read()

            new_text = _decode_newlines(new)

            # 1. Try exact replacement first

            if old in content:

                updated_content = content.replace(old, new_text, 1)

            else:

                # 2. Try fuzzy block replacement via difflib

                import difflib

                lines = content.splitlines(keepends=True)

                old_lines = old.splitlines(keepends=True)

                if not old_lines:

                    return False, f"Target edit text empty."

                # Find best matching slice of lines

                best_ratio = 0.0

                best_slice = None

                n_old = len(old_lines)

                for i in range(len(lines) - n_old + 1):

                    window = "".join(lines[i:i + n_old])

                    ratio = difflib.SequenceMatcher(None, window, old).ratio()

                    if ratio > best_ratio:

                        best_ratio = ratio

                        best_slice = (i, i + n_old)

                if best_ratio >= 0.85 and best_slice:

                    start, end = best_slice

                    lines[start:end] = [new_text + ("\n" if not new_text.endswith("\n") else "")]

                    updated_content = "".join(lines)

                else:

                    return False, f"Teks tidak ditemukan di {target} (fuzzy match score: {best_ratio:.2f} < 0.85)"

            # 3. Post-edit syntax check for Python files

            if target.endswith(".py"):

                import ast

                try:

                    ast.parse(updated_content, filename=target)

                except SyntaxError as syn_err:

                    return False, f"Edit ditolak karena menyebabkan SyntaxError pada baris {syn_err.lineno}: {syn_err.msg}"

            with open(target, "w", encoding="utf-8") as f:

                f.write(updated_content)

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

    # ------------------------------------------------------------ manipulasi berkas
    def remove(self, path: str, recursive: bool = False) -> Tuple[bool, str]:
        """Hapus file atau direktori."""
        import shutil
        if not path:
            return False, "Path kosong. Usage: rm <path> [-r]"
        target = self._resolve(path)
        if not os.path.exists(target):
            return False, f"Target tidak ditemukan: {target}"
        try:
            if os.path.isdir(target):
                if recursive:
                    shutil.rmtree(target)
                    return True, f"Direktori dihapus: {target}"
                os.rmdir(target)
                return True, f"Direktori kosong dihapus: {target}"
            os.remove(target)
            return True, f"File dihapus: {target}"
        except OSError as e:
            return False, f"Gagal menghapus {target}: {e}"

    def copy(self, src: str, dst: str, recursive: bool = False) -> Tuple[bool, str]:
        """Salin file atau direktori."""
        import shutil
        if not src or not dst:
            return False, "Usage: cp <src> <dst> [-r]"
        src_path = self._resolve(src)
        dst_path = self._resolve(dst)
        if not os.path.exists(src_path):
            return False, f"Sumber tidak ditemukan: {src_path}"
        try:
            if os.path.isdir(src_path):
                if recursive:
                    shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
                    return True, f"Direktori disalin dari {src_path} ke {dst_path}"
                return False, f"{src_path} adalah direktori. Gunakan recursive (-r) untuk menyalin direktori."
            os.makedirs(os.path.dirname(dst_path), exist_ok=True)
            shutil.copy2(src_path, dst_path)
            return True, f"File disalin dari {src_path} ke {dst_path}"
        except OSError as e:
            return False, f"Gagal menyalin: {e}"

    def move(self, src: str, dst: str) -> Tuple[bool, str]:
        """Pindahkan atau ganti nama file/direktori."""
        import shutil
        if not src or not dst:
            return False, "Usage: mv <src> <dst>"
        src_path = self._resolve(src)
        dst_path = self._resolve(dst)
        if not os.path.exists(src_path):
            return False, f"Sumber tidak ditemukan: {src_path}"
        try:
            os.makedirs(os.path.dirname(dst_path), exist_ok=True)
            shutil.move(src_path, dst_path)
            return True, f"Berhasil dipindahkan dari {src_path} ke {dst_path}"
        except OSError as e:
            return False, f"Gagal memindahkan: {e}"