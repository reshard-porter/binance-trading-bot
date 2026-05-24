import asyncio
from telethon import TelegramClient, events
from config import Config, logger
from telegram_signal_parser import SignalParser
from app import ExecutionEngine
from risk_manager import RiskManager
from binance_client import BinanceClient
from database import Database

async def main():
    logger.info("Initializing System Components...")
    
    # Initialize Core Services
    db = Database()
    binance = BinanceClient()
    risk = RiskManager()
    engine = ExecutionEngine(binance, risk, db)
    parser = SignalParser()
    
    # Telegram Client
    client = TelegramClient('sessions/trading_session', Config.TELEGRAM_API_ID, Config.TELEGRAM_API_HASH)
    
    # Fetch active chats to monitor
    active_chats = [chat for chat in Config.SIGNAL_CHATS if chat.get('active')]
    active_chat_ids = [chat['id'] for chat in active_chats]
    
    logger.info(f"Connecting to Telegram. Monitoring {len(active_chat_ids)} channels...")

    @client.on(events.NewMessage(chats=active_chat_ids))
    async def handler(event):
        try:
            chat = await event.get_chat()
            chat_title = getattr(chat, 'title', 'Unknown Channel')
            
            logger.info(f"Incoming message from {chat_title}...")
            
            # Anti-Ghost Signal Logic (wait and verify it isn't immediately deleted)
            await asyncio.sleep(1.5)
            
            signal = parser.extract_signal(event.raw_text, chat_title, event.chat_id, event.id)
            if signal:
                await engine.execute_signal(signal)
                
        except Exception as e:
            logger.error(f"Error handling message: {e}")

    await client.start(phone=Config.TELEGRAM_PHONE)
    logger.info("Bot is running and actively listening for signals. Press Ctrl+C to stop.")
    await client.run_until_disconnected()

if __name__ == '__main__':
    import os
    os.makedirs('sessions', exist_ok=True)
    asyncio.run(main())