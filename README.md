# 🤖 Code Documentation Assistant

> **AI-powered documentation generation and intelligent Q&A for any codebase**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![OpenAI](https://img.shields.io/badge/powered%20by-OpenAI-green.svg)](https://openai.com/)
[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

An intelligent assistant that analyzes codebases, generates comprehensive documentation, and answers questions about your code using advanced AI and retrieval-augmented generation (RAG).

## ✨ Features

- 🔍 **Multi-language Analysis** - Support for Python, JavaScript, TypeScript, Java, C++, Go, Rust, and more
- 📝 **AI Documentation Generation** - Comprehensive docs using OpenAI GPT models
- 🤖 **Interactive Q&A** - Ask questions about your codebase with intelligent answers
- 🏗️ **Architecture Detection** - Identifies design patterns and project structure
- 📊 **Code Quality Metrics** - Complexity analysis and maintainability scoring
- 🎨 **Beautiful CLI** - Rich, interactive command-line interface
- 🔗 **RAG System** - Advanced search and question-answering capabilities
- 📁 **Flexible Input** - GitHub repositories or local directories

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd code-doc-assistant

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env

# Add your OpenAI API key to .env
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Usage

**Interactive Mode** (Recommended):
```bash
python main.py --interactive
```

**Quick Analysis**:
```bash
# Analyze GitHub repository
python main.py --repo https://github.com/user/repo

# Analyze local directory
python main.py --local /path/to/project

# Batch mode with custom output
python main.py --local . --batch --output my_docs
```

## 🎯 Usage Examples

### Interactive Mode
```bash
python main.py --interactive
```
- Beautiful CLI with progress bars and rich formatting
- Step-by-step guidance through analysis and documentation
- Interactive Q&A session with your codebase

### Batch Processing
```bash
python main.py --repo https://github.com/facebook/react --batch
```
Generates complete documentation suite automatically.

### Testing the Tool
```bash
# Run comprehensive tests
python tests/test_basic.py

# Try the examples
python examples/example_usage.py
```

