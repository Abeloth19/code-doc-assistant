import os
from pathlib import Path
from typing import Dict, List
from datetime import datetime
from .config import Config
from .utils import Logger

class DocumentationFormatter:
    def __init__(self):
        self.config = Config()

    def format_documentation_suite(self, documentation: Dict[str, str], analysis_results: Dict) -> Dict[str, str]:
        Logger.info("Formatting documentation suite")
        
        formatted_docs = {}
        
        # Main README
        formatted_docs['README.md'] = self._create_main_readme(documentation, analysis_results)
        
        # API Documentation
        if documentation.get('api_documentation'):
            formatted_docs['docs/API.md'] = self._format_api_docs(documentation['api_documentation'])
        
        # Setup Guide
        if documentation.get('setup_guide'):
            formatted_docs['docs/SETUP.md'] = self._format_setup_guide(documentation['setup_guide'])
        
        # Architecture Overview
        if documentation.get('project_overview'):
            formatted_docs['docs/ARCHITECTURE.md'] = self._format_architecture_docs(documentation['project_overview'])
        
        # File Documentation Index
        if documentation.get('file_documentation'):
            formatted_docs['docs/FILES.md'] = self._create_file_index(documentation['file_documentation'])
            
            # Individual file docs
            for file_path, file_doc in documentation['file_documentation'].items():
                safe_filename = file_path.replace('/', '_').replace('.', '_')
                formatted_docs[f'docs/files/{safe_filename}.md'] = self._format_file_doc(file_path, file_doc)
        
        Logger.success(f"Formatted {len(formatted_docs)} documentation files")
        return formatted_docs

    def save_documentation(self, formatted_docs: Dict[str, str], output_dir: str = "generated_docs") -> List[str]:
        Logger.info(f"Saving documentation to {output_dir}")
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        saved_files = []
        
        for relative_path, content in formatted_docs.items():
            file_path = output_path / relative_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                saved_files.append(str(file_path))
                Logger.success(f"Saved: {relative_path}")
            except Exception as e:
                Logger.error(f"Failed to save {relative_path}: {e}")
        
        return saved_files

    def _create_main_readme(self, documentation: Dict[str, str], analysis_results: Dict) -> str:
        repo_info = analysis_results.get('repo_info', {})
        summary = analysis_results.get('summary', {})
        
        project_name = repo_info.get('name', 'Project')
        description = repo_info.get('description', 'A software project')
        
        # Extract key info from project overview
        overview_content = documentation.get('project_overview', '')
        
        readme_content = f"""# {project_name}

{description}

## Overview

{overview_content[:500]}...

## Quick Stats

- **Languages**: {', '.join(summary.get('languages', {}).keys())}
- **Files**: {len(analysis_results.get('parsed_files', []))} analyzed
- **Functions**: {summary.get('total_functions', 0)}
- **Classes**: {summary.get('total_classes', 0)}

## Documentation

- 📚 [Setup Guide](docs/SETUP.md) - Installation and configuration
- 🏗️ [Architecture](docs/ARCHITECTURE.md) - Project structure and design
- 🔧 [API Reference](docs/API.md) - Functions and classes
- 📁 [File Documentation](docs/FILES.md) - Individual file details

## Getting Started

See the [Setup Guide](docs/SETUP.md) for detailed installation instructions.

## Project Structure

```
{self._generate_tree_structure(analysis_results)}
```

---

*Documentation generated automatically by Code Documentation Assistant*
*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        return readme_content

    def _format_api_docs(self, api_documentation: str) -> str:
        return f"""# API Documentation

{api_documentation}

---

*This API documentation was generated automatically from code analysis.*
*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

    def _format_setup_guide(self, setup_guide: str) -> str:
        return f"""# Setup Guide

{setup_guide}

## Additional Notes

- Make sure all prerequisites are installed before proceeding
- Check the main README for project overview
- See API documentation for usage details

---

*This setup guide was generated automatically from project analysis.*
*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

    def _format_architecture_docs(self, architecture_overview: str) -> str:
        return f"""# Architecture Overview

