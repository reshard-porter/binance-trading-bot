import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Enum as SQLEnum
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
from models import OrderStatus, Trade

Base = declarative_base()

class TradeDB(Base):
    __tablename__ = 'trades'
    id = Column(String, primary_key=True)
    symbol = Column(String)
    side = Column(String)
    entry_price = Column(Float)
    quantity = Column(Float)
    quote_quantity = Column(Float)
    stop_loss = Column(Float)
    take_profit = Column(Float)
    order_id = Column(Integer)
    status = Column(SQLEnum(OrderStatus))
    open_time = Column(DateTime, default=datetime.utcnow)
    source_name = Column(String)
    comment = Column(String)
    pnl = Column(Float, nullable=True)
    pnl_percent = Column(Float, nullable=True)
    close_time = Column(DateTime, nullable=True)
    close_price = Column(Float, nullable=True)

class Database:
    def __init__(self):
        db_url = os.getenv("DB_URL", "sqlite:///data/trades.db")
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        
    def add_trade(self, trade: Trade):
        session = self.Session()
        db_trade = TradeDB(
            id=trade.id, symbol=trade.symbol, side=trade.side, entry_price=trade.entry_price,
            quantity=trade.quantity, quote_quantity=trade.quote_quantity, stop_loss=trade.stop_loss,
            take_profit=trade.take_profit, order_id=trade.order_id, status=trade.status,
            open_time=trade.open_time, source_name=trade.source_name, comment=trade.comment
        )
        session.add(db_trade)
        session.commit()
        session.close()

    def update_trade(self, trade_id: str, **kwargs):
        session = self.Session()
        session.query(TradeDB).filter(TradeDB.id == trade_id).update(kwargs)
        session.commit()
        session.close()

    def get_active_trades(self):
        session = self.Session()
        trades = session.query(TradeDB).filter(TradeDB.status == OrderStatus.FILLED).all()
        session.close()
        return trades
        
    def get_all_trades(self):
        session = self.Session()
        trades = session.query(TradeDB).order_by(TradeDB.open_time.desc()).all()
        session.close()
        return trades