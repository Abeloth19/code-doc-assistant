import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional
from colorama import Fore, Style, init

init(autoreset=True)

class Logger:
    @staticmethod
    def info(message: str):
        print(f"{Fore.CYAN}ℹ {message}{Style.RESET_ALL}")
    
    @staticmethod
    def success(message: str):
        print(f"{Fore.GREEN}✓ {message}{Style.RESET_ALL}")
    
    @staticmethod
    def warning(message: str):
        print(f"{Fore.YELLOW}⚠ {message}{Style.RESET_ALL}")
    
    @staticmethod
    def error(message: str):
        print(f"{Fore.RED}✗ {message}{Style.RESET_ALL}")

class FileHelper:
    @staticmethod
    def create_temp_dir() -> str:
        return tempfile.mkdtemp()
    
    @staticmethod
    def cleanup_temp_dir(temp_dir: str):
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    @staticmethod
    def is_valid_repo_url(url: str) -> bool:
        return url.startswith(('https://github.com/', 'git@github.com:'))
    
    @staticmethod
    def get_repo_name_from_url(url: str) -> Optional[str]:
        if 'github.com' in url:
            parts = url.replace('https://github.com/', '').replace('.git', '').split('/')
            if len(parts) >= 2:
                return f"{parts[0]}/{parts[1]}"
        return None