# crypto_liquidity_dashboard_ar.py

import streamlit as st
import requests
import pandas as pd
import datetime
import matplotlib.pyplot as plt

st.set_page_config(page_title="لوحة سيولة السوق والعملات", layout="wide")

st.title("📊 لوحة سيولة السوق وحالة الخوف والطمع (Enhanced بالعربي)")

# -----------------------------
# بيانات حجم التداول آخر 7 أيام
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
# بيانات العملة من CoinGecko
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
# مؤشر الخوف والطمع
# -----------------------------
@st.cache_data(ttl=600)
def get_fear_greed_index():
    url = "https://api.alternative.me/fng/?limit=1"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        value = int(data['data'][0]['value'])
        classification_en = data['data'][0]['value_classification']
        # تحويل التصنيف العربي
        if classification_en.lower() in ["extreme fear"]:
            classification_ar = "خوف شديد"
        elif classification_en.lower() in ["fear"]:
            classification_ar = "خوف"
        elif classification_en.lower() in ["neutral"]:
            classification_ar = "حياد"
        elif classification_en.lower() in ["greed"]:
            classification_ar = "طمع"
        elif classification_en.lower() in ["extreme greed"]:
            classification_ar = "طمع شديد"
        else:
            classification_ar = classification_en
        return value, classification_ar
    else:
        return None, None

# -----------------------------
# واجهة المستخدم
# -----------------------------
coin_input = st.text_input("ادخل اسم العملة (CoinGecko ID, مثال: bitcoin, ethereum, solana):", "bitcoin")

if st.button("تحديث"):
    coin_data = get_coin_data(coin_input.lower())
    coin_chart = get_coin_chart(coin_input.lower())
    fear_greed_value, fear_greed_class = get_fear_greed_index()
    
    if coin_data:
        # -----------------------------
        # حساب السيولة
        # -----------------------------
        volume = coin_data["volume_24h"]
        liquidity_threshold = 100_000_000  # USD, adjustable
        if volume > liquidity_threshold:
            liquidity_signal = "داخل سيولة السوق"
            liquidity_color = "green"
            liquidity_emoji = "🟢"
        else:
            liquidity_signal = "خارج سيولة السوق / تدفق ضعيف"
            liquidity_color = "red"
            liquidity_emoji = "🔴"
        
        # -----------------------------
        # التوصية العامة
        # -----------------------------
        if liquidity_color == "green" and fear_greed_class in ["حياد", "طمع"]:
            recommendation = "✅ وقت مناسب للشراء أو الثبات"
        elif liquidity_color == "red" and fear_greed_class in ["خوف"]:
            recommendation = "⚠️ الحذر، السيولة ضعيفة لكن الخوف قد يتيح فرصة"
        else:
            recommendation = "🟡 راقب السوق وانتظر الفرصة المناسبة"
        
        # -----------------------------
        # عرض بيانات العملة
        # -----------------------------
        st.subheader(f"📈 بيانات العملة: {coin_data['name']} ({coin_data['symbol']})")
        st.write(f"السعر الحالي: ${coin_data['price']}")
        st.write(f"حجم التداول 24 ساعة: ${coin_data['volume_24h']}")
        st.write(f"أعلى / أقل سعر 24 ساعة: ${coin_data['high_24h']} / ${coin_data['low_24h']}")
        
        st.subheader("💧 حالة السيولة")
        st.markdown(f"<h2 style='color:{liquidity_color}'>{liquidity_emoji} {liquidity_signal}</h2>", unsafe_allow_html=True)
        
        st.subheader("😎 مؤشر الخوف والطمع")
        fg_color = "green" if fear_greed_class in ["طمع", "حياد"] else "red"
        st.markdown(f"<h2 style='color:{fg_color}'>{fear_greed_value} ({fear_greed_class})</h2>", unsafe_allow_html=True)
        
        st.subheader("📝 التوصية العامة")
        st.write(recommendation)
        
        # -----------------------------
        # رسم حجم التداول آخر 7 أيام
        # -----------------------------
        if coin_chart is not None:
            st.subheader("📊 حجم التداول آخر 7 أيام")
            fig, ax = plt.subplots(figsize=(8,3))
            ax.bar(coin_chart['date'], coin_chart['volume'], color=liquidity_color)
            ax.set_ylabel("حجم التداول (USD)")
            ax.set_xlabel("التاريخ")
            ax.set_title(f"{coin_data['name']} حجم التداول 7 أيام")
            st.pyplot(fig)
        
    else:
        st.error("لم يتم العثور على بيانات العملة. تأكد من كتابة CoinGecko ID صحيح.")
