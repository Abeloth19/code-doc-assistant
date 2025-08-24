#!/usr/bin/env python3

import sys
import os

# Add parent directory to path to import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.config import Config
from src.repository_manager import RepositoryManager
from src.code_analyzer import CodeAnalyzer
from src.documentation_generator import DocumentationGenerator
from src.rag_system import RAGSystem

def example_basic_usage():
    """
    Example: Basic usage of the Code Documentation Assistant
    """
    print("🤖 Code Documentation Assistant - Basic Example")
    
    # Initialize components
    config = Config()
    try:
        config.validate()
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("Please set OPENAI_API_KEY in your .env file")
        return
    
    repo_manager = RepositoryManager()
    code_analyzer = CodeAnalyzer()
    doc_generator = DocumentationGenerator()
    
    # Analyze current project
    print("\n📊 Analyzing current project...")
    repo_data = repo_manager.process_repository('.')
    
    if not repo_data:
        print("❌ Failed to analyze repository")
        return
    
    analysis_results = code_analyzer.analyze_repository(repo_data)
    
    # Print basic statistics
    summary = analysis_results.get('summary', {})
    print(f"✅ Analysis complete!")
    print(f"   📁 Files: {len(analysis_results.get('parsed_files', []))}")
    print(f"   🔧 Functions: {summary.get('total_functions', 0)}")
    print(f"   🏗️ Classes: {summary.get('total_classes', 0)}")
    print(f"   🌐 Languages: {list(summary.get('languages', {}).keys())}")
    
    # Generate project overview
    print("\n📝 Generating documentation...")
    overview = doc_generator.generate_project_overview(analysis_results)
    print("✅ Documentation generated!")
    
    # Save to file
    with open('example_overview.md', 'w') as f:
        f.write(overview)
    print("💾 Saved overview to: example_overview.md")
    
    # Cleanup
    repo_manager.cleanup(repo_data)

def example_rag_usage():
    """
    Example: Using the RAG system for Q&A
    """
    print("\n🧠 Testing RAG Q&A System")
    
    config = Config()
    try:
        config.validate()
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        return
    
    # Analyze project
    repo_manager = RepositoryManager()
    code_analyzer = CodeAnalyzer()
    doc_generator = DocumentationGenerator()
    
    repo_data = repo_manager.process_repository('.')
    analysis_results = code_analyzer.analyze_repository(repo_data)
    
    # Generate some documentation
    documentation = {
        'project_overview': doc_generator.generate_project_overview(analysis_results)
    }
    
    # Build RAG system
    print("🔗 Building knowledge base...")
    rag_system = RAGSystem()
    rag_system.add_documents(analysis_results, documentation)
    
    # Test questions
    test_questions = [
        "What is this project about?",
        "What programming languages are used?",
        "What are the main functions?"
    ]
    
    for question in test_questions:
        print(f"\n❓ Question: {question}")
        result = rag_system.answer_question(question)
        answer = result.get('answer', 'No answer available')
        confidence = result.get('confidence', 'unknown')
        
        print(f"💬 Answer ({confidence} confidence):")
        print(f"   {answer[:200]}...")
    
    # Cleanup
    repo_manager.cleanup(repo_data)

def example_file_analysis():
    """
    Example: Detailed file analysis
    """
    print("\n🔍 File Analysis Example")
    
    from src.code_parser import CodeParser
    from src.github_analyzer import GitHubAnalyzer
    
    # Analyze a specific file
    analyzer = GitHubAnalyzer()
    result = analyzer.analyze_codebase('.')
    
    if not result['files']:
        print("❌ No files found to analyze")
        return
    
    # Parse the first Python file found
    parser = CodeParser()
    python_files = [f for f in result['files'] if f['language'] == 'python']
    
    if python_files:
        file_info = python_files[0]
        print(f"\n📄 Analyzing: {file_info['path']}")
        
        parsed = parser.parse_file(file_info)
        
        print(f"   🔧 Functions: {len(parsed.get('functions', []))}")
        print(f"   🏗️ Classes: {len(parsed.get('classes', []))}")
        print(f"   📦 Imports: {len(parsed.get('imports', []))}")
        print(f"   💬 Comments: {len(parsed.get('comments', []))}")
        
        complexity = parsed.get('complexity', {})
        print(f"   📊 Complexity: {complexity.get('estimated_maintainability', 'Unknown')}")
        print(f"   📏 Lines: {complexity.get('total_lines', 0)}")

if __name__ == '__main__':
    print("🚀 Running Code Documentation Assistant Examples\n")
    
    try:
        example_basic_usage()
        example_file_analysis()
        example_rag_usage()
        
        print("\n🎉 All examples completed successfully!")
        
    except KeyboardInterrupt:
        print("\n⏹️ Examples interrupted by user")
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")