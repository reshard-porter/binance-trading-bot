import asyncio
import uuid
from datetime import datetime
from models import Trade, OrderStatus
from config import logger

class ExecutionEngine:
    def __init__(self, binance_client, risk_manager, database):
        self.client = binance_client
        self.risk = risk_manager
        self.db = database
        
    async def execute_signal(self, signal):
        logger.info(f"Execution Engine Evaluating Signal: {signal.symbol} {signal.order_type.name}")
        
        account_info = self.client.get_account_info()
        available_usdt = account_info.get('available_balance', 0)
        
        active_trades = len(self.db.get_active_trades())
        can_trade, reason = self.risk.can_execute_trade(account_info.get('total_equity', 0), active_trades)
        
        if not can_trade:
            logger.warning(f"Trade blocked by Risk Manager: {reason}")
            return
            
        current_price = self.client.get_current_price(signal.symbol)
        entry_price = signal.entry_price or current_price
        
        # Determine Trade Side
        side = 'BUY' if 'BUY' in signal.order_type.value else 'SELL'
        
        # Crypto spot generally restricts short selling unless on margin/futures. 
        # For this Spot implementation, we enforce Long-only (Buy to open).
        if side == 'SELL' and not self.client.futures:
            logger.warning("Short selling signals ignored on standard spot exchange.")
            return

        qty_coins = self.risk.calculate_position_size(entry_price, signal.stop_loss, available_usdt)
        qty_formatted = self.client.calculate_lot_size(signal.symbol, qty_coins * entry_price)
        
        if qty_formatted <= 0:
            logger.warning(f"Calculated quantity is too small for {signal.symbol}")
            return
            
        logger.info(f"Executing MARKET {side} for {qty_formatted} {signal.symbol} at ~{current_price}")
        
        # 1. Execute Entry (Market Order)
        entry_order = self.client.create_order(
            symbol=signal.symbol,
            side=side,
            order_type='MARKET',
            quantity=qty_formatted
        )
        
        if 'error' in entry_order:
            logger.error(f"Entry Execution Failed: {entry_order['error']}")
            return
            
        filled_price = entry_order.get('fills', [{}])[0].get('price', current_price)
        filled_price = float(filled_price)
        logger.info(f"Entry successful! Filled at {filled_price}")
        
        # 2. Setup Protection (OCO Order: Stop Loss + Take Profit)
        # Assuming Long side (we bought, now we set an OCO to Sell)
        oco_side = 'SELL' if side == 'BUY' else 'BUY'
        
        # We split the OCO if multiple TPs exist
        split_qty = self.client.calculate_lot_size(signal.symbol, (qty_formatted * filled_price) / len(signal.take_profits))
        
        for tp in signal.take_profits:
            if split_qty > 0:
                oco_response = self.client.create_oco_order(
                    symbol=signal.symbol,
                    side=oco_side,
                    quantity=split_qty,
                    price=float(tp),
                    stopPrice=float(signal.stop_loss)
                )
                if 'error' in oco_response:
                    logger.error(f"Failed to place OCO for TP {tp}: {oco_response['error']}")
                    
        # 3. Record Trade in DB
        trade = Trade(
            id=str(uuid.uuid4()),
            symbol=signal.symbol,
            side=side,
            entry_price=filled_price,
            quantity=qty_formatted,
            quote_quantity=qty_formatted * filled_price,
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profits[-1], # Primary TP
            order_id=entry_order.get('orderId', 0),
            status=OrderStatus.FILLED,
            open_time=datetime.utcnow(),
            source_name=signal.source_name,
            comment=f"Telegram Signal from {signal.source_name}"
        )
        self.db.add_trade(trade)