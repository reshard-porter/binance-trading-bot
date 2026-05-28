import streamlit as st
import pandas as pd
from database import Database
from config import Config
from binance_client import BinanceClient
import MetaTrader5 as mt5
import utils

st.set_page_config(page_title="Unified Trading Dashboard", layout="wide", page_icon="📈")
st.title("🤖 Unified Dual-Engine Dashboard")

# 1. Initialize Clients
try:
    db = Database()
except Exception as e:
    st.error(f"Database Error: {e}")
    st.stop()

@st.cache_resource
def get_binance_client():
    try:
        return BinanceClient()
    except Exception as e:
        return str(e)

@st.cache_resource
def init_mt5():
    if not mt5.initialize():
        return f"MT5 Init Failed: {mt5.last_error()}"
    return True

with st.spinner("Syncing with Binance and MetaTrader 5..."):
    binance = get_binance_client()
    mt5_status = init_mt5()

# --- THE UNIFIED TABS ---
tab1, tab2 = st.tabs(["🟢 Binance (Crypto)", "🔵 MetaTrader 5 (Forex & Indices)"])

# ==========================================
# TAB 1: BINANCE (CRYPTO)
# ==========================================
with tab1:
    st.subheader("Binance Testnet Status")
    
    if isinstance(binance, str):
        st.error(f"⚠️ Binance Connection Error: {binance}")
    else:
        try:
            trades = db.get_all_trades()
            df = pd.DataFrame([{
                'symbol': t.symbol, 'side': t.side, 'entry': t.entry_price,
                'status': t.status.name, 'pnl': t.pnl
            } for t in trades]) if trades else pd.DataFrame()
            
            account = binance.get_account_info()
            equity = account.get('total_equity', Config.TOTAL_CAPITAL_USDT)
            
            b_col1, b_col2, b_col3 = st.columns(3)
            b_col1.metric("Binance Equity (USDT)", utils.format_currency(equity))
            b_col2.metric("Total Executed Trades", len(df) if not df.empty else 0)
            
            total_pnl = df['pnl'].sum() if not df.empty and 'pnl' in df.columns else 0.0
            b_col3.metric("Total PNL", utils.format_currency(total_pnl))
            
            st.markdown("### 🟢 Active Binance Positions")
            if not df.empty:
                active = df[df['status'] == 'FILLED']
                if not active.empty:
                    st.dataframe(active, use_container_width=True)
                else:
                    st.info("No active crypto trades currently open.")
            else:
                st.info("No crypto trade history.")
        except Exception as e:
            st.warning(f"Could not load Binance data: {e}")

# ==========================================
# TAB 2: METATRADER 5 (FOREX)
# ==========================================
with tab2:
    st.subheader("MetaTrader 5 Live Status")
    
    if mt5_status is not True:
        st.error(f"⚠️ MetaTrader 5 Connection Error: {mt5_status}")
    else:
        account_info = mt5.account_info()
        if account_info:
            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            m_col1.metric("MT5 Live Equity", utils.format_currency(account_info.equity))
            m_col2.metric("MT5 Balance", utils.format_currency(account_info.balance))
            m_col3.metric("Free Margin", utils.format_currency(account_info.margin_free))
            m_col4.metric("Leverage", f"1:{account_info.leverage}")
            
            st.markdown("### 🔵 Active MT5 Positions")
            positions = mt5.positions_get()
            
            if positions:
                # Format live MT5 trades into a clean table
                pos_data = [{
                    'Ticket': p.ticket,
                    'Symbol': p.symbol,
                    'Type': 'BUY' if p.type == 0 else 'SELL',
                    'Volume/Lots': p.volume,
                    'Entry Price': p.price_open,
                    'Current Price': p.price_current,
                    'Stop Loss': p.sl,
                    'Take Profit': p.tp,
                    'Live PNL': utils.format_currency(p.profit)
                } for p in positions]
                
                st.dataframe(pd.DataFrame(pos_data), use_container_width=True)
            else:
                st.info("No active forex trades currently open.")
        else:
            st.warning("Could not fetch MT5 account info. Ensure the terminal is open and logged in.")