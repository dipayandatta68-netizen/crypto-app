import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(page_title="Crypto Trading System", layout="wide")

st.title("💰 Crypto Trading System (Final)")

# ---------------------------
# COINS
# ---------------------------
coin_map = {
    "BTC": {"binance": "BTCUSDT", "coingecko": "bitcoin"},
    "ETH": {"binance": "ETHUSDT", "coingecko": "ethereum"},
    "SOL": {"binance": "SOLUSDT", "coingecko": "solana"}
}

coin = st.selectbox("Select Coin", list(coin_map.keys()))

# ---------------------------
# DATA FETCH
# ---------------------------
def get_binance(symbol):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=5m&limit=150"
        data = requests.get(url, timeout=5).json()

        if isinstance(data, dict):
            return None

        df = pd.DataFrame(data)
        df = df.iloc[:, :6]
        df.columns = ["Time","Open","High","Low","Close","Volume"]

        df["Close"] = df["Close"].astype(float)
        df["Low"] = df["Low"].astype(float)
        df["High"] = df["High"].astype(float)
        df["Time"] = pd.to_datetime(df["Time"], unit="ms")

        return df
    except:
        return None


def get_coingecko(symbol):
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{symbol}/market_chart?vs_currency=usd&days=1"
        data = requests.get(url).json()

        prices = data.get("prices", [])
        df = pd.DataFrame(prices, columns=["Time","Close"])
        df["Time"] = pd.to_datetime(df["Time"], unit="ms")

        return df
    except:
        return None


def get_data():
    df = get_binance(coin_map[coin]["binance"])

    if df is None:
        st.warning("⚠️ Using backup data")
        df = get_coingecko(coin_map[coin]["coingecko"])

    return df


data = get_data()

if data is None or len(data) < 50:
    st.error("❌ Data not available")
    st.stop()

# ---------------------------
# INDICATORS
# ---------------------------
data["EMA20"] = data["Close"].ewm(span=20).mean()
data["EMA50"] = data["Close"].ewm(span=50).mean()

# RSI
delta = data["Close"].diff()
gain = delta.clip(lower=0)
loss = -delta.clip(upper=0)
avg_gain = gain.rolling(14).mean()
avg_loss = loss.rolling(14).mean()
rs = avg_gain / avg_loss
data["RSI"] = 100 - (100 / (1 + rs))

latest = data.iloc[-1]

price = latest["Close"]
ema20 = latest["EMA20"]
ema50 = latest["EMA50"]
rsi = latest["RSI"]

recent_high = data["High"].tail(20).max()
recent_low = data["Low"].tail(20).min()

# ---------------------------
# SIGNAL SYSTEM
# ---------------------------
signal = "WAIT"
entry = None
sl = None
target = None
confidence = "LOW"

# BUY CONDITION
if ema20 > ema50 and price > ema20 and rsi < 70:

    entry = ema20
    sl = recent_low
    risk = entry - sl
    target = entry + (risk * 2)

    if price <= ema20 * 1.01:
        signal = "BUY 🚀"
        confidence = "HIGH"

# SELL CONDITION
elif ema20 < ema50 and price < ema20 and rsi > 30:

    entry = ema20
    sl = recent_high
    risk = sl - entry
    target = entry - (risk * 2)

    if price >= ema20 * 0.99:
        signal = "SELL 🔻"
        confidence = "HIGH"

# ---------------------------
# UI
# ---------------------------
time_now = datetime.now().strftime("%I:%M %p")

col1, col2, col3 = st.columns(3)

col1.metric("💰 Price", f"${price:.2f}")
col2.metric("📊 Signal", signal)
col3.metric("⏰ Time", time_now)

# ---------------------------
# TRADE OUTPUT
# ---------------------------
if signal != "WAIT":

    st.success("🎯 TRADE SETUP")

    st.write(f"**Entry:** ${entry:.2f}")
    st.write(f"**Stop Loss:** ${sl:.2f}")
    st.write(f"**Target:** ${target:.2f}")
    st.write(f"**Confidence:** {confidence}")

    rr = abs(target - entry) / abs(entry - sl)
    st.write(f"**Risk/Reward:** {rr:.2f}")

else:
    st.warning("⏳ WAIT – No Trade")

# ---------------------------
# CHART
# ---------------------------
st.subheader("📈 Market Trend")

st.line_chart(data.set_index("Time")[["Close","EMA20","EMA50"]])
