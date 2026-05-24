from typing import Tuple, Optional, List
from datetime import datetime
import pandas as pd
from models import Trade
from config import Config, logger

class RiskManager:
    """Risk management system"""
    
    def __init__(self):
        self.daily_pnl = 0.0
        self.peak_equity = Config.TOTAL_CAPITAL_USDT
        self.consecutive_losses = 0
        self.cooldown_until = None
        
    def can_execute_trade(self, current_equity: float, open_positions: int) -> Tuple[bool, str]:
        """Check if trade can be executed based on risk rules"""
        
        if self.cooldown_until and datetime.now() < self.cooldown_until:
            return False, f"Cooldown active until {self.cooldown_until}"
            
        if open_positions >= Config.MAX_CONCURRENT_TRADES:
            return False, f"Max concurrent trades reached ({Config.MAX_CONCURRENT_TRADES})"
            
        daily_loss_pct = abs(self.daily_pnl / Config.TOTAL_CAPITAL_USDT) * 100
        if self.daily_pnl < 0 and daily_loss_pct >= Config.MAX_DAILY_LOSS_PCT:
            return False, f"Daily loss limit reached ({daily_loss_pct:.2f}% > {Config.MAX_DAILY_LOSS_PCT}%)"
            
        if current_equity > self.peak_equity:
            self.peak_equity = current_equity
            
        drawdown = ((self.peak_equity - current_equity) / self.peak_equity) * 100
        if drawdown >= Config.MAX_DRAWDOWN_PCT:
            return False, f"Max drawdown reached ({drawdown:.2f}% > {Config.MAX_DRAWDOWN_PCT}%)"
            
        if self.consecutive_losses >= 3:
            self.cooldown_until = datetime.now() + pd.Timedelta(minutes=15)
            self.consecutive_losses = 0
            return False, f"3 consecutive losses, cooling down 15m"
            
        return True, "OK"
        
    def calculate_position_size(self, entry_price: float, stop_loss: float, account_balance: float, risk_percent: float = Config.RISK_PER_TRADE_PCT) -> float:
        """Calculate position size based on risk percent and distance to stop loss"""
        if account_balance <= 0 or entry_price <= 0:
            return 0.0

        risk_amount = account_balance * (risk_percent / 100)
        risk_per_coin = abs(entry_price - stop_loss)
        
        if risk_per_coin == 0:
            return 0.0
            
        # Target position size to lose exactly 'risk_amount' if SL is hit
        position_size_coins = risk_amount / risk_per_coin
        
        # Hard cap check based on account balance
        max_position_usdt = account_balance * (Config.MAX_POSITION_SIZE_PCT / 100)
        max_coins_allowed = max_position_usdt / entry_price
        
        final_size = min(position_size_coins, max_coins_allowed)
        logger.info(f"Risk calculation: Account=${account_balance:.2f} | Risk Amount=${risk_amount:.2f} | SL Distance=${risk_per_coin:.2f} | Allowed={final_size} coins")
        
        return final_size