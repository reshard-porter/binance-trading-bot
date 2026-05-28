import asyncio
import logging
import re
import os
from telethon import TelegramClient, events
from dotenv import load_dotenv

# Import both execution engines
from binance_client import BinanceClient
from mt5_client import MT5Client

load_dotenv()

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load Credentials
API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
PHONE = os.getenv('TELEGRAM_PHONE')

# Initialize the dual engines
try:
    binance = BinanceClient()
    mt5 = MT5Client()
except Exception as e:
    logger.error(f"Failed to initialize engines: {e}")

client = TelegramClient('sessions/trading_session', API_ID, API_HASH)

def parse_signal(text):
    """
    Standard Signal Parser.
    Expects format: BUY XAUUSD @ 2350 SL 2340 TP 2360
    """
    try:
        text = text.upper()
        action = "BUY" if "BUY" in text else "SELL" if "SELL" in text else None
        
        # Find symbol (Looks for a block of 3-9 uppercase letters like BTCUSDT or XAUUSD)
        symbol_match = re.search(r'\b([A-Z]{3,9})\b', text.replace(action, "") if action else text)
        symbol = symbol_match.group(1) if symbol_match else None
        
        # Extract all numbers (Entry, SL, TP)
        numbers = re.findall(r'\d+(?:\.\d+)?', text)
        
        if action and symbol and len(numbers) >= 3:
            return {
                'action': action,
                'symbol': symbol,
                'entry': float(numbers[0]),
                'sl': float(numbers[1]),
                'tp': float(numbers[2])
            }
    except Exception as e:
        logger.error(f"Parsing error: {e}")
    return None

# Replace with your actual Telegram Channel ID(s)
TARGET_CHANNELS = [-100123456789] 

@client.on(events.NewMessage(chats=TARGET_CHANNELS))
async def handler(event):
    text = event.message.message
    logger.info(f"📩 New Message Received:\n{text}")
    
    signal = parse_signal(text)
    if not signal:
        logger.warning("Could not extract a valid trade setup from the message.")
        return
        
    logger.info(f"🎯 Parsed: {signal['action']} {signal['symbol']} | SL: {signal['sl']} | TP: {signal['tp']}")
    
    # --- THE ROUTER ---
    # Crypto goes to Binance, Forex/Indices go to MT5
    if "USDT" in signal['symbol'] or "BTC" in signal['symbol']:
        logger.info("➡️ Routing signal to Binance (Crypto Engine)...")
        # Example execution (assuming your binance_client has an execute_signal method)
        # binance.execute_signal(signal) 
    else:
        logger.info("➡️ Routing signal to MetaTrader 5 (Forex Engine)...")
        mt5.execute_signal(signal)

async def main():
    await client.start(phone=PHONE)
    logger.info("🟢 Unified Trading Router is ACTIVE. Listening for Crypto and Forex signals...")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())