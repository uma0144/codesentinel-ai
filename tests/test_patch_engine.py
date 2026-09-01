import pytest
from core.patch_engine import PatchEngine

def test_patch_engine_diff_and_stats():
    orig = "def foo():\n    return 1\n"
    mod = "def foo():\n    return 2\n"
    diff = PatchEngine.generate_unified_diff(orig, mod, "foo.py")
    assert "--- a/foo.py" in diff
    assert "+++ b/foo.py" in diff
    
    stats = PatchEngine.compute_stats(orig, mod)
    assert stats["total_changes"] >= 1

def test_html_diff_generation():
    orig = "a = 1\n"
    mod = "a = 2\n"
    html = PatchEngine.generate_html_diff_table(orig, mod)
    assert "<table" in html
