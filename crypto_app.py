import streamlit as st
import pandas as pd
import requests
import pytz
from datetime import datetime
import yfinance as yf

st.set_page_config(page_title="Crypto Trading Pro", layout="wide")

st.title("💰 Crypto Trading System (PRO)")

coin = st.selectbox("Select Coin", ["BTC", "ETH"])
symbol = coin + "USDT"

# -----------------------------
# DATA FETCH (STRONG FIX)
# -----------------------------
def get_binance():
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1m&limit=200"
        data = requests.get(url, timeout=5).json()

        df = pd.DataFrame(data, columns=[
            "time","o","h","l","c","v","ct","qv","n","tb","tq","i"
        ])

        df["close"] = pd.to_numeric(df["c"], errors="coerce")
        df["high"] = pd.to_numeric(df["h"], errors="coerce")
        df["low"] = pd.to_numeric(df["l"], errors="coerce")

        df["time"] = pd.to_datetime(df["time"], unit="ms")

        df = df[["time","close","high","low"]].dropna()

        st.success("✅ Live data (Binance)")
        return df

    except:
        return None


def get_backup():
    try:
        ticker = coin + "-USD"
        df = yf.download(ticker, period="1d", interval="1m")

        df = df.rename(columns={
            "Close":"close",
            "High":"high",
            "Low":"low"
        })

        df["time"] = df.index

        df = df[["time","close","high","low"]].dropna()

        st.warning("⚠ Using backup (Yahoo Finance)")
        return df.reset_index(drop=True)

    except:
        return None


df = get_binance()
if df is None:
    df = get_backup()

if df is None or len(df) < 50:
    st.error("❌ Market data unavailable")
    st.stop()

# -----------------------------
# INDICATORS (PRO LEVEL)
# -----------------------------
df["EMA20"] = df["close"].ewm(span=20).mean()
df["EMA50"] = df["close"].ewm(span=50).mean()

# RSI
delta = df["close"].diff()
gain = delta.clip(lower=0)
loss = -delta.clip(upper=0)

avg_gain = gain.rolling(14).mean()
avg_loss = loss.rolling(14).mean()

rs = avg_gain / avg_loss
df["RSI"] = 100 - (100 / (1 + rs))

# Momentum
df["momentum"] = df["close"].pct_change(5)

# -----------------------------
# LATEST VALUES
# -----------------------------
price = float(df["close"].iloc[-1])
ema20 = float(df["EMA20"].iloc[-1])
ema50 = float(df["EMA50"].iloc[-1])
rsi = float(df["RSI"].iloc[-1])
momentum = float(df["momentum"].iloc[-1])

# -----------------------------
# PRO SIGNAL LOGIC (LESS HOLD)
# -----------------------------
signal = "HOLD"
confidence = 50

# BUY conditions
if price > ema20 and ema20 > ema50 and rsi < 70 and momentum > 0:
    signal = "BUY"
    confidence = 80

# SELL conditions
elif price < ema20 and ema20 < ema50 and rsi > 30 and momentum < 0:
    signal = "SELL"
    confidence = 80

# Aggressive fallback (reduce HOLD)
elif rsi < 45 and momentum > 0:
    signal = "BUY"
    confidence = 65

elif rsi > 55 and momentum < 0:
    signal = "SELL"
    confidence = 65

# -----------------------------
# TARGET / STOPLOSS (SMART)
# -----------------------------
if signal == "BUY":
    target = price * 1.01
    stoploss = price * 0.995
elif signal == "SELL":
    target = price * 0.99
    stoploss = price * 1.005
else:
    target = price
    stoploss = price

# -----------------------------
# TIME (IST FIX)
# -----------------------------
ist = pytz.timezone("Asia/Kolkata")
now = datetime.now(ist).strftime("%I:%M %p")

# -----------------------------
# DISPLAY
# -----------------------------
st.subheader(f"💲 Price: ${price:.2f}")

if signal == "BUY":
    st.success("🟢 BUY")
elif signal == "SELL":
    st.error("🔴 SELL")
else:
    st.warning("🟡 HOLD")

st.write(f"Confidence: {confidence}%")
st.write(f"Entry: {price:.2f}")
st.write(f"Target: {target:.2f}")
st.write(f"Stop Loss: {stoploss:.2f}")
st.write(f"🕒 Signal Time: {now}")

# -----------------------------
# CHART (FULL FIX)
# -----------------------------
try:
    chart = df.copy().set_index("time")
    chart = chart[["close","EMA20","EMA50"]].dropna()

    if len(chart) > 30:
        st.line_chart(chart.tail(150))
    else:
        st.warning("⚠ Not enough chart data")

except:
    st.warning("⚠ Chart error handled safely")
