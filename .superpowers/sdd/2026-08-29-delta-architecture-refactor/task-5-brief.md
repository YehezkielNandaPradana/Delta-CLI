### Task 5: End-to-End System Smoke Test

**Files:**
- Create: `tests/test_e2e_refactor.py`

- [ ] **Step 1: Write failing E2E test**

```python
# tests/test_e2e_refactor.py
import pytest
from delta.core.engine import DeltaEngine

@pytest.mark.asyncio
async def test_full_engine_lifecycle():
    engine = DeltaEngine()
    await engine.initialize()
    status = await engine.get_status()
    assert status["initialized"] is True
    await engine.shutdown()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_e2e_refactor.py -v`  
Expected: FAIL

- [ ] **Step 3: Ensure `DeltaEngine` lifecycle works end-to-end**

Update `delta/core/engine.py` to coordinate session, event bus, and subsystem initialization cleanly.

- [ ] **Step 4: Run full pytest suite**

Run: `pytest -v`  
Expected: All unit & E2E tests PASS.

- [ ] **Step 5: Commit**

```bash
git add delta/core/engine.py tests/test_e2e_refactor.py
git commit -m "feat(core): implement unified DeltaEngine lifecycle and pass E2E smoke tests"
```
