import streamlit as st
import pandas as pd
import requests
import pytz
from datetime import datetime
import yfinance as yf

st.set_page_config(page_title="Crypto Trading System", layout="wide")

st.title("💰 Crypto Trading System (Final)")

coin = st.selectbox("Select Coin", ["BTC", "ETH"])

symbol = coin + "USDT"

# -----------------------------
# FETCH DATA (BINANCE + BACKUP)
# -----------------------------
def get_binance():
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1m&limit=120"
        data = requests.get(url, timeout=5).json()

        df = pd.DataFrame(data, columns=[
            "time","o","h","l","c","v","ct","qv","n","tb","tq","i"
        ])

        df["close"] = df["c"].astype(float)
        df["time"] = pd.to_datetime(df["time"], unit="ms")

        st.success("✅ Live data (Binance)")
        return df

    except:
        return None


def get_backup():
    try:
        ticker = coin + "-USD"
        df = yf.download(ticker, period="1d", interval="1m")

        df = df.rename(columns={"Close": "close"})
        df["time"] = df.index

        st.warning("⚠ Using backup (Yahoo Finance)")
        return df.reset_index()

    except:
        return None


df = get_binance()
if df is None:
    df = get_backup()

if df is None or len(df) < 30:
    st.error("❌ Unable to fetch enough data")
    st.stop()

# -----------------------------
# INDICATORS
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

# -----------------------------
# LATEST VALUES
# -----------------------------
price = float(df["close"].iloc[-1])
ema20 = float(df["EMA20"].iloc[-1])
ema50 = float(df["EMA50"].iloc[-1])
rsi = float(df["RSI"].iloc[-1])

# -----------------------------
# SIGNAL LOGIC (REDUCED HOLD)
# -----------------------------
signal = "HOLD"
confidence = 50

# 🔥 More aggressive logic
if price > ema20 and ema20 > ema50:
    signal = "BUY"
    confidence = 75

elif price < ema20 and ema20 < ema50:
    signal = "SELL"
    confidence = 75

# Extra push using RSI
if rsi < 40:
    signal = "BUY"
    confidence = 80

elif rsi > 60:
    signal = "SELL"
    confidence = 80

# -----------------------------
# TARGET / SL
# -----------------------------
target = price * (1.01 if signal == "BUY" else 0.99)
stoploss = price * (0.99 if signal == "BUY" else 1.01)

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
    st.success(f"🟢 BUY")
elif signal == "SELL":
    st.error(f"🔴 SELL")
else:
    st.warning("🟡 HOLD")

st.write(f"Confidence: {confidence}%")
st.write(f"Entry: {price:.2f}")
st.write(f"Target: {target:.2f}")
st.write(f"Stop Loss: {stoploss:.2f}")
st.write(f"🕒 Signal Time: {now}")

# -----------------------------
# CHART (FIXED)
# -----------------------------
try:
    chart = df.copy()
    chart = chart.set_index("time")

    chart = chart[["close", "EMA20", "EMA50"]]
    chart = chart.dropna()

    if len(chart) > 20:
        st.line_chart(chart.tail(120))
    else:
        st.warning("⚠ Not enough data for chart")

except:
    st.warning("⚠ Chart error handled")