{architecture_overview}

## Additional Analysis

This document provides insights into the project's structure, patterns, and design decisions based on automated code analysis.

---

*This architecture documentation was generated automatically.*
*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

    def _create_file_index(self, file_documentation: Dict[str, str]) -> str:
        content = f"""# File Documentation Index

This section contains detailed documentation for individual files in the project.

## Documented Files

"""
        
        for file_path in sorted(file_documentation.keys()):
            safe_filename = file_path.replace('/', '_').replace('.', '_')
            content += f"- [{file_path}](files/{safe_filename}.md)\n"
        
        content += f"""

---

*File documentation generated automatically from code analysis.*
*Total files documented: {len(file_documentation)}*
*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        return content

    def _format_file_doc(self, file_path: str, file_documentation: str) -> str:
        return f"""# {file_path}

{file_documentation}

---

*File documentation generated automatically from code analysis.*
*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

[← Back to File Index](../FILES.md)
"""

    def _generate_tree_structure(self, analysis_results: Dict) -> str:
        parsed_files = analysis_results.get('parsed_files', [])
        
        if not parsed_files:
            return "No files analyzed"
        
        # Build directory structure
        dirs = {}
        for file_data in parsed_files[:20]:  # Limit for readability
            path_parts = file_data['path'].split('/')
            
            current_level = dirs
            for part in path_parts[:-1]:
                if part not in current_level:
                    current_level[part] = {}
                current_level = current_level[part]
            
            # Add file
            filename = path_parts[-1]
            language = file_data.get('language', '')
            current_level[filename] = f"({language})"
        
        return self._format_tree(dirs, prefix="")

    def _format_tree(self, tree_dict: Dict, prefix: str = "", is_last: bool = True) -> str:
        if not tree_dict:
            return ""
        
        result = ""
        items = list(tree_dict.items())
        
        for i, (name, subtree) in enumerate(items):
            is_last_item = (i == len(items) - 1)
            
            # Current item
            connector = "└── " if is_last_item else "├── "
            result += f"{prefix}{connector}{name}"
            
            # If it's a file (has language info)
            if isinstance(subtree, str):
                result += f" {subtree}\n"
            else:
                result += "/\n"
                # Recurse for subdirectories
                next_prefix = prefix + ("    " if is_last_item else "│   ")
                result += self._format_tree(subtree, next_prefix, is_last_item)
        
        return result

    def create_summary_report(self, analysis_results: Dict) -> str:
        summary = analysis_results.get('summary', {})
        architecture = analysis_results.get('architecture', {})
        recommendations = analysis_results.get('recommendations', [])
        
        report = f"""# Project Analysis Summary

## Code Statistics
- **Total Files**: {len(analysis_results.get('parsed_files', []))}
- **Languages**: {dict(summary.get('languages', {}))}
- **Functions**: {summary.get('total_functions', 0)}
- **Classes**: {summary.get('total_classes', 0)}

## Architecture Patterns
{self._format_architecture_patterns(architecture.get('patterns', {}))}

## Code Quality
- **Test Coverage**: {architecture.get('test_coverage', {}).get('coverage_level', 'Unknown')}
- **Entry Points**: {len(architecture.get('entry_points', []))}
- **Complexity Distribution**: {dict(summary.get('complexity_distribution', {}))}

## Recommendations
{chr(10).join(f'- {rec}' for rec in recommendations)}

---
*Analysis completed on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        return report

    def _format_architecture_patterns(self, patterns: Dict) -> str:
        if not patterns:
            return "- No specific patterns detected"
        
        detected = [pattern for pattern, detected in patterns.items() if detected]
        if not detected:
            return "- No specific patterns detected"
        
        return '\n'.join(f'- **{pattern.upper()}**: Detected' for pattern in detected)