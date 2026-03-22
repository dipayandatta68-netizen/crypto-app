import streamlit as st
import pandas as pd
import requests
import pytz
from datetime import datetime
import yfinance as yf

st.set_page_config(page_title="Crypto Trading Stable", layout="wide")

st.title("💰 Crypto Trading System (STABLE)")

coin = st.selectbox("Select Coin", ["BTC", "ETH"])
symbol = coin + "USDT"

# -----------------------------
# SAFE DATA FETCH
# -----------------------------
def get_binance():
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1m&limit=200"
        data = requests.get(url, timeout=5).json()

        df = pd.DataFrame(data)

        if df is None or len(df) == 0:
            return None

        df.columns = ["time","o","h","l","c","v","ct","qv","n","tb","tq","i"]

        df["close"] = pd.to_numeric(df["c"], errors="coerce")
        df["high"] = pd.to_numeric(df["h"], errors="coerce")
        df["low"] = pd.to_numeric(df["l"], errors="coerce")
        df["time"] = pd.to_datetime(df["time"], unit="ms")

        df = df[["time","close","high","low"]].dropna()

        return df if len(df) > 10 else None

    except:
        return None


def get_backup():
    try:
        ticker = coin + "-USD"
        df = yf.download(ticker, period="1d", interval="1m")

        if df is None or len(df) == 0:
            return None

        df = df.rename(columns={
            "Close":"close",
            "High":"high",
            "Low":"low"
        })

        df["time"] = df.index
        df = df[["time","close","high","low"]].dropna()

        return df if len(df) > 10 else None

    except:
        return None


# -----------------------------
# FETCH DATA (WITH FALLBACK)
# -----------------------------
df = get_binance()

if df is not None:
    st.success("✅ Live data (Binance)")
else:
    df = get_backup()
    if df is not None:
        st.warning("⚠ Using backup (Yahoo Finance)")
    else:
        st.error("❌ Data unavailable — try again later")
        st.stop()

# EXTRA SAFETY
df = df.dropna().reset_index(drop=True)

# -----------------------------
# INDICATORS (SAFE)
# -----------------------------
try:
    df["EMA20"] = df["close"].ewm(span=20).mean()
    df["EMA50"] = df["close"].ewm(span=50).mean()

    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()

    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))

    df["momentum"] = df["close"].pct_change(5)

except:
    st.error("❌ Indicator error")
    st.stop()

# -----------------------------
# LATEST VALUES (SAFE)
# -----------------------------
try:
    price = float(df["close"].iloc[-1])
    ema20 = float(df["EMA20"].iloc[-1])
    ema50 = float(df["EMA50"].iloc[-1])
    rsi = float(df["RSI"].iloc[-1])
    momentum = float(df["momentum"].iloc[-1])
except:
    st.error("❌ Data processing error")
    st.stop()

# -----------------------------
# SIGNAL LOGIC (STABLE)
# -----------------------------
signal = "HOLD"
confidence = 50

if price > ema20 and ema20 > ema50 and momentum > 0:
    signal = "BUY"
    confidence = 80

elif price < ema20 and ema20 < ema50 and momentum < 0:
    signal = "SELL"
    confidence = 80

elif rsi < 45:
    signal = "BUY"
    confidence = 65

elif rsi > 55:
    signal = "SELL"
    confidence = 65

# -----------------------------
# TARGET / SL
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
# TIME (IST)
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
# CHART (CRASH-PROOF)
# -----------------------------
try:
    chart = df.copy().set_index("time")
    chart = chart[["close","EMA20","EMA50"]].dropna()

    if len(chart) > 10:
        st.line_chart(chart.tail(120))
    else:
        st.info("ℹ Chart building...")

except:
    st.info("ℹ Chart safe mode")
