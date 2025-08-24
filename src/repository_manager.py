import json
from pathlib import Path
from typing import Dict, Optional
from .config import Config
from .utils import Logger
from .github_analyzer import GitHubAnalyzer

class RepositoryManager:
    def __init__(self):
        self.config = Config()
        self.github_analyzer = GitHubAnalyzer()
        self.cache_file = self.config.DATA_DIR / "repo_cache.json"

    def process_repository(self, source: str, use_cache: bool = True) -> Optional[Dict]:
        cache_key = self._get_cache_key(source)
        
        if use_cache:
            cached_data = self._load_from_cache(cache_key)
            if cached_data:
                Logger.info("Using cached repository data")
                return cached_data
        
        Logger.info(f"Processing repository: {source}")
        
        if source.startswith(('http', 'git@')):
            return self._process_remote_repository(source, cache_key)
        else:
            return self._process_local_repository(source, cache_key)

    def _process_remote_repository(self, repo_url: str, cache_key: str) -> Optional[Dict]:
        repo_info = self.github_analyzer.get_repo_info(repo_url)
        temp_dir = self.github_analyzer.clone_repository(repo_url)
        
        if not temp_dir:
            return None
            
        try:
            codebase_analysis = self.github_analyzer.analyze_codebase(temp_dir)
            
            result = {
                'source': repo_url,
                'type': 'remote',
                'repo_info': repo_info,
                'analysis': codebase_analysis,
                'temp_dir': temp_dir
            }
            
            self._save_to_cache(cache_key, result)
            return result
            
        except Exception as e:
            Logger.error(f"Error processing remote repository: {e}")
            return None

    def _process_local_repository(self, local_path: str, cache_key: str) -> Optional[Dict]:
        path = Path(local_path)
        if not path.exists():
            Logger.error(f"Local path does not exist: {local_path}")
            return None
            
        try:
            codebase_analysis = self.github_analyzer.analyze_codebase(str(path))
            
            result = {
                'source': local_path,
                'type': 'local',
                'repo_info': {'name': path.name},
                'analysis': codebase_analysis,
                'temp_dir': None
            }
            
            self._save_to_cache(cache_key, result)
            return result
            
        except Exception as e:
            Logger.error(f"Error processing local repository: {e}")
            return None

    def _get_cache_key(self, source: str) -> str:
        return source.replace('/', '_').replace(':', '_').replace('.', '_')

    def _load_from_cache(self, cache_key: str) -> Optional[Dict]:
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r') as f:
                    cache_data = json.load(f)
                    return cache_data.get(cache_key)
        except Exception as e:
            Logger.warning(f"Error loading cache: {e}")
        return None

    def _save_to_cache(self, cache_key: str, data: Dict):
        try:
            cache_data = {}
            if self.cache_file.exists():
                with open(self.cache_file, 'r') as f:
                    cache_data = json.load(f)
            
            data_to_cache = data.copy()
            data_to_cache.pop('temp_dir', None)
            cache_data[cache_key] = data_to_cache
            
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
                
            Logger.info("Repository data cached")
            
        except Exception as e:
            Logger.warning(f"Error saving to cache: {e}")

    def cleanup(self, repo_data: Dict):
        temp_dir = repo_data.get('temp_dir')
        if temp_dir:
            from .utils import FileHelper
            FileHelper.cleanup_temp_dir(temp_dir)
            Logger.info("Cleaned up temporary files")