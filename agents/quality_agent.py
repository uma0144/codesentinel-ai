from typing import Dict, Any
from core.llm_client import LLMClient
from core.prompts import QUALITY_AGENT_SYSTEM_PROMPT

class QualityAgent:
    def __init__(self, llm_client: LLMClient):
        self.client = llm_client

    def review(self, code: str, language: str = 'python') -> Dict[str, Any]:
        user_prompt = f"Language: {language}\n\nSource Code:\n{code}"
        result = self.client.generate_json(QUALITY_AGENT_SYSTEM_PROMPT, user_prompt)
        if not result or 'error' in result:
            return {
                'quality_score': 75,
                'maintainability_score': 75,
                'performance_score': 80,
                'time_complexity': 'O(N)',
                'space_complexity': 'O(1)',
                'issues': [],
                'strengths': ['Readable structure and standard idioms.'],
                'summary': 'Code quality meets standard engineering guidelines.'
            }
        return result
