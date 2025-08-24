from typing import Dict, List
from .code_parser import CodeParser
from .utils import Logger

class CodeAnalyzer:
    def __init__(self):
        self.parser = CodeParser()

    def analyze_repository(self, repo_data: Dict) -> Dict:
        files = repo_data['analysis']['files']
        Logger.info(f"Analyzing {len(files)} files")
        
        parsed_files = []
        summary_stats = {
            'total_functions': 0,
            'total_classes': 0,
            'total_imports': 0,
            'languages': {},
            'complexity_distribution': {'High': 0, 'Medium': 0, 'Low': 0}
        }
        
        for file_info in files:
            parsed_file = self.parser.parse_file(file_info)
            parsed_files.append(parsed_file)
            
            self._update_summary_stats(summary_stats, parsed_file)
        
        architecture_analysis = self._analyze_architecture(parsed_files)
        dependency_analysis = self._analyze_dependencies(parsed_files)
        
        return {
            'parsed_files': parsed_files,
            'summary': summary_stats,
            'architecture': architecture_analysis,
            'dependencies': dependency_analysis,
            'repo_info': repo_data.get('repo_info', {}),
            'recommendations': self._generate_recommendations(summary_stats, architecture_analysis)
        }

    def _update_summary_stats(self, stats: Dict, parsed_file: Dict):
        if 'parsing_error' in parsed_file:
            return
            
        stats['total_functions'] += len(parsed_file.get('functions', []))
        stats['total_classes'] += len(parsed_file.get('classes', []))
        stats['total_imports'] += len(parsed_file.get('imports', []))
        
        language = parsed_file.get('language', 'unknown')
        stats['languages'][language] = stats['languages'].get(language, 0) + 1
        
        complexity = parsed_file.get('complexity', {})
        maintainability = complexity.get('estimated_maintainability', 'Medium')
        stats['complexity_distribution'][maintainability] += 1

    def _analyze_architecture(self, parsed_files: List[Dict]) -> Dict:
        patterns = {
            'mvc': self._detect_mvc_pattern(parsed_files),
            'layered': self._detect_layered_architecture(parsed_files),
            'microservices': self._detect_microservices_pattern(parsed_files),
            'monolithic': self._detect_monolithic_pattern(parsed_files)
        }
        
        file_organization = self._analyze_file_organization(parsed_files)
        
        return {
            'patterns': patterns,
            'organization': file_organization,
            'entry_points': self._find_entry_points(parsed_files),
            'test_coverage': self._estimate_test_coverage(parsed_files)
        }

    def _analyze_dependencies(self, parsed_files: List[Dict]) -> Dict:
        all_imports = []
        import_frequency = {}
        
        for file in parsed_files:
            imports = file.get('imports', [])
            all_imports.extend(imports)
            
            for imp in imports:
                clean_import = self._clean_import_statement(imp)
                import_frequency[clean_import] = import_frequency.get(clean_import, 0) + 1
        
        external_deps = self._identify_external_dependencies(all_imports)
        internal_deps = self._identify_internal_dependencies(parsed_files)
        
        return {
            'external_dependencies': external_deps,
            'internal_dependencies': internal_deps,
            'most_used_imports': sorted(import_frequency.items(), key=lambda x: x[1], reverse=True)[:10],
            'dependency_graph': self._create_dependency_graph(parsed_files)
        }

    def _detect_mvc_pattern(self, files: List[Dict]) -> bool:
        paths = [f['path'].lower() for f in files]
        mvc_indicators = ['model', 'view', 'controller', 'routes', 'handlers']
        return sum(1 for indicator in mvc_indicators if any(indicator in path for path in paths)) >= 2

    def _detect_layered_architecture(self, files: List[Dict]) -> bool:
        paths = [f['path'].lower() for f in files]
        layer_indicators = ['service', 'repository', 'dao', 'controller', 'business', 'domain']
        return sum(1 for indicator in layer_indicators if any(indicator in path for path in paths)) >= 2

    def _detect_microservices_pattern(self, files: List[Dict]) -> bool:
        paths = [f['path'].lower() for f in files]
        microservice_indicators = ['service', 'api', 'gateway', 'config', 'docker']
        return sum(1 for indicator in microservice_indicators if any(indicator in path for path in paths)) >= 3

    def _detect_monolithic_pattern(self, files: List[Dict]) -> bool:
        return len(files) > 20 and not self._detect_microservices_pattern(files)

    def _analyze_file_organization(self, files: List[Dict]) -> Dict:
        directories = {}
        for file in files:
            path_parts = file['path'].split('/')
            if len(path_parts) > 1:
                directory = path_parts[0]
                directories[directory] = directories.get(directory, 0) + 1
        
        return {
            'directory_structure': directories,
            'depth': max(len(f['path'].split('/')) for f in files) if files else 0,
            'organization_score': len(directories) / len(files) if files else 0
        }

    def _find_entry_points(self, files: List[Dict]) -> List[str]:
        entry_points = []
        
        for file in files:
            structure = file.get('structure', {})
            if structure.get('has_main', False):
                entry_points.append(file['path'])
            
            path = file['path'].lower()
            if any(name in path for name in ['main', 'index', 'app', 'server']):
                entry_points.append(file['path'])
        
        return list(set(entry_points))

    def _estimate_test_coverage(self, files: List[Dict]) -> Dict:
        test_files = []
        regular_files = []
        
        for file in files:
            path = file['path'].lower()
            structure = file.get('structure', {})
            
            if (any(test_word in path for test_word in ['test', 'spec']) or 
                structure.get('has_tests', False)):
                test_files.append(file)
            else:
                regular_files.append(file)
        
        coverage_ratio = len(test_files) / max(len(regular_files), 1)
        
        return {
            'test_files': len(test_files),
            'regular_files': len(regular_files),
            'coverage_ratio': coverage_ratio,
            'coverage_level': 'High' if coverage_ratio > 0.5 else 'Medium' if coverage_ratio > 0.2 else 'Low'
        }

    def _clean_import_statement(self, import_stmt: str) -> str:
        import_stmt = import_stmt.strip()
        
        if import_stmt.startswith('from'):
            parts = import_stmt.split()
            if len(parts) >= 2:
                return parts[1]
        elif import_stmt.startswith('import'):
            parts = import_stmt.split()
            if len(parts) >= 2:
                return parts[1].split('.')[0]
        elif import_stmt.startswith('#include'):
            return import_stmt.split('<')[1].split('>')[0] if '<' in import_stmt else import_stmt.split('"')[1] if '"' in import_stmt else import_stmt
        
        return import_stmt.split()[0] if import_stmt.split() else import_stmt

    def _identify_external_dependencies(self, imports: List[str]) -> List[str]:
        external_patterns = [
            'numpy', 'pandas', 'requests', 'flask', 'django', 'react', 'express',
            'lodash', 'axios', 'moment', 'jquery', 'bootstrap', 'tensorflow',
            'pytorch', 'opencv', 'matplotlib', 'spring', 'hibernate'
        ]
        
        external_deps = []
        for imp in imports:
            clean_imp = self._clean_import_statement(imp).lower()
            for pattern in external_patterns:
                if pattern in clean_imp:
                    external_deps.append(clean_imp)
                    break
        
        return list(set(external_deps))[:10]

    def _identify_internal_dependencies(self, files: List[Dict]) -> List[Dict]:
        internal_deps = []
        file_names = {f['path'].split('/')[-1].split('.')[0] for f in files}
        
        for file in files:
            file_deps = []
            imports = file.get('imports', [])
            
            for imp in imports:
                clean_imp = self._clean_import_statement(imp)
                if any(name in clean_imp for name in file_names):
                    file_deps.append(clean_imp)
            
            if file_deps:
                internal_deps.append({
                    'file': file['path'],
                    'dependencies': file_deps[:5]
                })
        
        return internal_deps[:10]

    def _create_dependency_graph(self, files: List[Dict]) -> Dict:
        graph = {}
        
        for file in files:
            file_path = file['path']
            imports = file.get('imports', [])
            
            graph[file_path] = {
                'imports': len(imports),
                'functions': len(file.get('functions', [])),
                'classes': len(file.get('classes', []))
            }
        
        return graph

    def _generate_recommendations(self, summary: Dict, architecture: Dict) -> List[str]:
        recommendations = []
        
        if summary['total_functions'] == 0:
            recommendations.append("Consider breaking down large code blocks into functions for better modularity")
        
        complexity_dist = summary['complexity_distribution']
        if complexity_dist['Low'] > complexity_dist['High'] + complexity_dist['Medium']:
            recommendations.append("Many files have low maintainability - consider refactoring complex functions")
        
        if architecture['test_coverage']['coverage_level'] == 'Low':
            recommendations.append("Add more test coverage to improve code reliability")
        
        if not architecture['entry_points']:
            recommendations.append("Consider adding clear entry points (main functions) to your application")
        
        if len(summary['languages']) > 5:
            recommendations.append("Multiple languages detected - ensure consistency in coding standards")
        
        return recommendations