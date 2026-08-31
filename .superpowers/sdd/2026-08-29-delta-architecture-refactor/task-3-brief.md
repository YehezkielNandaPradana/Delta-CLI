### Task 3: Metasploit & Security Tool Fallback Stabilization

**Files:**
- Modify: `delta/pentest/metasploit.py`
- Modify: `delta/pentest/burp.py`
- Create: `tests/test_pentest_tool_fallbacks.py`

**Interfaces:**
- Consumes: `delta/core/events.py`
- Produces: `MetasploitClient` & `BurpClient` with safe `connect()` and `.is_available` methods.

- [ ] **Step 1: Write failing test for Metasploit fallback**

```python
# tests/test_pentest_tool_fallbacks.py
import pytest
from delta.pentest.metasploit import MetasploitClient
from delta.pentest.burp import BurpClient

def test_metasploit_client_offline_fallback():
    client = MetasploitClient(host="127.0.0.1", port=55553)
    connected = client.connect(password="wrong_pass")
    assert connected is False
    assert client.is_available is False

def test_burp_client_offline_fallback():
    client = BurpClient(api_url="http://127.0.0.1:9999")
    connected = client.connect()
    assert connected is False
    assert client.is_available is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_pentest_tool_fallbacks.py -v`  
Expected: FAIL (unhandled exceptions or connection errors)

- [ ] **Step 3: Update `delta/pentest/metasploit.py` and `delta/pentest/burp.py`**

Wrap RPC/HTTP connections in exception blocks and track `.is_available`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_pentest_tool_fallbacks.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add delta/pentest/metasploit.py delta/pentest/burp.py tests/test_pentest_tool_fallbacks.py
git commit -m "fix(pentest): add graceful connection fallbacks for Metasploit and Burp Suite"
```
