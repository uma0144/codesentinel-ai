from typing import Dict, Any, Optional, Callable
from core.static_analyzer import StaticAnalyzer
from core.patch_engine import PatchEngine
from core.llm_client import LLMClient
from agents.security_agent import SecurityAgent
from agents.quality_agent import QualityAgent
from agents.bug_hunter_agent import BugHunterAgent
from agents.test_agent import TestAgent
from benchmarks import load_benchmark_code, BENCHMARK_SCENARIOS, get_precomputed_review

class CodeReviewOrchestrator:
    '''Coordinates multi-agent code analysis, security review, test generation, and diff patching.'''
    
    def __init__(self, provider: str = "gemini", api_key: Optional[str] = None, model: Optional[str] = None):
        self.provider = provider
        self.api_key = api_key
        self.model = model
        self.client = LLMClient(provider=provider, api_key=api_key, model=model)
        self.security_agent = SecurityAgent(self.client)
        self.quality_agent = QualityAgent(self.client)
        self.bug_hunter = BugHunterAgent(self.client)
        self.test_agent = TestAgent(self.client)

    def review_code(
        self,
        code: str,
        language: str = "python",
        benchmark_key: Optional[str] = None,
        progress_callback: Optional[Callable[[str, float], None]] = None
    ) -> Dict[str, Any]:
        '''Executes full multi-agent review pipeline.'''
        
        # Step 1: Static AST & Complexity Pre-flight
        if progress_callback:
            progress_callback("Running Static AST & Complexity Analysis...", 0.15)
        static_results = StaticAnalyzer.analyze(code, language)
        
        # Check if benchmark demo mode or live LLM review
        if benchmark_key and (not self.api_key or self.provider == "demo"):
            precomputed = get_precomputed_review(benchmark_key, code)
            if precomputed:
                if progress_callback:
                    progress_callback("Auditing Security (OWASP / CWE / Secrets)...", 0.40)
                    progress_callback("Evaluating Code Quality & Architecture...", 0.60)
                    progress_callback("Hunting Runtime Bugs & Synthesizing Patch...", 0.80)
                    progress_callback("Synthesizing Unit Test Suite...", 0.95)
                
                security_review = precomputed["security"]
                quality_review = precomputed["quality"]
                bug_review = precomputed["bugs"]
                fixed_code = bug_review.get("fixed_code", code)
                test_review = precomputed["test_suite"]
                
                unified_diff = PatchEngine.generate_unified_diff(code, fixed_code, filename=f"source.{'py' if language=='python' else 'js'}")
                diff_stats = PatchEngine.compute_stats(code, fixed_code)
                fixed_static_results = StaticAnalyzer.analyze(fixed_code, language)
                
                sec_score = security_review.get("security_score", 70)
                qual_score = quality_review.get("quality_score", 75)
                rel_score = bug_review.get("reliability_score", 80)
                perf_score = quality_review.get("performance_score", 75)
                maint_score = static_results.get("metrics", {}).get("maintainability_index", 70)
                
                composite_score = int(
                    (sec_score * 0.35) +
                    (rel_score * 0.25) +
                    (qual_score * 0.20) +
                    (perf_score * 0.20)
                )
                
                if progress_callback:
                    progress_callback("Review Complete!", 1.0)
                    
                return {
                    "status": "success",
                    "language": language,
                    "composite_score": composite_score,
                    "scores": {
                        "security": sec_score,
                        "reliability": rel_score,
                        "quality": qual_score,
                        "performance": perf_score,
                        "maintainability": maint_score
                    },
                    "static_analysis": {
                        "original": static_results,
                        "fixed": fixed_static_results
                    },
                    "security": security_review,
                    "quality": quality_review,
                    "bugs": bug_review,
                    "test_suite": test_review,
                    "patch": {
                        "original_code": code,
                        "fixed_code": fixed_code,
                        "unified_diff": unified_diff,
                        "stats": diff_stats
                    }
                }
            
        # Step 2: Security Audit
        if progress_callback:
            progress_callback("Auditing Security (OWASP / CWE / Secrets)...", 0.40)
        
        security_review = self.security_agent.review(code, language)
        
        # Merge static heuristics into security review
        for h in static_results.get("heuristics", []):
            # Avoid duplicate rules if already caught
            if not any(v.get("cwe_id") == h.get("rule") for v in security_review.get("vulnerabilities", [])):
                security_review.setdefault("vulnerabilities", []).append({
                    "id": f"STATIC-{h.get('rule')}",
                    "title": f"Static Sentinel: {h.get('rule').replace('_', ' ').title()}",
                    "severity": h.get("severity", "MEDIUM"),
                    "cwe_id": h.get("rule"),
                    "owasp_category": "A05:2021-Security Misconfiguration",
                    "line_numbers": [h.get("line", 1)],
                    "description": h.get("message", "Flagged by pre-flight AST scanner."),
                    "attack_vector": "Potential exploitation via unchecked input or hardcoded secret.",
                    "remediation": "Apply secure coding pattern and environment-variable secret management."
                })
        
        # Step 3: Quality & Architecture Review
        if progress_callback:
            progress_callback("Evaluating Code Quality & Architecture...", 0.60)
        quality_review = self.quality_agent.review(code, language)
        
        # Step 4: Bug Diagnostics & Patch Synthesis
        if progress_callback:
            progress_callback("Hunting Runtime Bugs & Synthesizing Patch...", 0.80)
        bug_review = self.bug_hunter.review(code, language)
        fixed_code = bug_review.get("fixed_code", code)
        
        # Step 5: Test Generation
        if progress_callback:
            progress_callback("Synthesizing Unit Test Suite...", 0.95)
        test_review = self.test_agent.generate_tests(code, fixed_code, language)
        
        # Step 6: Diff & Patch Metrics Calculation
        unified_diff = PatchEngine.generate_unified_diff(code, fixed_code, filename=f"source.{ 'py' if language=='python' else 'js' }")
        diff_stats = PatchEngine.compute_stats(code, fixed_code)
        
        # Step 7: Post-fix Static Analysis
        fixed_static_results = StaticAnalyzer.analyze(fixed_code, language)
        
        # Step 8: Composite Scoring
        sec_score = security_review.get("security_score", 70)
        qual_score = quality_review.get("quality_score", 75)
        rel_score = bug_review.get("reliability_score", 80)
        perf_score = quality_review.get("performance_score", 75)
        maint_score = static_results.get("metrics", {}).get("maintainability_index", 70)
        
        composite_score = int(
            (sec_score * 0.35) +
            (rel_score * 0.25) +
            (qual_score * 0.20) +
            (perf_score * 0.20)
        )
        
        if progress_callback:
            progress_callback("Review Complete!", 1.0)
            
        return {
            "status": "success",
            "language": language,
            "composite_score": composite_score,
            "scores": {
                "security": sec_score,
                "reliability": rel_score,
                "quality": qual_score,
                "performance": perf_score,
                "maintainability": maint_score
            },
            "static_analysis": {
                "original": static_results,
                "fixed": fixed_static_results
            },
            "security": security_review,
            "quality": quality_review,
            "bugs": bug_review,
            "test_suite": test_review,
            "patch": {
                "original_code": code,
                "fixed_code": fixed_code,
                "unified_diff": unified_diff,
                "stats": diff_stats
            }
        }
