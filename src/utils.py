import re
from typing import List, Dict, Optional
import streamlit as st

def is_stock_query(query: str) -> bool:
    """Determine if a query is stock-related"""
    stock_keywords = [
        'stock', 'share', 'shares', 'price', 'ticker', 'market', 'trading',
        'volume', 'chart', 'performance', 'trend', 'bull', 'bear',
        'nasdaq', 'nyse', 'sp500', 's&p', 'dow', 'equity', 'securities'
    ]
    
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in stock_keywords)

def extract_stock_symbols(query: str) -> List[str]:
    """Extract stock symbols from a query"""
    # Common stock symbols (3-5 uppercase letters)
    symbol_pattern = r'\b[A-Z]{1,5}\b'
    potential_symbols = re.findall(symbol_pattern, query)
    
    # Known major stock symbols
    known_symbols = {
        'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'TSLA', 'META', 'NFLX',
        'NVDA', 'AMD', 'INTC', 'CRM', 'ORCL', 'IBM', 'ADBE', 'PYPL',
        'UBER', 'LYFT', 'SPOT', 'TWTR', 'SNAP', 'PINS', 'SQ', 'SHOP',
        'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'V', 'MA', 'AXP',
        'JNJ', 'PFE', 'MRK', 'ABBV', 'TMO', 'UNH', 'CVS', 'WBA',
        'KO', 'PEP', 'MCD', 'SBUX', 'NKE', 'DIS', 'HD', 'WMT',
        'SPY', 'QQQ', 'IWM', 'VTI', 'VOO'  # ETFs
    }
    
    # Company name to symbol mapping
    company_mappings = {
        'apple': 'AAPL',
        'microsoft': 'MSFT',
        'google': 'GOOGL',
        'alphabet': 'GOOGL',
        'amazon': 'AMZN',
        'tesla': 'TSLA',
        'facebook': 'META',
        'meta': 'META',
        'netflix': 'NFLX',
        'nvidia': 'NVDA',
        'intel': 'INTC',
        'amd': 'AMD',
        'oracle': 'ORCL',
        'salesforce': 'CRM',
        'adobe': 'ADBE',
        'paypal': 'PYPL',
        'uber': 'UBER',
        'spotify': 'SPOT',
        'twitter': 'TWTR',
        'snapchat': 'SNAP',
        'pinterest': 'PINS',
        'square': 'SQ',
        'shopify': 'SHOP',
        'jpmorgan': 'JPM',
        'goldman': 'GS',
        'visa': 'V',
        'mastercard': 'MA',
        'johnson': 'JNJ',
        'pfizer': 'PFE',
        'merck': 'MRK',
        'cocacola': 'KO',
        'coca-cola': 'KO',
        'pepsi': 'PEP',
        'mcdonald': 'MCD',
        'mcdonalds': 'MCD',
        'starbucks': 'SBUX',
        'nike': 'NKE',
        'disney': 'DIS',
        'walmart': 'WMT',
        'homedepot': 'HD'
    }
    
    symbols = set()
    query_lower = query.lower()
    
    # Add symbols found by pattern matching
    for symbol in potential_symbols:
        if symbol in known_symbols:
            symbols.add(symbol)
    
    # Add symbols found by company name matching
    for company, symbol in company_mappings.items():
        if company in query_lower:
            symbols.add(symbol)
    
    return list(symbols)

def format_currency(amount: float, currency: str = "USD") -> str:
    """Format currency amount"""
    try:
        if amount >= 1e12:
            return f"${amount/1e12:.2f}T"
        elif amount >= 1e9:
            return f"${amount/1e9:.2f}B"
        elif amount >= 1e6:
            return f"${amount/1e6:.2f}M"
        elif amount >= 1e3:
            return f"${amount/1e3:.2f}K"
        else:
            return f"${amount:.2f}"
    except:
        return f"${amount}"

def format_percentage(value: float, decimals: int = 2) -> str:
    """Format percentage with proper sign"""
    try:
        formatted = f"{value:+.{decimals}f}%"
        return formatted
    except:
        return f"{value}%"

def clean_text(text: str) -> str:
    """Clean and normalize text"""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s\-\.,!?()$%]', ' ', text)
    
    # Remove extra spaces
    text = ' '.join(text.split())
    
    return text.strip()

def truncate_text(text: str, max_length: int = 100, add_ellipsis: bool = True) -> str:
    """Truncate text to specified length"""
    if len(text) <= max_length:
        return text
    
    truncated = text[:max_length-3] if add_ellipsis else text[:max_length]
    return truncated + "..." if add_ellipsis else truncated

