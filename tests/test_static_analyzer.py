import pytest
from core.static_analyzer import StaticAnalyzer

def test_static_analyzer_python_metrics():
    code = """
import os
import sys

def compute_sum(a, b):
    # Sum calculation
    if a > 0:
        return a + b
    return b
"""
    result = StaticAnalyzer.analyze(code, "python")
    assert result["syntax_valid"] is True
    assert result["metrics"]["total_lines"] > 0
    assert result["metrics"]["function_count"] == 1
    assert "os" in result["symbols"]["imports"]

def test_static_analyzer_syntax_error():
    broken_code = "def broken(:"
    result = StaticAnalyzer.analyze(broken_code, "python")
    assert result["syntax_valid"] is False
    assert result["syntax_error"] is not None

def test_static_analyzer_heuristics_hardcoded_secret():
    code = 'API_SECRET = "AIzaSyD-1234567890abcdefghijklmnopqrst"'
    result = StaticAnalyzer.analyze(code, "python")
    heuristics = result["heuristics"]
    assert any(h["rule"] == "HARDCODED_SECRET" for h in heuristics)
