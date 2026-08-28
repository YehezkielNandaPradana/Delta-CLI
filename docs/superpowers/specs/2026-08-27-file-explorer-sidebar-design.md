# Spec: Interactive File Explorer & In-App Code Viewer for Delta Web UI

**Date:** 2026-08-27  
**Status:** Approved  
**Author:** Delta Engineering Team  

---

## 1. Executive Summary
Dokumen ini mendefinisikan arsitektur backend REST API dan visual frontend UI untuk fitur **Interactive File Explorer** pada sidebar Delta Web IDE. Pengguna dapat menavigasi direktori kerja aktif dalam bentuk nested tree hierarchy, melakukan pencarian/filter instan, melihat ukuran file/folder, serta membuka dan membaca konten file langsung di dalam **In-App Code Viewer Modal** tanpa meninggalkan antarmuka web.

---

## 2. Backend REST Endpoints (`delta/web/server.py` & `delta/web/bridge.py`)

### 2.1 Directory Tree Endpoint: `GET /api/fs/tree`
- **Query Params**: `path` (opsional, default ke working directory `os.getcwd()` atau `engine.cwd`).
- **Response Format**:
  ```json
  {
    "status": "ok",
    "root_path": "D:\\Project\\Delta-CLI",
    "total_files": 45,
    "total_folders": 12,
    "tree": [
      {
        "name": "delta",
        "path": "delta",
        "is_dir": true,
        "size": 45020,
        "children": [
          {
            "name": "ai",
            "path": "delta/ai",
            "is_dir": true,
            "size": 18200,
            "children": [
              {
                "name": "events.py",
                "path": "delta/ai/events.py",
                "is_dir": false,
                "size": 6120,
                "extension": ".py"
              }
            ]
          }
        ]
      },
      {
        "name": "README.md",
        "path": "README.md",
        "is_dir": false,
        "size": 1540,
        "extension": ".md"
      }
    ]
  }
  ```
- **Security & Safety Rules**:
  - Batasi akses path hanya di dalam working directory (mencegah directory traversal keluar dari workspace root).
  - Filter otomatis direktori internal seperti `.git`, `__pycache__`, `.pytest_cache`, `.venv`, `node_modules` (atau tandai sebagai hidden).

### 2.2 File Content Reader Endpoint: `GET /api/fs/read`
- **Query Params**: `path` (relatif terhadap workspace root).
- **Response Format**:
  ```json
  {
    "status": "ok",
    "path": "delta/ai/events.py",
    "filename": "events.py",
    "size": 6120,
    "content": "... file content ...",
    "line_count": 210,
    "extension": ".py"
  }
  ```
- **Error Handling**:
  - Mengembalikan status 400/404 jika file tidak ditemukan atau jika mencoba membaca binary file yang tidak didukung teks (misal `.exe`, `.dll`, `.so`).

---

## 3. Frontend UI Component & Interaction (`delta/web/static/index.html`)

### 3.1 Files Explorer View
- Saat tombol **Files Explorer** di sidebar diklik (`switchNav('files')`):
  1. Melakukan fetch `GET /api/fs/tree`.
  2. Merender container Cyber Glass dengan:
     - **Header Bar**: Root directory path badge, count chip `📁 X folders · 📄 Y files`, Refresh button `sync`, dan Search Filter input.
     - **Nested Tree Container**:
       - Baris folder memiliki toggle expand/collapse (`folder` / `folder_open`), jumlah file, dan ukuran total.
       - Baris file menampilkan icon sesuai ekstensi (`.py` → `code`, `.js/.ts` → `javascript`, `.json` → `data_object`, `.md` → `description`, `.html/.css` → `html`, default → `draft`).
       - Hover effect dengan glass background highlight dan klik membuka file.
     - **Instant Filter Search**:
       - Ketikan pada search bar menyaring node tree secara instan berdasarkan nama file/folder.

### 3.2 In-App Code Viewer Modal
- Ketika item file diklik:
  1. Melakukan fetch `GET /api/fs/read?path=<filepath>`.
  2. Membuka modal viewer elegan:
     - **Modal Header**: Icon file, nama file, path lengkap, line count, file size, tombol `Copy Code`, tombol `Send to Chat (Ask AI)`, dan tombol `Close`.
     - **Code Content Box**: Dark theme font-mono container dengan formatted line numbers dan scrolling halus.

---

## 4. Verification & Testing
1. Unit tests pada `tests/test_web_server.py`:
   - Test `GET /api/fs/tree` mengembalikan list file/folder dari current working directory.
   - Test security: Memastikan path traversal di luar working directory ditolak.
   - Test `GET /api/fs/read` membaca file teks dengan sukses.
2. Frontend integration test pada `tests/test_web_frontend.py`:
   - Memastikan fungsi `renderFilesExplorer` dan `openFileViewer` terdaftar di template web.
