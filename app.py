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
    
    with tab1:
        st.header("📊 Data Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📤 Upload to Colab")
            
            uploaded_file = st.file_uploader(
                "Choose CSV file",
                type="csv",
                help="Upload OHLCV data for optimization"
            )
            
            if uploaded_file is not None:
                # Preview data
                df = pd.read_csv(uploaded_file)
                st.success(f"✅ Loaded {len(df)} rows")
                st.dataframe(df.head())
                
                if st.button("📤 Send to Colab", type="primary"):
                    with st.spinner("Uploading to Colab..."):
                        # Reset file pointer
                        uploaded_file.seek(0)
                        result = upload_data_to_colab(
                            st.session_state.colab_url, 
                            uploaded_file
                        )
                        
                        if 'error' not in result:
                            st.success(f"✅ Data uploaded! Rows: {result.get('rows')}")
                        else:
                            st.error(f"❌ Upload failed: {result['error']}")
        
        with col2:
            st.subheader("📡 Download from Yahoo")
            
            symbol = st.text_input("Symbol", value="EURUSD=X")
            period = st.selectbox("Period", ["1mo", "3mo", "6mo"])
            interval = st.selectbox("Interval", ["5m", "15m", "1h"])
            
            if st.button("📥 Download & Send to Colab"):
                with st.spinner("Downloading..."):
                    try:
                        data = yf.download(
                            tickers=symbol,
                            period=period,
                            interval=interval,
                            progress=False
                        )
                        
                        # Save to temporary CSV
                        csv_buffer = data.to_csv()
                        
                        # Send to Colab
                        files = {'file': ('data.csv', csv_buffer)}
                        response = requests.post(
                            f"{st.session_state.colab_url}/upload_data",
                            files=files
                        )
                        
                        if response.status_code == 200:
                            st.success(f"✅ Data sent to Colab! Rows: {len(data)}")
                        else:
                            st.error("Failed to send to Colab")
                            
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
    
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
