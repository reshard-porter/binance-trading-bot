import MetaTrader5 as mt5
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - MT5_CLIENT - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MT5Client:
    def __init__(self):
        """Initializes the connection to the MetaTrader 5 desktop terminal."""
        if not mt5.initialize():
            logger.error(f"MT5 initialization failed. Error code: {mt5.last_error()}")
            raise ConnectionError("Make sure MetaTrader 5 is open and logged in.")
        logger.info("🟢 Successfully connected to MetaTrader 5 Terminal.")

    def get_account_info(self):
        """Fetches live balance and equity."""
        account = mt5.account_info()
        if account is None:
            logger.error(f"Failed to retrieve MT5 account info. Error: {mt5.last_error()}")
            return None
        return account._asdict()

    def calculate_dynamic_lot(self, symbol: str, risk_percent: float = 1.0) -> float:
        """
        EXECUTION STRATEGY 1: Risk Management
        Defaults to the safest minimum lot size for the specific asset if 
        complex tick-value math cannot be determined.
        """
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            logger.warning(f"Could not find {symbol} to calculate lots. Defaulting to 0.01")
            return 0.01
        
        # For a fully dynamic model, you would calculate: (Balance * Risk%) / (SL_Points * Tick_Value)
        # To ensure the bot doesn't crash on unfamiliar indices, we rely on broker minimums as a baseline.
        min_volume = symbol_info.volume_min
        return float(min_volume)

    def execute_signal(self, signal_data: dict):
        """
        EXECUTION STRATEGY 2: Strict Order Formatting
        Parses the Telegram signal and sends it to the broker.
        Expected format: {'symbol': 'XAUUSD', 'action': 'BUY', 'sl': 2340.0, 'tp': 2360.0}
        """
        symbol = signal_data.get('symbol')
        action = signal_data.get('action', '').upper()
        sl = float(signal_data.get('sl', 0.0))
        tp = float(signal_data.get('tp', 0.0))

        # 1. Verify the asset exists in the broker
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            logger.error(f"Asset '{symbol}' not found on this MT5 broker. Trade aborted.")
            return None

        # 2. Ensure the asset is visible in Market Watch
        if not symbol_info.visible:
            mt5.symbol_select(symbol, True)

        # 3. Determine pricing and direction
        if action == 'BUY':
            order_type = mt5.ORDER_TYPE_BUY
            price = mt5.symbol_info_tick(symbol).ask
        elif action == 'SELL':
            order_type = mt5.ORDER_TYPE_SELL
            price = mt5.symbol_info_tick(symbol).bid
        else:
            logger.error(f"Unknown action '{action}' for {symbol}. Must be BUY or SELL.")
            return None

        # 4. Calculate Risk-Adjusted Lot Size
        lot_size = self.calculate_dynamic_lot(symbol)

        # 5. Build the MT5 Request Payload
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot_size,
            "type": order_type,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": 20, # EXECUTION STRATEGY 3: 20-point max slippage allowed
            "magic": 777777, # Unique ID so we know this bot placed the trade
            "comment": "Telegram Signal",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC, # Immediate or Cancel
        }

        # 6. Send Order to Broker
        result = mt5.order_send(request)
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(f"❌ MT5 Order Failed: {result.retcode} - {result.comment}")
            return None

        logger.info(f"✅ MT5 Trade Executed: {action} {symbol} | Lot: {lot_size} | Entry: {price}")
        return result._asdict()

    def shutdown(self):
        """Safely disconnects from MT5."""
        mt5.shutdown()
        logger.info("MT5 Connection Closed.")

# --- QUICK TEST BLOCK ---
# If you run this specific file directly, it will test your connection
if __name__ == "__main__":
    try:
        client = MT5Client()
        account = client.get_account_info()
        if account:
            print(f"\n✅ SUCCESS! Connected to MT5.")
            print(f"Broker: {account.get('company')}")
            print(f"Server: {account.get('server')}")
            print(f"Live Equity: ${account.get('equity')}")
        client.shutdown()
    except Exception as e:
        print(f"\n❌ FAILED: {e}")