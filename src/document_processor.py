import os
import json
from typing import List, Dict
from sentence_transformers import SentenceTransformer
import PyPDF2
import streamlit as st

class DocumentProcessor:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """Initialize document processor with sentence transformer model"""
        try:
            self.model = SentenceTransformer(model_name)
        except Exception as e:
            st.error(f"Error loading sentence transformer model: {e}")
            raise
        self.supported_extensions = {'.txt', '.pdf'}
    
    def load_documents(self, documents_path: str) -> List[Dict]:
        """Load all documents from the specified directory"""
        documents = []
        
        if not os.path.exists(documents_path):
            st.warning(f"Documents directory '{documents_path}' not found.")
            return documents
        
        for root, _, filenames in os.walk(documents_path):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                file_ext = os.path.splitext(filename)[1].lower()
                
                if file_ext in self.supported_extensions:
                    try:
                        content = self._read_file(file_path, file_ext)
                        if content.strip():
                            documents.append({
                                'id': len(documents),
                                'filename': filename,
                                'content': content,
                                'path': file_path
                            })
                            st.success(f"✅ Loaded: {filename}")
                    except Exception as e:
                        st.error(f"❌ Failed to load {filename}: {str(e)}")
        
        return documents
    
    def _read_file(self, file_path: str, file_ext: str) -> str:
        """Read content from a file based on its extension"""
        if file_ext == '.txt':
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                return file.read()
        
        elif file_ext == '.pdf':
            content = ""
import os
import json
from typing import List, Dict
from sentence_transformers import SentenceTransformer
import PyPDF2
import streamlit as st

class DocumentProcessor:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """Initialize document processor with sentence transformer model"""
        try:
            self.model = SentenceTransformer(model_name)
        except Exception as e:
            st.error(f"Error loading sentence transformer model: {e}")
            raise
        self.supported_extensions = {'.txt', '.pdf'}
    
    def load_documents(self, documents_path: str) -> List[Dict]:
        """Load all documents from the specified directory"""
        documents = []
        
        if not os.path.exists(documents_path):
            st.warning(f"Documents directory '{documents_path}' not found.")
            return documents
        
        for root, _, filenames in os.walk(documents_path):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                file_ext = os.path.splitext(filename)[1].lower()
                
                if file_ext in self.supported_extensions:
                    try:
                        content = self._read_file(file_path, file_ext)
                        if content.strip():
                            documents.append({
                                'id': len(documents),
                                'filename': filename,
                                'content': content,
                                'path': file_path
                            })
                            st.success(f"✅ Loaded: {filename}")
                    except Exception as e:
                        st.error(f"❌ Failed to load {filename}: {str(e)}")
        
        return documents
    
    def _read_file(self, file_path: str, file_ext: str) -> str:
        """Read content from a file based on its extension"""
        if file_ext == '.txt':
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                return file.read()
        
        elif file_ext == '.pdf':
            content = ""
            try:
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        content += page.extract_text() + "\n"
                return content
            except Exception as e:
                st.error(f"Error reading PDF {file_path}: {str(e)}")
                return ""
        
        return ""
    
    def generate_embeddings(self, documents: List[Dict]) -> List:
        """Generate embeddings for all documents"""
        if not documents:
            return []
        
        texts = [doc['content'] for doc in documents]
        
        try:
            with st.spinner("Generating document embeddings..."):
                embeddings = self.model.encode(texts)
            return embeddings.tolist()
        except Exception as e:
            st.error(f"Error generating embeddings: {e}")
            return []
    
    def encode_query(self, query: str):
        """Encode a single query"""
        try:
            return self.model.encode([query])[0]
        except Exception as e:
            st.error(f"Error encoding query: {e}")
            return None