import streamlit as st
import requests
import pandas as pd
import ta
import numpy as np
import os
import google.generativeai as genai

# 🔒 جلب المفتاح من Environment Variable
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    st.warning("مفتاح Gemini API مش موجود! التحليل بالـ AI هيوقف لحد ما تضيفه في Secrets.")
    ai_enabled = False
else:
    genai.configure(api_key=api_key)
    ai_enabled = True

st.set_page_config(layout="wide")
st.title("🚀 Crypto AI Analyzer PRO - النسخة المحسّنة بالقوة")

# اختيار مدة البيانات التاريخية
days = st.selectbox("مدة البيانات التاريخية", ["90","365"])
days = int(days)

# دالة لجلب أقوى موديل يدعم generateContent
def get_best_model():
    if not ai_enabled:
        return None
    models = genai.list_models()
    for m in models:
        if "generateContent" in m.supported_generation_methods:
            return m.name
    return None

best_model = get_best_model()
if ai_enabled and not best_model:
    st.error("❌ مفيش موديل يدعم generateContent في حسابك دلوقتي")
    st.stop()
elif ai_enabled:
    st.info(f"الموديل المستخدم للتحليل AI: {best_model}")

# زر فلتر أفضل 10 عملات
if st.button("فلتر أفضل 10 عملات"):
    st.info("جلب أفضل 50 عملة من CoinGecko ...")
    coins_list = requests.get(
        "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=50&page=1"
    ).json()

    top_coins = []

    for c in coins_list:
        coin_symbol = c['symbol'].upper()
        coin_id = c['id']

        # جلب البيانات التاريخية
        try:
            url = f"https://min-api.cryptocompare.com/data/v2/histoday?fsym={coin_symbol}&tsym=USD&limit={days}"
            r = requests.get(url).json()
            df = pd.DataFrame(r["Data"]["Data"])
            if len(df) < 20:
                continue
        except:
            continue

        price = df["close"].iloc[-1]
        volume = df["volumeto"].iloc[-1]

        # مؤشرات فنية
        df["RSI"] = ta.momentum.RSIIndicator(df["close"]).rsi()
        ema20 = ta.trend.EMAIndicator(df["close"], window=20)
        ema50 = ta.trend.EMAIndicator(df["close"], window=50)
        macd = ta.trend.MACD(df["close"])
        df["EMA20"] = ema20.ema_indicator()
        df["EMA50"] = ema50.ema_indicator()
        df["MACD"] = macd.macd()
        df["MACD_SIGNAL"] = macd.macd_signal()

        rsi = df["RSI"].iloc[-1]
        ema20_val = df["EMA20"].iloc[-1]
        ema50_val = df["EMA50"].iloc[-1]
        macd_val = df["MACD"].iloc[-1]
        macd_signal = df["MACD_SIGNAL"].iloc[-1]

        # Volume Profile
        vp = df.groupby(pd.cut(df["close"], 20))["volumeto"].sum()
        vp_zone = vp.idxmax()
        vp_range = f"{vp_zone.left:.2f} - {vp_zone.right:.2f} USD"

        volume_spike = volume > df["volumeto"].mean() * 2
        whale_flag = "🚨 تجمع حيتان" if volume_spike else ""

        # MarketCap و Rank
        try:
            cg = requests.get(f"https://api.coingecko.com/api/v3/coins/{coin_id}").json()
            marketcap = cg.get("market_data", {}).get("market_cap", {}).get("usd", None)
            rank = cg.get("market_cap_rank", None)
            if marketcap is None or rank is None:
                continue
        except:
            continue

        # Score
        score = 0
        if rsi < 35: score += 2
        if ema20_val > ema50_val: score += 2
        if macd_val > macd_signal: score += 2
        if volume_spike: score += 2
        if rank < 100: score += 2

        top_coins.append({
            "symbol": coin_symbol,
            "id": coin_id,
            "price": price,
            "marketcap": marketcap,
            "volume": volume,
            "rank": rank,
            "RSI": rsi,
            "EMA20": ema20_val,
            "EMA50": ema50_val,
            "MACD": macd_val,
            "VolumeProfile": vp_range,
            "Score": score,
            "Whale": whale_flag
        })

    # ترتيب العملات حسب Score
    top_coins = sorted(top_coins, key=lambda x: x["Score"], reverse=True)
    top_10 = top_coins[:10]

    st.subheader("🏆 أفضل 10 عملات حسب Score")
    for i, coin in enumerate(top_10,1):
        st.write(f"### {i}. {coin['symbol']} - Score: {coin['Score']} - السعر: {coin['price']}$ - Rank: {coin['rank']}")
        st.write(f"Market Cap: {coin['marketcap']} | Volume: {coin['volume']}")
        st.write(f"RSI: {round(coin['RSI'],2)} | EMA20: {round(coin['EMA20'],2)} | EMA50: {round(coin['EMA50'],2)} | MACD: {round(coin['MACD'],2)}")
        st.write(f"Volume Profile Zone: {coin['VolumeProfile']}")
        if coin["Whale"]:
            st.success(coin["Whale"])

        # زر تحليل AI لكل عملة
        if ai_enabled:
            if st.button(f"🤖 تحليل AI لـ {coin['symbol']}", key=f"ai_{coin['symbol']}"):
                prompt = f"""
                حلل العملة التالية:

                Coin: {coin['symbol']}
                Price: {coin['price']}
                Volume: {coin['volume']}
                MarketCap: {coin['marketcap']}
                Rank: {coin['rank']}
                RSI: {coin['RSI']}
                EMA20: {coin['EMA20']}
                EMA50: {coin['EMA50']}
                MACD: {coin['MACD']}
                VolumeProfile: {coin['VolumeProfile']}
                Score: {coin['Score']}/10

                اكتب تقرير كامل يشمل:
                - الاتجاه
                - الدعم والمقاومة
                - أفضل نقطة شراء
                - الهدف
                - وقف الخسارة
                - توقع الحركة القادمة
                """
                with st.spinner("جاري تحليل AI ..."):
                    model = genai.GenerativeModel(best_model)
                    response = model.generate_content(prompt)
                    st.write(response.text)

