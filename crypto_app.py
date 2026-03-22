import streamlit as st
import pandas as pd
import requests
import time

st.set_page_config(page_title="Crypto Intelligence Pro", layout="wide")

st.title("🚀 Crypto Intelligence Pro")

# ---------------------------
# LIVE MODE
# ---------------------------
live_mode = st.toggle("⚡ Live Mode (3s refresh)", value=False)

# ---------------------------
# COIN MAP (DUAL API SUPPORT)
# ---------------------------
coin_map = {
    "BTC": {"binance": "BTCUSDT", "coingecko": "bitcoin"},
    "ETH": {"binance": "ETHUSDT", "coingecko": "ethereum"},
    "BNB": {"binance": "BNBUSDT", "coingecko": "binancecoin"},
    "SOL": {"binance": "SOLUSDT", "coingecko": "solana"}
}

selected_coin = st.selectbox("Select Coin", list(coin_map.keys()))

# ---------------------------
# BINANCE DATA (FAST)
# ---------------------------
def get_binance_data(symbol):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1m&limit=100"
    try:
        res = requests.get(url, timeout=5)
        data = res.json()

        if not data or isinstance(data, dict):
            return None

        df = pd.DataFrame(data)
        df = df.iloc[:, :6]
        df.columns = ["Time","Open","High","Low","Close","Volume"]

        df["Close"] = df["Close"].astype(float)
        df["Time"] = pd.to_datetime(df["Time"], unit="ms")

        return df

    except:
        return None

# ---------------------------
# COINGECKO DATA (BACKUP)
# ---------------------------
def get_coingecko_data(symbol):
    url = f"https://api.coingecko.com/api/v3/coins/{symbol}/market_chart?vs_currency=usd&days=1"
    try:
        res = requests.get(url, timeout=5)
        data = res.json()

        prices = data.get("prices", [])
        if not prices:
            return None

        df = pd.DataFrame(prices, columns=["Time", "Close"])
        df["Time"] = pd.to_datetime(df["Time"], unit="ms")

        return df

    except:
        return None

# ---------------------------
# SMART FETCH (AUTO SWITCH)
# ---------------------------
def get_data():
    binance_symbol = coin_map[selected_coin]["binance"]
    cg_symbol = coin_map[selected_coin]["coingecko"]

    data = get_binance_data(binance_symbol)

    if data is None:
        st.warning("⚠️ Binance failed → Switching to backup API")
        data = get_coingecko_data(cg_symbol)

    return data

# ---------------------------
# MAIN LOOP
# ---------------------------
while True:

    data = get_data()

    if data is None or len(data) < 20:
        st.error("❌ Data not available")
    else:
        # ---------------------------
        # INDICATORS
        # ---------------------------
        data["EMA20"] = data["Close"].ewm(span=20).mean()
        data["EMA50"] = data["Close"].ewm(span=50).mean()

        latest = data.iloc[-1]

        price = latest["Close"]
        ema20 = latest["EMA20"]
        ema50 = latest["EMA50"]

        # ---------------------------
        # SIGNAL LOGIC (IMPROVED)
        # ---------------------------
        if ema20 > ema50 and price > ema20:
            signal = "BUY 🚀"
            color = "green"
        elif ema20 < ema50 and price < ema20:
            signal = "SELL 🔻"
            color = "red"
        else:
            signal = "WAIT ⏳"
            color = "yellow"

        # ---------------------------
        # DISPLAY
        # ---------------------------
        st.metric("💰 Price", f"${price:.2f}")

        st.markdown(f"""
        <h2 style='color:{color};'>📊 Signal: {signal}</h2>
        """, unsafe_allow_html=True)

        # ---------------------------
        # CHART
        # ---------------------------
        st.line_chart(data.set_index("Time")[["Close","EMA20","EMA50"]])

    # ---------------------------
    # LIVE MODE REFRESH
    # ---------------------------
    if live_mode:
        time.sleep(3)
        st.rerun()
    else:
        break
