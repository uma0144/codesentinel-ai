import json
from typing import Dict, Any

class ReportExporter:
    '''Generates exportable Markdown, GitHub PR Review Comments, and JSON audit reports.'''
    
    @staticmethod
    def to_markdown(review_result: Dict[str, Any], filename: str = "source_file") -> str:
        scores = review_result.get("scores", {})
        sec = review_result.get("security", {})
        qual = review_result.get("quality", {})
        bugs = review_result.get("bugs", {})
        tests = review_result.get("test_suite", {})
        stats = review_result.get("patch", {}).get("stats", {})
        
        sec_score = scores.get('security', 0)
        rel_score = scores.get('reliability', 0)
        perf_score = scores.get('performance', 0)
        maint_score = scores.get('maintainability', 0)
        
        sec_rating = 'Safe' if sec_score >= 80 else ('Warning' if sec_score >= 50 else 'Critical Risk')
        rel_rating = 'Robust' if rel_score >= 80 else ('Moderate' if rel_score >= 50 else 'Fragile')
        perf_rating = 'High' if perf_score >= 80 else 'Needs Optimization'
        maint_rating = 'Clean' if maint_score >= 65 else 'Complex'
        
        lines = [
            f"# CodeSentinel AI ? Automated Code Review & Security Audit Report",
            f"",
            f"**Target File:** `{filename}`  ",
            f"**Language:** `{review_result.get('language', 'Unknown').capitalize()}`  ",
            f"**Overall Code Health Score:** **{review_result.get('composite_score', 0)} / 100**  ",
            f"",
            f"---",
            f"",
            f"## Executive Scorecard",
            f"",
            f"| Dimension | Score | Rating |",
            f"| :--- | :---: | :---: |",
            f"| Security Posture | **{sec_score} / 100** | {sec_rating} |",
            f"| Runtime Reliability | **{rel_score} / 100** | {rel_rating} |",
            f"| Performance Efficiency | **{perf_score} / 100** | {perf_rating} |",
            f"| Maintainability Index | **{maint_score} / 100** | {maint_rating} |",
            f"",
            f"---",
            f"",
            f"## Security Audit & Vulnerabilities ({len(sec.get('vulnerabilities', []))} Found)",
            f""
        ]
        
        if sec.get("vulnerabilities"):
            for v in sec.get("vulnerabilities", []):
                lines.extend([
                    f"### [{v.get('severity', 'MEDIUM')}] {v.get('title')}",
                    f"- **Identifier:** `{v.get('id')}` | **CWE:** `{v.get('cwe_id')}` | **OWASP:** `{v.get('owasp_category')}`",
                    f"- **Affected Lines:** `{', '.join(map(str, v.get('line_numbers', [])))}`",
                    f"- **Description:** {v.get('description')}",
                    f"- **Attack Vector:** {v.get('attack_vector')}",
                    f"- **Remediation:** {v.get('remediation')}",
                    f""
                ])
        else:
            lines.append("*No security vulnerabilities detected.*")
            lines.append("")

        lines.extend([
            f"---",
            f"",
            f"## Bug Diagnostics & Logic Flaws ({len(bugs.get('bugs_detected', []))} Found)",
            f""
        ])

        if bugs.get("bugs_detected"):
            for b in bugs.get("bugs_detected", []):
                lines.extend([
                    f"### [{b.get('severity', 'MEDIUM')}] {b.get('title')} ({b.get('type')})",
                    f"- **Lines:** `{', '.join(map(str, b.get('line_numbers', [])))}`",
                    f"- **Root Cause:** {b.get('root_cause')}",
                    f"- **Reproduction:** {b.get('reproduction_scenario')}",
                    f"- **Fix Strategy:** {b.get('fix_strategy')}",
                    f""
                ])
        else:
            lines.append("*No critical runtime bugs detected.*")
            lines.append("")

        lines.extend([
            f"---",
            f"",
            f"## Generated Unit Test Suite (`{tests.get('test_file_name', 'test_suite.py')}`)",
            f"",
            f"```{review_result.get('language', 'python')}",
            f"{tests.get('test_code', '# No tests generated')}",
            f"```",
            f"",
            f"---",
            f"",
            f"## Unified Git Diff Patch (+{stats.get('additions', 0)} / -{stats.get('deletions', 0)})",
            f"",
            f"```diff",
            f"{review_result.get('patch', {}).get('unified_diff', '')}",
            f"```",
            f"",
            f"*Generated automatically by CodeSentinel AI Multi-Agent Engine.*"
        ])
        
        return "\n".join(lines)

    @staticmethod
    def to_json(review_result: Dict[str, Any]) -> str:
        return json.dumps(review_result, indent=2)
