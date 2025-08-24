#!/usr/bin/env python3

import unittest
import sys
import os
from unittest.mock import Mock, patch

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.config import Config
from src.code_parser import CodeParser
from src.utils import Logger, FileHelper
from src.github_analyzer import GitHubAnalyzer

class TestConfig(unittest.TestCase):
    def test_config_initialization(self):
        config = Config()
        self.assertIsNotNone(config.SUPPORTED_EXTENSIONS)
        self.assertIn('.py', config.SUPPORTED_EXTENSIONS)
        self.assertEqual(config.SUPPORTED_EXTENSIONS['.py'], 'python')

class TestCodeParser(unittest.TestCase):
    def setUp(self):
        self.parser = CodeParser()

    def test_extract_functions_python(self):
        content = """
def test_function():
    pass

def another_function(param1, param2):
    return param1 + param2
        """
        
        functions = self.parser.extract_functions(content, 'python')
        self.assertEqual(len(functions), 2)
        self.assertEqual(functions[0]['name'], 'test_function')
        self.assertEqual(functions[1]['name'], 'another_function')

    def test_extract_classes_python(self):
        content = """
class TestClass:
    def method1(self):
        pass

class AnotherClass(BaseClass):
    def method2(self):
        pass
        """
        
        classes = self.parser.extract_classes(content, 'python')
        self.assertEqual(len(classes), 2)
        self.assertEqual(classes[0]['name'], 'TestClass')
        self.assertEqual(classes[1]['name'], 'AnotherClass')

    def test_extract_imports_python(self):
        content = """
import os
import sys
from pathlib import Path
from typing import Dict, List
        """
        
        imports = self.parser.extract_imports(content, 'python')
        self.assertGreater(len(imports), 0)

    def test_calculate_complexity(self):
        content = """
def complex_function():
    if True:
        for i in range(10):
            while i > 0:
                if i % 2 == 0:
                    pass
        """
        
        complexity = self.parser.calculate_complexity(content, 'python')
        self.assertIsInstance(complexity, dict)
        self.assertIn('total_lines', complexity)
        self.assertIn('cyclomatic_complexity', complexity)

class TestFileHelper(unittest.TestCase):
    def test_is_valid_repo_url(self):
        valid_urls = [
            'https://github.com/user/repo',
            'git@github.com:user/repo.git'
        ]
        
        invalid_urls = [
            'https://gitlab.com/user/repo',
            'not-a-url',
            ''
        ]
        
        for url in valid_urls:
            self.assertTrue(FileHelper.is_valid_repo_url(url))
        
        for url in invalid_urls:
            self.assertFalse(FileHelper.is_valid_repo_url(url))

    def test_get_repo_name_from_url(self):
        url = 'https://github.com/user/repo'
        result = FileHelper.get_repo_name_from_url(url)
        self.assertEqual(result, 'user/repo')
        
        url_with_git = 'https://github.com/user/repo.git'
        result = FileHelper.get_repo_name_from_url(url_with_git)
        self.assertEqual(result, 'user/repo')

class TestGitHubAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = GitHubAnalyzer()

    def test_analyze_codebase_current_directory(self):
        result = self.analyzer.analyze_codebase('.')
        
        self.assertIsInstance(result, dict)
        self.assertIn('files', result)
        self.assertIn('language_stats', result)
        self.assertIn('total_files', result)
        
        # Should find at least our Python files
        self.assertGreater(result['total_files'], 0)
        if result['language_stats']:
            self.assertIn('python', result['language_stats'])

    @patch('requests.Session.get')
    def test_get_repo_info_success(self, mock_get):
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'name': 'test-repo',
            'description': 'A test repository',
            'language': 'Python',
            'stargazers_count': 10,
            'forks_count': 5
        }
        mock_get.return_value = mock_response
        
        result = self.analyzer.get_repo_info('https://github.com/user/test-repo')
        
        self.assertEqual(result['name'], 'test-repo')
        self.assertEqual(result['description'], 'A test repository')
        self.assertEqual(result['language'], 'Python')

    @patch('requests.Session.get')
    def test_get_repo_info_failure(self, mock_get):
        # Mock failed API response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        result = self.analyzer.get_repo_info('https://github.com/user/nonexistent-repo')
        
        self.assertEqual(result, {})

class TestIntegration(unittest.TestCase):
    """Integration tests for core functionality"""
    
    def test_full_analysis_pipeline(self):
        """Test the complete analysis pipeline on current project"""
        from src.repository_manager import RepositoryManager
        from src.code_analyzer import CodeAnalyzer
        
        # Test repository processing
        repo_manager = RepositoryManager()
        repo_data = repo_manager.process_repository('.')
        
        self.assertIsNotNone(repo_data)
        self.assertIn('analysis', repo_data)
        
        # Test code analysis
        code_analyzer = CodeAnalyzer()
        analysis_results = code_analyzer.analyze_repository(repo_data)
        
        self.assertIsInstance(analysis_results, dict)
        self.assertIn('summary', analysis_results)
        self.assertIn('parsed_files', analysis_results)
        
        summary = analysis_results['summary']
        self.assertIn('total_functions', summary)
        self.assertIn('total_classes', summary)
        self.assertIn('languages', summary)

def run_tests():
    """Run all tests with detailed output"""
    print("🧪 Running Code Documentation Assistant Tests\n")
    
    # Create test suite
    test_classes = [
        TestConfig,
        TestCodeParser,
        TestFileHelper,
        TestGitHubAnalyzer,
        TestIntegration
    ]
    
    suite = unittest.TestSuite()
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"📊 Test Results:")
    print(f"   ✅ Tests run: {result.testsRun}")
    print(f"   ❌ Failures: {len(result.failures)}")
    print(f"   🚫 Errors: {len(result.errors)}")
    
    if result.failures:
        print(f"\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"   - {test}: {traceback.split(chr(10))[-2]}")
    
    if result.errors:
        print(f"\n🚫 ERRORS:")
        for test, traceback in result.errors:
            print(f"   - {test}: {traceback.split(chr(10))[-2]}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\n🎯 Overall: {'SUCCESS' if success else 'FAILED'}")
    
    return success

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)