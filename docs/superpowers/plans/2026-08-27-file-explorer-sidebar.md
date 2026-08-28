# Interactive File Explorer & In-App Code Viewer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an interactive File Explorer in the Delta Web UI sidebar that fetches and renders the current working directory tree with collapsible folders, size metrics, instant search filter, and opens files in an In-App Code Viewer Modal.

**Architecture:** Implement backend REST endpoints (`GET /api/fs/tree` and `GET /api/fs/read`) in `delta/web/server.py` and `delta/web/bridge.py` with directory traversal protection. In the frontend (`delta/web/static/index.html` and mirror `delta/web/index.html`), create a dynamic tree renderer with expand/collapse, file extension icons, instant search, and a syntax-themed code viewer modal with copy & send-to-chat capabilities.

**Tech Stack:** Python 3.10+ (standard library `os`, `pathlib`, `json`, `http.server`), Vanilla JavaScript (ES6+), Tailwind CSS, Material Symbols.

## Global Constraints

- Prevent path traversal attacks; all file and folder operations must resolve strictly within the workspace root.
- Exclude internal noisy folders by default (`.git`, `__pycache__`, `.pytest_cache`, `.venv`, `node_modules`).
- Maintain dark/light mode compatibility across all new UI components.
- Zero extra external package dependencies (pure Python stdlib + pure browser JavaScript).

---

### Task 1: Backend FS Endpoints (`/api/fs/tree` & `/api/fs/read`)

**Files:**
- Modify: `delta/web/bridge.py:40-95`
- Modify: `delta/web/server.py:120-150`
- Test: `tests/test_web_server.py`

**Interfaces:**
- Consumes: `engine.cwd` or `os.getcwd()`
- Produces: `EngineBridge.get_directory_tree(sub_path: str = "") -> Dict[str, Any]`, `EngineBridge.read_file_content(file_path: str) -> Dict[str, Any]`

- [ ] **Step 1: Write tests for `/api/fs/tree` and `/api/fs/read` endpoints**

Add to `tests/test_web_server.py`:
```python
def test_fs_tree_endpoint():
    server = DeltaWebServer(engine=None, host="127.0.0.1", port=8994)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.5)

    try:
        req = urllib.request.Request("http://127.0.0.1:8994/api/fs/tree")
        with urllib.request.urlopen(req, timeout=2) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["status"] == "ok"
            assert "tree" in data
            assert isinstance(data["tree"], list)
            assert data["total_files"] >= 0
    finally:
        server.shutdown()

def test_fs_read_endpoint():
    server = DeltaWebServer(engine=None, host="127.0.0.1", port=8993)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.5)

    try:
        req = urllib.request.Request("http://127.0.0.1:8993/api/fs/read?path=setup.py")
        with urllib.request.urlopen(req, timeout=2) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["status"] == "ok"
            assert data["filename"] == "setup.py"
            assert "content" in data
            assert data["line_count"] > 0
    finally:
        server.shutdown()

def test_fs_read_security_traversal_prevention():
    server = DeltaWebServer(engine=None, host="127.0.0.1", port=8992)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.5)

    try:
        req = urllib.request.Request("http://127.0.0.1:8992/api/fs/read?path=../../windows/system32/cmd.exe")
        try:
            with urllib.request.urlopen(req, timeout=2) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                assert data["status"] == "error"
        except urllib.error.HTTPError as err:
            assert err.code in (400, 403, 404)
    finally:
        server.shutdown()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_web_server.py -k test_fs_ -v`
Expected: FAIL

- [ ] **Step 3: Implement tree builder and safe file reader in `delta/web/bridge.py`**

In `delta/web/bridge.py`:
```python
    def get_directory_tree(self, sub_path: str = "") -> Dict[str, Any]:
        root_dir = os.path.abspath(getattr(self.engine, "cwd", None) or os.getcwd())
        target_dir = os.path.abspath(os.path.join(root_dir, sub_path))

        # Security: Prevent directory traversal outside root
        if not target_dir.startswith(root_dir):
            return {"status": "error", "message": "Access denied: Path outside workspace"}

        ignored_names = {".git", "__pycache__", ".pytest_cache", ".venv", "node_modules", ".idea", ".vscode"}

        def build_tree(current_path: str, max_depth: int = 4, depth: int = 0) -> List[Dict[str, Any]]:
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

        # Security check
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
```

