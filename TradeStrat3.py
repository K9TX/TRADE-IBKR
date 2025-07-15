from ib_async import *
import asyncio
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DonchianStrategy:
    def __init__(self, period=20):
        """
        Initialize Donchian Channel Strategy
        period: Number of periods for channel calculation (default 20 periods = 100 minutes)
        """
        self.period = period
        
    def calculate_channels(self, highs, lows):
        """Calculate Donchian Channels"""
        upper_channel = pd.Series(highs).rolling(window=self.period).max().iloc[-1]
        lower_channel = pd.Series(lows).rolling(window=self.period).min().iloc[-1]
        middle_channel = (upper_channel + lower_channel) / 2
        
        return {
            'upper': upper_channel,
            'lower': lower_channel,
            'middle': middle_channel,
            'prev_upper': pd.Series(highs).rolling(window=self.period).max().iloc[-2],
            'prev_lower': pd.Series(lows).rolling(window=self.period).max().iloc[-2]
        }

async def get_historical_data(ib, contract, duration='2 D', bar_size='5 mins'):
    """Get historical 5-minute bar data"""
    bars = await ib.reqHistoricalDataAsync(
        contract,
        endDateTime='',
        durationStr=duration,
        barSizeSetting=bar_size,
        whatToShow='TRADES',
        useRTH=True,
        formatDate=1
    )
    return {
        'highs': [bar.high for bar in bars],
        'lows': [bar.low for bar in bars],
        'closes': [bar.close for bar in bars]
    }

async def get_current_position(ib, symbol):
    """Get current position for a symbol"""
    portfolio = ib.portfolio()
    for item in portfolio:
        if item.contract.symbol == symbol:
            return item.position
    return 0

async def place_order(ib, contract, action, quantity, order_type='MKT', stop_price=None):
    """Place and monitor an order"""
    if order_type == 'MKT':
        order = MarketOrder(action, quantity)
    elif order_type == 'STP':
        order = StopOrder(action, quantity, stop_price)
    
    trade = ib.placeOrder(contract, order)
    logger.info(f"{action} {order_type} order placed for {quantity} shares" + 
                (f" at {stop_price}" if stop_price else ""))
    
    # Wait for order to fill
    while not trade.isDone():
        await asyncio.sleep(1)
    
    if trade.orderStatus.status == 'Filled':
        logger.info(f"Order filled at average price: {trade.orderStatus.avgFillPrice}")
        return True
    else:
        logger.error(f"Order failed with status: {trade.orderStatus.status}")
        return False

async def main():
    ib = IB()
    try:
        # Connect to IB
        await ib.connectAsync('127.0.0.1', 7497, clientId=123)
        logger.info("Connected to IB")

        # Initialize strategy
        donchian_strategy = DonchianStrategy(period=20)  # 20 periods = 100 minutes
        symbol = 'MSFT'  # Trading Microsoft stock
        
        # Define stock contract
        stock = Stock(symbol, 'SMART', 'USD')
        await ib.qualifyContractsAsync(stock)
        logger.info(f"{symbol} contract qualified")

        # Trading state variables
        entry_price = None
        stop_loss = None

        while True:  # Continuous monitoring loop
            try:
                # Get current market data
                ticker = ib.reqMktData(stock, '', False, False)
                await asyncio.sleep(2)  # Wait for market data
                current_price = ticker.last if ticker.last else ticker.close
                
                if current_price is None:
                    logger.error(f"Could not fetch current price for {symbol}")
                    continue
                
                logger.info(f"Current {symbol} price: {current_price}")

                # Get historical data and calculate Donchian Channels
                historical_data = await get_historical_data(ib, stock)
                channels = donchian_strategy.calculate_channels(
                    historical_data['highs'],
                    historical_data['lows']
                )
                
                logger.info(f"Upper Channel: {channels['upper']:.2f}")
                logger.info(f"Middle Channel: {channels['middle']:.2f}")
                logger.info(f"Lower Channel: {channels['lower']:.2f}")

                # Get current position
                position = await get_current_position(ib, symbol)
                
                # Calculate position size (example: investing 5% of account equity)
                account = await ib.accountSummaryAsync()
                equity = float([v.value for v in account if v.tag == 'NetLiquidation'][0])
                max_position = int((equity * 0.05) / current_price)  # 5% of account

                # Trading logic
                if position == 0:  # No position, look for entry
                    # Breakout strategy
                    if current_price > channels['upper']:  # Bullish breakout
                        # Enter long position
                        shares_to_buy = max_position
                        if shares_to_buy > 0:
                            success = await place_order(ib, stock, 'BUY', shares_to_buy)
                            if success:
                                entry_price = current_price
                                # Set stop loss at lower channel
                                stop_loss = channels['lower']
                                logger.info(f"Long position entered at {entry_price:.2f}")
                                logger.info(f"Stop loss set at {stop_loss:.2f}")
                        else:
                            logger.info("Insufficient funds to place order")
                            
                    elif current_price < channels['lower']:  # Bearish breakout
                        # Enter short position
                        shares_to_short = max_position
                        if shares_to_short > 0:
                            success = await place_order(ib, stock, 'SELL', shares_to_short)
                            if success:
                                entry_price = current_price
                                # Set stop loss at upper channel
                                stop_loss = channels['upper']
                                logger.info(f"Short position entered at {entry_price:.2f}")
                                logger.info(f"Stop loss set at {stop_loss:.2f}")
                        else:
                            logger.info("Insufficient funds to place order")

                else:  # Managing existing position
                    if position > 0:  # Long position
                        # Update trailing stop to lower channel
                        new_stop = channels['lower']
                        if new_stop > stop_loss:  # Trail stop only upward
                            stop_loss = new_stop
                            logger.info(f"Updated trailing stop to {stop_loss:.2f}")
                        
                        # Check if stop loss is hit
                        if current_price < stop_loss:
                            success = await place_order(ib, stock, 'SELL', position)
                            if success:
                                logger.info(f"Long position closed at {current_price:.2f}")
                                entry_price = None
                                stop_loss = None
                                
                    else:  # Short position
                        # Update trailing stop to upper channel
                        new_stop = channels['upper']
                        if new_stop < stop_loss:  # Trail stop only downward
                            stop_loss = new_stop
                            logger.info(f"Updated trailing stop to {stop_loss:.2f}")
                        
                        # Check if stop loss is hit
                        if current_price > stop_loss:
                            success = await place_order(ib, stock, 'BUY', abs(position))
                            if success:
                                logger.info(f"Short position closed at {current_price:.2f}")
                                entry_price = None
                                stop_loss = None

                # Wait before next check (5-minute interval)
                await asyncio.sleep(300)  # 5 minutes

            except Exception as e:
                logger.error(f"Error in trading loop: {e}")
                await asyncio.sleep(60)  # Wait a minute before retrying

    except Exception as e:
        logger.error(f"Fatal error occurred: {e}")
    finally:
        if ib.isConnected():
            ib.disconnect()
            logger.info("Disconnected from IB")

if __name__ == "__main__":
    asyncio.run(main())