# خانة تحليل عملة محددة
st.subheader("🔍 تحليل عملة محددة")
custom_coin = st.text_input("ادخل رمز العملة (مثل BTC):").upper()
if st.button("جلب بيانات العملة", key="custom_coin_data"):
    try:
        url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids={custom_coin}"
        data = requests.get(url).json()
        if not data:
            st.error("العملة مش موجودة في CoinGecko.")
        else:
            c = data[0]
            st.write(f"### {c['symbol'].upper()} - السعر: {c['current_price']}$ - Rank: {c['market_cap_rank']}")
            st.write(f"Market Cap: {c['market_cap']} | Volume: {c['total_volume']}")
            st.write(f"High 24h: {c['high_24h']} | Low 24h: {c['low_24h']}")
            if ai_enabled and st.button(f"🤖 تحليل AI لـ {c['symbol'].upper()}", key=f"ai_custom_{c['symbol']}"):
                prompt = f"""
                حلل العملة التالية:

                Coin: {c['symbol'].upper()}
                Price: {c['current_price']}
                Volume: {c['total_volume']}
                MarketCap: {c['market_cap']}
                Rank: {c['market_cap_rank']}

                اكتب تقرير كامل يشمل:
                - الاتجاه
                - الدعم والمقاومة
                - أفضل نقطة شراء
                - الهدف
                - وقف الخسارة
                - توقع الحركة القادمة
                """
                with st.spinner("جاري تحليل AI ..."):
                    model = genai.GenerativeModel(best_model)
                    response = model.generate_content(prompt)
                    st.write(response.text)
    except Exception as e:
        st.error(f"❌ حدث خطأ: {e}")
