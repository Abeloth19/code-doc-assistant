import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import Dict, List, Tuple, Optional
import pickle
import os
import openai
from .config import Config
from .utils import Logger

class RAGSystem:
    def __init__(self):
        self.config = Config()
        self.client = openai.OpenAI(api_key=self.config.OPENAI_API_KEY)
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            max_features=5000,
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.95
        )
        self.document_vectors = None
        self.documents = []
        self.metadata = []
        self.project_context = ""

    def add_documents(self, analysis_results: Dict, documentation: Dict[str, str]):
        Logger.info("Building RAG knowledge base")
        
        self.documents = []
        self.metadata = []
        self.project_context = self._build_project_context(analysis_results)
        
        # Add project overview
        if documentation.get('project_overview'):
            self.documents.append(documentation['project_overview'])
            self.metadata.append({
                'type': 'overview',
                'source': 'project_overview',
                'category': 'documentation'
            })
        
        # Add API documentation
        if documentation.get('api_documentation'):
            self.documents.append(documentation['api_documentation'])
            self.metadata.append({
                'type': 'api',
                'source': 'api_documentation',
                'category': 'documentation'
            })
        
        # Add setup guide
        if documentation.get('setup_guide'):
            self.documents.append(documentation['setup_guide'])
            self.metadata.append({
                'type': 'setup',
                'source': 'setup_guide',
                'category': 'documentation'
            })
        
        # Add individual file analyses
        for file_analysis in analysis_results.get('parsed_files', []):
            if 'parsing_error' in file_analysis:
                continue
                
            file_content = self._create_file_summary(file_analysis)
            self.documents.append(file_content)
            self.metadata.append({
                'type': 'file_analysis',
                'source': file_analysis['path'],
                'language': file_analysis['language'],
                'category': 'code'
            })
        
        # Add file-specific documentation
        for file_path, file_doc in documentation.get('file_documentation', {}).items():
            self.documents.append(file_doc)
            self.metadata.append({
                'type': 'file_documentation',
                'source': file_path,
                'category': 'documentation'
            })
        
        # Vectorize documents
        if self.documents:
            try:
                self.document_vectors = self.vectorizer.fit_transform(self.documents)
                Logger.success(f"Built knowledge base with {len(self.documents)} documents")
            except Exception as e:
                Logger.error(f"Error vectorizing documents: {e}")
                self.document_vectors = None
        else:
            Logger.warning("No documents to vectorize")

    def search(self, query: str, top_k: int = 5, min_similarity: float = 0.1) -> List[Tuple[str, float, Dict]]:
        if not self.document_vectors or not query.strip():
            return []
        
        try:
            query_vector = self.vectorizer.transform([query])
            similarities = cosine_similarity(query_vector, self.document_vectors)[0]
            
            # Fix numpy array issue
            similarities = np.array(similarities).flatten()
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            results = []
            for idx in top_indices:
                similarity_score = float(similarities[idx])
                if similarity_score > min_similarity:
                    results.append((
                        self.documents[idx],
                        similarity_score,
                        self.metadata[idx]
                    ))
            
            return results
            
        except Exception as e:
            Logger.error(f"Error in search: {e}")
            return []

    def answer_question(self, question: str, use_ai: bool = True) -> Dict:
        search_results = self.search(question, top_k=5)
        
        if not search_results:
            return {
                'answer': "I couldn't find relevant information to answer your question in the codebase.",
                'sources': [],
                'confidence': 'low'
            }
        
        # Check if we have OpenAI client
        if use_ai and hasattr(self, 'client') and self.client:
            return self._generate_ai_answer(question, search_results)
        else:
            return self._generate_simple_answer(question, search_results)

    def _generate_ai_answer(self, question: str, search_results: List[Tuple[str, float, Dict]]) -> Dict:
        context_parts = []
        sources = []
        
        for doc, score, metadata in search_results[:3]:
            source_info = f"Source: {metadata['source']} ({metadata['type']})"
            context_parts.append(f"{source_info}\n{doc[:800]}...")
            sources.append({
                'source': metadata['source'],
                'type': metadata['type'],
                'confidence': float(score)
            })
        
        context = "\n\n---\n\n".join(context_parts)
        
        prompt = f"""
You are a helpful code documentation assistant. Answer the user's question based on the provided context from the codebase analysis.

PROJECT CONTEXT:
{self.project_context}

RELEVANT CONTEXT:
{context}

USER QUESTION: {question}

Please provide a clear, helpful answer based on the context. If the context doesn't contain enough information, say so clearly. Focus on being accurate and cite which sources you're referencing.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert code documentation assistant. Provide clear, accurate answers based on the provided codebase context."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.3
            )
            
            answer = response.choices[0].message.content.strip()
            confidence = 'high' if search_results[0][1] > 0.5 else 'medium' if search_results[0][1] > 0.3 else 'low'
            
            return {
                'answer': answer,
                'sources': sources,
                'confidence': confidence
            }
            
        except Exception as e:
            Logger.error(f"Error generating AI answer: {e}")
            return self._generate_simple_answer(question, search_results)

    def _generate_simple_answer(self, question: str, search_results: List[Tuple[str, float, Dict]]) -> Dict:
        sources = []
        answer_parts = []
        
        for doc, score, metadata in search_results[:3]:
            sources.append({
                'source': metadata['source'],
                'type': metadata['type'],
                'confidence': float(score)
            })
            
            preview = doc[:300] + "..." if len(doc) > 300 else doc
            answer_parts.append(f"**From {metadata['source']}**: {preview}")
        
        answer = f"Based on the codebase analysis, here are the most relevant findings for your question:\n\n" + \
                "\n\n".join(answer_parts)
        
        confidence = 'high' if search_results[0][1] > 0.4 else 'medium' if search_results[0][1] > 0.25 else 'low'
        
        return {
            'answer': answer,
            'sources': sources,
            'confidence': confidence
        }

    def get_suggestions(self, partial_query: str = "") -> List[str]:
        suggestions = [
            "What is the main purpose of this project?",
            "How do I set up and install this project?",
            "What are the key functions in this codebase?",
            "What programming languages are used?",
            "What external dependencies does this project use?",
            "How is the project structured?",
            "Are there any tests in this project?",
            "What design patterns are used?",
            "How do I run this application?",
            "What are the main classes and their purposes?"
        ]
        
        if partial_query:
            # Simple filtering based on partial query
            filtered = [s for s in suggestions if any(word.lower() in s.lower() for word in partial_query.split())]
            return filtered[:5] if filtered else suggestions[:5]
        
        return suggestions[:5]

    def _create_file_summary(self, file_analysis: Dict) -> str:
        path = file_analysis['path']
        language = file_analysis['language']
        functions = file_analysis.get('functions', [])
        classes = file_analysis.get('classes', [])
        imports = file_analysis.get('imports', [])
        complexity = file_analysis.get('complexity', {})
        
        summary_parts = [
            f"File: {path} (Language: {language})",
            f"Lines of code: {complexity.get('code_lines', 0)}",
            f"Complexity: {complexity.get('estimated_maintainability', 'Unknown')}"
        ]
        
        if functions:
            func_names = [f['name'] for f in functions[:5]]
            summary_parts.append(f"Functions: {', '.join(func_names)}")
            if len(functions) > 5:
                summary_parts.append(f"... and {len(functions) - 5} more functions")
        
        if classes:
            class_names = [c['name'] for c in classes[:3]]
            summary_parts.append(f"Classes: {', '.join(class_names)}")
            if len(classes) > 3:
                summary_parts.append(f"... and {len(classes) - 3} more classes")
        
        if imports:
            summary_parts.append(f"Key imports: {', '.join(imports[:5])}")
        
        return ' | '.join(summary_parts)

    def _build_project_context(self, analysis_results: Dict) -> str:
        summary = analysis_results.get('summary', {})
        repo_info = analysis_results.get('repo_info', {})
        
        context_parts = [
            f"Project: {repo_info.get('name', 'Unknown')}",
            f"Languages: {list(summary.get('languages', {}).keys())}",
            f"Total files: {len(analysis_results.get('parsed_files', []))}",
            f"Functions: {summary.get('total_functions', 0)}",
            f"Classes: {summary.get('total_classes', 0)}"
        ]
        
        if repo_info.get('description'):
            context_parts.insert(1, f"Description: {repo_info['description']}")
        
        return " | ".join(context_parts)

    def save_index(self, filepath: str):
        try:
            data = {
                'vectorizer': self.vectorizer,
                'document_vectors': self.document_vectors,
                'documents': self.documents,
                'metadata': self.metadata,
                'project_context': self.project_context
            }
            with open(filepath, 'wb') as f:
                pickle.dump(data, f)
            Logger.success(f"RAG index saved to {filepath}")
        except Exception as e:
            Logger.error(f"Failed to save RAG index: {e}")

    def load_index(self, filepath: str) -> bool:
        try:
            if os.path.exists(filepath):
                with open(filepath, 'rb') as f:
                    data = pickle.load(f)
                    self.vectorizer = data['vectorizer']
                    self.document_vectors = data['document_vectors']
                    self.documents = data['documents']
                    self.metadata = data['metadata']
                    self.project_context = data.get('project_context', '')
                Logger.success(f"RAG index loaded from {filepath}")
                return True
        except Exception as e:
            Logger.error(f"Failed to load RAG index: {e}")
        return False