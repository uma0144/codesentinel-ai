import os
import json
from typing import Dict, Any, List, Optional

BENCHMARK_SCENARIOS = {
    'sql_injection': {
        'title': 'SQL Injection, Hardcoded Secret & Resource Leak',
        'language': 'python',
        'file': 'benchmarks/sql_injection.py',
        'description': 'Unsanitized user input concatenated into raw SQLite query, hardcoded production API key, and unclosed database connection.',
        'expected_cwe': ['CWE-89', 'CWE-798', 'CWE-22', 'CWE-772']
    },
    'race_condition': {
        'title': 'Async/Thread Race Condition in Financial Transfer',
        'language': 'python',
        'file': 'benchmarks/race_condition.py',
        'description': 'Multi-threaded bank transfer with check-then-act race condition causing double spending / negative balances.',
        'expected_cwe': ['CWE-362', 'CWE-820']
    },
    'memory_leak': {
        'title': 'Unbounded Cache Memory Leak & Socket Handle Leak',
        'language': 'python',
        'file': 'benchmarks/memory_leak.py',
        'description': 'Global cache without LRU eviction/TTL causing OOM crash, plus unclosed TCP socket file descriptors.',
        'expected_cwe': ['CWE-772', 'CWE-400']
    },
    'broken_auth': {
        'title': 'Broken JWT Authentication & Hardcoded Secret',
        'language': 'python',
        'file': 'benchmarks/broken_auth.py',
        'description': 'Insecure JWT verification bypassing signature verification and using static weak secret.',
        'expected_cwe': ['CWE-287', 'CWE-347', 'CWE-798']
    },
    'redos_regex': {
        'title': 'ReDoS Catastrophic Backtracking & Prototype Pollution',
        'language': 'javascript',
        'file': 'benchmarks/redos_regex.js',
        'description': 'Nested quantifier exponential regex vulnerability triggering Denial of Service and unsafe recursive object assignment.',
        'expected_cwe': ['CWE-1333', 'CWE-1321']
    }
}

def load_benchmark_code(key: str) -> str:
    if key in BENCHMARK_SCENARIOS:
        filepath = BENCHMARK_SCENARIOS[key]['file']
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
    return ''

def get_precomputed_review(key: str, code: str) -> Optional[Dict[str, Any]]:
    json_path = os.path.join(os.path.dirname(__file__), 'data.json')
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get(key)
        except Exception:
            return None
    return None
