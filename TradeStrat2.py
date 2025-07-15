from ib_async import *
import asyncio
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MACDStrategy:
    def __init__(self, fast_period=12, slow_period=26, signal_period=9):
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        
    def calculate_macd(self, prices):
        """Calculate MACD and Signal line"""
        price_series = pd.Series(prices)
        
        # Calculate EMAs
        fast_ema = price_series.ewm(span=self.fast_period, adjust=False).mean()
        slow_ema = price_series.ewm(span=self.slow_period, adjust=False).mean()
        
        # Calculate MACD line
        macd_line = fast_ema - slow_ema
        
        # Calculate Signal line
        signal_line = macd_line.ewm(span=self.signal_period, adjust=False).mean()
        
        # Calculate MACD histogram
        macd_histogram = macd_line - signal_line
        
        return {
            'macd_line': macd_line.iloc[-1],
            'signal_line': signal_line.iloc[-1],
            'histogram': macd_histogram.iloc[-1],
            'prev_histogram': macd_histogram.iloc[-2] if len(macd_histogram) > 1 else 0
        }

async def get_historical_data(ib, contract, duration='3 M', bar_size='1 day'):
    """Get historical data for MACD calculation"""
    bars = await ib.reqHistoricalDataAsync(
        contract,
        endDateTime='',
        durationStr=duration,
        barSizeSetting=bar_size,
        whatToShow='TRADES',
        useRTH=True,
        formatDate=1
    )
    return [bar.close for bar in bars]

async def get_current_position(ib, symbol):
    """Get current position for a symbol"""
    portfolio = ib.portfolio()
    for item in portfolio:
        if item.contract.symbol == symbol:
            return item.position
    return 0

async def place_order(ib, contract, action, quantity):
    """Place and monitor an order"""
    order = MarketOrder(action, quantity)
    trade = ib.placeOrder(contract, order)
    logger.info(f"{action} order placed for {quantity} shares")
    
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
        macd_strategy = MACDStrategy()
        symbol = 'AAPL'  # Trading Apple stock
        
        # Define stock contract
        stock = Stock(symbol, 'SMART', 'USD')
        await ib.qualifyContractsAsync(stock)
        logger.info(f"{symbol} contract qualified")

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

                # Get historical data and calculate MACD
                historical_prices = await get_historical_data(ib, stock)
                macd_data = macd_strategy.calculate_macd(historical_prices)
                
                logger.info(f"MACD Line: {macd_data['macd_line']:.2f}")
                logger.info(f"Signal Line: {macd_data['signal_line']:.2f}")
                logger.info(f"Histogram: {macd_data['histogram']:.2f}")

                # Get current position
                position = await get_current_position(ib, symbol)
                
                # Trading logic
                # Buy signal: MACD line crosses above Signal line (histogram turns positive)
                # Sell signal: MACD line crosses below Signal line (histogram turns negative)
                
                # Calculate position size (example: investing 5% of account equity)
                account = await ib.accountSummaryAsync()
                equity = float([v.value for v in account if v.tag == 'NetLiquidation'][0])
                max_position = int((equity * 0.05) / current_price)  # 5% of account

                if macd_data['histogram'] > 0 and macd_data['prev_histogram'] <= 0:  # Bullish crossover
                    if position <= 0:  # No existing long position
                        shares_to_buy = max_position
                        if shares_to_buy > 0:
                            success = await place_order(ib, stock, 'BUY', shares_to_buy)
                            if success:
                                logger.info(f"Successfully bought {shares_to_buy} shares of {symbol}")
                        else:
                            logger.info("Insufficient funds to place order")
                    else:
                        logger.info(f"Already holding {symbol} position")

                elif macd_data['histogram'] < 0 and macd_data['prev_histogram'] >= 0:  # Bearish crossover
                    if position > 0:  # Existing long position
                        success = await place_order(ib, stock, 'SELL', position)
                        if success:
                            logger.info(f"Successfully sold {position} shares of {symbol}")
                    else:
                        logger.info("No position to sell")

                # Wait before next check (e.g., check every 5 minutes)
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
