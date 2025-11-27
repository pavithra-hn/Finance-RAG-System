from typing import List, Dict
import streamlit as st
from sentence_transformers import SentenceTransformer

class QueryProcessor:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """Initialize query processor with the same model as document processor"""
        try:
            self.model = SentenceTransformer(model_name)
        except Exception as e:
            st.error(f"Error loading query processing model: {e}")
            raise
    
    def encode_query(self, query: str):
        """Encode a query into embedding"""
        try:
            return self.model.encode([query])[0]
        except Exception as e:
            st.error(f"Error encoding query: {e}")
            return None
    
    def retrieve_documents(self, query: str, vector_store, top_k: int = 5) -> List[Dict]:
        """Retrieve most relevant documents for a query"""
        try:
            # Encode the query
            query_embedding = self.encode_query(query)
            
            if query_embedding is None:
                return []
            
            # Search vector store
            search_results = vector_store.search(query_embedding, top_k)
            
            if not search_results:
                st.warning("No relevant documents found")
                return []
            
            # Retrieve documents and add similarity scores
            retrieved_docs = []
            for doc_idx, distance in search_results:
                doc = vector_store.get_document(doc_idx)
                if doc:
                    # Convert L2 distance to similarity score (lower distance = higher similarity)
                    similarity_score = 1.0 / (1.0 + distance)
                    doc_with_score = doc.copy()
                    doc_with_score['similarity_score'] = similarity_score
                    doc_with_score['distance'] = distance
                    retrieved_docs.append(doc_with_score)
            
            # Sort by similarity score (highest first)
            retrieved_docs.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            return retrieved_docs
            
        except Exception as e:
            st.error(f"Error retrieving documents: {e}")
            return []
    
    def filter_documents_by_threshold(self, documents: List[Dict], threshold: float = 0.3) -> List[Dict]:
        """Filter documents by similarity threshold"""
        return [doc for doc in documents if doc.get('similarity_score', 0) >= threshold]
    
    def prepare_context(self, documents: List[Dict], max_length: int = 2000) -> str:
        """Prepare context string from retrieved documents"""
        if not documents:
            return ""
        
        context_parts = []
        current_length = 0
        
        for doc in documents:
            doc_content = f"Document: {doc['filename']}\n{doc['content']}\n---\n"
            
            if current_length + len(doc_content) > max_length and context_parts:
                break
            
            context_parts.append(doc_content)
            current_length += len(doc_content)
        
        return "\n".join(context_parts)
    
    def get_query_type(self, query: str) -> str:
        """Determine the type of query to better handle it"""
        query_lower = query.lower()
        
        # Stock-related keywords
        stock_keywords = ['stock', 'share', 'price', 'ticker', 'market', 'trading', 
                         'volume', 'chart', 'performance', 'trend']
        
        # Financial analysis keywords
        analysis_keywords = ['earnings', 'revenue', 'profit', 'financial', 'report',
                           'quarterly', 'annual', 'balance sheet', 'income statement']
        
        # Comparison keywords
        comparison_keywords = ['compare', 'vs', 'versus', 'difference', 'better',
                             'against', 'contrast']
        
        if any(keyword in query_lower for keyword in stock_keywords):
            return "stock_query"
        elif any(keyword in query_lower for keyword in analysis_keywords):
            return "financial_analysis"
        elif any(keyword in query_lower for keyword in comparison_keywords):
            return "comparison"
        else:
            return "general"
    
    def enhance_query(self, query: str, query_type: str) -> str:
        """Enhance query based on its type for better retrieval"""
        enhancements = {
            "stock_query": "stock price market performance trading",
            "financial_analysis": "financial earnings revenue profit report",
            "comparison": "comparison analysis performance metrics",
            "general": "financial analysis report"
        }
        
        enhancement = enhancements.get(query_type, "")
        return f"{query} {enhancement}".strip()
    
    def get_retrieval_summary(self, documents: List[Dict]) -> Dict:
        """Get summary of retrieval results"""
        if not documents:
            return {"total": 0, "sources": [], "avg_similarity": 0}
        
        sources = [doc['filename'] for doc in documents]
        similarities = [doc.get('similarity_score', 0) for doc in documents]
        
        return {
            "total": len(documents),
            "sources": sources,
            "avg_similarity": sum(similarities) / len(similarities) if similarities else 0,
            "min_similarity": min(similarities) if similarities else 0,
            "max_similarity": max(similarities) if similarities else 0
        }