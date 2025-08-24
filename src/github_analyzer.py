import requests
import os
import tempfile
import shutil
from git import Repo
from pathlib import Path
from typing import Dict, List, Optional
from .config import Config
from .utils import Logger, FileHelper

class GitHubAnalyzer:
    def __init__(self):
        self.config = Config()
        self.session = requests.Session()
        if self.config.GITHUB_TOKEN:
            self.session.headers.update({
                'Authorization': f'token {self.config.GITHUB_TOKEN}',
                'Accept': 'application/vnd.github.v3+json'
            })

    def clone_repository(self, repo_url: str) -> Optional[str]:
        if not FileHelper.is_valid_repo_url(repo_url):
            Logger.error(f"Invalid repository URL: {repo_url}")
            return None
            
        temp_dir = FileHelper.create_temp_dir()
        try:
            Logger.info(f"Cloning repository: {repo_url}")
            Repo.clone_from(repo_url, temp_dir, depth=1)
            Logger.success(f"Repository cloned to: {temp_dir}")
            return temp_dir
        except Exception as e:
            Logger.error(f"Failed to clone repository: {e}")
            FileHelper.cleanup_temp_dir(temp_dir)
            return None

    def get_repo_info(self, repo_url: str) -> Dict:
        repo_name = FileHelper.get_repo_name_from_url(repo_url)
        if not repo_name:
            return {}
        
        try:
            Logger.info(f"Fetching repository info for: {repo_name}")
            response = self.session.get(f'https://api.github.com/repos/{repo_name}')
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'name': data.get('name', ''),
                    'description': data.get('description', ''),
                    'language': data.get('language', ''),
                    'stars': data.get('stargazers_count', 0),
                    'forks': data.get('forks_count', 0),
                    'size': data.get('size', 0),
                    'created_at': data.get('created_at', ''),
                    'updated_at': data.get('updated_at', ''),
                    'topics': data.get('topics', [])
                }
            else:
                Logger.warning(f"Failed to fetch repo info: {response.status_code}")
                
        except Exception as e:
            Logger.error(f"Error fetching repository info: {e}")
            
        return {}

    def analyze_codebase(self, path: str) -> Dict:
        path = Path(path)
        if not path.exists():
            Logger.error(f"Path does not exist: {path}")
            return {}
            
        Logger.info(f"Analyzing codebase at: {path}")
        
        files = []
        language_stats = {}
        total_lines = 0
        
        for file_path in path.rglob('*'):
            if not file_path.is_file():
                continue
                
            if file_path.suffix not in self.config.SUPPORTED_EXTENSIONS:
                continue
                
            if file_path.stat().st_size > self.config.MAX_FILE_SIZE:
                Logger.warning(f"Skipping large file: {file_path}")
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                relative_path = file_path.relative_to(path)
                language = self.config.SUPPORTED_EXTENSIONS[file_path.suffix]
                lines = len(content.split('\n'))
                
                files.append({
                    'path': str(relative_path),
                    'full_path': str(file_path),
                    'language': language,
                    'content': content,
                    'size': len(content),
                    'lines': lines
                })
                
                language_stats[language] = language_stats.get(language, 0) + 1
                total_lines += lines
                
                if len(files) >= self.config.MAX_FILES_TO_PROCESS:
                    Logger.warning(f"Reached max file limit ({self.config.MAX_FILES_TO_PROCESS})")
                    break
                    
            except Exception as e:
                Logger.warning(f"Error reading file {file_path}: {e}")
                continue
        
        Logger.success(f"Analyzed {len(files)} files across {len(language_stats)} languages")
        
        return {
            'files': files,
            'language_stats': language_stats,
            'total_files': len(files),
            'total_lines': total_lines,
            'analyzed_path': str(path)
        }