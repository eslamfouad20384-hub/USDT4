# crypto_whale_dashboard_ar.py

import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

st.set_page_config(page_title="لوحة تحكم الحيتان والسوق", layout="wide")
st.title("🦈 لوحة تحكم الحيتان وحالة السوق - بالعربي")

# -----------------------------
# 1️⃣ السيولة العامة (Liquidity Flow)
# -----------------------------
@st.cache_data(ttl=300)
def get_total_market_volume():
    url = "https://api.coingecko.com/api/v3/global"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        total_vol = data['data']['total_volume']['usd']
        return total_vol
    return None

# -----------------------------
# 2️⃣ مؤشر الخوف والطمع
# -----------------------------
@st.cache_data(ttl=600)
def get_fear_greed_index():
    url = "https://api.alternative.me/fng/?limit=1"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        value = int(data['data'][0]['value'])
        class_en = data['data'][0]['value_classification']
        mapping = {
            "extreme fear": "خوف شديد",
            "fear": "خوف",
            "neutral": "حياد",
            "greed": "طمع",
            "extreme greed": "طمع شديد"
        }
        class_ar = mapping.get(class_en.lower(), class_en)
        return value, class_ar
    return None, None

# -----------------------------
# 3️⃣ نشاط الحيتان (Top 10 Coins as approximation)
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
        df = pd.DataFrame(response.json())
        df = df[['name','symbol','total_volume']]
        df['volume_million'] = df['total_volume'] / 1_000_000
        return df
    return None

# -----------------------------
# 4️⃣ Stablecoin Dominance
# -----------------------------
@st.cache_data(ttl=300)
def get_stablecoin_dominance():
    url = "https://api.coingecko.com/api/v3/global"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        market = data['data']['market_cap_percentage']
        stable_d = market.get('usdt',0) + market.get('usdc',0)
        btc_d = market.get('btc',0)
        eth_d = market.get('eth',0)
        return stable_d, btc_d, eth_d
    return None, None, None

# -----------------------------
# 5️⃣ Exchange Flow approximation (In/Out)
# -----------------------------
@st.cache_data(ttl=300)
def get_exchange_flow():
    # تقريب: نستخدم الحجم الكلي كبديل لتدفقات دخول وخروج
    # في نسخة كاملة ممكن تستخدم APIs من CryptoQuant أو Glassnode
    total_volume = get_total_market_volume()
    # تخيل أن 55% داخلة، 45% خارجة
    inflow = total_volume * 0.55
    outflow = total_volume * 0.45
    return inflow, outflow

# -----------------------------
# زر التحديث
# -----------------------------
if st.button("تحديث كل المؤشرات"):
    # سيولة
    total_vol = get_total_market_volume()
    liquidity_threshold = 25_000_000_000
    if total_vol is not None:
        if total_vol > liquidity_threshold:
            liquidity_signal = "داخل سيولة السوق"
            liquidity_color = "green"
            liquidity_emoji = "🟢"
        else:
            liquidity_signal = "خارج سيولة السوق / تدفق ضعيف"
            liquidity_color = "red"
            liquidity_emoji = "🔴"
        st.subheader("💧 السيولة العامة")
        st.markdown(f"<h2 style='color:{liquidity_color}'>{liquidity_emoji} {liquidity_signal}</h2>", unsafe_allow_html=True)
        st.write(f"حجم التداول الإجمالي: ${total_vol:,.0f}")

    # الخوف والطمع
    fg_value, fg_class = get_fear_greed_index()
    if fg_value is not None:
        fg_color = "green" if fg_class in ["طمع","حياد"] else "red"
        st.subheader("😎 مؤشر الخوف والطمع")
        st.markdown(f"<h2 style='color:{fg_color}'>{fg_value} ({fg_class})</h2>", unsafe_allow_html=True)
        st.write("""
        **تفسير المؤشر:**  
        - 0-20: خوف شديد → السوق هابط، فرصة شراء على المدى الطويل  
        - 21-40: خوف → السوق متردد، الحذر مطلوب  
        - 41-60: حياد → السوق متوازن، متابعة السوق  
        - 61-80: طمع → السوق صاعد، قد يكون وقت بيع جزئي  
        - 81-100: طمع شديد → السوق متحمس جدًا، خطر تضخم الفقاعة
        """)

    # نشاط الحيتان
    whale_df = get_whale_activity()
    if whale_df is not None:
        st.subheader("🐋 نشاط الحيتان (Top 10 Coins تقريبًا)")
        st.write("حجم التداول بالملايين:")
        st.dataframe(whale_df[['name','symbol','volume_million']])
        st.subheader("📊 رسم بياني لنشاط الحيتان")
        fig, ax = plt.subplots(figsize=(8,3))
        ax.bar(whale_df['symbol'], whale_df['volume_million'], color='blue')
        ax.set_ylabel("حجم التداول (مليون دولار)")
        ax.set_xlabel("رمز العملة")
        ax.set_title("نشاط الحيتان تقريبياً")
        st.pyplot(fig)

    # Stablecoin Dominance
    stable_d, btc_d, eth_d = get_stablecoin_dominance()
    if stable_d is not None:
        st.subheader("💵 سيطرة الستابل كوين")
        st.write(f"نسبة الستابل كوين في السوق: {stable_d:.2f}%")
        if stable_d > 10:
            st.write("🟢 السيولة جاهزة للدخول → احتمال صعود السوق")
        else:
            st.write("🔴 السيولة ضعيفة → السوق ممكن يهبط أو متذبذب")

    # Exchange Flow
    inflow, outflow = get_exchange_flow()
    st.subheader("🏦 تقريب تدفقات البورصات (Inflow/Outflow)")
    st.write(f"تقريب السيولة الداخلة: ${inflow:,.0f}")
    st.write(f"تقريب السيولة الخارجة: ${outflow:,.0f}")
    if inflow > outflow:
        st.write("🟢 تدفقات داخل البورصات أقل من الخارج → السوق متجه صعود")
    else:
        st.write("🔴 تدفقات داخل البورصات أعلى → ضغط بيع محتمل")

    # -----------------------------
    # التوصية العامة بالعربي
    # -----------------------------
    st.subheader("📝 التوصية العامة")
    if liquidity_color == "green" and fg_class in ["حياد","طمع"] and stable_d>10:
        rec = "✅ السوق داخله سيولة، وقت مناسب للشراء أو الثبات"
    elif liquidity_color=="red" and fg_class in ["خوف"]:
        rec = "⚠️ الحذر، السوق ضعيف لكن قد توجد فرصة شراء على المدى الطويل"
    else:
        rec = "🟡 راقب السوق وانتظر الفرصة المناسبة"
    st.write(rec)
