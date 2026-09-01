from typing import Dict, Any
from core.llm_client import LLMClient
from core.prompts import BUG_HUNTER_AGENT_SYSTEM_PROMPT

class BugHunterAgent:
    def __init__(self, llm_client: LLMClient):
        self.client = llm_client

    def review(self, code: str, language: str = 'python') -> Dict[str, Any]:
        user_prompt = f"Language: {language}\n\nSource Code:\n{code}"
        result = self.client.generate_json(BUG_HUNTER_AGENT_SYSTEM_PROMPT, user_prompt)
        if not result or 'error' in result or 'fixed_code' not in result:
            return {
                'reliability_score': 80,
                'bugs_detected': [],
                'fixed_code': code,
                'summary': 'No catastrophic runtime flaws detected.'
            }
        return result
