import streamlit as st
import pandas as pd
import requests
import time

# ---------------------------
# PAGE CONFIG
# ---------------------------
st.set_page_config(page_title="Crypto Intelligence Pro", layout="wide")

st.title("🚀 Crypto Intelligence Pro")

# ---------------------------
# LIVE MODE
# ---------------------------
live_mode = st.toggle("⚡ Live Mode (3s refresh)", value=False)

# ---------------------------
# COIN SELECTION
# ---------------------------
coin_map = {
    "BTC": "BTCUSDT",
    "ETH": "ETHUSDT",
    "BNB": "BNBUSDT",
    "SOL": "SOLUSDT"
}

selected_coin = st.selectbox("Select Coin", list(coin_map.keys()))
symbol = coin_map[selected_coin]

# ---------------------------
# FETCH DATA (BINANCE)
# ---------------------------
def get_crypto_data(symbol="BTCUSDT", interval="1m", limit=100):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    
    try:
        data = requests.get(url, timeout=10).json()
        
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
# MAIN LOOP (LIVE MODE)
# ---------------------------
while True:
    
    data = get_crypto_data(symbol)

    if data is None or len(data) < 50:
        st.warning("⚠️ Data not available")
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
        # SIGNAL LOGIC
        # ---------------------------
        if ema20 > ema50:
            signal = "BUY"
            color = "green"
        elif ema20 < ema50:
            signal = "SELL"
            color = "red"
        else:
            signal = "WAIT"
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
    # LIVE REFRESH
    # ---------------------------
    if live_mode:
        time.sleep(3)
        st.rerun()
    else:
        break
