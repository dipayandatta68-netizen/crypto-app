import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
import time

st.set_page_config(layout="wide")
st.title("🚀 Crypto Intelligence Pro")

# -----------------------
# LIVE MODE
# -----------------------
if st.toggle("⚡ Live Mode (3s)"):
    time.sleep(3)
    st.rerun()

# -----------------------
# COINS
# -----------------------
coins = {
    "BTC": "BTCUSDT",
    "ETH": "ETHUSDT",
    "SOL": "SOLUSDT",
    "XRP": "XRPUSDT"
}

selected_coin = st.selectbox("Select Coin", list(coins.keys()))
symbol = coins[selected_coin]

# -----------------------
# BINANCE DATA
# -----------------------
def get_data(symbol, interval="5m", limit=150):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
        data = requests.get(url).json()

        df = pd.DataFrame(data, columns=[
            "time","Open","High","Low","Close","Volume",
            "close_time","qav","trades","tbbav","tbqav","ignore"
        ])

        df["Open"] = df["Open"].astype(float)
        df["High"] = df["High"].astype(float)
        df["Low"] = df["Low"].astype(float)
        df["Close"] = df["Close"].astype(float)
        df["Volume"] = df["Volume"].astype(float)

        return df[["Open","High","Low","Close","Volume"]]

    except:
        return pd.DataFrame()

# -----------------------
# INDICATORS
# -----------------------
def add_indicators(df):
    df["EMA20"] = df["Close"].ewm(span=20).mean()
    df["EMA50"] = df["Close"].ewm(span=50).mean()

    delta = df["Close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss
    df["RSI"] = 100 - (100 / (1 + rs))

    exp1 = df["Close"].ewm(span=12).mean()
    exp2 = df["Close"].ewm(span=26).mean()
    df["MACD"] = exp1 - exp2
    df["Signal"] = df["MACD"].ewm(span=9).mean()

    df["VWAP"] = (df["Close"] * df["Volume"]).cumsum() / df["Volume"].cumsum()
    df["Vol_Avg"] = df["Volume"].rolling(20).mean()

    return df.fillna(method="bfill")

# -----------------------
# ANALYSIS ENGINE
# -----------------------
def analyze(df):
    latest = df.iloc[-1]

    score = 0

    # Trend
    if latest["EMA20"] > latest["EMA50"]:
        trend = "BUY"
        score += 1
    else:
        trend = "SELL"
        score += 1

    # RSI
    if latest["RSI"] > 55 or latest["RSI"] < 45:
        score += 1

    # MACD
    if latest["MACD"] > latest["Signal"]:
        score += 1

    # VWAP
    if latest["Close"] > latest["VWAP"]:
        score += 1

    # Volume
    if latest["Volume"] > latest["Vol_Avg"] * 1.2:
        score += 1

    confidence = int((score / 5) * 100)

    return trend, confidence

# -----------------------
# DATA LOAD
# -----------------------
df = get_data(symbol)

if df.empty:
    st.warning("Data not available")
    st.stop()

df = add_indicators(df)

latest = df.iloc[-1]
prev = df.iloc[-2]

price = latest["Close"]

# -----------------------
# FILTERS (WIN RATE BOOST)
# -----------------------
trend_strength = abs(latest["EMA20"] - latest["EMA50"])
strong_trend = trend_strength > (price * 0.001)

range_market = 45 < latest["RSI"] < 55
strong_volume = latest["Volume"] > latest["Vol_Avg"] * 1.2

trend, confidence = analyze(df)

# -----------------------
# SNIPER ENTRY
# -----------------------
pullback_buy = price <= latest["EMA20"] * 1.002
pullback_sell = price >= latest["EMA20"] * 0.998

momentum_up = latest["Close"] > prev["High"]
momentum_down = latest["Close"] < prev["Low"]

decision = "WAIT"
entry_signal = "WAIT"

if confidence >= 70 and strong_trend and not range_market and strong_volume:

    if trend == "BUY" and pullback_buy:
        decision = "BUY 🚀"
        if momentum_up:
            entry_signal = "ENTER NOW"

    elif trend == "SELL" and pullback_sell:
        decision = "SELL 🔻"
        if momentum_down:
            entry_signal = "ENTER NOW"

# -----------------------
# STRUCTURE SL
# -----------------------
df["Swing_High"] = df["High"].rolling(10).max()
df["Swing_Low"] = df["Low"].rolling(10).min()

swing_high = df["Swing_High"].iloc[-2]
swing_low = df["Swing_Low"].iloc[-2]

if "BUY" in decision:
    sl = swing_low - price * 0.001
    target = price + (price - sl) * 2

elif "SELL" in decision:
    sl = swing_high + price * 0.001
    target = price - (sl - price) * 2
else:
    sl, target = 0, 0

# -----------------------
# TRADE MANAGEMENT
# -----------------------
risk = abs(price - sl)

tp1 = price + risk if "BUY" in decision else price - risk
tp2 = price + risk*1.5 if "BUY" in decision else price - risk*1.5

if "trade_active" not in st.session_state:
    st.session_state.trade_active = False
    st.session_state.sl = sl

# -----------------------
# UI
# -----------------------
tab1, tab2 = st.tabs(["📊 Chart", "⚡ Trade"])

with tab1:
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        open=df["Open"],
        high=df["High"],
        low=df["Low"],
        close=df["Close"]
    ))
    fig.add_trace(go.Scatter(y=df["EMA20"], name="EMA20"))
    fig.add_trace(go.Scatter(y=df["EMA50"], name="EMA50"))
    fig.update_layout(height=500, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.markdown(f"## 💰 {selected_coin} | {round(price,2)}")

    if "BUY" in decision:
        st.success(decision)
    elif "SELL" in decision:
        st.error(decision)
    else:
        st.warning("WAIT")

    st.progress(confidence/100)
    st.write(f"Confidence: {confidence}%")

    st.markdown("### 🎯 Entry Signal")
    if entry_signal == "ENTER NOW":
        st.success("ENTER NOW")
    else:
        st.warning("WAIT")

    if decision != "WAIT":
        col1, col2, col3 = st.columns(3)
        col1.metric("Entry", round(price,2))
        col2.metric("SL", round(sl,2))
        col3.metric("Target", round(target,2))

        st.write(f"TP1: {round(tp1,2)} | TP2: {round(tp2,2)}")

        if not st.session_state.trade_active:
            if st.button("🚀 Start Trade"):
                st.session_state.trade_active = True

    if st.session_state.trade_active:
        st.success("Trade Active")

        if st.button("❌ Close Trade"):
            st.session_state.trade_active = False