import streamlit as st
import pandas as pd
import plotly.express as px
from database import Database
from config import Config
from binance_client import BinanceClient
import utils

# Setup Configuration
st.set_page_config(page_title="Binance Signal Bot", layout="wide", page_icon="📈")
db = Database()

# Initialize Binance (to fetch real-time balances if needed)
@st.cache_resource
def get_binance_client():
    return BinanceClient()

binance = get_binance_client()

st.title("🤖 Automated Trading Dashboard")
st.markdown("Monitor your Telegram signal bot's performance, open positions, and account health.")

# --- METRICS ROW ---
trades = db.get_all_trades()
df = pd.DataFrame([{
    'id': t.id, 'symbol': t.symbol, 'side': t.side, 'entry_price': t.entry_price,
    'quantity': t.quantity, 'quote_quantity': t.quote_quantity, 'status': t.status.name,
    'open_time': t.open_time, 'pnl': t.pnl, 'source': t.source_name
} for t in trades]) if trades else pd.DataFrame()

col1, col2, col3, col4 = st.columns(4)

account = binance.get_account_info()
equity = account.get('total_equity', Config.TOTAL_CAPITAL_USDT)

with col1:
    st.metric("Total Equity (USDT)", utils.format_currency(equity))
with col2:
    st.metric("Total Trades Executed", len(df) if not df.empty else 0)
with col3:
    win_rate = 0.0
    if not df.empty and 'pnl' in df.columns:
        closed = df.dropna(subset=['pnl'])
        if len(closed) > 0:
            wins = len(closed[closed['pnl'] > 0])
            win_rate = (wins / len(closed)) * 100
    st.metric("Win Rate", utils.format_percentage(win_rate))
with col4:
    total_pnl = df['pnl'].sum() if not df.empty and 'pnl' in df.columns else 0.0
    st.metric("Total PNL", utils.format_currency(total_pnl))

# --- ACTIVE TRADES ---
st.subheader("🟢 Active Open Positions")
if not df.empty:
    active = df[df['status'] == 'FILLED']
    if not active.empty:
        st.dataframe(active[['symbol', 'side', 'entry_price', 'quantity', 'quote_quantity', 'source', 'open_time']], use_container_width=True)
    else:
        st.info("No active trades currently open.")
else:
    st.info("System has no trade history.")

# --- TRADE HISTORY ---
st.subheader("📚 Trade History")
if not df.empty:
    st.dataframe(df, use_container_width=True)
    
    # Simple PNL Chart
    if 'pnl' in df.columns and len(df.dropna(subset=['pnl'])) > 0:
        st.subheader("Performance Over Time")
        closed_df = df.dropna(subset=['pnl']).sort_values('open_time')
        closed_df['Cumulative PNL'] = closed_df['pnl'].cumsum()
        fig = px.line(closed_df, x='open_time', y='Cumulative PNL', title="Cumulative PNL (USDT)")
        st.plotly_chart(fig, use_container_width=True)