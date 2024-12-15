import requests
import pandas as pd
import numpy as np
import talib
from telegram import Bot
import streamlit as st

# API Keys
LUNARCRUSH_API_KEY = "your_lunarcrush_api_key"
TELEGRAM_TOKEN = "your_telegram_bot_token"
TELEGRAM_CHAT_ID = "your_chat_id"

# LunarCrush API URL
LUNARCRUSH_API = "https://api.lunarcrush.com/v2"

def fetch_lunarcrush_data(symbols):
    """Fetch social and market data for the specified symbols from LunarCrush."""
    params = {
        "key": LUNARCRUSH_API_KEY,
        "data": "assets",
        "symbol": ",".join(symbols),
    }
    response = requests.get(LUNARCRUSH_API, params=params)
    if response.status_code == 200:
        return response.json().get("data", [])
    else:
        print(f"Error fetching LunarCrush data: {response.status_code}")
        return []

def fetch_market_data():
    """Fetch top 100 coins from LunarCrush."""
    params = {
        "key": LUNARCRUSH_API_KEY,
        "data": "market",
        "sort": "galaxy_score",  # Sort by Galaxy Score
        "limit": 100,
    }
    response = requests.get(LUNARCRUSH_API, params=params)
    if response.status_code == 200:
        return response.json().get("data", [])
    else:
        print(f"Error fetching market data: {response.status_code}")
        return []

def apply_technical_analysis(prices):
    """Apply RSI and MACD on price data."""
    if len(prices) < 26:  # Ensure enough data points for MACD
        return {"rsi": None, "macd_diff": None}
    prices_array = np.array(prices)
    rsi = talib.RSI(prices_array, timeperiod=14)
    macd, macd_signal, _ = talib.MACD(prices_array, fastperiod=12, slowperiod=26, signalperiod=9)
    return {
        "rsi": rsi[-1] if len(rsi) > 0 else None,
        "macd_diff": macd[-1] - macd_signal[-1] if len(macd) > 0 and len(macd_signal) > 0 else None,
    }

def analyze_coins():
    """Analyze top coins using LunarCrush and technical analysis."""
    print("Fetching market data...")
    market_data = fetch_market_data()
    coins = []
    for coin in market_data:
        symbol = coin.get("s")
        name = coin.get("n")
        price = coin.get("p")
        galaxy_score = coin.get("gs")
        alt_rank = coin.get("acr")
        price_history = coin.get("sparkline", {}).get("price", [])

        # Perform Technical Analysis
        ta_results = apply_technical_analysis(price_history)

        coins.append({
            "symbol": symbol,
            "name": name,
            "price": price,
            "galaxy_score": galaxy_score,
            "alt_rank": alt_rank,
            "rsi": ta_results["rsi"],
            "macd_diff": ta_results["macd_diff"],
        })
    return coins

def send_telegram_alerts(coins):
    """Send alerts for coins meeting criteria via Telegram."""
    bot = Bot(token=TELEGRAM_TOKEN)
    for coin in coins:
        if coin["galaxy_score"] > 80 and coin["rsi"] < 30:  # Strong sentiment and oversold condition
            message = (
                f"🚀 {coin['name']} ({coin['symbol']}) Analysis:\n"
                f"Price: ${coin['price']:.2f}\n"
                f"Galaxy Score: {coin['galaxy_score']}\n"
                f"RSI: {coin['rsi']:.2f} (Oversold)\n"
                "Consider buying for potential upside!"
            )
            bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)

def create_dashboard(coins):
    """Create a Streamlit dashboard."""
    st.title("LunarCrush Cryptocurrency Analysis")
    st.write("### Top Coins by Galaxy Score and Technical Indicators")
    df = pd.DataFrame(coins)
    st.dataframe(df)
    st.bar_chart(df.set_index("symbol")[["galaxy_score", "rsi"]])

def main():
    print("Analyzing coins...")
    coins = analyze_coins()
    print("Sending Telegram alerts...")
    send_telegram_alerts(coins)
    print("Launching dashboard...")
    create_dashboard(coins)

if __name__ == "__main__":
    main()
