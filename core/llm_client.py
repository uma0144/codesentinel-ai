import os
import json
import re
from typing import Dict, Any, Optional

try:
    import google.generativeai as genai
except ImportError:
    genai = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

class LLMClient:
    '''Unified client supporting Gemini, OpenAI, Groq, Anthropic, and Mock fallback.'''
    
    def __init__(self, provider: str = "gemini", api_key: Optional[str] = None, model: Optional[str] = None):
        self.provider = provider.lower()
        self.api_key = api_key or os.getenv(f"{self.provider.upper()}_API_KEY", "")
        self.model = model
        
        if self.provider == "gemini" and self.api_key and genai:
            genai.configure(api_key=self.api_key)
            self.model_name = model or "gemini-1.5-flash"
            self.gemini_model = genai.GenerativeModel(self.model_name)
        elif self.provider in ("openai", "groq") and self.api_key and OpenAI:
            base_url = "https://api.groq.com/openai/v1" if self.provider == "groq" else None
            self.openai_client = OpenAI(api_key=self.api_key, base_url=base_url)
            self.model_name = model or ("llama-3.3-70b-versatile" if self.provider == "groq" else "gpt-4o-mini")
        else:
            self.gemini_model = None
            self.openai_client = None

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        '''Generates response text from the configured provider.'''
        if self.provider == "gemini" and self.gemini_model:
            try:
                full_prompt = f"{system_prompt}\n\n--- USER CODE INPUT ---\n{user_prompt}"
                response = self.gemini_model.generate_content(full_prompt)
                return response.text
            except Exception as e:
                return self._fallback_error(f"Gemini API Error: {str(e)}")
                
        elif self.provider in ("openai", "groq") and self.openai_client:
            try:
                response = self.openai_client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.2
                )
                return response.choices[0].message.content or ""
            except Exception as e:
                return self._fallback_error(f"{self.provider.capitalize()} API Error: {str(e)}")
        else:
            return ""

    def generate_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        '''Generates and parses structured JSON from LLM.'''
        raw_text = self.generate(system_prompt, user_prompt)
        if not raw_text:
            return {}
        return self._extract_json(raw_text)

    @staticmethod
    def _extract_json(text: str) -> Dict[str, Any]:
        text = text.strip()
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if json_match:
            text = json_match.group(1)
        else:
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                text = text[start:end+1]
        try:
            return json.loads(text)
        except Exception:
            return {"error": "Failed to parse JSON", "raw_output": text}

    @staticmethod
    def _fallback_error(message: str) -> str:
        return json.dumps({"error": message, "vulnerabilities": [], "issues": [], "bugs_detected": []})
