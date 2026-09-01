import pytest
from benchmarks import BENCHMARK_SCENARIOS, load_benchmark_code, get_precomputed_review

def test_all_benchmarks_loadable():
    for key, info in BENCHMARK_SCENARIOS.items():
        code = load_benchmark_code(key)
        assert len(code) > 0, f"Benchmark {key} failed to load."
        review = get_precomputed_review(key, code)
        assert review is not None, f"Precomputed review missing for {key}"
        assert "security" in review
        assert "bugs" in review
        assert "test_suite" in review
