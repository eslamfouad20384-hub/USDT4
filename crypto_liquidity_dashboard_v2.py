# crypto_liquidity_dashboard_v2.py

import streamlit as st
import requests
import pandas as pd
import datetime
import matplotlib.pyplot as plt

st.set_page_config(page_title="Crypto Liquidity Dashboard", layout="wide")

st.title("📊 Crypto Market Liquidity & Fear/Greed Dashboard (Enhanced)")

# -----------------------------
# Function: Get coin market chart data (last 7 days)
# -----------------------------
@st.cache_data(ttl=300)
def get_coin_chart(coin_id):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {
        'vs_currency': 'usd',
        'days': 7,
        'interval': 'daily'
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data['total_volumes'], columns=['timestamp', 'volume'])
        df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df[['date', 'volume']]
    else:
        return None

# -----------------------------
# Function: Get coin data from CoinGecko
# -----------------------------
@st.cache_data(ttl=300)
def get_coin_data(coin_id):
    url = f"https://api.coingecko.com/api/v3/coins/markets"
    params = {
        'vs_currency': 'usd',
        'ids': coin_id,
        'order': 'market_cap_desc',
        'per_page': 1,
        'page': 1,
        'sparkline': 'false'
    }
    response = requests.get(url, params=params)
    if response.status_code == 200 and len(response.json()) > 0:
        data = response.json()[0]
        return {
            "name": data["name"],
            "symbol": data["symbol"].upper(),
            "price": data["current_price"],
            "volume_24h": data["total_volume"],
            "high_24h": data["high_24h"],
            "low_24h": data["low_24h"],
        }
    else:
        return None

# -----------------------------
# Function: Get Fear & Greed Index
# -----------------------------
@st.cache_data(ttl=600)
def get_fear_greed_index():
    url = "https://api.alternative.me/fng/?limit=1"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        value = int(data['data'][0]['value'])
        classification = data['data'][0]['value_classification']
        return value, classification
    else:
        return None, None

# -----------------------------
# User input
# -----------------------------
coin_input = st.text_input("Enter coin id (CoinGecko format, e.g., bitcoin, ethereum, solana):", "bitcoin")

if st.button("Update Dashboard"):
    coin_data = get_coin_data(coin_input.lower())
    coin_chart = get_coin_chart(coin_input.lower())
    fear_greed_value, fear_greed_class = get_fear_greed_index()
    
    if coin_data:
        # -----------------------------
        # Compute liquidity signal
        # -----------------------------
        volume = coin_data["volume_24h"]
        liquidity_threshold = 100_000_000  # USD, adjustable
        if volume > liquidity_threshold:
            liquidity_signal = "High liquidity (money entering)"
            liquidity_color = "green"
            liquidity_emoji = "🟢"
        else:
            liquidity_signal = "Low liquidity (money leaving / low inflow)"
            liquidity_color = "red"
            liquidity_emoji = "🔴"
        
        # -----------------------------
        # Recommendation based on liquidity and fear/greed
        # -----------------------------
        if liquidity_color == "green" and fear_greed_class.lower() in ["neutral", "greed"]:
            recommendation = "✅ Good time to consider buying or holding"
        elif liquidity_color == "red" and fear_greed_class.lower() in ["fear"]:
            recommendation = "⚠️ Caution, low liquidity but market fear could present opportunity"
        else:
            recommendation = "🟡 Wait & monitor market conditions"
        
        # -----------------------------
        # Display data
        # -----------------------------
        st.subheader(f"📈 Coin Data: {coin_data['name']} ({coin_data['symbol']})")
        st.write(f"Price: ${coin_data['price']}")
        st.write(f"24h Volume: ${coin_data['volume_24h']}")
        st.write(f"24h High / Low: ${coin_data['high_24h']} / ${coin_data['low_24h']}")
        
        st.subheader("💧 Liquidity Status")
        st.markdown(f"<h2 style='color:{liquidity_color}'>{liquidity_emoji} {liquidity_signal}</h2>", unsafe_allow_html=True)
        
        st.subheader("😎 Fear & Greed Index")
        fg_color = "green" if fear_greed_class.lower() in ["greed", "neutral"] else "red"
        st.markdown(f"<h2 style='color:{fg_color}'>{fear_greed_value} ({fear_greed_class})</h2>", unsafe_allow_html=True)
        
        st.subheader("📝 Recommendation")
        st.write(recommendation)
        
        # -----------------------------
        # Volume chart last 7 days
        # -----------------------------
        if coin_chart is not None:
            st.subheader("📊 7-Day Volume Chart")
            fig, ax = plt.subplots(figsize=(8,3))
            ax.bar(coin_chart['date'], coin_chart['volume'], color=liquidity_color)
            ax.set_ylabel("Volume (USD)")
            ax.set_xlabel("Date")
            ax.set_title(f"{coin_data['name']} 7-Day Trading Volume")
            st.pyplot(fig)
        
    else:
        st.error("Coin data not found. Make sure the CoinGecko coin ID is correct.")
