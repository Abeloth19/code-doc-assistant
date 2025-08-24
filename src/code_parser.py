import ast
import re
from typing import Dict, List, Any, Optional
from pathlib import Path
from .utils import Logger

class CodeParser:
    def __init__(self):
        self.function_patterns = {
            'python': r'def\s+(\w+)\s*\([^)]*\):',
            'javascript': r'(?:function\s+(\w+)\s*\(|(?:const|let|var)\s+(\w+)\s*=\s*(?:function|\([^)]*\)\s*=>))',
            'typescript': r'(?:function\s+(\w+)\s*\(|(?:const|let|var)\s+(\w+)\s*:\s*[^=]*=\s*(?:function|\([^)]*\)\s*=>))',
            'java': r'(?:public|private|protected)?\s*(?:static)?\s*(?:final)?\s*\w+\s+(\w+)\s*\([^)]*\)\s*(?:throws\s+\w+(?:,\s*\w+)*)?\s*{',
            'cpp': r'(?:[\w:]+\s+)?(\w+)\s*\([^)]*\)\s*(?:const)?\s*{',
            'c': r'(?:[\w\s*]+\s+)?(\w+)\s*\([^)]*\)\s*{',
            'go': r'func\s+(?:\(\w+\s+\*?\w+\)\s+)?(\w+)\s*\([^)]*\)',
            'rust': r'fn\s+(\w+)\s*\([^)]*\)',
            'php': r'(?:public|private|protected)?\s*(?:static)?\s*function\s+(\w+)\s*\(',
            'ruby': r'def\s+(\w+)\s*(?:\([^)]*\))?',
            'swift': r'func\s+(\w+)\s*\([^)]*\)',
            'kotlin': r'(?:fun\s+(\w+)\s*\(|(?:public|private|protected)?\s*fun\s+(\w+)\s*\()'
        }
        
        self.class_patterns = {
            'python': r'class\s+(\w+)\s*(?:\([^)]*\))?:',
            'javascript': r'class\s+(\w+)(?:\s+extends\s+\w+)?',
            'typescript': r'(?:export\s+)?class\s+(\w+)(?:\s+extends\s+\w+)?(?:\s+implements\s+[\w,\s]+)?',
            'java': r'(?:public|private|protected)?\s*(?:abstract|final)?\s*class\s+(\w+)(?:\s+extends\s+\w+)?(?:\s+implements\s+[\w,\s]+)?',
            'cpp': r'class\s+(\w+)(?:\s*:\s*(?:public|private|protected)\s+\w+)?',
            'c': r'(?:typedef\s+)?struct\s+(\w+)',
            'go': r'type\s+(\w+)\s+struct',
            'rust': r'(?:pub\s+)?struct\s+(\w+)',
            'php': r'(?:abstract\s+)?class\s+(\w+)(?:\s+extends\s+\w+)?',
            'ruby': r'class\s+(\w+)(?:\s*<\s*\w+)?',
            'swift': r'(?:public|private|internal)?\s*(?:final\s+)?class\s+(\w+)(?:\s*:\s*[\w,\s]+)?',
            'kotlin': r'(?:open|final|abstract)?\s*class\s+(\w+)(?:\s*:\s*[\w,\s()]+)?'
        }

        self.import_patterns = {
            'python': r'(?:from\s+[\w.]+\s+)?import\s+[\w.,\s*]+',
            'javascript': r'import\s+.*?from\s+[\'"][^\'"]+[\'"]|require\([\'"][^\'"]+[\'"]\)',
            'typescript': r'import\s+.*?from\s+[\'"][^\'"]+[\'"]',
            'java': r'import\s+(?:static\s+)?[\w.]+(?:\.\*)?;',
            'cpp': r'#include\s*[<"][^>"]+[>"]',
            'c': r'#include\s*[<"][^>"]+[>"]',
            'go': r'import\s+(?:\(\s*)?[\'"][^\'"]+[\'"](?:\s*\))?',
            'rust': r'use\s+[\w:]+(?:\s*as\s+\w+)?;',
            'php': r'(?:require|include)(?:_once)?\s+[\'"][^\'"]+[\'"];|use\s+[\w\\]+(?:\s+as\s+\w+)?;',
            'ruby': r'require\s+[\'"][^\'"]+[\'"]',
            'swift': r'import\s+\w+',
            'kotlin': r'import\s+[\w.]+(?:\.\*)?'
        }

    def parse_file(self, file_info: Dict) -> Dict:
        content = file_info['content']
        language = file_info['language']
        path = file_info['path']
        
        Logger.info(f"Parsing {language} file: {path}")
        
        try:
            analysis = {
                'path': path,
                'language': language,
                'functions': self.extract_functions(content, language),
                'classes': self.extract_classes(content, language),
                'imports': self.extract_imports(content, language),
                'comments': self.extract_comments(content, language),
                'variables': self.extract_variables(content, language),
                'complexity': self.calculate_complexity(content, language),
                'structure': self.analyze_structure(content, language),
                'docstrings': self.extract_docstrings(content, language)
            }
            
            return analysis
            
        except Exception as e:
            Logger.error(f"Error parsing file {path}: {e}")
            return self._create_error_analysis(path, language, str(e))

    def extract_functions(self, content: str, language: str) -> List[Dict]:
        functions = []
        pattern = self.function_patterns.get(language, '')
        
        if not pattern:
            return functions
            
        try:
            matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)
            
            for match in matches:
                func_name = None
                for group in match.groups():
                    if group:
                        func_name = group
                        break
                
                if func_name and not func_name.startswith('_'):
                    line_num = content[:match.start()].count('\n') + 1
                    signature = match.group(0).strip()
                    
                    func_body = self._extract_function_body(content, match.end(), language)
                    
                    functions.append({
                        'name': func_name,
                        'line': line_num,
                        'signature': signature,
                        'body_preview': func_body[:200] + '...' if len(func_body) > 200 else func_body,
                        'estimated_lines': len(func_body.split('\n')) if func_body else 1
                    })
        except Exception as e:
            Logger.warning(f"Error extracting functions for {language}: {e}")
            
        return functions

    def extract_classes(self, content: str, language: str) -> List[Dict]:
        classes = []
        pattern = self.class_patterns.get(language, '')
        
        if not pattern:
            return classes
            
        try:
            matches = re.finditer(pattern, content, re.MULTILINE)
            
            for match in matches:
                class_name = match.group(1)
                line_num = content[:match.start()].count('\n') + 1
                
                methods = self._extract_class_methods(content, match.end(), language)
                
                classes.append({
                    'name': class_name,
                    'line': line_num,
                    'signature': match.group(0).strip(),
                    'methods': methods,
                    'method_count': len(methods)
                })
        except Exception as e:
            Logger.warning(f"Error extracting classes for {language}: {e}")
            
        return classes

    def extract_imports(self, content: str, language: str) -> List[str]:
        imports = []
        pattern = self.import_patterns.get(language, '')
        
        if pattern:
            try:
                matches = re.findall(pattern, content, re.MULTILINE)
                imports = [match.strip() for match in matches if match.strip()]
            except Exception as e:
                Logger.warning(f"Error extracting imports for {language}: {e}")
        
        return imports[:20]

    def extract_comments(self, content: str, language: str) -> List[Dict]:
        comments = []
        
        comment_patterns = {
            'python': r'#.*$',
            'javascript': r'//.*$|/\*[\s\S]*?\*/',
            'typescript': r'//.*$|/\*[\s\S]*?\*/',
            'java': r'//.*$|/\*[\s\S]*?\*/',
            'cpp': r'//.*$|/\*[\s\S]*?\*/',
            'c': r'//.*$|/\*[\s\S]*?\*/',
            'go': r'//.*$|/\*[\s\S]*?\*/',
            'rust': r'//.*$|/\*[\s\S]*?\*/',
            'php': r'//.*$|/\*[\s\S]*?\*/|#.*$',
            'ruby': r'#.*$',
            'swift': r'//.*$|/\*[\s\S]*?\*/',
            'kotlin': r'//.*$|/\*[\s\S]*?\*/'
        }
        
        pattern = comment_patterns.get(language, '')
        if pattern:
            try:
                matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)
                for match in matches:
                    comment_text = match.group(0).strip()
                    if len(comment_text) > 3:
                        line_num = content[:match.start()].count('\n') + 1
                        comments.append({
                            'text': comment_text,
                            'line': line_num,
                            'type': 'single' if comment_text.startswith(('/', '#')) else 'multi'
                        })
            except Exception as e:
                Logger.warning(f"Error extracting comments for {language}: {e}")
        
        return comments[:10]

    def extract_variables(self, content: str, language: str) -> List[str]:
        variable_patterns = {
            'python': r'(\w+)\s*=\s*(?!def|class)',
            'javascript': r'(?:const|let|var)\s+(\w+)',
            'typescript': r'(?:const|let|var)\s+(\w+)',
            'java': r'(?:public|private|protected)?\s*(?:static)?\s*(?:final)?\s*\w+\s+(\w+)\s*[=;]',
            'cpp': r'(?:int|float|double|char|string|bool|auto)\s+(\w+)',
            'go': r'(?:var\s+(\w+)|(\w+)\s*:=)',
            'rust': r'let\s+(?:mut\s+)?(\w+)'
        }
        
        variables = []
        pattern = variable_patterns.get(language, '')
        
        if pattern:
            try:
                matches = re.findall(pattern, content)
                for match in matches:
                    var_name = match if isinstance(match, str) else next(m for m in match if m)
                    if var_name and not var_name.startswith('_'):
                        variables.append(var_name)
            except Exception as e:
                Logger.warning(f"Error extracting variables for {language}: {e}")
        
        return list(set(variables))[:15]

    def calculate_complexity(self, content: str, language: str) -> Dict:
        lines = content.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        
        control_patterns = r'\b(if|for|while|switch|case|try|catch|except|elif|else)\b'
        control_structures = len(re.findall(control_patterns, content))
        
        return {
            'total_lines': len(lines),
            'code_lines': len(non_empty_lines),
            'blank_lines': len(lines) - len(non_empty_lines),
            'cyclomatic_complexity': control_structures,
            'estimated_maintainability': self._estimate_maintainability(len(non_empty_lines), control_structures)
        }

    def analyze_structure(self, content: str, language: str) -> Dict:
        return {
            'has_main': 'main' in content.lower(),
            'has_tests': any(test_word in content.lower() for test_word in ['test', 'spec', 'assert']),
            'has_documentation': len(re.findall(r'"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'|/\*\*[\s\S]*?\*/', content)) > 0,
            'indentation_style': 'tabs' if '\t' in content else 'spaces',
            'avg_line_length': sum(len(line) for line in content.split('\n')) / len(content.split('\n')) if content.split('\n') else 0
        }

    def extract_docstrings(self, content: str, language: str) -> List[Dict]:
        docstrings = []
        
        if language == 'python':
            pattern = r'"""([\s\S]*?)"""|\'\'\'([\s\S]*?)\'\'\''
            matches = re.finditer(pattern, content)
            
            for match in matches:
                docstring = match.group(1) or match.group(2)
                if docstring and len(docstring.strip()) > 10:
                    line_num = content[:match.start()].count('\n') + 1
                    docstrings.append({
                        'content': docstring.strip(),
                        'line': line_num,
                        'length': len(docstring.strip())
                    })
        
        return docstrings[:5]

    def _extract_function_body(self, content: str, start_pos: int, language: str) -> str:
        try:
            remaining_content = content[start_pos:]
            if language == 'python':
                lines = remaining_content.split('\n')
                body_lines = []
                indent_level = None
                
                for line in lines:
                    if line.strip():
                        current_indent = len(line) - len(line.lstrip())
                        if indent_level is None and line.strip():
                            indent_level = current_indent
                        elif indent_level is not None and current_indent <= indent_level and line.strip():
                            break
                    body_lines.append(line)
                    
                return '\n'.join(body_lines[:10])
            else:
                brace_count = 0
                body = []
                for char in remaining_content:
                    body.append(char)
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            break
                    if len(body) > 500:
                        break
                
                return ''.join(body)
        except:
            return ""

    def _extract_class_methods(self, content: str, start_pos: int, language: str) -> List[str]:
        try:
            class_content = content[start_pos:start_pos + 1000]
            methods = []
            
            if language == 'python':
                method_pattern = r'def\s+(\w+)\s*\('
            else:
                method_pattern = self.function_patterns.get(language, '')
                
            if method_pattern:
                matches = re.findall(method_pattern, class_content)
                methods = [match for match in matches if isinstance(match, str)][:5]
                
            return methods
        except:
            return []

    def _estimate_maintainability(self, code_lines: int, complexity: int) -> str:
        score = max(0, 100 - (code_lines // 10) - (complexity * 3))
        
        if score >= 80:
            return "High"
        elif score >= 60:
            return "Medium"
        else:
            return "Low"

    def _create_error_analysis(self, path: str, language: str, error: str) -> Dict:
        return {
            'path': path,
            'language': language,
            'functions': [],
            'classes': [],
            'imports': [],
            'comments': [],
            'variables': [],
            'complexity': {'total_lines': 0, 'code_lines': 0, 'cyclomatic_complexity': 0},
            'structure': {},
            'docstrings': [],
            'parsing_error': error
        }