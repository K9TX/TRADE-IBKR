from ib_async import *
import asyncio
import logging
#this is for Spot Buy Market Order for WIPRO stock on NSE
# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    ib = IB()
    try:
        await ib.connectAsync('127.0.0.1', 7497, clientId=123)
        logger.info("Connected to IB")

        # Define WIPRO stock contract for NSE
        wipro_contract = Stock('WIPRO', 'NSE', 'INR')
        logger.info("Qualifying WIPRO contract...")
        await ib.qualifyContractsAsync(wipro_contract)
        logger.info("Qualified WIPRO contract.")

        # Place a market buy order for WIPRO (quantity: 100)
        order = MarketOrder('BUY', 100)
        trade = ib.placeOrder(wipro_contract, order)
        logger.info(f"Immediate Buy order placed for WIPRO: {trade}")

    except Exception as e:
        logger.error(f"Connection or setup error: {e}")
    finally:
        if ib.isConnected():
            ib.disconnect()
            logger.info("Disconnected from IB")

if __name__== "__main__":
    asyncio.run(main())