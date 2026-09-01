import ast
import re
import math
from typing import Dict, Any, List

class StaticAnalyzer:
    @staticmethod
    def analyze_python(code: str) -> Dict[str, Any]:
        lines = code.splitlines()
        total_lines = len(lines)
        blank_lines = sum(1 for line in lines if not line.strip())
        comment_lines = sum(1 for line in lines if line.strip().startswith('#'))
        code_lines = total_lines - blank_lines - comment_lines
        
        syntax_valid = True
        syntax_error = None
        tree = None
        
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            syntax_valid = False
            syntax_error = f"{e.msg} (line {e.lineno}, col {e.offset})"
        
        complexity = 1
        functions = []
        classes = []
        imports = []
        heuristics = []
        
        if tree and syntax_valid:
            for node in ast.walk(tree):
                if isinstance(node, (ast.If, ast.For, ast.While, ast.ExceptHandler, ast.With, ast.Assert)):
                    complexity += 1
                elif isinstance(node, ast.BoolOp):
                    complexity += len(node.values) - 1
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    functions.append(node.name)
                elif isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
                
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name) and node.func.id in ('eval', 'exec', 'input', '__import__'):
                        heuristics.append({
                            'rule': 'DANGEROUS_CALL',
                            'severity': 'HIGH',
                            'message': f'Potentially dangerous call to `{node.func.id}()` detected on line {getattr(node, "lineno", 1)}',
                            'line': getattr(node, 'lineno', 1)
                        })
                    if isinstance(node.func, ast.Attribute) and node.func.attr in ('raw', 'execute'):
                        heuristics.append({
                            'rule': 'RAW_SQL_EXECUTION',
                            'severity': 'HIGH',
                            'message': f'Possible raw database query call (`{node.func.attr}`) on line {getattr(node, "lineno", 1)}',
                            'line': getattr(node, 'lineno', 1)
                        })
        
        StaticAnalyzer._check_regex_heuristics(code, heuristics)
        
        loc_for_mi = max(1, code_lines)
        cyclomatic = max(1, complexity)
        halstead_vol = max(1, loc_for_mi * 8.0)
        mi = 171 - 5.2 * math.log(halstead_vol) - 0.23 * cyclomatic - 16.2 * math.log(loc_for_mi)
        normalized_mi = max(0, min(100, int((mi * 100) / 171)))
        
        return {
            'language': 'python',
            'syntax_valid': syntax_valid,
            'syntax_error': syntax_error,
            'metrics': {
                'total_lines': total_lines,
                'code_lines': code_lines,
                'comment_lines': comment_lines,
                'blank_lines': blank_lines,
                'cyclomatic_complexity': complexity,
                'maintainability_index': normalized_mi,
                'function_count': len(functions),
                'class_count': len(classes)
            },
            'symbols': {
                'functions': functions,
                'classes': classes,
                'imports': list(set(imports))
            },
            'heuristics': heuristics
        }

    @staticmethod
    def analyze_generic(code: str, language: str = 'javascript') -> Dict[str, Any]:
        lines = code.splitlines()
        total_lines = len(lines)
        blank_lines = sum(1 for line in lines if not line.strip())
        comment_lines = sum(1 for line in lines if line.strip().startswith('//') or line.strip().startswith('/*'))
        code_lines = total_lines - blank_lines - comment_lines
        
        keywords = [r'if', r'for', r'while', r'switch', r'case', r'catch', r'&&', r'\|\|']
        complexity = 1
        for kw in keywords:
            complexity += len(re.findall(kw, code))
        
        heuristics = []
        StaticAnalyzer._check_regex_heuristics(code, heuristics)
        
        loc_for_mi = max(1, code_lines)
        cyclomatic = max(1, complexity)
        halstead_vol = max(1, loc_for_mi * 8.0)
        mi = 171 - 5.2 * math.log(halstead_vol) - 0.23 * cyclomatic - 16.2 * math.log(loc_for_mi)
        normalized_mi = max(0, min(100, int((mi * 100) / 171)))
        
        return {
            'language': language,
            'syntax_valid': True,
            'syntax_error': None,
            'metrics': {
                'total_lines': total_lines,
                'code_lines': code_lines,
                'comment_lines': comment_lines,
                'blank_lines': blank_lines,
                'cyclomatic_complexity': complexity,
                'maintainability_index': normalized_mi,
                'function_count': len(re.findall(r'function\s+[a-zA-Z0-9_]+', code)),
                'class_count': len(re.findall(r'class\s+[a-zA-Z0-9_]+', code))
            },
            'symbols': {
                'functions': re.findall(r'function\s+([a-zA-Z0-9_]+)', code),
                'classes': re.findall(r'class\s+([a-zA-Z0-9_]+)', code),
                'imports': re.findall(r'import\s+(\w+)', code)
            },
            'heuristics': heuristics
        }

    @staticmethod
    def _check_regex_heuristics(code: str, heuristics: List[Dict[str, Any]]):
        lines = code.splitlines()
        for idx, line in enumerate(lines, 1):
            if re.search(r"(?i)(api[_-]?key|secret|password|auth[_-]?token|jwt[_-]?secret)\s*=\s*['\"][A-Za-z0-9_\-\$=]{8,}['\"]", line):
                heuristics.append({
                    'rule': 'HARDCODED_SECRET',
                    'severity': 'CRITICAL',
                    'message': f'Potential hardcoded secret or API credential detected on line {idx}',
                    'line': idx
                })
            if re.search(r"(?i)(SELECT|INSERT|UPDATE|DELETE).*(%s|\.format\(|\+\s*[a-zA-Z_]|f['\"])", line):
                heuristics.append({
                    'rule': 'SQL_INJECTION_PATTERN',
                    'severity': 'HIGH',
                    'message': f'Unsafe dynamic SQL string formatting detected on line {idx}',
                    'line': idx
                })
            if re.search(r"(?i)open\s*\(.*\+.*\)|\bos\.path\.join\(.*request\.", line):
                heuristics.append({
                    'rule': 'PATH_TRAVERSAL_RISK',
                    'severity': 'MEDIUM',
                    'message': f'Potential unvalidated path concatenation on line {idx}',
                    'line': idx
                })

    @staticmethod
    def analyze(code: str, language: str = 'python') -> Dict[str, Any]:
        if language.lower() in ('python', 'py'):
            return StaticAnalyzer.analyze_python(code)
        return StaticAnalyzer.analyze_generic(code, language)
