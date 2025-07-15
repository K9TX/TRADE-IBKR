from ib_async import *
import asyncio
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def calculate_ema(data, period=200):
    """Calculate Exponential Moving Average"""
    return pd.Series(data).ewm(span=period, adjust=False).mean().iloc[-1]

async def get_historical_data(ib, contract, duration='1 Y', bar_size='1 day'):
    """Get historical data for EMA calculation"""
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

async def main():
    ib = IB()
    try:
        # Connect to IB
        await ib.connectAsync('127.0.0.1', 7497, clientId=123)
        logger.info("Connected to IB")

        # Define Tesla contract
        tesla = Stock('TSLA', 'SMART', 'USD')
        await ib.qualifyContractsAsync(tesla)
        logger.info("Tesla contract qualified")

        # Get current market data
        ticker = ib.reqMktData(tesla, '', False, False)
        await asyncio.sleep(2)  # Wait for market data
        current_price = ticker.last if ticker.last else ticker.close
        if current_price is None:
            logger.error("Could not fetch current price for Tesla")
            return
        logger.info(f"Current Tesla price: {current_price}")

        # Get historical data and calculate EMA 200
        historical_prices = await get_historical_data(ib, tesla)
        ema_200 = calculate_ema(historical_prices, period=200)
        logger.info(f"EMA 200: {ema_200}")

        # Trading logic
        position = 0
        portfolio = ib.portfolio()
        for item in portfolio:
            if item.contract.symbol == 'TSLA':
                position = item.position
                break

        if current_price > ema_200:  # Bullish signal
            if position <= 0:  # No existing long position
                # Calculate position size (example: investing 10% of account equity)
                account = await ib.accountSummaryAsync()
                equity = float([v.value for v in account if v.tag == 'NetLiquidation'][0])
                investment_amount = equity * 0.10  # 10% of account
                shares_to_buy = int(investment_amount / current_price)

                if shares_to_buy > 0:
                    # Place buy order
                    order = MarketOrder('BUY', shares_to_buy)
                    trade = ib.placeOrder(tesla, order)
                    logger.info(f"Buy order placed for {shares_to_buy} Tesla shares")
                    
                    # Wait for order to fill
                    while not trade.isDone():
                        await asyncio.sleep(1)
                    
                    if trade.orderStatus.status == 'Filled':
                        logger.info(f"Order filled at average price: {trade.orderStatus.avgFillPrice}")
                    else:
                        logger.error(f"Order failed with status: {trade.orderStatus.status}")
                else:
                    logger.info("Insufficient funds to place order")
            else:
                logger.info("Already holding Tesla position")
        else:
            logger.info("Price below EMA 200, no buy signal")

    except Exception as e:
        logger.error(f"Error occurred: {e}")
    finally:
        if ib.isConnected():
            ib.disconnect()
            logger.info("Disconnected from IB")

if __name__ == "__main__":
    asyncio.run(main())
