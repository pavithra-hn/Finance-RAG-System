import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import streamlit as st
from typing import Optional, List, Dict
from datetime import datetime, timedelta

class StockDataHandler:
    def __init__(self):
        """Initialize stock data handler"""
        self.cache = {}  # Simple cache for API calls
    
    def get_stock_data(self, symbol: str, period: str = "1mo", interval: str = "1d") -> Optional[pd.DataFrame]:
        """Fetch stock data from Yahoo Finance"""
        try:
            # Create cache key
            cache_key = f"{symbol}_{period}_{interval}"
            
            # Check cache first (simple time-based cache)
            if cache_key in self.cache:
                cached_data, timestamp = self.cache[cache_key]
                # Cache for 5 minutes
                if datetime.now() - timestamp < timedelta(minutes=5):
                    return cached_data
            
            # Fetch data from yfinance
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period, interval=interval)
            
            if data.empty:
                st.warning(f"No data found for symbol: {symbol}")
                return None
            
            # Cache the data
            self.cache[cache_key] = (data, datetime.now())
            
            return data
            
        except Exception as e:
            st.error(f"Error fetching stock data for {symbol}: {e}")
            return None
    
    def get_stock_info(self, symbol: str) -> Dict:
        """Get basic stock information"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return {
                'symbol': symbol,
                'company_name': info.get('longName', 'N/A'),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'market_cap': info.get('marketCap', 'N/A'),
                'pe_ratio': info.get('trailingPE', 'N/A'),
                'dividend_yield': info.get('dividendYield', 'N/A'),
                'current_price': info.get('currentPrice', 'N/A')
            }
        except Exception as e:
            st.error(f"Error fetching stock info for {symbol}: {e}")
            return {'symbol': symbol, 'error': str(e)}
    
    def create_stock_chart(self, data: pd.DataFrame, symbol: str, chart_type: str = "candlestick") -> go.Figure:
        """Create interactive stock chart"""
        try:
            fig = make_subplots(
                rows=2, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.03,
                subplot_titles=(f'{symbol} Stock Price', 'Volume'),
                row_width=[0.2, 0.7]
            )
            
            # Price chart
            if chart_type == "candlestick":
                fig.add_trace(
                    go.Candlestick(
                        x=data.index,
                        open=data['Open'],
                        high=data['High'],
                        low=data['Low'],
                        close=data['Close'],
                        name="Price"
                    ),
                    row=1, col=1
                )
            else:
                fig.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=data['Close'],
                        mode='lines',
                        name='Close Price',
                        line=dict(color='blue', width=2)
                    ),
                    row=1, col=1
                )
            
            # Volume chart
            fig.add_trace(
                go.Bar(
                    x=data.index,
                    y=data['Volume'],
                    name="Volume",
                    marker_color='lightblue'
                ),
                row=2, col=1
            )
            
            # Update layout
            fig.update_layout(
                title=f'{symbol} Stock Analysis',
                yaxis_title='Price ($)',
                yaxis2_title='Volume',
                xaxis_rangeslider_visible=False,
                height=600,
                showlegend=True,
                template='plotly_white'
            )
            
            # Update x-axis
            fig.update_xaxes(title_text="Date", row=2, col=1)
            
            return fig
            
        except Exception as e:
            st.error(f"Error creating chart for {symbol}: {e}")
            return None
    
    def create_comparison_chart(self, symbols: List[str], period: str = "1mo") -> Optional[go.Figure]:
        """Create comparison chart for multiple stocks"""
        try:
            fig = go.Figure()
            
            for symbol in symbols:
                data = self.get_stock_data(symbol, period)
                if data is not None and not data.empty:
                    # Normalize to percentage change
                    normalized = (data['Close'] / data['Close'].iloc[0] - 1) * 100
                    
                    fig.add_trace(
                        go.Scatter(
                            x=data.index,
                            y=normalized,
                            mode='lines',
                            name=symbol,
                            line=dict(width=2)
                        )
                    )
            
            fig.update_layout(
                title=f'Stock Comparison - {period} Performance (%)',
                xaxis_title='Date',
                yaxis_title='Percentage Change (%)',
                height=500,
                template='plotly_white',
                hovermode='x unified'
            )
            
            return fig
            
        except Exception as e:
            st.error(f"Error creating comparison chart: {e}")
            return None
    
    def get_stock_summary(self, symbol: str, period: str = "1mo") -> Dict:
        """Get stock summary statistics"""
        try:
            data = self.get_stock_data(symbol, period)
            if data is None or data.empty:
                return {}
            
            latest_price = data['Close'].iloc[-1]
            first_price = data['Close'].iloc[0]
            price_change = latest_price - first_price
            price_change_pct = (price_change / first_price) * 100
            
            return {
                'symbol': symbol,
                'period': period,
                'current_price': round(latest_price, 2),
                'price_change': round(price_change, 2),
                'price_change_pct': round(price_change_pct, 2),
                'high': round(data['High'].max(), 2),
                'low': round(data['Low'].min(), 2),
                'avg_volume': int(data['Volume'].mean()),
                'volatility': round(data['Close'].pct_change().std() * 100, 2),
                'trading_days': len(data)
            }
            
        except Exception as e:
            st.error(f"Error getting stock summary for {symbol}: {e}")
            return {}
    
    def detect_trend(self, data: pd.DataFrame, window: int = 5) -> str:
        """Detect stock trend based on moving averages"""
        try:
            if len(data) < window:
                return "insufficient_data"
            
            # Calculate short and long moving averages
            short_ma = data['Close'].rolling(window=window).mean().iloc[-1]
            long_ma = data['Close'].rolling(window=window*2).mean().iloc[-1]
            current_price = data['Close'].iloc[-1]
            
            if current_price > short_ma > long_ma:
                return "uptrend"
            elif current_price < short_ma < long_ma:
                return "downtrend"
            else:
                return "sideways"
                
        except Exception as e:
            return "error"
    
    def get_market_status(self) -> Dict:
        """Get current market status"""
        try:
            # Use SPY as market indicator
            spy_data = self.get_stock_data("SPY", period="1d", interval="1m")
            
            if spy_data is None or spy_data.empty:
                return {"status": "unknown", "message": "Unable to fetch market data"}
            
            now = datetime.now()
            market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
            market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
            
            # Simple market hours check (EST)
            if market_open <= now <= market_close and now.weekday() < 5:
                status = "open"
            else:
                status = "closed"
            
            latest_price = spy_data['Close'].iloc[-1]
            first_price = spy_data['Close'].iloc[0]
            change_pct = ((latest_price - first_price) / first_price) * 100
            
            return {
                "status": status,
                "spy_change": round(change_pct, 2),
                "last_update": spy_data.index[-1].strftime("%Y-%m-%d %H:%M:%S")
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}