from pathlib import Path

def test_no_bak_files():
    bak_files = list(Path("delta").rglob("*.bak"))
    assert len(bak_files) == 0, f"Found backup files: {bak_files}"
