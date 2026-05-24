from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from enum import Enum

class OrderType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    BUY_LIMIT = "BUY_LIMIT"
    SELL_LIMIT = "SELL_LIMIT"
    BUY_STOP = "BUY_STOP"
    SELL_STOP = "SELL_STOP"

class OrderStatus(Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"

@dataclass
class SignalData:
    """Represents a trading signal from Telegram"""
    source_name: str
    source_id: int
    symbol: str
    order_type: OrderType
    entry_price: Optional[float]
    stop_loss: float
    take_profits: List[float]
    timestamp: datetime
    raw_message: str
    message_id: int
    
@dataclass
class Trade:
    """Represents an active trade"""
    id: str
    symbol: str
    side: str  
    entry_price: float
    quantity: float
    quote_quantity: float  
    stop_loss: float
    take_profit: float
    order_id: int
    status: OrderStatus
    open_time: datetime
    source_name: str
    comment: str
    pnl: Optional[float] = None
    pnl_percent: Optional[float] = None
    close_time: Optional[datetime] = None
    close_price: Optional[float] = None
    
@dataclass
class Position:
    """Represents current open position with real-time data"""
    trade: Trade
    current_price: float
    unrealized_pnl: float
    unrealized_pnl_percent: float
    current_sl: float
    current_tp: float
    
@dataclass
class AccountInfo:
    """Account balance and status"""
    total_equity: float
    available_balance: float
    total_unrealized_pnl: float
    total_daily_pnl: float
    total_weekly_pnl: float
    total_monthly_pnl: float
    open_positions: int
    max_drawdown: float
    current_drawdown: float
    win_rate: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    
@dataclass
class RiskMetrics:
    """Risk management metrics"""
    daily_loss_used_pct: float
    drawdown_used_pct: float
    consecutive_losses: int
    risk_per_trade: float
    max_position_size: float
    recommended_position_size: float
    is_risk_limits_reached: bool
    reason: Optional[str] = None