- [ ] **Step 4: Route `/api/fs/tree` and `/api/fs/read` in `delta/web/server.py`**

In `delta/web/server.py` `do_GET`:
```python
            if clean_path == "/api/fs/tree":
                from urllib.parse import parse_qs
                query = parse_qs(parsed_url.query)
                sub_path = query.get("path", [""])[0]
                res = self.bridge.get_directory_tree(sub_path) if self.bridge else {"status": "error", "message": "Bridge offline"}
                body = json.dumps(res).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self._safe_write(body)
                return

            if clean_path == "/api/fs/read":
                from urllib.parse import parse_qs
                query = parse_qs(parsed_url.query)
                file_path = query.get("path", [""])[0]
                res = self.bridge.read_file_content(file_path) if self.bridge else {"status": "error", "message": "Bridge offline"}
                status_code = 200 if res.get("status") == "ok" else (403 if "Access denied" in res.get("message", "") else 404)
                body = json.dumps(res).encode("utf-8")
                self.send_response(status_code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self._safe_write(body)
                return
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/test_web_server.py -k test_fs_ -v`
Expected: PASS

---

### Task 2: Frontend File Explorer Interactive Tree View

**Files:**
- Modify: `delta/web/static/index.html:890-930`
- Modify: `delta/web/index.html:890-930`
- Test: `tests/test_web_frontend.py`

**Interfaces:**
- Consumes: `GET /api/fs/tree`
- Produces: `renderFilesExplorer()`, `renderTreeNode(item)`, `toggleFolder(folderPath)`, `filterFileTree(query)`

- [ ] **Step 1: Write test verifying frontend File Explorer functions**

Add to `tests/test_web_frontend.py`:
```python
def test_files_explorer_frontend_script():
    from pathlib import Path
    static_html = Path("delta/web/static/index.html").read_text(encoding="utf-8")
    assert "renderFilesExplorer" in static_html
    assert "toggleFolderNode" in static_html
    assert "filterFileTree" in static_html
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_web_frontend.py -k test_files_explorer_frontend_script -v`
Expected: FAIL

- [ ] **Step 3: Implement `renderFilesExplorer` and tree helpers in HTML templates**

