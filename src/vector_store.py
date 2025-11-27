import faiss
import numpy as np
from typing import List, Dict, Tuple
import streamlit as st

class VectorStore:
    def __init__(self):
        """Initialize FAISS vector store"""
        self.index = None
        self.documents = []
        self.dimension = None
    
    def build_index(self, embeddings: List, documents: List[Dict]):
        """Build FAISS index from embeddings and store documents"""
        if not embeddings or not documents:
            st.warning("No embeddings or documents provided for indexing")
            return
        
        try:
            # Convert embeddings to numpy array
            embeddings_array = np.array(embeddings, dtype=np.float32)
            self.dimension = embeddings_array.shape[1]
            
            # Create FAISS index
            self.index = faiss.IndexFlatL2(self.dimension)
            self.index.add(embeddings_array)
            
            # Store documents
            self.documents = documents
            
            st.success(f"✅ Built FAISS index with {len(documents)} documents")
            st.info(f"📐 Embedding dimension: {self.dimension}")
            
        except Exception as e:
            st.error(f"Error building FAISS index: {e}")
            raise
    
    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> List[Tuple[int, float]]:
        """Search for similar documents using query embedding"""
        if self.index is None:
            st.error("Index not built. Please build the index first.")
            return []
        
        try:
            # Ensure query embedding is the right shape and type
            if isinstance(query_embedding, list):
                query_embedding = np.array(query_embedding, dtype=np.float32)
            
            if len(query_embedding.shape) == 1:
                query_embedding = query_embedding.reshape(1, -1)
            
            # Search the index
            distances, indices = self.index.search(query_embedding, min(top_k, len(self.documents)))
            
            # Return results as (index, distance) tuples
            results = []
            for i, (idx, distance) in enumerate(zip(indices[0], distances[0])):
                if idx != -1:  # Valid result
                    results.append((int(idx), float(distance)))
            
            return results
            
        except Exception as e:
            st.error(f"Error searching index: {e}")
            return []
    
    def get_document(self, doc_id: int) -> Dict:
        """Retrieve document by ID"""
        if 0 <= doc_id < len(self.documents):
            return self.documents[doc_id]
        return {}
    
    def get_documents_by_indices(self, indices: List[int]) -> List[Dict]:
        """Retrieve multiple documents by their indices"""
        documents = []
        for idx in indices:
            if 0 <= idx < len(self.documents):
                documents.append(self.documents[idx])
        return documents
    
    def get_index_stats(self) -> Dict:
        """Get statistics about the index"""
        if self.index is None:
            return {"status": "Index not built"}
        
        return {
            "status": "Active",
            "total_documents": len(self.documents),
            "dimension": self.dimension,
            "index_type": "FAISS IndexFlatL2",
            "is_trained": self.index.is_trained,
            "ntotal": self.index.ntotal
        }
    
    def rebuild_index(self, embeddings: List, documents: List[Dict]):
        """Rebuild the index with new data"""
        st.info("Rebuilding FAISS index...")
        self.build_index(embeddings, documents)
    
    def add_documents(self, embeddings: List, documents: List[Dict]):
        """Add new documents to existing index"""
        if self.index is None:
            st.warning("No existing index found. Building new index...")
            self.build_index(embeddings, documents)
            return
        
        try:
            # Convert new embeddings to numpy array
            embeddings_array = np.array(embeddings, dtype=np.float32)
            
            # Add to existing index
            self.index.add(embeddings_array)
            
            # Update document store
            start_id = len(self.documents)
            for i, doc in enumerate(documents):
                doc['id'] = start_id + i
            
            self.documents.extend(documents)
            
            st.success(f"✅ Added {len(documents)} new documents to index")
            
        except Exception as e:
            st.error(f"Error adding documents to index: {e}")
            raise