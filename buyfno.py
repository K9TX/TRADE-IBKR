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

        # Step 1: Get current market price of NVIDIA
        nvidia_stock = Stock('NVDA', 'SMART', 'USD')
        await ib.qualifyContractsAsync(nvidia_stock)
        ticker = ib.reqMktData(nvidia_stock, '', False, False)
        await asyncio.sleep(2)  # Wait for market data
        market_price = ticker.last if ticker.last else ticker.close if hasattr(ticker, 'close') else None
        if market_price is None:
            logger.error("Could not fetch market price for NVIDIA.")
            return
        logger.info(f"Current NVIDIA market price: {market_price}")

        # Step 2: Get all available option contracts for NVIDIA (all expiries)
        option_details = await ib.reqContractDetailsAsync(Option('NVDA', '', 0, 'C', 'SMART', 'USD'))
        expiries = sorted({cd.contract.lastTradeDateOrContractMonth for cd in option_details})
        if not expiries:
            logger.error("No expiries found for NVIDIA options.")
            return
        expiry = expiries[0]  # Use the nearest expiry

        strikes = sorted({cd.contract.strike for cd in option_details if cd.contract.lastTradeDateOrContractMonth == expiry})
        if not strikes:
            logger.error("No strikes found for NVIDIA options.")
            return

        # Step 3: Find the strike price nearest to the market price
        nearest_strike = min(strikes, key=lambda x: abs(x - market_price))
        logger.info(f"Nearest strike: {nearest_strike}")

        # Step 4: Create the option contract and buy
        nvidia_call = Option('NVDA', expiry, nearest_strike, 'C', 'SMART', 'USD')
        await ib.qualifyContractsAsync(nvidia_call)
        logger.info("Qualified NVIDIA CALL option contract.")

        order = MarketOrder('BUY', 1)
        trade = ib.placeOrder(nvidia_call, order)
        logger.info(f"Immediate Buy order placed for NVIDIA CALL option (strike {nearest_strike}): {trade}")

    except Exception as e:
        logger.error(f"Connection or setup error: {e}")
    finally:
        if ib.isConnected():
            ib.disconnect()
            logger.info("Disconnected from IB")

if __name__ == "__main__":
    asyncio.run(main())