# 📈 IBKR TWS Automated Trading Bot

This is an automated trading bot that connects to Interactive Brokers' **TWS (Trader Workstation)** via the IB API. It is designed to execute **live market orders**, track **positions**, and implement **three technical trading strategies** using popular indicators:
(Imp -->for the successfull connection to Api TWS must be Locally running in Background !)

- EMA 200 (Exponential Moving Average)
- MACD (Moving Average Convergence Divergence)
- Donchian Channels

---

## 🚀 Features

- ✅ Seamless integration with **IBKR TWS or IB Gateway**
- ✅ Automated **market order execution** (buy/sell)
- ✅ Real-time **position tracking** and **account monitoring**
- ✅ Supports **multiple strategy modules**, each independently configurable
- ✅ Modular architecture for easy extension or customization
- ✅ Error handling and logging for monitoring bot performance

---

## ⚙️ Strategies Overview

### 1. 📉 EMA 200-Based Trend Strategy
Uses the 200-period Exponential Moving Average to identify long-term trends.

- **Buy Signal**: Price crosses **above** the EMA 200 → Indicates bullish trend
- **Sell Signal**: Price crosses **below** the EMA 200 → Indicates bearish trend

> Often used for identifying macro trends in high-timeframe trading.

---

### 2. ⚡ MACD Strategy
A momentum-based approach using MACD and Signal line crossovers.

- **Buy Signal**: MACD crosses **above** the Signal line (bullish divergence)
- **Sell Signal**: MACD crosses **below** the Signal line (bearish divergence)

> Includes options for histogram filtering and divergence detection (customizable).

---

### 3. 📊 Donchian Channels Breakout Strategy
Captures breakouts using the highest high and lowest low of a configurable period (default: 20 candles).

- **Buy Signal**: Price breaks **above** the 20-period high
- **Sell Signal**: Price breaks **below** the 20-period low

> Ideal for trend breakout trading and volatility plays.

---

## 🧠 Architecture

## Technologies

- Python
- IBKR TWS API (`ib_async` or `ibapi`)
- Pandas, NumPy, Matplotlib (for data analysis and plotting)
- Technical Analysis libraries (e.g. `ta`, `bt`, or `talib`)

## Requirements

- IBKR TWS or IB Gateway installed and running
- Python 3.8+
- API access enabled in TWS

## Installation

```bash
git clone https://github.com/k9tx/TRADE-IBKR
cd TRADE-IBKR
pip install -r requirements.txt
