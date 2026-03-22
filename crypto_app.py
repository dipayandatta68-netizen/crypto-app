import streamlit as st
import pandas as pd
import requests
import datetime
import time
import plotly.graph_objects as go

st.set_page_config(page_title="Crypto Trading System", layout="wide")

st.title("💰 Crypto Trading System (Final)")

# ---------------------------
# SELECT COIN
# ---------------------------
coin = st.selectbox("Select Coin", ["BTC", "ETH", "BNB", "SOL"])
symbol = coin + "USDT"

# ---------------------------
# FETCH DATA
# ---------------------------
def get_data():
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=5m&limit=200"
        res = requests.get(url)
        data = res.json()

        df = pd.DataFrame(data)
        df = df[[0,1,2,3,4]]
        df.columns = ["Time","Open","High","Low","Close"]

        df["Time"] = pd.to_datetime(df["Time"], unit='ms')

        for col in ["Open","High","Low","Close"]:
            df[col] = df[col].astype(float)

        return df

    except:
        try:
            st.warning("⚠️ Using backup data")

            url = f"https://api.coingecko.com/api/v3/coins/{coin.lower()}/market_chart?vs_currency=usd&days=1"
            res = requests.get(url)
            data = res.json()

            prices = data["prices"]
            df = pd.DataFrame(prices, columns=["Time","Close"])

            df["Time"] = pd.to_datetime(df["Time"], unit='ms')

            df["Open"] = df["Close"]
            df["High"] = df["Close"]
            df["Low"] = df["Close"]

            return df

        except:
            return None


data = get_data()

if data is None or len(data) < 50:
    st.error("❌ Data not available")
    st.stop()

# ---------------------------
# INDICATORS
# ---------------------------
data["EMA20"] = data["Close"].ewm(span=20).mean()
data["EMA50"] = data["Close"].ewm(span=50).mean()

delta = data["Close"].diff()
gain = delta.clip(lower=0)
loss = -delta.clip(upper=0)

avg_gain = gain.rolling(14).mean()
avg_loss = loss.rolling(14).mean()

rs = avg_gain / avg_loss
data["RSI"] = 100 - (100 / (1 + rs))

# ---------------------------
# SIGNAL LOGIC
# ---------------------------
latest = data.iloc[-1]

price = latest["Close"]
ema20 = latest["EMA20"]
ema50 = latest["EMA50"]
rsi = latest["RSI"]

recent_high = data["High"].tail(20).max()
recent_low = data["Low"].tail(20).min()

signal = "NO TRADE"
entry = "-"
target = "-"
sl = "-"

if price > ema20 and ema20 > ema50 and rsi > 55:
    signal = "BUY"
    entry = round(price, 2)
    target = round(price * 1.01, 2)
    sl = round(price * 0.995, 2)

elif price < ema20 and ema20 < ema50 and rsi < 45:
    signal = "SELL"
    entry = round(price, 2)
    target = round(price * 0.99, 2)
    sl = round(price * 1.005, 2)

elif price > recent_high:
    signal = "BREAKOUT BUY"
    entry = round(price, 2)
    target = round(price * 1.015, 2)
    sl = round(price * 0.995, 2)

elif price < recent_low:
    signal = "BREAKDOWN SELL"
    entry = round(price, 2)
    target = round(price * 0.985, 2)
    sl = round(price * 1.005, 2)

# ---------------------------
# DISPLAY
# ---------------------------
st.subheader(f"💲 Price: ${round(price,2)}")

now = datetime.datetime.now().strftime("%I:%M %p")

if "BUY" in signal:
    st.success(f"📈 {signal} at {now}")
elif "SELL" in signal:
    st.error(f"📉 {signal} at {now}")
else:
    st.warning("⚠️ NO TRADE")

st.write(f"🎯 Entry: {entry}")
st.write(f"🏆 Target: {target}")
st.write(f"🛑 Stop Loss: {sl}")

# ---------------------------
# CHART
# ---------------------------
fig = go.Figure()

fig.add_trace(go.Scatter(x=data["Time"], y=data["Close"], name="Price"))
fig.add_trace(go.Scatter(x=data["Time"], y=data["EMA20"], name="EMA20"))
fig.add_trace(go.Scatter(x=data["Time"], y=data["EMA50"], name="EMA50"))

fig.update_layout(height=500)

st.plotly_chart(fig, use_container_width=True)

# ---------------------------
# LIVE MODE
# ---------------------------
if st.toggle("⚡ Live Mode (5s refresh)"):
    time.sleep(5)
    st.rerun()
