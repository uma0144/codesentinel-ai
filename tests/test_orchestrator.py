import pytest
from core.orchestrator import CodeReviewOrchestrator
from benchmarks import load_benchmark_code

def test_orchestrator_benchmark_review():
    code = load_benchmark_code("sql_injection")
    orchestrator = CodeReviewOrchestrator(provider="gemini", api_key=None)
    result = orchestrator.review_code(code, "python", benchmark_key="sql_injection")
    
    assert result["status"] == "success"
    assert result["composite_score"] > 0
    assert len(result["security"]["vulnerabilities"]) > 0
    assert "SELECT" in result["patch"]["fixed_code"]
    assert result["test_suite"]["framework"] == "pytest"
