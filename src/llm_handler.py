import os
import google.generativeai as genai
from typing import Optional
import streamlit as st

class LLMHandler:
    def __init__(self):
        """Initialize Google Gemini client"""
        self.api_key = os.getenv('GOOGLE_API_KEY')
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            self.client_initialized = True
        else:
            self.client_initialized = False
            st.warning("⚠️ Google API key not found. LLM responses will be limited.")
    
    def generate_response(self, query: str, document_context: str = "", stock_data: str = "") -> str:
        """Generate response using Google Gemini"""
        if not self.client_initialized:
            return self._fallback_response(query, document_context, stock_data)
        
        try:
            # Construct the prompt
            system_prompt = """You are a helpful financial assistant with access to financial documents and real-time stock data. 
            Provide accurate, informative, and well-structured responses to financial queries. 
            When relevant, include specific numbers, trends, and insights from the provided context.
            Keep responses concise but comprehensive, and always cite your sources when using specific data points."""
            
            user_prompt = self._construct_user_prompt(query, document_context, stock_data)
            
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            # Make API call
            response = self.model.generate_content(full_prompt)
            
            return response.text.strip()
            
        except Exception as e:
            st.error(f"Error generating LLM response: {e}")
            return self._fallback_response(query, document_context, stock_data)
    
    def _construct_user_prompt(self, query: str, document_context: str, stock_data: str) -> str:
        """Construct the user prompt with context"""
        prompt_parts = [f"User Query: {query}"]
        
        if document_context.strip():
            prompt_parts.append(f"\nRelevant Financial Documents:\n{document_context}")
        
        if stock_data.strip():
            prompt_parts.append(f"\nReal-time Stock Data:\n{stock_data}")
        
        prompt_parts.append("\nPlease provide a comprehensive answer based on the available information.")
        
        return "\n".join(prompt_parts)
    
    def _fallback_response(self, query: str, document_context: str, stock_data: str) -> str:
        """Provide fallback response when API is not available"""
        response_parts = []
        
        # Basic query analysis
        query_lower = query.lower()
        
        if any(keyword in query_lower for keyword in ['stock', 'price', 'market', 'trend']):
            response_parts.append("📈 **Stock Analysis Request Detected**")
            
            if stock_data:
                response_parts.append("\n**Current Stock Information:**")
                response_parts.append(stock_data)
            else:
                response_parts.append("\nI can help you with stock analysis. Please specify a stock symbol (e.g., AAPL, MSFT) for detailed information.")
        
        elif any(keyword in query_lower for keyword in ['earnings', 'revenue', 'financial', 'report']):
            response_parts.append("📊 **Financial Report Analysis Request**")
            
            if document_context:
                response_parts.append("\n**Relevant Information from Financial Documents:**")
                # Extract key sentences from context
                sentences = document_context.split('\n')[:5]  # First 5 lines
                for sentence in sentences:
                    if sentence.strip() and len(sentence) > 20:
                        response_parts.append(f"• {sentence.strip()}")
        
        else:
            response_parts.append("🔍 **Financial Query Processing**")
            response_parts.append("I've analyzed your query and found relevant information.")
        
        # Add document context if available
        if document_context and not any(keyword in query_lower for keyword in ['earnings', 'revenue', 'financial']):
            response_parts.append("\n**Related Financial Information:**")
            key_lines = [line for line in document_context.split('\n')[:3] if line.strip() and len(line) > 15]
            for line in key_lines:
                response_parts.append(f"• {line.strip()}")
        
        # Add helpful note
        response_parts.append("\n*Note: For more detailed AI-powered analysis, please configure the Google API key.*")
        
        return "\n".join(response_parts)
    
    def summarize_documents(self, documents: list) -> str:
        """Summarize multiple documents"""
        if not self.client_initialized or not documents:
            return "Document summarization requires Google API key configuration."
        
        try:
            # Prepare document content
            doc_content = "\n\n".join([f"Document: {doc.get('filename', 'Unknown')}\n{doc.get('content', '')[:1000]}" 
                                     for doc in documents[:3]])  # Limit to first 3 docs
            
            prompt = f"Summarize the key financial information from these documents concisely:\n\n{doc_content}"
            
            response = self.model.generate_content(prompt)
            
            return response.text.strip()
            
        except Exception as e:
            st.error(f"Error summarizing documents: {e}")
            return "Unable to generate document summary."
    
    def analyze_stock_sentiment(self, stock_data: str, news_context: str = "") -> str:
        """Analyze stock sentiment from data and news"""
        if not self.client_initialized:
            return "Sentiment analysis requires Google API key configuration."
        
        try:
            prompt = f"""Analyze the sentiment and outlook for this stock based on the following information:

Stock Data:
{stock_data}

Additional Context:
{news_context}

Provide a brief sentiment analysis (Bullish/Bearish/Neutral) with reasoning."""

            response = self.model.generate_content(prompt)
            
            return response.text.strip()
            
        except Exception as e:
            st.error(f"Error analyzing stock sentiment: {e}")
            return "Unable to generate sentiment analysis."
    
    def check_api_status(self) -> dict:
        """Check Google API status and configuration"""
        if not self.api_key:
            return {
                "status": "not_configured",
                "message": "Google API key not found in environment variables"
            }
        
        if not self.client_initialized:
            return {
                "status": "client_error",
                "message": "Google Gemini client initialization failed"
            }
        
        try:
            # Test API with a simple request
            response = self.model.generate_content("test")
            
            return {
                "status": "active",
                "message": "Google Gemini API is configured and working",
                "model": "gemini-1.5-flash"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"API test failed: {str(e)}"
            }