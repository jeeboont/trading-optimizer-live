"""
Streamlit Trading Optimizer - Direct Colab Integration (DEBUGGED VERSION)
This version has enhanced debugging and error handling
"""

import streamlit as st
import pandas as pd
import numpy as np
import json
import plotly.graph_objects as go
from datetime import datetime
import yfinance as yf
import requests
import time
import io

# ==========================================
# PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="Trading Strategy Optimizer - Live Colab",
    page_icon="🔄",
    layout="wide"
)

# ==========================================
# SESSION STATE
# ==========================================

if 'colab_url' not in st.session_state:
    st.session_state.colab_url = None
if 'optimization_running' not in st.session_state:
    st.session_state.optimization_running = False
if 'optimization_results' not in st.session_state:
    st.session_state.optimization_results = None
if 'debug_logs' not in st.session_state:
    st.session_state.debug_logs = []

# ==========================================
# DEBUG LOGGING FUNCTION
# ==========================================

def debug_log(message):
    """Add debug message to session state"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.debug_logs.append(f"[{timestamp}] {message}")
    print(f"DEBUG: {message}")  # Also print to console

# ==========================================
# COLAB CONNECTION FUNCTIONS (ENHANCED)
# ==========================================

def test_colab_connection(url):
    """Test if Colab server is accessible"""
    try:
        debug_log(f"Testing connection to: {url}")
        response = requests.get(f"{url}/", timeout=5)
        debug_log(f"Connection test response: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        debug_log(f"Connection test failed: {str(e)}")
        return False

def run_colab_optimization(url, config):
    """Send optimization request to Colab"""
    try:
        debug_log(f"Sending optimization to: {url}/optimize")
        debug_log(f"Config size: {len(str(config))} characters")
        
        response = requests.post(
            f"{url}/optimize",
            json=config,
            headers={'Content-Type': 'application/json'},
            timeout=1800  # 30 minutes timeout for real optimization
        )
        
        debug_log(f"Optimization response status: {response.status_code}")
        debug_log(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            debug_log(f"Optimization response: {result}")
            return result
        else:
            debug_log(f"HTTP Error {response.status_code}: {response.text}")
            return {'error': f'HTTP {response.status_code}: {response.text}'}
            
    except requests.exceptions.Timeout:
        debug_log("Request timeout - Colab might be processing")
        return {'error': 'Request timeout - check if Colab is still running'}
    except requests.exceptions.ConnectionError:
        debug_log("Connection error - check Colab URL")
        return {'error': 'Connection error - check if Colab URL is correct'}
    except Exception as e:
        debug_log(f"Optimization request error: {str(e)}")
        return {'error': str(e)}

def check_optimization_status(url):
    """Check optimization progress"""
    try:
        debug_log("Checking optimization status...")
        response = requests.get(f"{url}/status", timeout=5)
        if response.status_code == 200:
            status = response.json()
            debug_log(f"Status: {status}")
            return status
        else:
            debug_log(f"Status check failed: {response.status_code}")
            return None
    except Exception as e:
        debug_log(f"Status check error: {str(e)}")
        return None

def get_optimization_results(url):
    """Get final results from Colab"""
    try:
        debug_log("Getting final results...")
        response = requests.get(f"{url}/results", timeout=10)
        if response.status_code == 200:
            results = response.json()
            debug_log(f"Got results: {len(str(results))} characters")
            
            # Fix numpy serialization issues
            def convert_numpy(obj):
                if hasattr(obj, 'item'):  # numpy scalar
                    return obj.item()
                elif isinstance(obj, dict):
                    return {k: convert_numpy(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_numpy(item) for item in obj]
                else:
                    return obj
            
            # Convert numpy types to regular Python types
            clean_results = convert_numpy(results)
            return clean_results
        else:
            debug_log(f"Results fetch failed: {response.status_code}")
            return None
    except Exception as e:
        debug_log(f"Results fetch error: {str(e)}")
        return None

def upload_data_to_colab(url, csv_data):
    """Send CSV data to Colab"""
    try:
        debug_log(f"Uploading data to Colab: {len(csv_data)} characters")
        response = requests.post(
            f"{url}/upload_data",
            data=csv_data,
            headers={'Content-Type': 'text/plain'},
            timeout=60  # Increased timeout for data upload
        )
        
        debug_log(f"Upload response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            debug_log(f"Upload successful: {result}")
            return result
        else:
            debug_log(f"Upload failed: {response.text}")
            return {'error': f'Upload failed: {response.text}'}
            
    except Exception as e:
        debug_log(f"Upload error: {str(e)}")
        return {'error': str(e)}

# ==========================================
# MAIN APP
# ==========================================

st.title("🔄 Trading Strategy Optimizer")
st.markdown("*Direct Integration with Google Colab (Debug Version)*")

# Debug panel in sidebar
with st.sidebar:
    st.header("🔌 Colab Connection")
    
    # Connection status indicator
    if st.session_state.colab_url:
        if test_colab_connection(st.session_state.colab_url):
            st.success("✅ Connected to Colab")
        else:
            st.error("❌ Connection Lost")
            st.session_state.colab_url = None
    
    # URL input
    st.markdown("### Setup Instructions:")
    st.info("""
    1. Open the Colab notebook
    2. Run all cells
    3. Copy the ngrok URL
    4. Paste it below
    """)
    
    colab_url = st.text_input(
        "Colab API URL",
        value=st.session_state.colab_url or "",
        placeholder="https://xxxxx-xxx-xxx.ngrok.io",
        help="Enter the ngrok URL from your Colab output"
    )
    
    if st.button("🔗 Connect to Colab"):
        if colab_url:
            debug_log(f"Attempting to connect to: {colab_url}")
            with st.spinner("Testing connection..."):
                if test_colab_connection(colab_url):
                    st.session_state.colab_url = colab_url
                    st.success("✅ Successfully connected!")
                    debug_log("Connection successful!")
                    st.balloons()
                else:
                    st.error("❌ Could not connect. Check URL and ensure Colab is running.")
                    debug_log("Connection failed!")
        else:
            st.warning("Please enter a URL")
    
    # Debug panel
    if st.checkbox("🐛 Show Debug Logs"):
        st.markdown("### Debug Logs:")
        if st.session_state.debug_logs:
            for log in st.session_state.debug_logs[-10:]:  # Show last 10 logs
                st.text(log)
            
            if st.button("Clear Logs"):
                st.session_state.debug_logs = []
                st.rerun()
        else:
            st.text("No logs yet...")

# ==========================================
# MAIN CONTENT TABS
# ==========================================

if st.session_state.colab_url:
    # Connected - show main interface
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Data Upload", 
        "⚙️ Optimization", 
        "📈 Results", 
        "📱 Pine Script"
    ])
    
    # ==========================================
    # TAB 1: DATA UPLOAD (Your existing code)
    # ==========================================
    
    # Predefined popular assets for dropdown
    POPULAR_ASSETS = {
        'Crypto': {
            'Bitcoin (BTC-USD)': 'BTC-USD',
            'Ethereum (ETH-USD)': 'ETH-USD',
            'Litecoin (LTC-USD)': 'LTC-USD',
            'Ripple (XRP-USD)': 'XRP-USD',
            'Cardano (ADA-USD)': 'ADA-USD',
        },
        'Forex': {
            'EUR/USD': 'EURUSD=X',
            'GBP/USD': 'GBPUSD=X',
            'USD/JPY': 'USDJPY=X',
            'AUD/USD': 'AUDUSD=X',
            'USD/CAD': 'USDCAD=X',
        },
        'Commodities': {
            'Gold': 'GC=F',
            'Silver': 'SI=F',
            'Crude Oil': 'CL=F',
            'Natural Gas': 'NG=F',
        },
        'Stocks': {
            'Apple': 'AAPL',
            'Microsoft': 'MSFT',
            'Tesla': 'TSLA',
            'Amazon': 'AMZN',
            'Google': 'GOOGL',
        },
        'ETFs': {
            'S&P 500 (SPY)': 'SPY',
            'Nasdaq (QQQ)': 'QQQ',
            'Dow Jones (DIA)': 'DIA',
        }
    }
    
    # Timeframe configurations with data limits
    TIMEFRAME_LIMITS = {
        '1m': {'name': '1 Minute', 'max_days': 7, 'period': '7d', 'description': 'Max 7 days'},
        '2m': {'name': '2 Minutes', 'max_days': 60, 'period': '1mo', 'description': 'Max 60 days'},
        '5m': {'name': '5 Minutes', 'max_days': 60, 'period': '1mo', 'description': 'Max 60 days'},
        '15m': {'name': '15 Minutes', 'max_days': 60, 'period': '1mo', 'description': 'Max 60 days'},
        '1h': {'name': '1 Hour', 'max_days': 730, 'period': '2y', 'description': 'Max 2 years'},
        '1d': {'name': 'Daily', 'max_days': None, 'period': '1y', 'description': 'All available'},
    }
    
    def search_ticker(query):
        """Search for ticker symbols"""
        try:
            debug_log(f"Searching for ticker: {query}")
            # Try common variations
            variations = [
                query.upper(),
                f"{query.upper()}-USD",
                f"{query.upper()}USD=X",
                f"{query.upper()}=F"
            ]
            
            for symbol in variations:
                try:
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    if info and ('longName' in info or 'shortName' in info):
                        debug_log(f"Found ticker: {symbol}")
                        return {
                            'symbol': symbol,
                            'name': info.get('longName') or info.get('shortName', symbol),
                            'found': True
                        }
                except:
                    continue
            
            debug_log(f"Ticker not verified: {query}")
            return {'symbol': query.upper(), 'name': 'Symbol not verified', 'found': False}
        except Exception as e:
            debug_log(f"Ticker search error: {str(e)}")
            return {'symbol': query.upper(), 'name': 'Symbol not verified', 'found': False}
    
    # Data Upload Tab Content
    with tab1:
        st.header("📊 Data Upload")
        
        # Initialize session state
        if 'selected_assets' not in st.session_state:
            st.session_state.selected_assets = []
        if 'data_uploaded' not in st.session_state:
            st.session_state.data_uploaded = False
        
        col1, col2 = st.columns([3, 2])
        
        with col1:
            st.subheader("🎯 Asset Selection")
            
            # Asset selection method
            selection_method = st.radio(
                "Choose selection method:",
                ["Popular Assets (Dropdown)", "Custom Search"],
                horizontal=True
            )
            
            if selection_method == "Popular Assets (Dropdown)":
                # Category selection
                category = st.selectbox(
                    "Select category:",
                    options=list(POPULAR_ASSETS.keys())
                )
                
                # Asset selection from category
                asset_options = list(POPULAR_ASSETS[category].keys())
                selected_display = st.selectbox(
                    f"Select {category} asset:",
                    options=['-- Select --'] + asset_options
                )
                
                if selected_display != '-- Select --':
                    symbol = POPULAR_ASSETS[category][selected_display]
                    
                    col_add, col_info = st.columns([1, 3])
                    with col_add:
                        if st.button("➕ Add Asset", type="primary", use_container_width=True):
                            if symbol not in [a['symbol'] for a in st.session_state.selected_assets]:
                                if len(st.session_state.selected_assets) < 5:
                                    st.session_state.selected_assets.append({
                                        'symbol': symbol,
                                        'name': selected_display
                                    })
                                    st.success(f"Added {selected_display}")
                                    debug_log(f"Added asset: {symbol}")
                                    st.rerun()
                                else:
                                    st.error("Maximum 5 assets allowed")
                            else:
                                st.warning("Asset already selected")
                    
                    with col_info:
                        st.info(f"Symbol: {symbol}")
            
            else:  # Custom Search
                search_query = st.text_input(
                    "Enter symbol or company name:",
                    placeholder="e.g., AAPL, Bitcoin, EUR/USD"
                )
                
                if search_query:
                    col_search, col_add = st.columns([2, 1])
                    
                    with col_search:
                        if st.button("🔍 Search", use_container_width=True):
                            with st.spinner("Searching..."):
                                result = search_ticker(search_query)
                                st.session_state.search_result = result
                    
                    if 'search_result' in st.session_state:
                        result = st.session_state.search_result
                        if result['found']:
                            st.success(f"Found: {result['name']} ({result['symbol']})")
                        else:
                            st.warning(f"Not verified, but you can still add: {result['symbol']}")
                        
                        if st.button(f"➕ Add {result['symbol']}", type="primary"):
                            if result['symbol'] not in [a['symbol'] for a in st.session_state.selected_assets]:
                                if len(st.session_state.selected_assets) < 5:
                                    st.session_state.selected_assets.append({
                                        'symbol': result['symbol'],
                                        'name': result['name']
                                    })
                                    st.success(f"Added {result['symbol']}")
                                    debug_log(f"Added custom asset: {result['symbol']}")
                                    st.rerun()
                                else:
                                    st.error("Maximum 5 assets allowed")
                            else:
                                st.warning("Asset already selected")
            
            # Display selected assets
            if st.session_state.selected_assets:
                st.markdown("---")
                st.subheader("📋 Selected Assets")
                
                for i, asset in enumerate(st.session_state.selected_assets):
                    col_name, col_remove = st.columns([4, 1])
                    with col_name:
                        st.write(f"{i+1}. **{asset['name']}** ({asset['symbol']})")
                    with col_remove:
                        if st.button("❌", key=f"remove_{asset['symbol']}"):
                            st.session_state.selected_assets.remove(asset)
                            debug_log(f"Removed asset: {asset['symbol']}")
                            st.rerun()
                
                st.info(f"Selected: {len(st.session_state.selected_assets)}/5 assets")
        
        with col2:
            st.subheader("⏰ Timeframe & Period")
            
            # Timeframe selection with data limits display
            selected_timeframe = st.selectbox(
                "Select timeframe:",
                options=list(TIMEFRAME_LIMITS.keys()),
                format_func=lambda x: f"{TIMEFRAME_LIMITS[x]['name']} ({TIMEFRAME_LIMITS[x]['description']})",
                index=2  # Default to 5m
            )
            
            tf_config = TIMEFRAME_LIMITS[selected_timeframe]
            
            # Display timeframe info card
            st.info(f"""
            **{tf_config['name']} Data Limits:**
            - Maximum available: {tf_config['description']}
            - Auto-selected period: {tf_config['period']}
            - Best for: {'Intraday' if selected_timeframe in ['1m', '2m', '5m', '15m'] else 'Swing/Position'}
            """)
            
            # Period selection (simplified)
            use_max_period = st.checkbox("Use maximum available period", value=True)
            
            if not use_max_period:
                custom_period = st.selectbox(
                    "Custom period:",
                    options=['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y'],
                    index=2
                )
                period = custom_period
            else:
                period = tf_config['period']
            
            st.success(f"Will download: {period} of {tf_config['name']} data")
        
        # Download section
        st.markdown("---")
        st.subheader("📥 Download & Send to Colab")
        
        if not st.session_state.selected_assets:
            st.warning("Please select at least one asset to continue")
        else:
            col_download, col_status = st.columns([2, 1])
            
            with col_download:
                if st.button("📥 Download & Send to Colab", 
                            type="primary", 
                            use_container_width=True,
                            disabled=not st.session_state.colab_url):
                    
                    debug_log(f"Starting download for {len(st.session_state.selected_assets)} assets")
                    
                    with st.spinner(f"Downloading {len(st.session_state.selected_assets)} assets..."):
                        # Download data for all selected assets
                        all_data = {}
                        failed = []
                        
                        progress_bar = st.progress(0)
                        for i, asset in enumerate(st.session_state.selected_assets):
                            debug_log(f"Downloading {asset['symbol']}...")
                            progress_bar.progress((i + 1) / len(st.session_state.selected_assets))
                            
                            try:
                                ticker = yf.Ticker(asset['symbol'])
                                data = ticker.history(
                                    period=period,
                                    interval=selected_timeframe
                                )
                                
                                if not data.empty:
                                    all_data[asset['symbol']] = data
                                    st.success(f"✅ {asset['symbol']}: {len(data)} rows")
                                    debug_log(f"Downloaded {asset['symbol']}: {len(data)} rows")
                                else:
                                    failed.append(asset['symbol'])
                                    st.warning(f"⚠️ {asset['symbol']}: No data")
                                    debug_log(f"No data for {asset['symbol']}")
                            except Exception as e:
                                failed.append(asset['symbol'])
                                st.error(f"❌ {asset['symbol']}: {str(e)}")
                                debug_log(f"Failed to download {asset['symbol']}: {str(e)}")
                        
                        if all_data:
                            debug_log("Preparing data for Colab...")
                            # Combine all data (for Colab optimization)
                            if len(all_data) == 1:
                                # Single asset - send as is
                                combined_data = list(all_data.values())[0]
                            else:
                                # Multiple assets - send first asset for now (you can modify this)
                                combined_data = list(all_data.values())[0]
                                st.info(f"Note: Using {list(all_data.keys())[0]} for optimization")
                            
                            # Convert to CSV
                            csv_buffer = io.StringIO()
                            combined_data.to_csv(csv_buffer)
                            csv_data = csv_buffer.getvalue()
                            
                            debug_log(f"CSV data prepared: {len(csv_data)} characters")
                            
                            # Send to Colab
                            if st.session_state.colab_url:
                                result = upload_data_to_colab(st.session_state.colab_url, csv_data)
                                if 'error' not in result:
                                    st.success(f"✅ Data sent to Colab! Rows: {result.get('rows', 'Unknown')}")
                                    st.session_state.data_uploaded = True
                                    
                                    # Store metadata for optimization
                                    st.session_state.data_metadata = {
                                        'assets': [a['symbol'] for a in st.session_state.selected_assets],
                                        'timeframe': selected_timeframe,
                                        'period': period,
                                        'rows': len(combined_data)
                                    }
                                    debug_log("Data upload successful!")
                                else:
                                    st.error(f"Failed to send to Colab: {result.get('error')}")
                                    debug_log(f"Upload failed: {result.get('error')}")
                        
                        if failed:
                            st.warning(f"Failed to download: {', '.join(failed)}")
            
            with col_status:
                if st.session_state.data_uploaded:
                    st.success("✅ Data Ready")
                else:
                    st.info("⏳ Awaiting data")
        
        # Show data preview if uploaded
        if st.session_state.data_uploaded and 'data_metadata' in st.session_state:
            st.markdown("---")
            st.subheader("📊 Data Summary")
            
            meta = st.session_state.data_metadata
            col1, col2, col3, col4 = st.columns(4)
            
            col1.metric("Assets", len(meta['assets']))
            col2.metric("Timeframe", TIMEFRAME_LIMITS[meta['timeframe']]['name'])
            col3.metric("Period", meta['period'])
            col4.metric("Total Rows", f"{meta['rows']:,}")
            
            st.info(f"Assets: {', '.join(meta['assets'])}")
    
    # ==========================================
    # TAB 2: OPTIMIZATION (FIXED)
    # ==========================================
    
    with tab2:
        st.header("⚙️ Optimization Configuration")
        
        # Check connection and data status
        if not st.session_state.colab_url:
            st.warning("⚠️ Please connect to Colab first")
            st.stop()
        
        if not st.session_state.data_uploaded:
            st.info("📊 Please upload data first")
            st.stop()
        
        st.subheader("🎯 3-Step Optimization Strategy")
        
        # Optimization approach selector
        approach = st.radio(
            "Select optimization approach:",
            ["Quick Test", "Standard 3-Step", "Comprehensive 3-Step", "Custom"],
            index=1,
            help="Based on your proven 3-step methodology"
        )
        
        if approach == "Quick Test":
            st.info("""
            **Quick Test (2-3 minutes)**
            - Limited ranges for fast validation
            - Good for testing setup
            """)
            config = {
                'optimization_type': '3_step',
                # Step 1: Core
                'pivot_periods': [10],
                'atr_factors': [2.0],
                'atr_periods': [14],
                # Step 2: Risk
                'risk_percents': [1.0],
                'cb_buffer_pcts': [0.03],
                # Step 3: Filters
                'use_xtrend': True,
                'use_ema': True,
                'use_adx': False,
                'ema_periods': [30],
                'adx_thresholds': [20]
            }
            
        elif approach == "Standard 3-Step":
            st.success("""
            **Standard 3-Step Optimization (10-15 minutes)**
            - Your proven parameter ranges
            - Walk-forward validation
            - Systematic progression
            """)
            config = {
                'optimization_type': '3_step',
                # Step 1: Core Parameters (as you specified)
                'pivot_periods': [5, 7, 10, 12, 15],  
                'atr_factors': [0.8, 1.0, 1.2, 1.5, 2.0],  # Coarse grid
                'atr_periods': [10, 14, 20, 30],
                # Step 2: Risk Management 
                'risk_percents': [0.5, 1.0, 1.5, 2.0],
                'cb_buffer_pcts': [0.01, 0.03, 0.05, 0.07, 0.10, 0.13],
                # Step 3: Filters
                'filter_combinations': [
                    {'use_xtrend': True, 'use_ema': False, 'use_adx': False},
                    {'use_xtrend': True, 'use_ema': True, 'use_adx': False},
                    {'use_xtrend': True, 'use_ema': False, 'use_adx': True},
                    {'use_xtrend': True, 'use_ema': True, 'use_adx': True},
                ],
                'ema_periods': [30, 50, 100],
                'adx_thresholds': [15, 20, 25]
            }
            
        elif approach == "Comprehensive 3-Step":
            st.warning("""
            **Comprehensive 3-Step (30-45 minutes)**
            - Full parameter ranges
            - Fine-tuning after coarse search
            - Maximum optimization depth
            """)
            config = {
                'optimization_type': '3_step_comprehensive',
                # Step 1: Core - Full range
                'pivot_periods': list(range(2, 16)),  # 2-15 all integers
                'atr_factors': [0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0],
                'atr_periods': list(range(10, 41, 2)),  # 10-40 step 2
                # Step 2: Risk - Full range
                'risk_percents': [0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0],
                'cb_buffer_pcts': [0.01, 0.02, 0.03, 0.04, 0.05, 0.07, 0.10, 0.13, 0.15],
                # Step 3: Filters - All combinations
                'filter_combinations': 'all',  # Test all possible combinations
                'ema_periods': list(range(50, 251, 50)),  # 50-250 step 50
                'adx_thresholds': list(range(5, 26, 5))  # 5-25 step 5
            }
        
        else:  # Custom
            st.info("Define your custom 3-step parameters")
            config = {'optimization_type': '3_step_custom'}
            
            # Custom parameter inputs (your existing code)
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### Step 1: Core Parameters")
                
                # Pivot periods
                pivot_min = st.number_input("Pivot Min", 2, 30, 5)
                pivot_max = st.number_input("Pivot Max", 2, 30, 15)
                pivot_step = st.number_input("Pivot Step", 1, 5, 1)
                config['pivot_periods'] = list(range(pivot_min, pivot_max + 1, pivot_step))
                
                # ATR Factor
                atr_factor_min = st.number_input("ATR Factor Min", 0.5, 3.0, 0.8)
                atr_factor_max = st.number_input("ATR Factor Max", 0.5, 3.0, 2.0)
                atr_factor_step = st.number_input("ATR Factor Step", 0.05, 0.5, 0.1)
                config['atr_factors'] = [round(x, 2) for x in 
                                       np.arange(atr_factor_min, atr_factor_max + atr_factor_step, atr_factor_step)]
                
                # ATR Period
                atr_period_min = st.number_input("ATR Period Min", 5, 50, 10)
                atr_period_max = st.number_input("ATR Period Max", 5, 50, 30)
                atr_period_step = st.number_input("ATR Period Step", 1, 10, 5)
                config['atr_periods'] = list(range(atr_period_min, atr_period_max + 1, atr_period_step))
                
            with col2:
                st.markdown("### Step 2: Risk Management")
                
                # Risk Percent
                risk_values = st.text_input(
                    "Risk % (comma separated)",
                    "0.5, 1.0, 1.5, 2.0"
                )
                config['risk_percents'] = [float(x.strip()) for x in risk_values.split(',')]
                
                # CB Buffer
                cb_values = st.text_input(
                    "CB Buffer % (comma separated)",
                    "0.01, 0.03, 0.05, 0.07, 0.10, 0.13"
                )
                config['cb_buffer_pcts'] = [float(x.strip()) for x in cb_values.split(',')]
                
                st.markdown("### Step 3: Filters")
                
                # Filter combinations
                use_xtrend = st.checkbox("Test XTrend", True)
                use_ema = st.checkbox("Test EMA", True)
                use_adx = st.checkbox("Test ADX", False)
                
                if use_ema:
                    ema_values = st.text_input("EMA Periods", "30, 50, 100")
                    config['ema_periods'] = [int(x.strip()) for x in ema_values.split(',')]
                
                if use_adx:
                    adx_values = st.text_input("ADX Thresholds", "15, 20, 25")
                    config['adx_thresholds'] = [int(x.strip()) for x in adx_values.split(',')]
        
        # Display optimization summary
        st.markdown("---")
        st.subheader("📊 Optimization Summary")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if 'pivot_periods' in config:
                st.metric(
                    "Step 1: Core Combinations",
                    len(config['pivot_periods']) * len(config['atr_factors']) * len(config['atr_periods'])
                )
        
        with col2:
            if 'risk_percents' in config:
                st.metric(
                    "Step 2: Risk Combinations",
                    len(config['risk_percents']) * len(config['cb_buffer_pcts'])
                )
        
        with col3:
            if approach != "Custom":
                st.metric(
                    "Step 3: Filter Tests",
                    len(config.get('filter_combinations', [])) if isinstance(config.get('filter_combinations'), list) else "All"
                )
        
        # Walk-forward validation settings
        with st.expander("📈 Walk-Forward Validation Settings", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                train_split = st.slider(
                    "Training Data %",
                    50, 90, 70, 5,
                    help="Your recommended 70/30 split"
                )
                config['train_split'] = train_split / 100
                
            with col2:
                walk_forward_windows = st.number_input(
                    "Walk-Forward Windows",
                    1, 10, 1,
                    help="Number of rolling windows for validation"
                )
                config['walk_forward_windows'] = walk_forward_windows
        
        # Additional settings
        config['min_trades'] = st.number_input("Minimum Trades for Valid Result", 10, 100, 30)
        config['optimization_metric'] = st.selectbox(
            "Primary Optimization Metric",
            ["composite_score", "sharpe_ratio", "profit_factor", "win_rate"],
            help="Composite score uses weighted combination"
        )
        
        # Run optimization button (FIXED)
        st.markdown("---")
        
        # Show current status and reset option
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if st.session_state.optimization_running:
                st.warning("⚠️ Optimization flag is currently active")
            else:
                st.success("✅ Ready to start optimization")
        
        with col2:
            if st.button("🔄 Reset", help="Reset optimization status"):
                st.session_state.optimization_running = False
                debug_log("Optimization flag manually reset")
                st.success("Flag reset!")
                st.rerun()
        
        if st.button("🚀 Start 3-Step Optimization", type="primary", use_container_width=True):
            debug_log("Optimization button clicked!")
            debug_log(f"Current optimization_running flag: {st.session_state.optimization_running}")
            
            if not st.session_state.optimization_running:
                debug_log("Flag is False - proceeding with optimization")
                st.session_state.optimization_running = True
                st.session_state.optimization_config = config
                
                debug_log("Preparing to send optimization to Colab...")
                debug_log(f"Config keys: {list(config.keys())}")
                debug_log(f"Colab URL: {st.session_state.colab_url}")
                
                # Create a placeholder for real-time updates
                status_placeholder = st.empty()
                progress_placeholder = st.empty()
                
                try:
                    # Send to Colab (quick start request, don't wait for completion)
                    status_placeholder.info("🚀 Sending optimization request to Colab...")
                    result = run_colab_optimization(st.session_state.colab_url, config)
                    
                    debug_log(f"Optimization response received: {result}")
                    
                    if result and 'error' not in result:
                        status_placeholder.success("✅ 3-Step Optimization Started!")
                        
                        st.info("""
                        **Optimization Progress:**
                        1. Step 1: Core Parameters → Finding optimal Pivot/ATR settings
                        2. Step 2: Risk Management → Optimizing CB and position sizing
                        3. Step 3: Filters → Testing combinations and thresholds
                        
                        **This is now running in Colab!** You can:
                        - Monitor progress in your Colab notebook
                        - Check back here in 10-15 minutes for results
                        - Use the "Check Results" button below
                        """)
                        
                        # Store the initial result
                        st.session_state.optimization_results = result
                        
                        # For Quick Test, check immediately for results since it completes fast
                        if config.get('optimization_type') == '3_step' and len(config.get('pivot_periods', [])) == 1:
                            # Quick test - check for immediate completion
                            time.sleep(2)  # Give it 2 seconds to complete
                            quick_results = get_optimization_results(st.session_state.colab_url)
                            if quick_results and 'assets' in quick_results:
                                st.session_state.optimization_results = quick_results
                                status_placeholder.success("✅ Quick Test Complete!")
                                progress_placeholder.success("🎉 Results are ready in the Results tab!")
                                st.balloons()
                                st.session_state.optimization_running = False
                        
                        # Add manual result checking buttons
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if st.button("🔄 Check Progress", use_container_width=True, key="check_progress"):
                                with st.spinner("Checking progress..."):
                                    status_check = check_optimization_status(st.session_state.colab_url)
                                    debug_log(f"Progress check result: {status_check}")
                                    if status_check:
                                        if status_check.get('running') == False:
                                            st.success("✅ Optimization Complete!")
                                            # Get results immediately when complete
                                            final_results = get_optimization_results(st.session_state.colab_url)
                                            if final_results and 'assets' in final_results:
                                                st.session_state.optimization_results = final_results
                                                st.success("✅ Results updated! Check the Results tab.")
                                                st.balloons()
                                            else:
                                                st.error("Could not retrieve results")
                                        else:
                                            progress = status_check.get('progress', 0)
                                            message = status_check.get('message', 'Processing...')
                                            st.info(f"⏳ Progress: {progress}% - {message}")
                                    else:
                                        st.warning("Could not check status - optimization may still be running")
                        
                        with col2:
                            if st.button("📈 Get Results", use_container_width=True, key="get_results"):
                                with st.spinner("Retrieving results..."):
                                    debug_log("Manual results fetch requested")
                                    final_results = get_optimization_results(st.session_state.colab_url)
                                    debug_log(f"Retrieved results: {final_results is not None}")
                                    if final_results and ('assets' in final_results or 'message' not in final_results):
                                        st.session_state.optimization_results = final_results
                                        st.success("✅ Results retrieved! Check the Results tab.")
                                        st.balloons()
                                    else:
                                        st.info("⏳ Results not ready yet. Optimization may still be running.")
                                        debug_log(f"Results not ready, got: {final_results}")
                        
                        # Auto status checking in background (non-blocking)
                        progress_placeholder.info("💡 **Tip:** Monitor your Colab notebook for real-time progress!")
                        
                        # Reset flag immediately since we're not blocking
                        st.session_state.optimization_running = False
                        
                    else:
                        error_msg = result.get('error', 'Unknown error') if result else 'No response from Colab'
                        status_placeholder.error(f"❌ Failed to start: {error_msg}")
                        st.session_state.optimization_running = False
                        
                except requests.exceptions.Timeout:
                    # This is normal for long optimizations
                    status_placeholder.info("⏳ Optimization started (request timed out, but this is normal)")
                    st.info("""
                    **Optimization Status:** Request timed out, but this is expected for real optimizations.
                    
                    Your optimization is likely running in Colab. You can:
                    1. **Monitor Colab directly** - Check your Step 3b output for progress
                    2. **Come back in 10-15 minutes** and use the "Get Results" button
                    3. **Check the Results tab** periodically
                    """)
                    
                    # Add result checking button for timeout case
                    if st.button("📈 Try Get Results Now", use_container_width=True):
                        try:
                            final_results = get_optimization_results(st.session_state.colab_url)
                            if final_results and 'assets' in final_results:
                                st.session_state.optimization_results = final_results
                                st.success("✅ Results found! Check the Results tab.")
                                st.balloons()
                            else:
                                st.info("⏳ Results not ready yet. Keep checking Colab progress.")
                        except:
                            st.info("⏳ Still processing. Check your Colab output for progress.")
                    
                    st.session_state.optimization_running = False
                    
                except Exception as e:
                    status_placeholder.error(f"❌ Connection error: {str(e)}")
                    debug_log(f"Exception during optimization: {str(e)}")
                    st.session_state.optimization_running = False
            
            else:
                debug_log(f"Flag is True - blocking optimization. Flag value: {st.session_state.optimization_running}")
                st.warning("⚠️ Optimization is already running!")
                st.info("If this seems stuck, use the Reset button above.")
    
    # ==========================================
    # TAB 3: RESULTS (Enhanced)
    # ==========================================

    with tab3:
        st.header("📈 Optimization Results")
        
        # Manual results fix (temporary)
        if st.button("🔧 Load Manual Results (Quick Test)", help="Load the completed Quick Test results from Colab"):
            manual_results = {
                "assets": {
                    "BTC-USD": {
                        "metrics": {
                            "max_drawdown": 7.5,
                            "profit_factor": 1.75,
                            "sharpe_ratio": 0.17,
                            "total_return": 2030,
                            "total_trades": 29,
                            "win_rate": 17.2
                        },
                        "parameters": {
                            "atr_factor": 2.0,
                            "atr_period": 14,
                            "cb_buffer_pct": 0.03,
                            "pivot_period": 10,
                            "risk_percent": 1.0
                        },
                        "score": 14.12
                    }
                },
                "comparison": {
                    "best_by_score": "BTC-USD",
                    "best_by_sharpe": "BTC-USD",
                    "best_by_win_rate": "BTC-USD",
                    "rankings": [
                        {
                            "asset": "BTC-USD",
                            "score": 14.12,
                            "sharpe": 0.17,
                            "win_rate": 17.2
                        }
                    ]
                },
                "type": "single_asset"
            }
            st.session_state.optimization_results = manual_results
            st.success("✅ Quick Test results loaded!")
            st.balloons()
        
        if st.session_state.optimization_results:
            results = st.session_state.optimization_results
            debug_log(f"Displaying results: {type(results)}")
            
            # Check if this is multi-asset results
            if isinstance(results, dict) and 'assets' in results:
                st.success("✅ Multi-Asset Optimization Results")
                
                # Asset Comparison Overview
                comparison = results.get('comparison', {})
                if comparison:
                    st.subheader("🏆 Asset Performance Comparison")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        best_score = comparison.get('best_by_score', 'N/A')
                        st.metric("🥇 Best Overall Score", best_score)
                    
                    with col2:
                        best_sharpe = comparison.get('best_by_sharpe', 'N/A')
                        st.metric("📈 Best Sharpe Ratio", best_sharpe)
                    
                    with col3:
                        best_winrate = comparison.get('best_by_win_rate', 'N/A')
                        st.metric("🎯 Best Win Rate", best_winrate)
                
                # Rankings Table
                if 'rankings' in comparison:
                    st.subheader("📊 Asset Rankings")
                    rankings_data = []
                    for rank in comparison['rankings']:
                        rankings_data.append({
                            'Rank': len(rankings_data) + 1,
                            'Asset': rank['asset'],
                            'Score': f"{rank['score']:.2f}",
                            'Sharpe Ratio': f"{rank['sharpe']:.2f}",
                            'Win Rate': f"{rank['win_rate']:.1f}%"
                        })
                    
                    rankings_df = pd.DataFrame(rankings_data)
                    st.dataframe(
                        rankings_df,
                        use_container_width=True,
                        hide_index=True
                    )
                
                # Detailed Asset Results
                st.subheader("📋 Detailed Results by Asset")
                
                assets = results.get('assets', {})
                asset_names = list(assets.keys())
                
                if asset_names:
                    selected_asset = st.selectbox(
                        "Select asset for detailed analysis:",
                        options=asset_names,
                        index=0
                    )
                    
                    if selected_asset in assets:
                        asset_data = assets[selected_asset]
                        
                        # Performance Metrics
                        st.markdown(f"### 📊 **{selected_asset}** Performance")
                        
                        metrics = asset_data.get('metrics', {})
                        col1, col2, col3, col4 = st.columns(4)
                        
                        col1.metric("Total Return", f"${metrics.get('total_return', 0):,}")
                        col2.metric("Total Trades", f"{metrics.get('total_trades', 0):,}")
                        col3.metric("Win Rate", f"{metrics.get('win_rate', 0):.1f}%")
                        col4.metric("Sharpe Ratio", f"{metrics.get('sharpe_ratio', 0):.2f}")
                        
                        col1, col2, col3, col4 = st.columns(4)
                        col1.metric("Profit Factor", f"{metrics.get('profit_factor', 0):.2f}")
                        col2.metric("Max Drawdown", f"{metrics.get('max_drawdown', 0):.1f}%")
                        col3.metric("Score", f"{asset_data.get('score', 0):.2f}")
                        col4.metric("Status", "✅ Optimized")
                        
                        # Optimized Parameters
                        st.markdown(f"### ⚙️ **{selected_asset}** Optimized Parameters")
                        
                        params = asset_data.get('parameters', {})
                        
                        # Core Parameters
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("**📈 Core Settings**")
                            st.info(f"""
                            **Pivot Period:** {params.get('pivot_period', 'N/A')}
                            **ATR Period:** {params.get('atr_period', 'N/A')}
                            **ATR Factor:** {params.get('atr_factor', 'N/A')}
                            """)
                        
                        with col2:
                            st.markdown("**💰 Risk Management**")
                            st.info(f"""
                            **Risk Percent:** {params.get('risk_percent', 'N/A')}%
                            **CB Buffer:** {params.get('cb_buffer_pct', 'N/A')}%
                            """)
                        
                        # Filter Settings
                        st.markdown("**🔍 Active Filters**")
                        filter_col1, filter_col2, filter_col3 = st.columns(3)
                        
                        filter_col1.success("✅ XTrend Filter" if params.get('use_xtrend') else "❌ XTrend Filter")
                        filter_col2.success("✅ EMA Filter" if params.get('use_ema') else "❌ EMA Filter")
                        filter_col3.success("✅ ADX Filter" if params.get('use_adx') else "❌ ADX Filter")
                        
                        # Export Options
                        st.markdown("---")
                        st.subheader("💾 Export Options")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            # Create export data
                            export_data = {
                                'asset': selected_asset,
                                'optimization_date': datetime.now().isoformat(),
                                'performance_metrics': metrics,
                                'optimized_parameters': params,
                                'score': asset_data.get('score', 0)
                            }
                            
                            st.download_button(
                                f"📄 Download {selected_asset} Results (JSON)",
                                data=json.dumps(export_data, indent=2),
                                file_name=f"{selected_asset}_optimization_results_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                                mime="application/json",
                                use_container_width=True
                            )
                        
                        with col2:
                            # Pine Script parameters format
                            pine_params = f"""// {selected_asset} Optimized Parameters
// Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

// Core Parameters
pivot_period = {params.get('pivot_period', 10)}
atr_period = {params.get('atr_period', 14)}
atr_factor = {params.get('atr_factor', 2.0)}

// Risk Management
risk_percent = {params.get('risk_percent', 1.0)}
cb_buffer_pct = {params.get('cb_buffer_pct', 0.03)}

// Filters
use_xtrend = {"true" if params.get('use_xtrend') else "false"}
use_ema = {"true" if params.get('use_ema') else "false"}
use_adx = {"true" if params.get('use_adx') else "false"}

// Performance: {metrics.get('win_rate', 0):.1f}% WR, {metrics.get('sharpe_ratio', 0):.2f} Sharpe, Score: {asset_data.get('score', 0):.2f}
"""
                            
                            st.download_button(
                                f"📱 Download {selected_asset} Pine Script Params",
                                data=pine_params,
                                file_name=f"{selected_asset}_pine_params_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                                mime="text/plain",
                                use_container_width=True
                            )
                
                # Show raw results for debugging (collapsed by default)
                with st.expander("🐛 Debug: Raw Results Data"):
                    st.json(results)
            
            else:
                # Fallback for other result formats
                st.info("Results in alternative format:")
                st.json(results)
        
        else:
            st.info("⏳ No optimization results yet. Run an optimization first.")
            
            # Show debug logs in results tab too
            if st.session_state.debug_logs:
                with st.expander("🐛 Recent Debug Logs"):
                    for log in st.session_state.debug_logs[-5:]:
                        st.text(log)
    
    # ==========================================
    # TAB 4: PINE SCRIPT (Simplified for now)
    # ==========================================
    
    with tab4:
        st.header("📱 Pine Script Generator")
        
        if st.session_state.optimization_results:
            results = st.session_state.optimization_results
            
            # Basic Pine Script template
            pine_script = f"""// Trading Strategy - Live Colab Optimization
// Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}
// Debug Version

//@version=5
strategy("Colab Optimized Strategy", overlay=true,
         initial_capital=10000,
         default_qty_type=strategy.percent_of_equity,
         default_qty_value=1.0)

// === RESULTS FROM COLAB ===
// {results}

// === BASIC STRATEGY TEMPLATE ===
// Add your strategy logic here based on the optimization results
"""
            
            st.code(pine_script, language='javascript')
            
            st.download_button(
                "💾 Download Pine Script Template",
                data=pine_script,
                file_name="colab_optimized_strategy.pine",
                mime="text/plain",
                use_container_width=True
            )
        
        else:
            st.warning("⚠️ No optimization results available")

else:
    # Not connected - show connection prompt
    st.warning("⚠️ Not connected to Google Colab")
    
    st.markdown("""
    ### 🔌 How to Connect:
    
    1. **Open Google Colab** and run the optimization notebook
    2. **Get the ngrok URL** from the Colab output  
    3. **Enter the URL** in the sidebar
    4. **Click Connect** to establish connection
    
    ### 🐛 Debug Features Added:
    
    - ✅ **Enhanced logging** - Track all API calls and responses
    - ✅ **Better error handling** - More detailed error messages
    - ✅ **Connection testing** - Verify Colab is responding
    - ✅ **Request debugging** - See exactly what's being sent
    - ✅ **Progress monitoring** - Real-time optimization tracking
    
    ### 🚀 Get Started:
    
    1. Copy the Colab notebook to your Google Drive
    2. Run all cells in the notebook
    3. Copy the ngrok URL that appears
    4. Paste it in the sidebar and connect!
    """)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #888;'>
        Trading Strategy Optimizer | Debug Version | Direct Colab Integration
    </div>
    """,
    unsafe_allow_html=True
)
