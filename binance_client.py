from binance.client import Client
from binance.exceptions import BinanceAPIException
from typing import Optional, Dict, List
from config import Config, logger
import pandas as pd

class BinanceClient:
    """Wrapper for Binance API interactions"""
    
    def __init__(self):
        self.client = None
        self.testnet = Config.BINANCE_TESTNET
        self.futures = Config.BINANCE_FUTURES
        self._initialize_client()
        
    def _initialize_client(self):
        """Initialize Binance client"""
        try:
            if self.testnet:
                self.client = Client(
                    Config.BINANCE_API_KEY,
                    Config.BINANCE_API_SECRET,
                    testnet=True
                )
                logger.info("Binance Testnet client initialized")
            else:
                self.client = Client(
                    Config.BINANCE_API_KEY,
                    Config.BINANCE_API_SECRET
                )
                logger.warning("LIVE Binance client initialized - BE CAREFUL!")
        except Exception as e:
            logger.error(f"Failed to initialize Binance client: {e}")
            raise

    def get_account_info(self) -> Dict:
        """Get account balance and information"""
        try:
            account = self.client.get_account()

            total_equity = 0.0
            for balance in account['balances']:
                asset = balance['asset']
                free = float(balance['free'])
                locked = float(balance['locked'])

                if free > 0 or locked > 0:
                    if asset != 'USDT':
                        try:
                            symbol = f"{asset}USDT"
                            # Pass silent=True so we don't log Testnet dust errors
                            price = self.get_current_price(symbol, silent=True)
                            total_equity += (free + locked) * price
                        except:
                            pass
                    else:
                        total_equity += free + locked

            usdt_balance = float(next(
                (b['free'] for b in account['balances'] if b['asset'] == 'USDT'), 0
            ))

            return {
                'total_equity': total_equity,
                'available_balance': usdt_balance,
                'maker_commission': float(account['makerCommission']),
                'taker_commission': float(account['takerCommission']),
                'can_trade': account['canTrade'],
                'can_withdraw': account['canWithdraw']
            }
        except BinanceAPIException as e:
            logger.error(f"API Error getting account info: {e}")
            return {}

    def get_current_price(self, symbol: str, silent: bool = False) -> float:
        """Get current price for symbol"""
        try:
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            return float(ticker['price'])
        except Exception as e:
            # -1121 is the invalid symbol error. Only log it if we didn't ask it to be silent.
            if not (silent and "-1121" in str(e)):
                logger.error(f"Error getting price for {symbol}: {e}")
            return 0.0
            
    def get_klines(self, symbol: str, interval: str, limit: int = 100) -> pd.DataFrame:
        """Get historical klines/candles"""
        try:
            klines = self.client.get_klines(
                symbol=symbol,
                interval=interval,
                limit=limit
            )
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            logger.error(f"Error getting klines for {symbol}: {e}")
            return pd.DataFrame()
            
    def create_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None
    ) -> Dict:
        """Create a new spot order"""
        try:
            params = {
                'symbol': symbol,
                'side': side,
                'type': order_type,
                'quantity': quantity
            }
            if price and order_type in ['LIMIT', 'STOP_LOSS_LIMIT', 'TAKE_PROFIT_LIMIT']:
                params['price'] = str(price)
                params['timeInForce'] = 'GTC'
                
            order = self.client.create_order(**params)
            logger.info(f"Order created: {order}")
            return order
        except BinanceAPIException as e:
            logger.error(f"Order creation failed: {e}")
            return {'error': str(e)}
            
    def create_oco_order(self, symbol: str, side: str, quantity: float, price: float, stopPrice: float) -> Dict:
        """Creates a One-Cancels-the-Other (OCO) order (Take profit + Stop loss)"""
        try:
            order = self.client.create_oco_order(
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=str(price),
                stopPrice=str(stopPrice),
                stopLimitPrice=str(stopPrice),
                stopLimitTimeInForce='GTC'
            )
            logger.info(f"OCO Order created: {order}")
            return order
        except BinanceAPIException as e:
            logger.error(f"OCO creation failed: {e}")
            return {'error': str(e)}

    def cancel_order(self, symbol: str, order_id: int) -> bool:
        """Cancel an order"""
        try:
            result = self.client.cancel_order(symbol=symbol, orderId=order_id)
            logger.info(f"Order {order_id} cancelled: {result}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            return False

    def get_symbol_info(self, symbol: str) -> Dict:
        """Get symbol-specific information"""
        try:
            info = self.client.get_symbol_info(symbol)
            return info
        except Exception as e:
            logger.error(f"Error getting symbol info for {symbol}: {e}")
            return {}
            
    def calculate_lot_size(self, symbol: str, usdt_amount: float) -> float:
        """Calculate quantity based on USDT amount considering lot sizes"""
        try:
            price = self.get_current_price(symbol)
            if price == 0: return 0.0
            raw_quantity = usdt_amount / price
            symbol_info = self.get_symbol_info(symbol)
            if symbol_info:
                for filt in symbol_info['filters']:
                    if filt['filterType'] == 'LOT_SIZE':
                        step_size = float(filt['stepSize'])
                        min_qty = float(filt['minQty'])
                        max_qty = float(filt['maxQty'])
                        
                        import math
                        quantity = math.floor(raw_quantity / step_size) * step_size
                        quantity = max(min_qty, min(quantity, max_qty))
                        
                        # Format avoiding scientific notation
                        precision = int(round(-math.log(step_size, 10), 0))
                        return float(f"{quantity:.{precision}f}")
            return round(raw_quantity, 6)
        except Exception as e:
            logger.error(f"Error calculating lot size: {e}")
            return 0.0