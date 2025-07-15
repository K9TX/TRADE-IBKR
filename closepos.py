from ib_async import *
import asyncio
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    ib = IB()
    try:
        await ib.connectAsync('127.0.0.1', 7497, clientId=123)
        logger.info("Connected to IB")

        # Get all open positions
        positions = await ib.reqPositionsAsync()
        if not positions:
            logger.info("No open positions to close.")
        else:
            for pos in positions:
                if pos.position > 0:
                    # Place a market sell order to close long positions
                    order = MarketOrder('SELL', pos.position)
                    trade = ib.placeOrder(pos.contract, order)
                    logger.info(f"Sell order placed to close position: {pos.contract.symbol} {pos.position}")
                elif pos.position < 0:
                    # Place a market buy order to close short positions
                    order = MarketOrder('BUY', abs(pos.position))
                    trade = ib.placeOrder(pos.contract, order)
                    logger.info(f"Buy order placed to close short position: {pos.contract.symbol} {abs(pos.position)}")
                else:
                    logger.info(f"No position to close for {pos.contract.symbol}")
                await asyncio.sleep(1)  # Give IB time to process each order

            # Optional: Wait for all orders to fill
            await asyncio.sleep(5)
            logger.info("All close orders sent. Check TWS for order status.")

    except Exception as e:
        logger.error(f"Connection or setup error: {e}")
    finally:
        if ib.isConnected():
            ib.disconnect()
            logger.info("Disconnected from IB")

if __name__ == "__main__":
    asyncio.run(main())