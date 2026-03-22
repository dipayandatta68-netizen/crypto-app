import streamlit as st
import pandas as pd
import numpy as np
import requests
import yfinance as yf
from datetime import datetime

st.set_page_config(page_title="Crypto Trading System", layout="wide")

st.title("💰 Crypto Trading System (Final)")

coin = st.selectbox("Select Coin", ["BTC", "ETH", "BNB"])

symbol_map = {
    "BTC": "BTCUSDT",
    "ETH": "ETHUSDT",
    "BNB": "BNBUSDT"
}

symbol = symbol_map[coin]

# -----------------------------
# BINANCE DATA
# -----------------------------
def get_binance_data(symbol):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=15m&limit=500"
    res = requests.get(url, timeout=10)
    data = res.json()

    if not isinstance(data, list) or len(data) < 50:
        return None

    df = pd.DataFrame(data, columns=[
        "time","open","high","low","close","volume",
        "close_time","qav","trades","tbbav","tbqav","ignore"
    ])

    df["time"] = pd.to_datetime(df["time"], unit='ms')
    df["close"] = pd.to_numeric(df["close"], errors='coerce')
    df["high"] = pd.to_numeric(df["high"], errors='coerce')
    df["low"] = pd.to_numeric(df["low"], errors='coerce')

    return df[["time","close","high","low"]]


# -----------------------------
# BACKUP DATA
# -----------------------------
def get_backup_data(coin):
    df = yf.download(f"{coin}-USD", interval="15m", period="2d")

    if df is None or df.empty:
        return None

    df = df.reset_index()

    if "Datetime" in df.columns:
        df.rename(columns={"Datetime": "time"}, inplace=True)
    elif "Date" in df.columns:
        df.rename(columns={"Date": "time"}, inplace=True)

    df.rename(columns={
        "Close": "close",
        "High": "high",
        "Low": "low"
    }, inplace=True)

    return df[["time","close","high","low"]]


# -----------------------------
# LOAD DATA (SMART FALLBACK)
# -----------------------------
df = None

try:
    df = get_binance_data(symbol)
    if df is None or len(df) < 200:
        raise Exception("Weak Binance data")
    st.success("✅ Live data (Binance)")
except:
    st.warning("⚠ Using stable backup (Yahoo Finance)")
    df = get_backup_data(coin)

# FINAL SAFETY CHECK
if df is None or len(df) < 50:
    st.error("❌ Unable to fetch market data")
    st.stop()

df = df.dropna()


# -----------------------------
# INDICATORS
# -----------------------------
df["EMA20"] = df["close"].ewm(span=20).mean()
df["EMA50"] = df["close"].ewm(span=50).mean()

delta = df["close"].diff()
gain = (delta.where(delta > 0, 0)).rolling(14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
rs = gain / loss
df["RSI"] = 100 - (100 / (1 + rs))

latest = df.iloc[-1]

price = float(latest["close"])
ema20 = float(latest["EMA20"])
ema50 = float(latest["EMA50"])
rsi = float(latest["RSI"])


# -----------------------------
# SIGNAL LOGIC (SMART)
# -----------------------------
signal = "HOLD"
confidence = 50

if price > ema20 > ema50 and 50 < rsi < 70:
    signal = "BUY"
    confidence = 85

elif price < ema20 < ema50 and 30 < rsi < 50:
    signal = "SELL"
    confidence = 85


# -----------------------------
# TRADE PLAN
# -----------------------------
entry = price

if signal == "BUY":
    target = price * 1.025
    stop_loss = price * 0.98

elif signal == "SELL":
    target = price * 0.975
    stop_loss = price * 1.02

else:
    target = price
    stop_loss = price


# -----------------------------
# UI OUTPUT
# -----------------------------
st.subheader(f"💲 Price: ${round(price,2)}")

if signal == "BUY":
    st.success("📈 BUY SIGNAL")
elif signal == "SELL":
    st.error("📉 SELL SIGNAL")
else:
    st.warning("⚠ HOLD")

st.write(f"Confidence: {confidence}%")
st.write(f"Entry: {round(entry,2)}")
st.write(f"Target: {round(target,2)}")
st.write(f"Stop Loss: {round(stop_loss,2)}")

# TIME (12H)
now = datetime.now().strftime("%I:%M %p")
st.write(f"🕒 Signal Time: {now}")

# -----------------------------
# CHART
# -----------------------------
chart = df.set_index("time")[["close","EMA20","EMA50"]].tail(150)
st.line_chart(chart)
