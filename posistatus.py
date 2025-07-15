from ib_async import *
import asyncio
import logging
import pandas as pd

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def show_open_positions(ib):
    """
    Show only current open positions (positions with non-zero quantity).
    """
    positions = await ib.reqPositionsAsync()
    open_positions = [pos for pos in positions if pos.position != 0]

    print("Current Open Positions:")
    if not open_positions:
        print("No open positions found.")
    else:
        data = []
        for pos in open_positions:
            data.append({
                'Symbol': pos.contract.symbol,
                'Exchange': pos.contract.exchange,
                'Currency': pos.contract.currency,
                'Position': pos.position,
                'Account': pos.account
            })
        df = pd.DataFrame(data)
        print(df)

async def show_trade_history(ib):
    """
    Show trade history (executions).
    """
    executions = await ib.reqExecutionsAsync()
    print("\nTrade History:")
    if not executions:
        print("No trade history found.")
    else:
        exec_data = []
        for exec in executions:
            exec_data.append({
                'Symbol': exec.contract.symbol,
                'Exchange': exec.contract.exchange,
                'Currency': exec.contract.currency,
                'Side': exec.execution.side,
                'Shares': exec.execution.shares,
                'Price': exec.execution.price,
                'Time': exec.execution.time
            })
        exec_df = pd.DataFrame(exec_data)
        print(exec_df)

async def show_pnl(ib):
    """
    Show unrealized and realized PnL for the account.
    """
    account_summary = await ib.reqAccountSummaryAsync()
    print("All account summary tags and values:")
    for item in account_summary:
        print(f"{item.tag}: {item.value}")


    """
    Show unrealized PnL for each open position (if supported).
    """
    positions = await ib.reqPositionsAsync()
    open_positions = [pos for pos in positions if pos.position != 0]
    if not open_positions:
        print("No open positions found.")
        return

    print("Unrealized PnL per open position:")
    for pos in open_positions:
        try:
            # You need your account code and the contract's conId
            pnl = await ib.reqPnLSingleAsync(account=pos.account, modelCode="", conId=getattr(pos.contract, "conId", 0))
            print(f"{pos.contract.symbol} ({pos.contract.exchange}): Unrealized PnL = {pnl.unrealizedPnL}, Realized PnL = {pnl.realizedPnL}")
        except Exception as e:
            print(f"Could not fetch PnL for {pos.contract.symbol}: {e}")

async def main():
    ib = IB()
    try:
        await ib.connectAsync('127.0.0.1', 7497, clientId=123)
        logger.info("Connected to IB")

        # Show trade history
        await show_trade_history(ib)
        # Show open positions (non-zero only)
        await show_open_positions(ib)
     

    except Exception as e:
        logger.error(f"Connection or setup error: {e}")
    finally:
        if ib.isConnected():
            ib.disconnect()
            logger.info("Disconnected from IB")

if __name__ == "__main__":
    asyncio.run(main())