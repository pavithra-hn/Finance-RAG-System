import streamlit as st
import os
import time
import uuid
import shutil
from pathlib import Path
from dotenv import load_dotenv
import plotly.graph_objects as go

# Import custom modules
from src.document_processor import DocumentProcessor
from src.vector_store import VectorStore
from src.query_processor import QueryProcessor
from src.stock_data import StockDataHandler
from src.llm_handler import LLMHandler
from src.utils import is_stock_query, extract_stock_symbols

# Load environment variables
load_dotenv()

# Paths and supported file types
DOCUMENTS_DIR = "documents"
UPLOADS_DIR = os.path.join(DOCUMENTS_DIR, "uploads")
SUPPORTED_FILE_EXTENSIONS = {".pdf", ".txt"}
SUPPORTED_FILE_TYPES = ["pdf", "txt"]

# Page configuration
st.set_page_config(
    page_title="Finance RAG System",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        color: #1a1a1a;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #1976d2;
        color: #0f1c2e;
    }
    .bot-message {
        background-color: #f1f8e9;
        border-left: 4px solid #388e3c;
        color: #1a1a1a;
    }
    .sidebar-content {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
    }
    .chat-message strong {
        color: inherit;
    }
</style>
""", unsafe_allow_html=True)



def handle_file_upload(system):
    """Callback to handle file uploads only when the uploader state changes."""
    uploaded_files = st.session_state.documents_uploader
    if uploaded_files:
        saved_files = []
        for file in uploaded_files:
            try:
                destination = save_uploaded_file(file)
                saved_files.append(Path(destination).name)
            except Exception as e:
                st.error(f"Error saving {file.name}: {str(e)}")
        
        if saved_files:
            refresh_document_index(system)
            st.toast(f"✅ Stored {len(saved_files)} file(s): {', '.join(saved_files)}")


def ensure_document_directories():
    """Ensure base and upload directories exist."""
    os.makedirs(DOCUMENTS_DIR, exist_ok=True)
    os.makedirs(UPLOADS_DIR, exist_ok=True)


def save_uploaded_file(uploaded_file):
    """Persist an uploaded file to the backend storage."""
    file_ext = Path(uploaded_file.name).suffix.lower()
    if file_ext not in SUPPORTED_FILE_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {file_ext}")
    
    safe_stem = Path(uploaded_file.name).stem.replace(" ", "_")
    unique_name = f"{safe_stem}_{uuid.uuid4().hex}{file_ext}"
    destination = os.path.join(UPLOADS_DIR, unique_name)
    
    with open(destination, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    return destination


def list_uploaded_files():
    """List all files stored via the uploader."""
    files = []
    if not os.path.exists(UPLOADS_DIR):
        return files
    
    for filename in sorted(os.listdir(UPLOADS_DIR)):
        file_path = os.path.join(UPLOADS_DIR, filename)
        if not os.path.isfile(file_path):
            continue
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext not in SUPPORTED_FILE_EXTENSIONS:
            continue
        size_kb = os.path.getsize(file_path) / 1024 if os.path.exists(file_path) else 0
        files.append({
            "name": filename,
            "path": file_path,
            "size_kb": size_kb,
            "key": filename.replace(" ", "_")
        })
    return files


def refresh_document_index(system):
    """Reload documents from disk and rebuild the vector index."""
    documents = system['doc_processor'].load_documents(DOCUMENTS_DIR)
    if documents:
        embeddings = system['doc_processor'].generate_embeddings(documents)
        if embeddings:
            system['vector_store'].rebuild_index(embeddings, documents)
        else:
            st.warning("Unable to generate embeddings for the current documents.")
    else:
        system['vector_store'].index = None
        system['vector_store'].documents = []
        system['vector_store'].dimension = None
        st.info("No documents available. Upload files to begin querying.")
    system['documents'] = documents


def render_document_manager(system):
    """Display upload and deletion controls for knowledge base files."""
    st.subheader("📁 Document Manager")
    st.caption("Upload PDF or TXT files to ground the model's responses.")
    
    # Use the callback for handling uploads
    uploaded_files = st.file_uploader(
        "Upload one or more documents",
        accept_multiple_files=True,
        type=SUPPORTED_FILE_TYPES,
        key="documents_uploader",
        on_change=handle_file_upload,
        args=(system,)
    )
    
    stored_files = list_uploaded_files()
    if stored_files:
        st.markdown("**Uploaded files**")
        for file_info in stored_files:
            col1, col2 = st.columns([5, 1])
            col1.write(f"{file_info['name']} ({file_info['size_kb']:.1f} KB)")
            if col2.button("Remove", key=f"delete_{file_info['key']}"):
                os.remove(file_info['path'])
                st.info(f"Removed {file_info['name']}")
                refresh_document_index(system)
                st.rerun()
    else:
        st.caption("No uploaded files yet.")
    
    st.caption(f"Total documents indexed: {len(system.get('documents', []))}")


@st.cache_resource
def initialize_system():
    """Initialize the RAG system components"""
    try:
        with st.spinner("Initializing Finance RAG System..."):
            ensure_document_directories()
            
            # Initialize components
            doc_processor = DocumentProcessor()
            vector_store = VectorStore()
            query_processor = QueryProcessor()
            stock_handler = StockDataHandler()
            llm_handler = LLMHandler()
            
            # Process documents
            documents = doc_processor.load_documents(DOCUMENTS_DIR)
            
            embeddings = doc_processor.generate_embeddings(documents)
            if embeddings:
                vector_store.build_index(embeddings, documents)
                st.success(f"Loaded {len(documents)} documents successfully!")
            else:
                st.info("Upload documents to start receiving grounded responses.")
            
            return {
                'doc_processor': doc_processor,
                'vector_store': vector_store,
                'query_processor': query_processor,
                'stock_handler': stock_handler,
                'llm_handler': llm_handler,
                'documents': documents
            }
    except Exception as e:
        st.error(f"Error initializing system: {str(e)}")
        return None

def main():
    # Session cleanup: Clear documents on new session
    if 'initialized' not in st.session_state:
        # New session detected, clear uploaded documents
        if os.path.exists(UPLOADS_DIR):
            shutil.rmtree(UPLOADS_DIR)
        os.makedirs(UPLOADS_DIR, exist_ok=True)
        st.session_state.initialized = True
    
    # Header
    st.markdown('<h1 class="main-header">💰 Finance RAG System</h1>', unsafe_allow_html=True)
    
    # Initialize system
    system = initialize_system()
    if not system:
        st.stop()
    
    render_document_manager(system)
    
    # Sidebar
    with st.sidebar:
        st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
        st.header("🔧 System Information")
        
        # API Key check
        google_key = os.getenv('GOOGLE_API_KEY')
        if google_key:
            st.success("✅ Google API Key configured")
        else:
            st.error("❌ Google API Key not found")
            st.info("Please set GOOGLE_API_KEY in your environment variables")
        
        # Document count
        st.info(f"📄 Documents loaded: {len(system['documents'])}")
        
        # Sample queries
        st.subheader("💡 Sample Queries")
        sample_queries = [
            "What is Apple's stock performance this week?",
            "Show me Microsoft stock trends",
            "Summarize the latest earnings report",
            "What are the market trends for tech stocks?",
            "Compare AAPL vs MSFT stock performance"
        ]
        
        for query in sample_queries:
            if st.button(query, key=f"sample_{hash(query)}"):
                st.session_state.query_input = query
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Initialize session state
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'query_input' not in st.session_state:
        st.session_state.query_input = ""
    
    # Chat interface
    st.subheader("💬 Ask me about finance and stocks!")
    
    # Display chat history
    for message in st.session_state.messages:
        with st.container():
            if message["role"] == "user":
                st.markdown(f'<div class="chat-message user-message"><strong>You:</strong> {message["content"]}</div>', 
                           unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-message bot-message"><strong>Finance Bot:</strong> {message["content"]}</div>', 
                           unsafe_allow_html=True)
                
                # Display charts if available
                if "chart" in message:
                    st.plotly_chart(message["chart"], use_container_width=True)
    
    # Query input
    col1, col2 = st.columns([4, 1])
    
    with col1:
        query = st.text_input(
            "Enter your financial query:",
            value=st.session_state.get('query_input', ''),
            placeholder="e.g., What is Apple's stock performance this week?",
            key="main_query_input"
        )
    
    with col2:
        submit_button = st.button("Send 🚀", type="primary")
    
    # Process query
    if submit_button and query:
        # Clear the input
        st.session_state.query_input = ""
        
        # Add user message
        st.session_state.messages.append({"role": "user", "content": query})
        
        with st.spinner("Processing your query..."):
            try:
                start_time = time.time()
                
                # Process the query
                response_data = process_query(system, query)
                
                processing_time = time.time() - start_time
                
                # Add bot response
                bot_message = {
                    "role": "assistant",
                    "content": response_data["answer"]
                }
                
                if response_data.get("chart"):
                    bot_message["chart"] = response_data["chart"]
                
                st.session_state.messages.append(bot_message)
                
                # Show processing time
                st.success(f"✅ Response generated in {processing_time:.2f} seconds")
                
                # Rerun to update the display
                st.rerun()
                
            except Exception as e:
                st.error(f"Error processing query: {str(e)}")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"I encountered an error while processing your query: {str(e)}"
                })

def process_query(system, query):
    """Process a user query and return response with potential visualizations"""
    response_data = {"answer": "", "chart": None}
    
    # Check if it's a stock-related query
    is_stock = is_stock_query(query)
    stock_symbols = extract_stock_symbols(query) if is_stock else []
    
    # Retrieve relevant documents
    relevant_docs = system['query_processor'].retrieve_documents(
        query, system['vector_store'], top_k=3
    )
    
    # Get stock data if needed
    stock_data_summary = ""
    chart = None
    
    if is_stock and stock_symbols:
        try:
            # Get stock data for the first symbol (or multiple symbols)
            symbol = stock_symbols[0]  # Use first symbol for simplicity
            stock_data = system['stock_handler'].get_stock_data(symbol, period="1mo")
            
            if stock_data is not None and not stock_data.empty:
                # Create visualization
                chart = system['stock_handler'].create_stock_chart(stock_data, symbol)
                response_data["chart"] = chart
                
                # Create summary for LLM
                latest_price = stock_data['Close'].iloc[-1]
                price_change = stock_data['Close'].iloc[-1] - stock_data['Close'].iloc[0]
                price_change_pct = (price_change / stock_data['Close'].iloc[0]) * 100
                
                stock_data_summary = f"""
                Stock Data for {symbol}:
                - Latest Price: ${latest_price:.2f}
                - 1-Month Change: ${price_change:.2f} ({price_change_pct:.1f}%)
                - 1-Month High: ${stock_data['High'].max():.2f}
                - 1-Month Low: ${stock_data['Low'].min():.2f}
                - Average Volume: {stock_data['Volume'].mean():.0f}
                """
        except Exception as e:
            stock_data_summary = f"Unable to fetch stock data for {symbol}: {str(e)}"
    
    # Generate LLM response
    context = "\n\n".join([doc["content"] for doc in relevant_docs])
    
    response_data["answer"] = system['llm_handler'].generate_response(
        query, context, stock_data_summary
    )
    
    return response_data

if __name__ == "__main__":
    main()