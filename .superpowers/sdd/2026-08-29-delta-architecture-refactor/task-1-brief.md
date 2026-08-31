### Task 1: Clean Up Technical Debt & Remove Backup Files

**Files:**
- Remove: `delta/ai/llm.py.bak`
- Remove: `delta/ai/events.py` (migrated to `delta/core/events.py`)

**Interfaces:**
- Produces: Clean tree without dead files or duplicated event definitions.

- [ ] **Step 1: Write failing test verifying absence of dead files**

```python
# tests/test_codebase_cleanliness.py
from pathlib import Path

def test_no_bak_files():
    bak_files = list(Path("delta").rglob("*.bak"))
    assert len(bak_files) == 0, f"Found backup files: {bak_files}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_codebase_cleanliness.py -v`  
Expected: FAIL (finds `delta/ai/llm.py.bak`)

- [ ] **Step 3: Remove backup file and redundant event module**

Remove `delta/ai/llm.py.bak` and remove `delta/ai/events.py` after consolidating into `delta/core/events.py`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_codebase_cleanliness.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_codebase_cleanliness.py
git rm delta/ai/llm.py.bak delta/ai/events.py || true
git commit -m "refactor(core): remove dead files and duplicate event modules"
```
