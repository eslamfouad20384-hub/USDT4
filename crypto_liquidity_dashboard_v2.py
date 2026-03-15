# crypto_market_dashboard_ar.py

import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

st.set_page_config(page_title="لوحة تحكم السوق والمؤشرات", layout="wide")

st.title("📊 لوحة تحكم السوق - السيولة وحالة الخوف والطمع ونوايا الحيتان")

# -----------------------------
# بيانات السيولة وحجم التداول الإجمالي (تقريبي) - نستخدم CoinGecko Top 100
# -----------------------------
@st.cache_data(ttl=300)
def get_total_market_volume():
    url = "https://api.coingecko.com/api/v3/global"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        total_vol = data['data']['total_volume']['usd']
        return total_vol
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
# تحركات الحيتان - بيانات تقريبية (CoinGecko Top 10 حجم التداول)
# -----------------------------
@st.cache_data(ttl=300)
def get_whale_activity():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        'vs_currency': 'usd',
        'order': 'market_cap_desc',
        'per_page': 10,
        'page': 1,
        'sparkline': 'false'
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data)
        df = df[['name', 'symbol', 'total_volume']]
        df['volume_million'] = df['total_volume'] / 1_000_000
        return df
    else:
        return None

# -----------------------------
# Stablecoin Dominance
# -----------------------------
@st.cache_data(ttl=300)
def get_stablecoin_dominance():
    url = "https://api.coingecko.com/api/v3/global"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        btc_dominance = data['data']['market_cap_percentage']['btc']
        eth_dominance = data['data']['market_cap_percentage']['eth']
        stablecoin_dominance = data['data']['market_cap_percentage']['usdt'] + data['data']['market_cap_percentage'].get('usdc',0)
        return stablecoin_dominance, btc_dominance, eth_dominance
    else:
        return None, None, None

# -----------------------------
# زر التحديث
# -----------------------------
if st.button("تحديث كل المؤشرات"):
    total_volume = get_total_market_volume()
    fear_greed_value, fear_greed_class = get_fear_greed_index()
    whale_df = get_whale_activity()
    stable_d, btc_d, eth_d = get_stablecoin_dominance()
    
    # -----------------------------
    # تفسير السيولة
    # -----------------------------
    liquidity_threshold = 25_000_000_000  # 25 مليار دولار كمثال للسيولة عالية
    if total_volume is not None:
        if total_volume > liquidity_threshold:
            liquidity_signal = "داخل سيولة السوق"
            liquidity_color = "green"
            liquidity_emoji = "🟢"
        else:
            liquidity_signal = "خارج سيولة السوق / تدفق ضعيف"
            liquidity_color = "red"
            liquidity_emoji = "🔴"
        st.subheader("💧 السيولة العامة")
        st.markdown(f"<h2 style='color:{liquidity_color}'>{liquidity_emoji} {liquidity_signal}</h2>", unsafe_allow_html=True)
        st.write(f"حجم التداول الإجمالي في السوق: ${total_volume:,.0f}")
    
    # -----------------------------
    # مؤشر الخوف والطمع
    # -----------------------------
    if fear_greed_value is not None:
        fg_color = "green" if fear_greed_class in ["طمع", "حياد"] else "red"
        st.subheader("😎 مؤشر الخوف والطمع")
        st.markdown(f"<h2 style='color:{fg_color}'>{fear_greed_value} ({fear_greed_class})</h2>", unsafe_allow_html=True)
        # التفسير بالعربي
        st.write("""
        **تفسير المؤشر:**  
        - 0-20: خوف شديد → السوق هابط، قد تكون فرصة شراء على المدى الطويل  
        - 21-40: خوف → السوق متردد، الحذر مطلوب  
        - 41-60: حياد → السوق متوازن، متابعة السوق  
        - 61-80: طمع → السوق صاعد، قد يكون وقت بيع جزئي  
        - 81-100: طمع شديد → السوق متحمس جدًا، خطر تضخم الفقاعة
        """)
    
    # -----------------------------
    # تحركات الحيتان
    # -----------------------------
    if whale_df is not None:
        st.subheader("🐋 نشاط الحيتان (Top 10 Market Cap)")
        st.write("حجم التداول لكل عملة بالملايين:")
        st.dataframe(whale_df[['name', 'symbol', 'volume_million']])
        # رسم بياني
        st.subheader("📊 رسم بياني لنشاط الحيتان")
        fig, ax = plt.subplots(figsize=(8,3))
        ax.bar(whale_df['symbol'], whale_df['volume_million'], color='blue')
        ax.set_ylabel("حجم التداول (مليون دولار)")
        ax.set_xlabel("رمز العملة")
        ax.set_title("نشاط الحيتان تقريبياً")
        st.pyplot(fig)
    
    # -----------------------------
    # Stablecoin Dominance
    # -----------------------------
    if stable_d is not None:
        st.subheader("💵 سيطرة الستابل كوين")
        st.write(f"نسبة الستابل كوين في السوق: {stable_d:.2f}%")
        if stable_d > 10:
            st.write("🟢 السيولة جاهزة للدخول → احتمال صعود السوق")
        else:
            st.write("🔴 السيولة ضعيفة → السوق ممكن يهبط أو متذبذب")
    
    # -----------------------------
    # التوصية العامة
    # -----------------------------
    st.subheader("📝 التوصية العامة")
    if liquidity_color == "green" and fear_greed_class in ["حياد", "طمع"] and stable_d > 10:
        recommendation = "✅ السوق داخله سيولة، وقت مناسب للشراء أو الثبات"
    elif liquidity_color == "red" and fear_greed_class in ["خوف"]:
        recommendation = "⚠️ الحذر، السوق ضعيف لكن قد توجد فرصة للشراء على المدى الطويل"
    else:
        recommendation = "🟡 راقب السوق وانتظر الفرصة المناسبة"
    st.write(recommendation)
