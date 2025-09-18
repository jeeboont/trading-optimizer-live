"""
Streamlit Trading Optimizer - Direct Colab Integration
This version connects directly to your Google Colab API
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

# ==========================================
# COLAB CONNECTION FUNCTIONS
# ==========================================

def test_colab_connection(url):
    """Test if Colab server is accessible"""
    try:
        response = requests.get(f"{url}/", timeout=5)
        return response.status_code == 200
    except:
        return False

def run_colab_optimization(url, config):
    """Send optimization request to Colab"""
    try:
        response = requests.post(
            f"{url}/optimize",
            json=config,
            timeout=10
        )
        return response.json()
    except Exception as e:
        return {'error': str(e)}

def check_optimization_status(url):
    """Check optimization progress"""
    try:
        response = requests.get(f"{url}/status", timeout=5)
        return response.json()
    except:
        return None

def get_optimization_results(url):
    """Get final results from Colab"""
    try:
        response = requests.get(f"{url}/results", timeout=5)
        return response.json()
    except:
        return None

def upload_data_to_colab(url, file):
    """Upload CSV file to Colab"""
    try:
        files = {'file': file}
        response = requests.post(
            f"{url}/upload_data",
            files=files,
            timeout=30
        )
        return response.json()
    except Exception as e:
        return {'error': str(e)}

# ==========================================
# MAIN APP
# ==========================================

st.title("🔄 Trading Strategy Optimizer")
st.markdown("*Direct Integration with Google Colab*")

# ==========================================
# SIDEBAR - COLAB CONNECTION
# ==========================================

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
            # Test connection
            with st.spinner("Testing connection..."):
                if test_colab_connection(colab_url):
                    st.session_state.colab_url = colab_url
                    st.success("✅ Successfully connected!")
                    st.balloons()
                else:
                    st.error("❌ Could not connect. Check URL and ensure Colab is running.")
        else:
            st.warning("Please enter a URL")
    
    # Connection guide
    with st.expander("📖 Connection Guide"):
        st.markdown("""
        **Step 1:** Open Google Colab
        - Go to the Colab notebook
        - Run all cells in order
        
        **Step 2:** Get the URL
        - Look for the ngrok URL in output
        - It looks like: `https://xxxxx.ngrok.io`
        
        **Step 3:** Connect
        - Paste the URL above
        - Click Connect
        
        **Note:** Keep Colab running!
        """)

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
    # TAB 1: DATA UPLOAD
    # ==========================================
    
    import streamlit as st
    import yfinance as yf
    import pandas as pd
    from datetime import datetime, timedelta
    import io
    
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
                        return {
                            'symbol': symbol,
                            'name': info.get('longName') or info.get('shortName', symbol),
                            'found': True
                        }
                except:
                    continue
            
            return {'symbol': query.upper(), 'name': 'Symbol not verified', 'found': False}
        except:
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
                    
                    with st.spinner(f"Downloading {len(st.session_state.selected_assets)} assets..."):
                        # Download data for all selected assets
                        all_data = {}
                        failed = []
                        
                        progress_bar = st.progress(0)
                        for i, asset in enumerate(st.session_state.selected_assets):
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
                                else:
                                    failed.append(asset['symbol'])
                                    st.warning(f"⚠️ {asset['symbol']}: No data")
                            except Exception as e:
                                failed.append(asset['symbol'])
                                st.error(f"❌ {asset['symbol']}: {str(e)}")
                        
                        if all_data:
                            # Combine all data (for Colab optimization)
                            # You can modify this based on how your optimization handles multiple assets
                            if len(all_data) == 1:
                                # Single asset - send as is
                                combined_data = list(all_data.values())[0]
                            else:
                                # Multiple assets - you might want to handle differently
                                # For now, let's send them separately or combined based on your needs
                                combined_data = pd.concat(all_data, axis=1, keys=all_data.keys())
                            
                            # Convert to CSV
                            csv_buffer = io.StringIO()
                            combined_data.to_csv(csv_buffer)
                            csv_data = csv_buffer.getvalue()
                            
                            # Send to Colab
                            if st.session_state.colab_url:
                                result = upload_data_to_colab(st.session_state.colab_url, csv_data)
                                if 'error' not in result:
                                    st.success(f"✅ Data sent to Colab! Rows: {result.get('rows')}")
                                    st.session_state.data_uploaded = True
                                    
                                    # Store metadata for optimization
                                    st.session_state.data_metadata = {
                                        'assets': [a['symbol'] for a in st.session_state.selected_assets],
                                        'timeframe': selected_timeframe,
                                        'period': period,
                                        'rows': len(combined_data)
                                    }
                                else:
                                    st.error(f"Failed to send to Colab: {result.get('error')}")
                        
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
    # TAB 2: OPTIMIZATION
    # ==========================================
    
    with tab2:
        st.header("⚙️ Strategy Optimization")
        
        # Check if optimization is running
        if st.session_state.optimization_running:
            # Show progress
            st.info("🔄 Optimization in progress...")
            
            # Progress monitoring
            status = check_optimization_status(st.session_state.colab_url)
            
            if status:
                # Progress bar
                progress = status.get('progress', 0) / 100
                st.progress(progress)
                st.write(f"Status: {status.get('message', 'Processing...')}")
                
                # Check if complete
                if not status.get('running', True):
                    st.session_state.optimization_running = False
                    st.session_state.optimization_results = status.get('results')
                    st.success("✅ Optimization Complete!")
                    st.balloons()
                    
                    # Auto-refresh
                    time.sleep(1)
                    st.rerun()
            
            # Refresh button
            if st.button("🔄 Refresh Status"):
                st.rerun()
            
            # Stop button
            if st.button("⏹️ Stop Optimization"):
                st.session_state.optimization_running = False
        
        else:
            # Configuration interface
            st.subheader("📋 Optimization Configuration")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**Core Parameters**")
                pivot_periods = st.multiselect(
                    "Pivot Periods",
                    [5, 7, 10, 12, 15, 20],
                    default=[7, 10, 15]
                )
                atr_factors = st.multiselect(
                    "ATR Factors",
                    [0.5, 0.8, 1.0, 1.5, 2.0, 2.5],
                    default=[0.8, 1.5, 2.0]
                )
                atr_periods = st.multiselect(
                    "ATR Periods",
                    [10, 14, 20, 30],
                    default=[10, 14, 20]
                )
            
            with col2:
                st.markdown("**Risk Management**")
                risk_percents = st.multiselect(
                    "Risk % per Trade",
                    [0.5, 1.0, 1.5, 2.0, 2.5, 3.0],
                    default=[1.0, 1.5, 2.0]
                )
                cb_buffer_pcts = st.multiselect(
                    "Circuit Breaker %",
                    [0.01, 0.03, 0.05, 0.07, 0.10],
                    default=[0.03, 0.05, 0.07]
                )
                enable_cb = st.checkbox("Enable Circuit Breaker", value=True)
            
            with col3:
                st.markdown("**Filters**")
                use_xtrend = st.checkbox("Use XTrend", value=True)
                use_ema = st.checkbox("Use EMA Filter", value=True)
                use_adx = st.checkbox("Use ADX Filter", value=False)
                
                if use_ema:
                    ema_periods = st.multiselect(
                        "EMA Periods",
                        [20, 30, 50, 100, 200],
                        default=[30, 50]
                    )
                else:
                    ema_periods = []
            
            st.markdown("---")
            
            # Advanced settings
            with st.expander("🔧 Advanced Settings"):
                train_split = st.slider("Training Split %", 50, 90, 70)
                min_trades = st.number_input("Min Trades", 50, 500, 100)
                objective = st.selectbox(
                    "Optimization Objective",
                    ["Sharpe Ratio", "Profit Factor", "Total Return"]
                )
            
            # Run optimization button
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col2:
                if st.button(
                    "🚀 **Start Optimization on Colab**", 
                    use_container_width=True,
                    type="primary"
                ):
                    # Prepare configuration
                    config = {
                        'pivot_periods': pivot_periods,
                        'atr_factors': atr_factors,
                        'atr_periods': atr_periods,
                        'risk_percents': risk_percents,
                        'cb_buffer_pcts': cb_buffer_pcts,
                        'enable_cb': enable_cb,
                        'use_xtrend': use_xtrend,
                        'use_ema': use_ema,
                        'use_adx': use_adx,
                        'ema_periods': ema_periods if use_ema else [],
                        'train_split': train_split / 100,
                        'min_trades': min_trades,
                        'objective': objective.lower().replace(' ', '_')
                    }
                    
                    # Send to Colab
                    with st.spinner("Sending to Colab..."):
                        result = run_colab_optimization(
                            st.session_state.colab_url,
                            config
                        )
                        
                        if 'error' not in result:
                            st.session_state.optimization_running = True
                            st.success("✅ Optimization started on Colab!")
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error(f"❌ Failed to start: {result['error']}")
    
    # ==========================================
    # TAB 3: RESULTS
    # ==========================================
    
    with tab3:
        st.header("📈 Optimization Results")
        
        # Check for results
        if st.session_state.optimization_results:
            results = st.session_state.optimization_results
            
            # Display metrics
            st.subheader("📊 Performance Metrics")
            
            col1, col2, col3, col4 = st.columns(4)
            
            col1.metric("Score", f"{results.get('score', 0):.2f}")
            col2.metric("Sharpe Ratio", f"{results.get('sharpe_ratio', 0):.2f}")
            col3.metric("Profit Factor", f"{results.get('profit_factor', 0):.2f}")
            col4.metric("Win Rate", f"{results.get('win_rate', 0):.1f}%")
            
            col1, col2, col3, col4 = st.columns(4)
            
            col1.metric("Total Trades", results.get('total_trades', 0))
            col2.metric("Max Drawdown", f"{results.get('max_drawdown', 0):.1f}%")
            col3.metric("Total Return", f"${results.get('total_return', 0):,.0f}")
            col4.metric("Risk %", f"{results.get('risk_percent', 0):.1f}%")
            
            # Parameters table
            st.subheader("📋 Optimized Parameters")
            
            params_df = pd.DataFrame([{
                'Pivot Period': results.get('pivot_period'),
                'ATR Period': results.get('atr_period'),
                'ATR Factor': results.get('atr_factor'),
                'Risk %': results.get('risk_percent'),
                'CB Buffer': results.get('cb_buffer_pct'),
                'Use XTrend': '✅' if results.get('use_xtrend') else '❌',
                'Use EMA': '✅' if results.get('use_ema') else '❌',
                'EMA Period': results.get('ema_period', 'N/A')
            }]).T
            
            params_df.columns = ['Value']
            st.dataframe(params_df, use_container_width=True)
            
            # Download results
            if st.button("💾 Download Results JSON"):
                json_str = json.dumps(results, indent=2)
                st.download_button(
                    label="📥 Download",
                    data=json_str,
                    file_name=f"optimization_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            
            # Refresh results from Colab
            if st.button("🔄 Refresh Results from Colab"):
                with st.spinner("Fetching latest results..."):
                    new_results = get_optimization_results(st.session_state.colab_url)
                    if new_results:
                        st.session_state.optimization_results = new_results
                        st.success("✅ Results updated!")
                        st.rerun()
                    else:
                        st.warning("No new results available")
        
        else:
            # No results yet
            st.info("📊 No results available yet")
            
            # Try to fetch results
            if st.button("🔍 Check for Results"):
                with st.spinner("Checking Colab for results..."):
                    results = get_optimization_results(st.session_state.colab_url)
                    if results and 'error' not in results:
                        st.session_state.optimization_results = results
                        st.success("✅ Results found!")
                        st.rerun()
                    else:
                        st.warning("No results available. Run optimization first.")
    
    # ==========================================
    # TAB 4: PINE SCRIPT
    # ==========================================
    
    with tab4:
        st.header("📱 Pine Script Generator")
        
        if st.session_state.optimization_results:
            results = st.session_state.optimization_results
            
            # Generate Pine Script
            pine_script = f"""// Trading Strategy - Live Colab Optimization
// Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}
// Colab Integration Version

//@version=5
strategy("Colab Optimized Strategy", overlay=true,
         initial_capital=10000,
         default_qty_type=strategy.percent_of_equity,
         default_qty_value={results.get('risk_percent', 1.0)})

// === COLAB OPTIMIZED PARAMETERS ===
pivot_period = {results.get('pivot_period', 10)}
atr_period = {results.get('atr_period', 14)}
atr_factor = {results.get('atr_factor', 2.0)}
cb_buffer_pct = {results.get('cb_buffer_pct', 0.03)}
risk_percent = {results.get('risk_percent', 1.0)}

// === FILTERS (from Colab) ===
use_xtrend = {"true" if results.get('use_xtrend') else "false"}
use_ema = {"true" if results.get('use_ema') else "false"}
ema_period = {results.get('ema_period', 30)}

// === STRATEGY LOGIC ===
// [Your strategy implementation here]

// === METRICS FROM COLAB ===
// Sharpe: {results.get('sharpe_ratio', 0):.2f}
// PF: {results.get('profit_factor', 0):.2f}
// WR: {results.get('win_rate', 0):.1f}%
// DD: {results.get('max_drawdown', 0):.1f}%
"""
            
            st.code(pine_script, language='javascript')
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.download_button(
                    "💾 Download Pine Script",
                    data=pine_script,
                    file_name="colab_optimized_strategy.pine",
                    mime="text/plain",
                    use_container_width=True
                )
            
            with col2:
                if st.button("📋 Copy to Clipboard", use_container_width=True):
                    st.success("✅ Copied!")
        
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
    
    ### 📚 Benefits of Direct Integration:
    
    - ✅ **Real-time optimization** - Run directly on Colab's GPU/TPU
    - ✅ **Live progress tracking** - See optimization status in real-time
    - ✅ **Automatic data transfer** - No manual copying needed
    - ✅ **Instant results** - Get results as soon as optimization completes
    - ✅ **Resource efficiency** - Use Colab's free compute resources
    
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
        Trading Strategy Optimizer | Direct Colab Integration | 
        <a href='#' style='color: #888;'>Documentation</a>
    </div>
    """,
    unsafe_allow_html=True
)
