import openai
from typing import Dict, List, Optional
from .config import Config
from .utils import Logger

class DocumentationGenerator:
    def __init__(self):
        self.config = Config()
        self.client = None
        if self.config.OPENAI_API_KEY:
            self.client = openai.OpenAI(api_key=self.config.OPENAI_API_KEY)
        else:
            Logger.warning("OpenAI API key not found - documentation generation will use fallback mode")

    def generate_file_documentation(self, parsed_file: Dict) -> str:
        if 'parsing_error' in parsed_file:
            return f"Unable to generate documentation due to parsing error: {parsed_file['parsing_error']}"
        
        prompt = self._create_file_documentation_prompt(parsed_file)
        
        if not self.client:
            return self._generate_fallback_documentation(parsed_file)
        
        try:
            Logger.info(f"Generating documentation for {parsed_file['path']}")
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert technical writer. Generate clear, comprehensive documentation for code files. Focus on purpose, functionality, and usage patterns."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1200,
                temperature=0.2
            )
            
            documentation = response.choices[0].message.content.strip()
            Logger.success(f"Generated documentation for {parsed_file['path']}")
            return documentation
            
        except Exception as e:
            Logger.error(f"Error generating documentation for {parsed_file['path']}: {e}")
            return f"Error generating documentation: {str(e)}"

    def generate_project_overview(self, analysis_results: Dict) -> str:
        prompt = self._create_overview_prompt(analysis_results)
        
        try:
            Logger.info("Generating project overview documentation")
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert technical writer and software architect. Generate comprehensive project documentation that explains the codebase architecture, patterns, and structure."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.2
            )
            
            overview = response.choices[0].message.content.strip()
            Logger.success("Generated project overview")
            return overview
            
        except Exception as e:
            Logger.error(f"Error generating project overview: {e}")
            return f"Error generating project overview: {str(e)}"

    def generate_api_documentation(self, analysis_results: Dict) -> str:
        all_functions = []
        all_classes = []
        
        for file_analysis in analysis_results.get('parsed_files', []):
            all_functions.extend(file_analysis.get('functions', []))
            all_classes.extend(file_analysis.get('classes', []))
        
        if not all_functions and not all_classes:
            return "No public API functions or classes found for documentation."
        
        prompt = self._create_api_documentation_prompt(all_functions[:20], all_classes[:10])
        
        try:
            Logger.info("Generating API documentation")
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert API documentation writer. Generate clear, structured API documentation with usage examples."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1800,
                temperature=0.2
            )
            
            api_docs = response.choices[0].message.content.strip()
            Logger.success("Generated API documentation")
            return api_docs
            
        except Exception as e:
            Logger.error(f"Error generating API documentation: {e}")
            return f"Error generating API documentation: {str(e)}"

    def generate_setup_guide(self, analysis_results: Dict) -> str:
        languages = analysis_results.get('summary', {}).get('languages', {})
        dependencies = analysis_results.get('dependencies', {}).get('external_dependencies', [])
        entry_points = analysis_results.get('architecture', {}).get('entry_points', [])
        
        prompt = self._create_setup_guide_prompt(languages, dependencies, entry_points)
        
        try:
            Logger.info("Generating setup guide")
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert technical writer. Generate a comprehensive setup and installation guide for developers."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.2
            )
            
            setup_guide = response.choices[0].message.content.strip()
            Logger.success("Generated setup guide")
            return setup_guide
            
        except Exception as e:
            Logger.error(f"Error generating setup guide: {e}")
            return f"Error generating setup guide: {str(e)}"

    def _create_file_documentation_prompt(self, parsed_file: Dict) -> str:
        functions_summary = self._format_functions_for_prompt(parsed_file.get('functions', []))
        classes_summary = self._format_classes_for_prompt(parsed_file.get('classes', []))
        imports = parsed_file.get('imports', [])[:10]
        complexity = parsed_file.get('complexity', {})
        
        return f"""
Generate comprehensive documentation for this code file:

**FILE**: {parsed_file['path']}
**LANGUAGE**: {parsed_file['language']}

**FUNCTIONS** ({len(parsed_file.get('functions', []))} total):
{functions_summary}

**CLASSES** ({len(parsed_file.get('classes', []))} total):
{classes_summary}

**KEY IMPORTS**:
{chr(10).join(imports) if imports else 'None'}

**COMPLEXITY METRICS**:
- Lines of code: {complexity.get('code_lines', 0)}
- Cyclomatic complexity: {complexity.get('cyclomatic_complexity', 0)}
- Maintainability: {complexity.get('estimated_maintainability', 'Unknown')}

**REQUIREMENTS**:
Generate documentation including:
1. **Purpose**: What this file does and its role in the project
2. **Key Components**: Main functions and classes with their responsibilities
3. **Dependencies**: Important imports and their purposes
4. **Usage**: How this file is typically used or called
5. **Notes**: Any important implementation details or patterns

Keep it concise but comprehensive. Use markdown formatting.
        """

    def _create_overview_prompt(self, analysis_results: Dict) -> str:
        summary = analysis_results.get('summary', {})
        architecture = analysis_results.get('architecture', {})
        dependencies = analysis_results.get('dependencies', {})
        repo_info = analysis_results.get('repo_info', {})
        
        return f"""
Generate a comprehensive project overview for this codebase:

**PROJECT**: {repo_info.get('name', 'Unknown Project')}
**DESCRIPTION**: {repo_info.get('description', 'No description available')}

**CODE STATISTICS**:
- Total files: {len(analysis_results.get('parsed_files', []))}
- Languages: {dict(summary.get('languages', {}))}
- Functions: {summary.get('total_functions', 0)}
- Classes: {summary.get('total_classes', 0)}
- External dependencies: {len(dependencies.get('external_dependencies', []))}

**ARCHITECTURE ANALYSIS**:
- Detected patterns: {architecture.get('patterns', {})}
- Entry points: {architecture.get('entry_points', [])}
- Test coverage: {architecture.get('test_coverage', {}).get('coverage_level', 'Unknown')}

**RECOMMENDATIONS**:
{chr(10).join('- ' + rec for rec in analysis_results.get('recommendations', []))}

**REQUIREMENTS**:
Generate documentation including:
1. **Project Overview**: Purpose and main functionality
2. **Architecture**: Overall structure and design patterns
3. **Technology Stack**: Languages, frameworks, and key dependencies
4. **Project Structure**: Directory organization and key modules
5. **Getting Started**: Basic setup and usage instructions
6. **Development Notes**: Important patterns or conventions used

Use markdown formatting with clear sections and headers.
        """

    def _create_api_documentation_prompt(self, functions: List[Dict], classes: List[Dict]) -> str:
        functions_detail = self._format_functions_detailed(functions)
        classes_detail = self._format_classes_detailed(classes)
        
        return f"""
Generate API documentation for the following code elements:

**FUNCTIONS** ({len(functions)} shown):
{functions_detail}

**CLASSES** ({len(classes)} shown):
{classes_detail}

**REQUIREMENTS**:
Generate API documentation including:
1. **Function Reference**: Each function with parameters, return values, and purpose
2. **Class Reference**: Each class with methods and attributes
3. **Usage Examples**: Basic code examples where helpful
4. **Parameter Details**: Types and descriptions where inferrable
5. **Return Values**: What each function/method returns

Use markdown formatting with clear sections. Focus on public/main functions and classes.
        """

    def _create_setup_guide_prompt(self, languages: Dict, dependencies: List[str], entry_points: List[str]) -> str:
        return f"""
Generate a setup and installation guide for this project:

**LANGUAGES USED**: {list(languages.keys())}
**EXTERNAL DEPENDENCIES**: {dependencies}
**ENTRY POINTS**: {entry_points}

**REQUIREMENTS**:
Generate a setup guide including:
1. **Prerequisites**: Required software and versions
2. **Installation**: Step-by-step installation instructions
3. **Configuration**: Any required configuration steps
4. **Running the Project**: How to start/run the application
5. **Development Setup**: Additional steps for development
6. **Troubleshooting**: Common issues and solutions

Use markdown formatting with clear step-by-step instructions.
        """

    def _format_functions_for_prompt(self, functions: List[Dict]) -> str:
        if not functions:
            return "None"
        
        formatted = []
        for func in functions[:10]:
            name = func.get('name', 'Unknown')
            signature = func.get('signature', '').replace('\n', ' ')[:100]
            lines = func.get('estimated_lines', 0)
            formatted.append(f"- {name}: {signature}... ({lines} lines)")
        
        if len(functions) > 10:
            formatted.append(f"... and {len(functions) - 10} more functions")
        
        return '\n'.join(formatted)

    def _format_classes_for_prompt(self, classes: List[Dict]) -> str:
        if not classes:
            return "None"
        
        formatted = []
        for cls in classes[:5]:
            name = cls.get('name', 'Unknown')
            methods = cls.get('methods', [])
            method_count = len(methods)
            formatted.append(f"- {name}: {method_count} methods")
        
        if len(classes) > 5:
            formatted.append(f"... and {len(classes) - 5} more classes")
        
        return '\n'.join(formatted)

    def _format_functions_detailed(self, functions: List[Dict]) -> str:
        if not functions:
            return "None"
        
        formatted = []
        for func in functions:
            name = func.get('name', 'Unknown')
            signature = func.get('signature', '').strip()
            body_preview = func.get('body_preview', '')[:150]
            formatted.append(f"""
**{name}**
- Signature: `{signature}`
- Preview: {body_preview}...
            """.strip())
        
        return '\n\n'.join(formatted)

    def _format_classes_detailed(self, classes: List[Dict]) -> str:
        if not classes:
            return "None"
        
        formatted = []
        for cls in classes:
            name = cls.get('name', 'Unknown')
            methods = cls.get('methods', [])
            signature = cls.get('signature', '').strip()
            
            methods_str = ', '.join(methods[:5])
            if len(methods) > 5:
                methods_str += f", ... and {len(methods) - 5} more"
            
            formatted.append(f"""
**{name}**
- Declaration: `{signature}`
- Methods: {methods_str if methods else 'None'}
            """.strip())
        
        return '\n\n'.join(formatted)

    def generate_full_documentation(self, analysis_results: Dict) -> Dict[str, str]:
        Logger.info("Generating complete project documentation")
        
        documentation = {
            'project_overview': self.generate_project_overview(analysis_results),
            'api_documentation': self.generate_api_documentation(analysis_results),
            'setup_guide': self.generate_setup_guide(analysis_results),
            'file_documentation': {}
        }
        
        # Generate documentation for key files (limit to avoid API costs)
        parsed_files = analysis_results.get('parsed_files', [])
        important_files = self._identify_important_files(parsed_files)
        
        for file_data in important_files[:5]:
            file_path = file_data['path']
            documentation['file_documentation'][file_path] = self.generate_file_documentation(file_data)
        
        Logger.success("Generated complete documentation suite")
        return documentation

    def _identify_important_files(self, parsed_files: List[Dict]) -> List[Dict]:
        scored_files = []
        
        for file_data in parsed_files:
            score = 0
            path = file_data.get('path', '').lower()
            
            # Score based on path importance
            if any(keyword in path for keyword in ['main', 'index', 'app', 'server', 'core']):
                score += 10
            if any(keyword in path for keyword in ['config', 'settings', 'setup']):
                score += 5
            
            # Score based on content
            functions = len(file_data.get('functions', []))
            classes = len(file_data.get('classes', []))
            score += functions * 2 + classes * 3
            
            # Avoid test files and very simple files
            if 'test' in path or (functions == 0 and classes == 0):
                score -= 5
            
            scored_files.append((score, file_data))
        
        # Sort by score and return top files
        scored_files.sort(key=lambda x: x[0], reverse=True)
        return [file_data for score, file_data in scored_files if score > 0]

    def _generate_fallback_documentation(self, parsed_file: Dict) -> str:
        """Generate basic documentation without AI when API key is not available"""
        path = parsed_file['path']
        language = parsed_file['language']
        functions = parsed_file.get('functions', [])
        classes = parsed_file.get('classes', [])
        imports = parsed_file.get('imports', [])
        complexity = parsed_file.get('complexity', {})
        
        doc = f"""# {path}

**Language:** {language}

## Overview
This {language} file contains {len(functions)} functions and {len(classes)} classes.

## Functions
"""
        
        if functions:
            for func in functions[:10]:
                doc += f"- `{func.get('name', 'Unknown')}` (line {func.get('line', '?')})\n"
        else:
            doc += "No functions found.\n"
        
        doc += "\n## Classes\n"
        if classes:
            for cls in classes:
                doc += f"- `{cls.get('name', 'Unknown')}` (line {cls.get('line', '?')})\n"
        else:
            doc += "No classes found.\n"
        
        if imports:
            doc += f"\n## Dependencies\n"
            for imp in imports[:10]:
                doc += f"- {imp}\n"
        
        doc += f"""
## Code Metrics
- Total lines: {complexity.get('total_lines', 0)}
- Code lines: {complexity.get('code_lines', 0)}
- Estimated maintainability: {complexity.get('estimated_maintainability', 'Unknown')}

*Note: This documentation was generated without AI. Add an OpenAI API key for enhanced documentation.*
"""
        
        return doc