import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
    
    SUPPORTED_EXTENSIONS = {
        '.py': 'python',
        '.js': 'javascript', 
        '.ts': 'typescript',
        '.jsx': 'javascript',
        '.tsx': 'typescript',
        '.java': 'java',
        '.cpp': 'cpp',
        '.c': 'c',
        '.go': 'go',
        '.rs': 'rust',
        '.php': 'php',
        '.rb': 'ruby',
        '.swift': 'swift',
        '.kt': 'kotlin'
    }
    
    MAX_FILE_SIZE = 50000
    MAX_FILES_TO_PROCESS = 100
    DATA_DIR = Path(__file__).parent.parent / "data"
    TEMP_DIR = DATA_DIR / "temp"
    
    @classmethod
    def validate(cls):
        cls.DATA_DIR.mkdir(exist_ok=True)
        cls.TEMP_DIR.mkdir(exist_ok=True)
        
        if not cls.OPENAI_API_KEY:
            print("⚠️  OpenAI API key not found - some features will be limited")
            print("   Set OPENAI_API_KEY in .env file for full functionality")
        
        return True