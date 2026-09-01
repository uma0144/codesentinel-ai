import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')
    DEFAULT_PROVIDER = os.getenv('DEFAULT_LLM_PROVIDER', 'gemini')
    DEFAULT_MODEL = os.getenv('DEFAULT_LLM_MODEL', 'gemini-1.5-flash')
