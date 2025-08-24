#!/usr/bin/env python3

import click
import os
import sys
from pathlib import Path
from typing import Optional

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.config import Config
from src.repository_manager import RepositoryManager
from src.code_analyzer import CodeAnalyzer
from src.documentation_generator import DocumentationGenerator
from src.doc_formatter import DocumentationFormatter
from src.rag_system import RAGSystem
from src.cli_interface import BeautifulCLI
from src.utils import Logger

class CodeDocumentationAssistant:
    def __init__(self):
        self.config = Config()
        self.cli = BeautifulCLI()
        self.repo_manager = RepositoryManager()
        self.code_analyzer = CodeAnalyzer()
        self.doc_generator = DocumentationGenerator()
        self.doc_formatter = DocumentationFormatter()
        self.rag_system = RAGSystem()
        
    def run_interactive(self):
        try:
            # Validate configuration
            self.config.validate()
        except ValueError as e:
            self.cli.show_error(f"Configuration error: {e}")
            self.cli.show_info("Please set OPENAI_API_KEY in your .env file")
            return
        
        self.cli.show_welcome()
        
        # Get repository source
        source_type, source_path = self.cli.get_repository_input()
        
        # Show analysis progress
        self.cli.show_analysis_progress()
        
        try:
            # Process repository
            repo_data = self.repo_manager.process_repository(source_path)
            if not repo_data:
                self.cli.show_error("Failed to analyze repository")
                return
            
            # Analyze code
            analysis_results = self.code_analyzer.analyze_repository(repo_data)
            
            # Show results
            self.cli.show_analysis_results(analysis_results)
            
            # Ask about documentation generation
            if self.cli.confirm_action("Would you like to generate documentation?"):
                doc_options = self.cli.show_documentation_options()
                
                if doc_options:
                    documentation = self._generate_documentation(analysis_results, doc_options)
                    formatted_docs = self.doc_formatter.format_documentation_suite(documentation, analysis_results)
                    doc_paths = self.doc_formatter.save_documentation(formatted_docs)
                    self.cli.show_documentation_generated(doc_paths)
                    documentation_generated = True
                else:
                    documentation = {}
                    documentation_generated = False
            else:
                documentation = {}
                documentation_generated = False
            
            # Interactive Q&A
            qa_sessions = 0
            if self.cli.confirm_action("Would you like to ask questions about the codebase?"):
                # Build RAG system
                with self.cli.console.status("[cyan]🔗 Building knowledge base...[/cyan]"):
                    self.rag_system.add_documents(analysis_results, documentation)
                
                self.cli.show_interactive_qa(self.rag_system)
                qa_sessions = 1
            
            # Show completion summary
            self.cli.show_completion_summary(analysis_results, documentation_generated, qa_sessions)
            
            # Cleanup
            self.repo_manager.cleanup(repo_data)
            
        except KeyboardInterrupt:
            self.cli.show_info("Operation cancelled by user")
        except Exception as e:
            self.cli.show_error(f"An error occurred: {str(e)}")
            Logger.error(f"Error in main execution: {e}")

    def _generate_documentation(self, analysis_results, doc_options):
        documentation = {}
        
        with self.cli.console.status("[cyan]📝 Generating documentation...[/cyan]"):
            if "overview" in doc_options:
                documentation['project_overview'] = self.doc_generator.generate_project_overview(analysis_results)
            
            if "api" in doc_options:
                documentation['api_documentation'] = self.doc_generator.generate_api_documentation(analysis_results)
            
            if "setup" in doc_options:
                documentation['setup_guide'] = self.doc_generator.generate_setup_guide(analysis_results)
            
            if "files" in doc_options:
                documentation['file_documentation'] = {}
                # Generate docs for top 3 important files
                parsed_files = analysis_results.get('parsed_files', [])
                important_files = self.doc_generator._identify_important_files(parsed_files)
                
                for file_data in important_files[:3]:
                    file_path = file_data['path']
                    documentation['file_documentation'][file_path] = self.doc_generator.generate_file_documentation(file_data)
        
        return documentation

    def run_batch(self, source_path: str, output_dir: str = "generated_docs"):
        try:
            self.config.validate()
            Logger.info(f"Starting batch analysis of: {source_path}")
            
            # Process repository
            repo_data = self.repo_manager.process_repository(source_path)
            if not repo_data:
                Logger.error("Failed to analyze repository")
                return False
            
            # Analyze code
            analysis_results = self.code_analyzer.analyze_repository(repo_data)
            Logger.success(f"Analyzed {len(analysis_results.get('parsed_files', []))} files")
            
            # Generate full documentation
            documentation = self.doc_generator.generate_full_documentation(analysis_results)
            
            # Format and save documentation
            formatted_docs = self.doc_formatter.format_documentation_suite(documentation, analysis_results)
            doc_paths = self.doc_formatter.save_documentation(formatted_docs, output_dir)
            
            Logger.success(f"Generated {len(doc_paths)} documentation files in {output_dir}")
            
            # Create RAG index for future Q&A
            self.rag_system.add_documents(analysis_results, documentation)
            rag_index_path = os.path.join(output_dir, "rag_index.pkl")
            self.rag_system.save_index(rag_index_path)
            
            # Cleanup
            self.repo_manager.cleanup(repo_data)
            
            return True
            
        except Exception as e:
            Logger.error(f"Batch processing failed: {e}")
            return False

@click.command()
@click.option('--repo', help='GitHub repository URL')
@click.option('--local', help='Local directory path')
@click.option('--output', default='generated_docs', help='Output directory for documentation')
@click.option('--batch', is_flag=True, help='Run in batch mode (no interaction)')
@click.option('--interactive', is_flag=True, help='Run in interactive mode')
def main(repo: Optional[str], local: Optional[str], output: str, batch: bool, interactive: bool):
    """
    🤖 Code Documentation Assistant
    
    Analyze codebases and generate comprehensive documentation using AI.
    """
    
    assistant = CodeDocumentationAssistant()
    
    # Determine mode
    if batch and (repo or local):
        source_path = repo or local
        success = assistant.run_batch(source_path, output)
        sys.exit(0 if success else 1)
    
    elif interactive or (not repo and not local):
        assistant.run_interactive()
    
    elif repo or local:
        source_path = repo or local
        assistant.run_batch(source_path, output)
    
    else:
        click.echo("Please specify --repo, --local, or run with --interactive")
        sys.exit(1)

if __name__ == '__main__':
    main()