def extract_financial_metrics(text: str) -> Dict:
    """Extract financial metrics from text"""
    metrics = {}
    
    # Revenue patterns
    revenue_pattern = r'revenue[:\s]*\$?(\d+(?:\.\d+)?)\s*(billion|million|b|m)?'
    revenue_match = re.search(revenue_pattern, text.lower())
    if revenue_match:
        amount = float(revenue_match.group(1))
        unit = revenue_match.group(2)
        if unit and unit.lower() in ['billion', 'b']:
            amount *= 1e9
        elif unit and unit.lower() in ['million', 'm']:
            amount *= 1e6
        metrics['revenue'] = amount
    
    # Profit/earnings patterns
    profit_pattern = r'(?:profit|earnings|income)[:\s]*\$?(\d+(?:\.\d+)?)\s*(billion|million|b|m)?'
    profit_match = re.search(profit_pattern, text.lower())
    if profit_match:
        amount = float(profit_match.group(1))
        unit = profit_match.group(2)
        if unit and unit.lower() in ['billion', 'b']:
            amount *= 1e9
        elif unit and unit.lower() in ['million', 'm']:
            amount *= 1e6
        metrics['profit'] = amount
    
    # EPS pattern
    eps_pattern = r'(?:eps|earnings per share)[:\s]*\$?(\d+(?:\.\d+)?)'
    eps_match = re.search(eps_pattern, text.lower())
    if eps_match:
        metrics['eps'] = float(eps_match.group(1))
    
    # Growth percentage
    growth_pattern = r'(?:growth|up|increase)[:\s]*(\d+(?:\.\d+)?)%'
    growth_match = re.search(growth_pattern, text.lower())
    if growth_match:
        metrics['growth'] = float(growth_match.group(1))
    
    return metrics

def validate_stock_symbol(symbol: str) -> bool:
    """Validate if a string could be a stock symbol"""
    if not symbol:
        return False
    
    # Basic validation: 1-5 uppercase letters
    return bool(re.match(r'^[A-Z]{1,5}$', symbol))

def get_query_intent(query: str) -> str:
    """Determine the intent of a user query"""
    query_lower = query.lower()
    
    # Price/value queries
    if any(word in query_lower for word in ['price', 'cost', 'worth', 'value', 'trading at']):
        return 'price_inquiry'
    
    # Performance/trend queries
    if any(word in query_lower for word in ['performance', 'trend', 'up', 'down', 'gain', 'loss']):
        return 'performance_inquiry'
    
    # Comparison queries
    if any(word in query_lower for word in ['compare', 'vs', 'versus', 'better', 'difference']):
        return 'comparison'
    
    # Analysis/report queries
    if any(word in query_lower for word in ['analyze', 'analysis', 'report', 'summary', 'review']):
        return 'analysis_request'
    
    # Prediction queries
    if any(word in query_lower for word in ['predict', 'forecast', 'future', 'will', 'expect']):
        return 'prediction_request'
    
    # News/update queries
    if any(word in query_lower for word in ['news', 'update', 'latest', 'recent', 'current']):
        return 'news_inquiry'
    
    return 'general_inquiry'

def create_response_template(intent: str, symbol: str = None) -> str:
    """Create response template based on query intent"""
    templates = {
        'price_inquiry': f"Here's the current price information for {symbol or 'the requested stock'}:",
        'performance_inquiry': f"Here's the performance analysis for {symbol or 'the requested stock'}:",
        'comparison': "Here's the comparison analysis:",
        'analysis_request': "Here's the detailed analysis:",
        'prediction_request': "Based on available data, here are the insights:",
        'news_inquiry': "Here are the latest updates:",
        'general_inquiry': "Here's the information you requested:"
    }
    
    return templates.get(intent, "Here's what I found:")

def log_query(query: str, response_time: float, success: bool = True):
    """Log query for analytics (simple implementation)"""
    try:
        # In a real implementation, you might want to log to a file or database
        log_entry = {
            'timestamp': st.session_state.get('current_time', 'unknown'),
            'query': query,
            'response_time': response_time,
            'success': success
        }
        
        # For now, just store in session state
        if 'query_log' not in st.session_state:
            st.session_state.query_log = []
        
        st.session_state.query_log.append(log_entry)
        
        # Keep only last 100 queries
        if len(st.session_state.query_log) > 100:
            st.session_state.query_log = st.session_state.query_log[-100:]
            
    except Exception as e:
        # Silent fail for logging
        pass