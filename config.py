import os
from dotenv import load_dotenv
from typing import List, Dict, Any
import logging

load_dotenv()

# Ensure directories exist
os.makedirs('logs', exist_ok=True)
os.makedirs('data', exist_ok=True)

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/trading.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class Config:
    """Main configuration class"""
    
    # Binance Configuration
    BINANCE_API_KEY = os.getenv('BINANCE_API_KEY', '')
    BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET', '')
    BINANCE_TESTNET = os.getenv('BINANCE_TESTNET', 'True').lower() == 'true'
    BINANCE_FUTURES = os.getenv('BINANCE_FUTURES', 'False').lower() == 'true'
    
    # Telegram Configuration
    TELEGRAM_API_ID = int(os.getenv('TELEGRAM_API_ID', '30790134'))
    TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH', '2a6e06bc75423cd72898311f3876fd96')
    TELEGRAM_PHONE = os.getenv('TELEGRAM_PHONE', '')
    
    # Trading Parameters
    TOTAL_CAPITAL_USDT = float(os.getenv('TOTAL_CAPITAL_USDT', '1000'))
    MAX_POSITION_SIZE_PCT = float(os.getenv('MAX_POSITION_SIZE_PCT', '5'))
    MAX_CONCURRENT_TRADES = int(os.getenv('MAX_CONCURRENT_TRADES', '4'))
    MAX_DAILY_LOSS_PCT = float(os.getenv('MAX_DAILY_LOSS_PCT', '10'))
    MAX_DRAWDOWN_PCT = float(os.getenv('MAX_DRAWDOWN_PCT', '15'))
    
    # Risk Parameters
    STOP_LOSS_PCT = float(os.getenv('STOP_LOSS_PCT', '2.0'))
    TAKE_PROFIT_PCT = float(os.getenv('TAKE_PROFIT_PCT', '4.0'))
    RISK_PER_TRADE_PCT = float(os.getenv('RISK_PER_TRADE_PCT', '1.0'))
    
    # Signal Sources from channels.txt
    SIGNAL_CHATS: List[Dict[str, Any]] = [
        {"name": "Forex Scalping Signals", "id": -100360327776, "active": True, "symbol_map": "BTCUSDT"},
        {"name": "Binance Killers", "id": -1001220789766, "active": True, "symbol_map": "BTCUSDT"},
        {"name": "Easy Forex OFFICIAL CHANNEL", "id": -1001284268486, "active": True, "symbol_map": "ETHUSDT"},
        {"name": "Magic Trader Signals", "id": -1003123676832, "active": True, "symbol_map": "BTCUSDT"},
        {"name": "XAUUSD GBPNZD EURUSD AUDUSD FX SIGNALS", "id": -1003844887048, "active": True, "symbol_map": "BTCUSDT"}, # Mapped for Crypto
        {"name": "FBS Analytics", "id": -1001387511343, "active": True, "symbol_map": "ETHUSDT"},
        {"name": "Gold Sniper", "id": -1001313672961, "active": True, "symbol_map": "BTCUSDT"},
        {"name": "IC Markets Signals", "id": -1001526740882, "active": True, "symbol_map": "BTCUSDT"},
        {"name": "Oracle Signals", "id": -1003886604100, "active": True, "symbol_map": "ETHUSDT"},
        {"name": "Signals - Bitcoin and Ethereum", "id": -1001746203369, "active": True, "symbol_map": "BTCUSDT"},
        {"name": "Bitcoin Bullets", "id": -1001351499165, "active": True, "symbol_map": "BTCUSDT"},
        {"name": "Learn 2 Trade", "id": -1001693246182, "active": True, "symbol_map": "BTCUSDT"},
        {"name": "GOLD SIGNALS DAILY", "id": -1002654294939, "active": True, "symbol_map": "BTCUSDT"},
        {"name": "SURE SHOT FX VIP", "id": -1003776528905, "active": True, "symbol_map": "BTCUSDT"},
        {"name": "United Kings Signals", "id": -1003947769165, "active": True, "symbol_map": "BTCUSDT"},
        {"name": "FOREX RESULTS", "id": -1001703717473, "active": True, "symbol_map": "ETHUSDT"},
    ]
    
    # Execution Parameters
    ENTRY_ZONE_POINTS = 30 
    CASCADE_LOCK_IN_POINTS = 100 
    ATR_LENGTH = 14
    TRAIL_START_MULTIPLIER = 2.5
    TRAIL_DISTANCE_MULTIPLIER = 1.5
    TIMEFRAME = "15m" 
    
    # Symbol Mapping (Forex -> Crypto for Binance matching)
    SYMBOL_MAPPING = {
        "XAUUSD": "BTCUSDT",  
        "GOLD": "BTCUSDT",
        "XAU/USD": "BTCUSDT",
        "EURUSD": "ETHUSDT",
        "GBPUSD": "BNBUSDT",
        "USDJPY": "SOLUSDT",
        "AUDUSD": "ADAUSDT",
        "NZDUSD": "DOGEUSDT",
        "USDCAD": "MATICUSDT",
        "USDCHF": "DOTUSDT",
    }
    
    # Trading Symbols
    TRADING_SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "ADAUSDT"]
    
    @classmethod
    def validate(cls) -> bool:
        """Validate configuration"""
        if not cls.BINANCE_API_KEY or not cls.BINANCE_API_SECRET:
            logger.error("Binance API credentials missing")
            return False
        if cls.TOTAL_CAPITAL_USDT <= 0:
            logger.error("Total capital must be positive")
            return False
        if cls.MAX_POSITION_SIZE_PCT <= 0 or cls.MAX_POSITION_SIZE_PCT > 100:
            logger.error("Invalid max position size percentage")
            return False
        return True