```javascript
        let currentFsTreeData = null;
        const collapsedFolders = new Set();

        function getFileIcon(ext) {
            switch ((ext || '').toLowerCase()) {
                case '.py': return { icon: 'code', color: 'text-yellow-500' };
                case '.js': case '.ts': case '.jsx': case '.tsx': return { icon: 'javascript', color: 'text-amber-400' };
                case '.json': return { icon: 'data_object', color: 'text-indigo-400' };
                case '.html': case '.htm': return { icon: 'html', color: 'text-orange-500' };
                case '.css': case '.scss': return { icon: 'css', color: 'text-sky-400' };
                case '.md': case '.txt': return { icon: 'description', color: 'text-zinc-400' };
                case '.png': case '.jpg': case '.svg': case '.gif': return { icon: 'image', color: 'text-emerald-400' };
                default: return { icon: 'draft', color: 'text-zinc-500' };
            }
        }

        function formatBytes(bytes) {
            if (!bytes || bytes === 0) return '0 B';
            const k = 1024;
            const sizes = ['B', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
        }

        async function renderFilesExplorer() {
            viewContainer.innerHTML = `
                <div class="p-4 md:p-6 flex-1 overflow-y-auto space-y-4 animate-fade-in text-sm flex flex-col h-full">
                    <!-- Header Bar -->
                    <div class="cyber-glass border border-zinc-200/80 dark:border-zinc-800 rounded-2xl p-4 flex flex-col md:flex-row md:items-center justify-between gap-3 shadow-sm">
                        <div class="space-y-1">
                            <div class="flex items-center gap-2">
                                <span class="material-symbols-outlined text-[20px] text-indigo-500">folder_open</span>
                                <h3 class="font-bold text-zinc-900 dark:text-zinc-100 text-sm tracking-wide">WORKSPACE FILES EXPLORER</h3>
                            </div>
                            <div class="text-[11px] font-mono text-zinc-400 dark:text-zinc-500 flex items-center gap-2" id="fs-stats-bar">
                                <span class="animate-pulse">Loading directory structure...</span>
                            </div>
                        </div>
                        <div class="flex items-center gap-2">
                            <div class="relative w-full md:w-64">
                                <span class="material-symbols-outlined absolute left-2.5 top-2 text-[16px] text-zinc-400">search</span>
                                <input type="text" id="fs-search-input" oninput="filterFileTree(this.value)" placeholder="Search files..." class="w-full bg-zinc-100/70 dark:bg-zinc-800/60 border border-zinc-200 dark:border-zinc-700/60 rounded-xl pl-8 pr-3 py-1.5 text-xs text-zinc-800 dark:text-zinc-200 focus:outline-none focus:border-indigo-500">
                            </div>
                            <button onclick="renderFilesExplorer()" title="Refresh" class="p-1.5 hover:bg-zinc-200/50 dark:hover:bg-zinc-700/50 rounded-xl transition-base text-zinc-400 hover:text-zinc-200">
                                <span class="material-symbols-outlined text-[18px]">sync</span>
                            </button>
                            <button onclick="switchNav('execution')" class="text-xs px-3 py-1.5 rounded-xl bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 font-medium hover:bg-indigo-500/20 border border-indigo-500/20 transition-base">
                                Back to Canvas
                            </button>
                        </div>
                    </div>

                    <!-- Tree Container -->
                    <div id="fs-tree-container" class="flex-1 overflow-y-auto cyber-glass border border-zinc-200/80 dark:border-zinc-800 rounded-2xl p-4 font-mono text-xs space-y-1">
                        <div class="flex items-center justify-center p-8 text-zinc-400 gap-2">
                            <span class="material-symbols-outlined animate-spin-slow">progress_activity</span>
                            <span>Scanning workspace files...</span>
                        </div>
                    </div>
                </div>
            `;

            try {
                const res = await fetch('/api/fs/tree');
                const data = await res.json();
                if (data.status === 'ok') {
                    currentFsTreeData = data;
                    document.getElementById('fs-stats-bar').innerHTML = `
                        <span class="truncate max-w-[280px]">${escapeHtml(data.root_path)}</span>
                        <span>•</span>
                        <span class="text-indigo-500 dark:text-indigo-400 font-semibold">${data.total_folders} folders</span>
                        <span>•</span>
                        <span class="text-emerald-500 font-semibold">${data.total_files} files</span>
                    `;
                    renderTreeDOM(data.tree);
                } else {
                    document.getElementById('fs-tree-container').innerHTML = `<div class="p-4 text-red-500">Error: ${escapeHtml(data.message)}</div>`;
                }
            } catch (err) {
                document.getElementById('fs-tree-container').innerHTML = `<div class="p-4 text-red-500">Failed to connect to backend filesystem API</div>`;
            }
        }

        function renderTreeDOM(nodes, filterQuery = '', parentEl = null) {
            const containerEl = parentEl || document.getElementById('fs-tree-container');
            if (!containerEl) return;
            if (!parentEl) containerEl.innerHTML = '';

            if (!nodes || nodes.length === 0) {
                if (!parentEl) containerEl.innerHTML = `<div class="p-4 text-zinc-400">No files found.</div>`;
                return;
            }

            nodes.forEach(item => {
                const isDir = item.is_dir;
                const pathId = item.path.replace(/[^a-zA-Z0-9_-]/g, '_');
                const isCollapsed = collapsedFolders.has(item.path);

                if (filterQuery && !item.name.toLowerCase().includes(filterQuery.toLowerCase()) && !isDir) {
                    return;
                }

                if (isDir) {
                    const dirEl = document.createElement('div');
                    dirEl.className = "flex flex-col space-y-0.5";
                    dirEl.innerHTML = `
                        <div onclick="toggleFolderNode('${escapeHtml(item.path)}')" class="flex items-center justify-between py-1 px-2.5 rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-800/60 cursor-pointer text-zinc-800 dark:text-zinc-200 transition-base select-none group">
                            <div class="flex items-center gap-2 min-w-0">
                                <span class="material-symbols-outlined text-[16px] text-zinc-400 transition-transform ${isCollapsed ? '' : 'rotate-90'}">chevron_right</span>
                                <span class="material-symbols-outlined text-[17px] text-indigo-500 group-hover:scale-105 transition-transform">${isCollapsed ? 'folder' : 'folder_open'}</span>
                                <span class="font-semibold text-[12px] truncate">${escapeHtml(item.name)}</span>
                            </div>
                            <span class="text-[10px] text-zinc-400 font-normal shrink-0">${item.children ? item.children.length + ' items' : ''}</span>
                        </div>
                        <div id="dir-children-${pathId}" class="pl-5 border-l border-zinc-200/60 dark:border-zinc-800 space-y-0.5 ml-2.5 ${isCollapsed ? 'hidden' : ''}"></div>
                    `;
                    containerEl.appendChild(dirEl);
                    const childrenContainer = dirEl.querySelector(`#dir-children-${pathId}`);
                    if (item.children && item.children.length > 0) {
                        renderTreeDOM(item.children, filterQuery, childrenContainer);
                    }
                } else {
                    const iconInfo = getFileIcon(item.extension);
                    const fileEl = document.createElement('div');
                    fileEl.className = "flex items-center justify-between py-1 px-2.5 rounded-lg hover:bg-white dark:hover:bg-zinc-800 cursor-pointer border border-transparent hover:border-zinc-200 dark:hover:border-zinc-700/60 text-zinc-700 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-zinc-100 transition-base select-none group";
                    fileEl.onclick = () => openFileCodeViewer(item.path);
                    fileEl.innerHTML = `
                        <div class="flex items-center gap-2 min-w-0">
                            <span class="material-symbols-outlined text-[16px] ${iconInfo.color} group-hover:scale-110 transition-transform">${iconInfo.icon}</span>
                            <span class="text-[12px] truncate">${escapeHtml(item.name)}</span>
                        </div>
                        <span class="text-[10px] text-zinc-400 font-mono shrink-0">${formatBytes(item.size)}</span>
                    `;
                    containerEl.appendChild(fileEl);
                }
            });
        }

        window.toggleFolderNode = function(folderPath) {
            if (collapsedFolders.has(folderPath)) {
                collapsedFolders.delete(folderPath);
            } else {
                collapsedFolders.add(folderPath);
            }
            if (currentFsTreeData) {
                renderTreeDOM(currentFsTreeData.tree, document.getElementById('fs-search-input')?.value || '');
            }
        };

        window.filterFileTree = function(query) {
            if (currentFsTreeData) {
                renderTreeDOM(currentFsTreeData.tree, query);
            }
        };
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_web_frontend.py -k test_files_explorer_frontend_script -v`
Expected: PASS

---

### Task 3: In-App Code Viewer Modal Component

**Files:**
- Modify: `delta/web/static/index.html:930-970`
- Modify: `delta/web/index.html:930-970`
- Test: `tests/test_web_frontend.py`

**Interfaces:**
- Consumes: `openFileCodeViewer(filePath: string)`
- Produces: Code viewer modal with line numbers, copy button, and insert-into-chat action

- [ ] **Step 1: Write test verifying Code Viewer Modal handlers**

Add to `tests/test_web_frontend.py`:
```python
def test_file_code_viewer_modal_functions():
    from pathlib import Path
    static_html = Path("delta/web/static/index.html").read_text(encoding="utf-8")
    assert "openFileCodeViewer" in static_html
    assert "code-viewer-modal" in static_html
    assert "askAiAboutFile" in static_html
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_web_frontend.py -k test_file_code_viewer_modal_functions -v`
Expected: FAIL

- [ ] **Step 3: Implement Code Viewer Modal and helpers**

```javascript
        window.openFileCodeViewer = async function(filePath) {
            let modal = document.getElementById('code-viewer-modal');
            if (!modal) {
                const modalHtml = `
                    <div id="code-viewer-modal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 hidden animate-fade-in">
                        <div class="bg-white dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-2xl w-full max-w-4xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden animate-process-enter">
                            <!-- Modal Header -->
                            <div class="px-5 py-3.5 border-b border-zinc-200 dark:border-zinc-800 flex items-center justify-between bg-zinc-50/50 dark:bg-zinc-900/50">
                                <div class="flex items-center gap-2.5 min-w-0">
                                    <span class="material-symbols-outlined text-[20px] text-indigo-500" id="viewer-file-icon">description</span>
                                    <div>
                                        <div class="font-bold text-zinc-900 dark:text-zinc-100 text-xs flex items-center gap-2">
                                            <span id="viewer-file-name">filename.py</span>
                                            <span class="text-[10px] font-mono font-normal text-zinc-400" id="viewer-file-meta">0 lines • 0 KB</span>
                                        </div>
                                        <div class="text-[10px] font-mono text-zinc-400 truncate max-w-md" id="viewer-file-path">path/to/file</div>
                                    </div>
                                </div>
                                <div class="flex items-center gap-2">
                                    <button onclick="askAiAboutFile()" class="px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs flex items-center gap-1.5 shadow-sm transition-base">
                                        <span class="material-symbols-outlined text-[14px]">smart_toy</span>
                                        <span>Ask AI</span>
                                    </button>
                                    <button onclick="copyViewerContent()" id="viewer-copy-btn" class="p-1.5 hover:bg-zinc-200/60 dark:hover:bg-zinc-800 rounded-xl transition-base text-zinc-400 hover:text-zinc-200" title="Copy code">
                                        <span class="material-symbols-outlined text-[18px]">content_copy</span>
                                    </button>
                                    <button onclick="closeModal('code-viewer-modal')" class="p-1.5 hover:bg-zinc-200/60 dark:hover:bg-zinc-800 rounded-xl transition-base text-zinc-400 hover:text-zinc-200" title="Close">
                                        <span class="material-symbols-outlined text-[18px]">close</span>
                                    </button>
                                </div>
                            </div>
                            <!-- Code Content Box -->
                            <div class="flex-1 overflow-auto p-4 bg-zinc-950 text-zinc-200 font-mono text-xs relative select-text" id="viewer-code-box">
                                <pre id="viewer-code-content" class="whitespace-pre overflow-x-auto leading-relaxed"></pre>
                            </div>
                        </div>
                    </div>
                `;
                document.body.insertAdjacentHTML('beforeend', modalHtml);
                modal = document.getElementById('code-viewer-modal');
            }

            modal.classList.remove('hidden');
            document.getElementById('viewer-file-name').innerText = filePath.split(/[\/\\]/).pop();
            document.getElementById('viewer-file-path').innerText = filePath;
            document.getElementById('viewer-code-content').innerText = "Loading file content...";

            try {
                const res = await fetch(`/api/fs/read?path=${encodeURIComponent(filePath)}`);
                const data = await res.json();
                if (data.status === 'ok') {
                    document.getElementById('viewer-file-meta').innerText = `${data.line_count} lines • ${formatBytes(data.size)}`;
                    document.getElementById('viewer-code-content').innerText = data.content;
                } else {
                    document.getElementById('viewer-code-content').innerText = `Error: ${data.message}`;
                }
            } catch (err) {
                document.getElementById('viewer-code-content').innerText = `Failed to load file: ${err.message}`;
            }
        };

        window.copyViewerContent = function() {
            const content = document.getElementById('viewer-code-content')?.innerText || '';
            navigator.clipboard.writeText(content);
            const copyBtn = document.getElementById('viewer-copy-btn');
            if (copyBtn) {
                copyBtn.innerHTML = `<span class="material-symbols-outlined text-[18px] text-emerald-500">check</span>`;
                setTimeout(() => {
                    copyBtn.innerHTML = `<span class="material-symbols-outlined text-[18px]">content_copy</span>`;
                }, 1500);
            }
        };

        window.askAiAboutFile = function() {
            const path = document.getElementById('viewer-file-path')?.innerText || '';
            closeModal('code-viewer-modal');
            switchNav('execution');
            sendPrompt(`Analyze file ${path}`);
        };
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_web_frontend.py -k test_file_code_viewer_modal_functions -v`
Expected: PASS

---

### Task 4: Full Regression Testing & Synchronization

**Files:**
- Test: `tests/test_web_server.py`
- Test: `tests/test_web_frontend.py`
- Test: `tests/test_agent_events.py`

- [ ] **Step 1: Run all test suites**

Run: `python -m pytest tests/ -v`
Expected: ALL PASS

- [ ] **Step 2: Check synchronization of `delta/web/static/index.html` and `delta/web/index.html`**

Run: `python -c "import filecmp; print('In sync:', filecmp.cmp('delta/web/static/index.html', 'delta/web/index.html'))"`
Expected: `In sync: True`
