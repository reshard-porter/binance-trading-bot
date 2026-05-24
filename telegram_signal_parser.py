import re
from typing import Optional, List
from datetime import datetime
from models import SignalData, OrderType
from config import Config, logger

class SignalParser:
    """Parse trading signals from Telegram messages"""
    
    def __init__(self):
        self.pending_messages = {}  
        self.processed_messages = set()  
        
    def extract_signal(self, text: str, source_name: str, source_id: int, message_id: int) -> Optional[SignalData]:
        msg_key = f"{source_id}_{message_id}"
        if msg_key in self.processed_messages:
            return None
            
        text_upper = text.upper()
        
        relevant_symbols = ["BTC", "ETH", "BNB", "SOL", "ADA", "XAUUSD", "GOLD", "XAU/USD"]
        if not any(symbol in text_upper for symbol in relevant_symbols):
            return None
            
        order_type = self._extract_order_type(text_upper)
        if not order_type:
            return None
            
        entry_price = self._extract_entry_price(text_upper)
        stop_loss = self._extract_stop_loss(text_upper)
        take_profits = self._extract_take_profits(text_upper)
        
        if not stop_loss or not take_profits:
            return None
            
        symbol = self._extract_symbol(text_upper, source_name)
        tradable_symbol = Config.SYMBOL_MAPPING.get(symbol, symbol)
        
        if tradable_symbol not in Config.TRADING_SYMBOLS and tradable_symbol != symbol:
            for ts in Config.TRADING_SYMBOLS:
                if tradable_symbol in ts or ts in tradable_symbol:
                    tradable_symbol = ts
                    break
                    
        if tradable_symbol not in Config.TRADING_SYMBOLS:
            logger.warning(f"Symbol {tradable_symbol} not in trading list")
            return None
            
        signal = SignalData(
            source_name=source_name,
            source_id=source_id,
            symbol=tradable_symbol,
            order_type=order_type,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profits=take_profits,
            timestamp=datetime.now(),
            raw_message=text[:500],
            message_id=message_id
        )
        
        self.processed_messages.add(msg_key)
        logger.info(f"Signal extracted from {source_name}: {signal.symbol} {signal.order_type.name}")
        return signal
        
    def _extract_order_type(self, text: str) -> Optional[OrderType]:
        patterns = [
            (r'\bBUY\s*LIMIT\b', OrderType.BUY_LIMIT),
            (r'\bSELL\s*LIMIT\b', OrderType.SELL_LIMIT),
            (r'\bBUY\s*STOP\b', OrderType.BUY_STOP),
            (r'\bSELL\s*STOP\b', OrderType.SELL_STOP),
            (r'\b(LONG|BUY)\b', OrderType.BUY),
            (r'\b(SHORT|SELL)\b', OrderType.SELL),
        ]
        for pattern, order_type in patterns:
            if re.search(pattern, text): return order_type
        return None
        
    def _extract_entry_price(self, text: str) -> Optional[float]:
        patterns = [
            r'(?:ENTRY|@|AT|NOW|ENTER)\s*:?\s*(\d+(?:\.\d+)?)',
            r'(?:BUY|SELL|LONG|SHORT)\s+(?:AT\s+)?(\d+(?:\.\d+)?)',
            r'PRICE\s*:?\s*(\d+(?:\.\d+)?)'
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match: return float(match.group(1))
        return None
        
    def _extract_stop_loss(self, text: str) -> Optional[float]:
        patterns = [r'(?:SL|STOP\s*LOSS|STOP)\s*:?\s*(\d+(?:\.\d+)?)', r'STOP\s+AT\s*:?\s*(\d+(?:\.\d+)?)']
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match: return float(match.group(1))
        return None
        
    def _extract_take_profits(self, text: str) -> List[float]:
        tps = []
        tp_pattern = r'(?:TP|TAKE\s*PROFIT)\s*(\d*)\s*:?\s*(\d+(?:\.\d+)?)'
        matches = re.findall(tp_pattern, text, re.IGNORECASE)
        
        if matches:
            tps = [float(match[1]) for match in matches]
        else:
            tp_section = re.search(r'(?:TP|TAKE\s*PROFIT)[\s:]*([\d\s/\.,]+)', text, re.IGNORECASE)
            if tp_section:
                numbers = re.findall(r'\d+(?:\.\d+)?', tp_section.group(1))
                tps = [float(n) for n in numbers]
                
        tps = sorted(list(set(tps)))
        if len(tps) > Config.MAX_CONCURRENT_TRADES:
            tps = tps[:Config.MAX_CONCURRENT_TRADES]
        return tps
        
    def _extract_symbol(self, text: str, source_name: str) -> str:
        crypto_symbols = {
            'BTC': 'BTCUSDT', 'ETH': 'ETHUSDT', 'BNB': 'BNBUSDT',
            'SOL': 'SOLUSDT', 'ADA': 'ADAUSDT', 'XRP': 'XRPUSDT'
        }
        for crypto, pair in crypto_symbols.items():
            if crypto in text: return pair
        if 'XAUUSD' in text or 'GOLD' in text or 'XAU/USD' in text: return 'XAUUSD'
        return 'BTCUSDT'