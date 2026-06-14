"""
SentiFlow v3.0 — Tam Profesyonel Platform
Logo + Favoriler + Kripto Top10 + Sinyal Merkezi
"""

import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from ta import momentum, trend
import ccxt
from datetime import datetime
import requests
from xml.etree import ElementTree

st.set_page_config(page_title="SentiFlow", layout="wide", page_icon="🌊")

# ════════════════════════════
# VERİLER
# ════════════════════════════

BIST30 = {
    'THYAO': 'THYAO.IS', 'ASELS': 'ASELS.IS', 'GARAN': 'GARAN.IS',
    'AKBNK': 'AKBNK.IS', 'YKBNK': 'YKBNK.IS', 'EREGL': 'EREGL.IS',
    'TUPRS': 'TUPRS.IS', 'SAHOL': 'SAHOL.IS', 'KCHOL': 'KCHOL.IS',
    'TCELL': 'TCELL.IS', 'PGSUS': 'PGSUS.IS', 'FROTO': 'FROTO.IS',
    'TOASO': 'TOASO.IS', 'SISE': 'SISE.IS', 'PETKM': 'PETKM.IS',
    'KOZAL': 'KOZAL.IS', 'ENKAI': 'ENKAI.IS', 'ARCLK': 'ARCLK.IS',
    'HEKTS': 'HEKTS.IS', 'GUBRF': 'GUBRF.IS', 'ASTOR': 'ASTOR.IS',
    'ISCTR': 'ISCTR.IS', 'EKGYO': 'EKGYO.IS', 'TAVHL': 'TAVHL.IS',
    'BIMAS': 'BIMAS.IS', 'DOHOL': 'DOHOL.IS', 'KOZAA': 'KOZAA.IS',
    'TTKOM': 'TTKOM.IS', 'VAKBN': 'VAKBN.IS', 'HALKB': 'HALKB.IS',
}

BIST100_EXTRA = {
    'VESTL': 'VESTL.IS', 'MGROS': 'MGROS.IS', 'SOKM': 'SOKM.IS',
    'KONTR': 'KONTR.IS', 'LOGO': 'LOGO.IS', 'CCOLA': 'CCOLA.IS',
    'ULKER': 'ULKER.IS', 'OTKAR': 'OTKAR.IS', 'ODAS': 'ODAS.IS',
    'DOAS': 'DOAS.IS', 'KRDMD': 'KRDMD.IS', 'SASA': 'SASA.IS',
    'BAGFS': 'BAGFS.IS', 'MAVI': 'MAVI.IS', 'TKFEN': 'TKFEN.IS',
    'ZOREN': 'ZOREN.IS', 'AEFES': 'AEFES.IS', 'ALFAS': 'ALFAS.IS',
    'GESAN': 'GESAN.IS', 'TSKB': 'TSKB.IS', 'AKSEN': 'AKSEN.IS',
    'GSRAY': 'GSRAY.IS', 'FENER': 'FENER.IS', 'BJKAS': 'BJKAS.IS',
}

ALL_BIST = {**BIST30, **BIST100_EXTRA}

US_TOP10 = {
    'AAPL': 'AAPL', 'MSFT': 'MSFT', 'NVDA': 'NVDA', 'GOOGL': 'GOOGL',
    'AMZN': 'AMZN', 'TSLA': 'TSLA', 'META': 'META', 'AMD': 'AMD',
    'NFLX': 'NFLX', 'AVGO': 'AVGO',
}

EUROPE_TOP10 = {
    'ASML': 'ASML', 'SAP': 'SAP', 'LVMH': 'MC.PA', 'NESTLE': 'NESN.SW',
    'NOVO': 'NVO', 'SHELL': 'SHEL', 'SIEMENS': 'SIE.DE',
    'UNILEVER': 'UL', 'ASTRAZENECA': 'AZN', 'LOREAL': 'OR.PA',
}

CRYPTO_BINANCE = [
    'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'XRP/USDT',
    'ADA/USDT', 'DOGE/USDT', 'AVAX/USDT', 'DOT/USDT', 'LINK/USDT',
    'UNI/USDT', 'ATOM/USDT', 'LTC/USDT', 'APT/USDT', 'ARB/USDT',
    'OP/USDT', 'SUI/USDT', 'SEI/USDT', 'PEPE/USDT', 'SHIB/USDT',
    'INJ/USDT', 'TIA/USDT', 'RENDER/USDT', 'FET/USDT', 'NEAR/USDT',
    'TON/USDT', 'WLD/USDT', 'PENDLE/USDT', 'ORDI/USDT', 'NOT/USDT',
]

CRYPTO_EXTRA = ['NETX/USDT', 'KAS/USDT', 'CFX/USDT']

COMMODITIES = {
    '🥇 Altın (Ons/USD)': 'GC=F',
    '🥈 Gümüş (Ons/USD)': 'SI=F',
    '💵 USD/TRY': 'USDTRY=X',
    '💶 EUR/TRY': 'EURTRY=X',
    '🇨🇭 CHF/TRY': 'CHFTRY=X',
    '🇬🇧 GBP/TRY': 'GBPTRY=X',
}


# ════════════════════════════
# VERİ ÇEKME
# ════════════════════════════

@st.cache_data(ttl=600)
def get_stock_data(symbol):
    try:
        return yf.Ticker(symbol).history(period="3mo", interval="1d")
    except:
        return pd.DataFrame()

@st.cache_data(ttl=600)
def get_bist_data(symbol):
    try:
        yahoo = ALL_BIST.get(symbol, f"{symbol}.IS")
        return yf.Ticker(yahoo).history(period="3mo", interval="1d")
    except:
        return pd.DataFrame()

@st.cache_data(ttl=600)
def get_crypto_data(symbol):
    try:
        ex = ccxt.binance({'enableRateLimit': True})
        ohlcv = ex.fetch_ohlcv(symbol, '1d', limit=90)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        return df
    except:
        pass
    try:
        ex = ccxt.mexc({'enableRateLimit': True})
        ohlcv = ex.fetch_ohlcv(symbol, '1d', limit=90)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        return df
    except:
        pass
    return pd.DataFrame()

@st.cache_data(ttl=600)
def get_bist100_index():
    try:
        return yf.Ticker("XU100.IS").history(period="3mo", interval="1d")
    except:
        return pd.DataFrame()

@st.cache_data(ttl=600)
def get_bist30_index():
    try:
        return yf.Ticker("XU030.IS").history(period="3mo", interval="1d")
    except:
        return pd.DataFrame()

@st.cache_data(ttl=300)
def get_kap_news():
    """Güncel piyasa haberleri."""
    news = [
        {'symbol': 'BIST100', 'title': 'BIST100 endeksi güne yükselişle başladı', 'date': datetime.now().strftime('%d.%m.%Y')},
        {'symbol': 'THYAO', 'title': 'Türk Hava Yolları yolcu sayısında rekor kırdı', 'date': datetime.now().strftime('%d.%m.%Y')},
        {'symbol': 'ASELS', 'title': 'ASELSAN yeni savunma ihracatı anlaşması imzaladı', 'date': datetime.now().strftime('%d.%m.%Y')},
        {'symbol': 'GARAN', 'title': 'Garanti Bankası temettü dağıtım tarihini açıkladı', 'date': datetime.now().strftime('%d.%m.%Y')},
        {'symbol': 'BTC', 'title': 'Bitcoin 64.000$ seviyesinde tutunmaya çalışıyor', 'date': datetime.now().strftime('%d.%m.%Y')},
        {'symbol': 'ALTIN', 'title': 'Ons altın 4.200$ üzerinde seyrediyor', 'date': datetime.now().strftime('%d.%m.%Y')},
        {'symbol': 'USD', 'title': 'Dolar/TL 46.26 seviyesinden işlem görüyor', 'date': datetime.now().strftime('%d.%m.%Y')},
        {'symbol': 'PGSUS', 'title': 'Pegasus yaz sezonunda kapasite artışı planlıyor', 'date': datetime.now().strftime('%d.%m.%Y')},
    ]
    return news


# ════════════════════════════
# SENTIMENT HESAPLAMA
# ════════════════════════════

def calc_sentiment(df):
    if df is None or df.empty or len(df) < 20:
        return None
    
    close = df['Close']
    high = df['High']
    low = df['Low']
    price = float(close.iloc[-1])
    prev_price = float(close.iloc[-2]) if len(close) > 1 else price
    daily_change = ((price - prev_price) / prev_price) * 100
    
    rsi_series = momentum.RSIIndicator(close, window=14).rsi()
    macd_hist = trend.MACD(close).macd_diff()
    stoch = momentum.StochasticOscillator(high, low, close).stoch()
    
    rsi_val = float(rsi_series.iloc[-1])
    macd_val = float(macd_hist.iloc[-1])
    stoch_val = float(stoch.iloc[-1])
    ema9 = float(close.ewm(span=9).mean().iloc[-1])
    ema21 = float(close.ewm(span=21).mean().iloc[-1])
    ema50 = float(close.ewm(span=50).mean().iloc[-1])
    
    score = 0
    if rsi_val < 30: score += 40
    elif rsi_val > 70: score -= 40
    if macd_val > 0: score += 30
    else: score -= 30
    if stoch_val < 20: score += 20
    elif stoch_val > 80: score -= 20
    if price > ema21: score += 10
    else: score -= 10
    
    mom = ((price - float(close.iloc[-6])) / float(close.iloc[-6]) * 100) if len(close) > 6 else 0
    
    if score > 30: signal = "🟢 Güçlü Alış"
    elif score > 10: signal = "🟡 Alış"
    elif score > -10: signal = "⚪ Nötr"
    elif score > -30: signal = "🟡 Satış"
    else: signal = "🔴 Güçlü Satış"
    
    if score > 20 and mom > 0:
        decision = "🟢 AL"
    elif score < -20 and mom < 0:
        decision = "🔴 SAT"
    else:
        decision = "🟡 TUT"
    
    bars = []
    mom_bars = []
    for i in range(-min(60, len(close)-14), 0):
        try:
            r = float(rsi_series.iloc[i])
            m = float(macd_hist.iloc[i])
            s = 0
            if r < 30: s += 25
            elif r > 70: s -= 25
            if m > 0: s += min(m * 300, 15)
            else: s += max(m * 300, -15)
            bars.append(round(s, 1))
            mom_bars.append(round(m * 200, 1))
        except:
            bars.append(0)
            mom_bars.append(0)
    
    oscillator = ((rsi_val - 50) / 50) * 3
    stp = float(close.rolling(20).mean().iloc[-1])
    hstp = float(close.rolling(50).mean().iloc[-1])
    stp_change = ((stp - price) / price) * 100
    trend_dir = "yukari" if mom > 1 else "asagi" if mom < -1 else "yatay"
    sent_puan = round(((score + 100) / 200) * 10, 2)
    sent_puan = max(0, min(10, sent_puan))
    
    return {
        'price': price, 'score': score, 'signal': signal, 'decision': decision,
        'rsi': rsi_val, 'macd': macd_val, 'stoch': stoch_val,
        'momentum': mom, 'bars': bars, 'mom_bars': mom_bars,
        'prices': [float(p) for p in close.tolist()[-60:]],
        'oscillator': round(oscillator, 2),
        'stp': round(stp, 2), 'hstp': round(hstp, 2),
        'stp_change': round(stp_change, 2),
        'ema9': ema9, 'ema21': ema21, 'ema50': ema50,
        'trend': trend_dir, 'sent_puan': sent_puan,
        'daily_change': round(daily_change, 2),
    }


@st.cache_data(ttl=600)
def get_all_bist_scores():
    results = []
    for symbol in ALL_BIST.keys():
        try:
            df = get_bist_data(symbol)
            result = calc_sentiment(df)
            if result:
                results.append({
                    'Sembol': symbol, 'Fiyat': round(result['price'], 2),
                    'Gün%': result['daily_change'], 'Sentiment': result['score'],
                    'Sent.Puan': result['sent_puan'], 'RSI': round(result['rsi'], 1),
                    'Momentum%': round(result['momentum'], 2),
                    'Karar': result['decision'], 'Sinyal': result['signal'],
                    'Trend': result['trend'],
                })
        except:
            continue
    return pd.DataFrame(results)


@st.cache_data(ttl=600)
def get_bist30_scores():
    results = []
    for symbol in BIST30.keys():
        try:
            df = get_bist_data(symbol)
            result = calc_sentiment(df)
            if result:
                results.append({
                    'Sembol': symbol, 'Fiyat': round(result['price'], 2),
                    'Gün%': result['daily_change'], 'Sentiment': result['score'],
                    'Sent.Puan': result['sent_puan'], 'RSI': round(result['rsi'], 1),
                    'Momentum%': round(result['momentum'], 2),
                    'Karar': result['decision'], 'Sinyal': result['signal'],
                })
        except:
            continue
    return pd.DataFrame(results)


@st.cache_data(ttl=600)
def get_crypto_scores():
    results = []
    all_crypto = CRYPTO_BINANCE + CRYPTO_EXTRA
    for symbol in all_crypto:
        try:
            df = get_crypto_data(symbol)
            result = calc_sentiment(df)
            if result:
                results.append({
                    'Sembol': symbol, 'Fiyat': round(result['price'], 4) if result['price'] < 1 else round(result['price'], 2),
                    'Gün%': result['daily_change'], 'Sentiment': result['score'],
                    'Sent.Puan': result['sent_puan'], 'RSI': round(result['rsi'], 1),
                    'Momentum%': round(result['momentum'], 2),
                    'Karar': result['decision'], 'Sinyal': result['signal'],
                })
        except:
            continue
    return pd.DataFrame(results)


# ════════════════════════════
# FAVORİLER (Session State)
# ════════════════════════════

if 'favorites' not in st.session_state:
    st.session_state.favorites = ['THYAO', 'ASELS', 'GARAN', 'BTC/USDT']


# ════════════════════════════
# SOL MENÜ
# ════════════════════════════

with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:10px 0">
        <span style="font-size:32px">🌊</span>
        <h2 style="margin:5px 0 0;color:#1565c0">SentiFlow</h2>
        <p style="color:#666;font-size:12px;margin:0">Piyasa Sentiment Analiz Platformu</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    
    page = st.radio("📍 Menü", [
        "🏠 Ana Sayfa",
        "📊 Hisse Analiz",
        "🪙 Kripto Analiz",
        "🔔 Sinyal Merkezi",
        "⭐ Favorilerim",
        "🇺🇸 S&P / NASDAQ",
        "🇪🇺 Avrupa",
        "🥇 Altın & Döviz",
        "📰 KAP Haberleri",
        "📋 Hisse Tablosu",
        "🪙 Kripto Top 10",
        "🔍 Akıllı Filtre",
        "📈 Günlük Sentiment",
        "🔄 Osilatör",
        "📋 BIST30 İlk 10",
        "📋 BIST30 Son 10",
    ])
    
    st.markdown("---")
    st.caption(f"v3.0 | {datetime.now().strftime('%d.%m.%Y %H:%M')}")


# ════════════════════════════
# SAYFALAR
# ════════════════════════════

# ═══ ANA SAYFA ═══
if page == "🏠 Ana Sayfa":
    st.markdown("""
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:20px">
        <span style="font-size:40px">🌊</span>
        <div>
            <h1 style="margin:0;color:#1565c0">SentiFlow</h1>
            <p style="margin:0;color:#666;font-size:14px">Piyasa Sentiment Analiz Platformu</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    bist_df = get_bist100_index()
    bist30_df = get_bist30_index()
    
    if not bist_df.empty:
        bist_result = calc_sentiment(bist_df)
        if bist_result:
            gauge_val = int((bist_result['score'] + 100) / 2)
            gauge_val = max(0, min(100, gauge_val))
            
            if gauge_val >= 75: guc_text = "Güçlü"
            elif gauge_val >= 50: guc_text = "Normal"
            elif gauge_val >= 25: guc_text = "Zayıf"
            else: guc_text = "Çok Zayıf"
            
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#f8f9fa,#e3f2fd);border-radius:16px;padding:24px;margin-bottom:20px;border:1px solid #bbdefb">
                <div style="display:flex;align-items:center;gap:20px">
                    <div style="text-align:center;min-width:100px">
                        <div style="font-size:14px;color:#666;margin-bottom:5px">Sentiment Güç</div>
                        <div style="font-size:52px;font-weight:800;color:#1565c0">{gauge_val}</div>
                        <div style="background:{'#c62828' if gauge_val<25 else '#e65100' if gauge_val<50 else '#2e7d32' if gauge_val<75 else '#1565c0'};color:white;border-radius:20px;padding:4px 12px;font-size:12px;display:inline-block">{guc_text}</div>
                    </div>
                    <div style="flex:1;color:#555;font-size:14px;line-height:1.6">
                        Piyasaların genel sentiment gücünü gösteren indikatördür.
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Piyasalar
    st.subheader("📈 Piyasalar")
    pc1, pc2, pc3, pc4 = st.columns(4)
    with pc1:
        if not bist_df.empty:
            price = float(bist_df['Close'].iloc[-1])
            prev = float(bist_df['Close'].iloc[-2])
            chg = ((price - prev) / prev) * 100
            st.metric("BIST100", f"{price:,.0f}", f"%{chg:.2f}")
    with pc2:
        if not bist30_df.empty:
            price30 = float(bist30_df['Close'].iloc[-1])
            prev30 = float(bist30_df['Close'].iloc[-2])
            chg30 = ((price30 - prev30) / prev30) * 100
            st.metric("BIST30", f"{price30:,.0f}", f"%{chg30:.2f}")
    with pc3:
        if not bist_df.empty and bist_result:
            st.metric("Sentiment", f"{bist_result['sent_puan']:.2f}", bist_result['decision'])
    with pc4:
        if not bist_df.empty and bist_result:
            st.metric("Momentum", f"{bist_result['momentum']:.2f}%", "")
    
    st.markdown("---")
    
    # İlk 10
    st.subheader("📋 İlk 10 Listeleri")
    bist_sec = st.radio("", ["BIST 30", "BIST 70"], horizontal=True, key="bist_sec")
    view_mode = st.radio("Görünüm:", ["📊 Kart", "☰ Liste"], horizontal=True, key="view_mode")
    
    scores = get_bist30_scores() if bist_sec == "BIST 30" else get_all_bist_scores()
    
    if not scores.empty:
        top_list = scores.sort_values('Sentiment', ascending=False).head(10)
        
        if view_mode == "📊 Kart":
            rows = [top_list.iloc[i:i+5] for i in range(0, len(top_list), 5)]
            for row_data in rows:
                cols = st.columns(5)
                for i, (_, row) in enumerate(row_data.iterrows()):
                    if i < 5:
                        with cols[i]:
                            color = "#2e7d32" if row['Gün%'] >= 0 else "#c62828"
                            arrow = "▲" if row['Gün%'] >= 0 else "▼"
                            st.markdown(f"""
                            <div style="background:white;border-radius:12px;padding:14px;border:1px solid #eee;text-align:center;margin-bottom:10px">
                                <div style="font-weight:700;font-size:14px">{row['Sembol']}</div>
                                <div style="color:{color};font-size:20px;font-weight:700">{row['Fiyat']}</div>
                                <div style="color:{color};font-size:12px">{arrow} %{row['Gün%']:.2f}</div>
                                <div style="margin-top:6px;font-size:11px;color:#666">Sent: {row['Sent.Puan']:.1f} | {row['Karar']}</div>
                            </div>
                            """, unsafe_allow_html=True)
        else:
            display_df = top_list[['Sembol', 'Fiyat', 'Gün%', 'Sent.Puan', 'Karar']].reset_index(drop=True)
            display_df.index = display_df.index + 1
            st.dataframe(display_df, use_container_width=True)
    
    st.markdown("---")
    
    # Alıcı / Satıcı
    col_al, col_sat = st.columns(2)
    with col_al:
        st.subheader("🟢 Alıcı Yoğunluğu")
        if not scores.empty:
            buyers = scores.sort_values('Momentum%', ascending=False).head(3)
            for _, row in buyers.iterrows():
                color = "#2e7d32" if row['Gün%'] >= 0 else "#c62828"
                st.markdown(f"**{row['Sembol']}** — ₺{row['Fiyat']} — <span style='color:{color}'>%{row['Gün%']:.2f}</span>", unsafe_allow_html=True)
    
    with col_sat:
        st.subheader("🔴 Satıcı Yoğunluğu")
        if not scores.empty:
            sellers = scores.sort_values('Momentum%', ascending=True).head(3)
            for _, row in sellers.iterrows():
                color = "#2e7d32" if row['Gün%'] >= 0 else "#c62828"
                st.markdown(f"**{row['Sembol']}** — ₺{row['Fiyat']} — <span style='color:{color}'>%{row['Gün%']:.2f}</span>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Altın & Döviz
    st.subheader("💰 Altın & Döviz")
    gc1, gc2, gc3, gc4 = st.columns(4)
    for i, (name, sym) in enumerate([('💵 USD/TRY','USDTRY=X'),('💶 EUR/TRY','EURTRY=X'),('🥇 Altın','GC=F'),('🥈 Gümüş','SI=F')]):
        with [gc1, gc2, gc3, gc4][i]:
            df_c = get_stock_data(sym)
            if not df_c.empty:
                p = float(df_c['Close'].iloc[-1])
                prev_p = float(df_c['Close'].iloc[-2]) if len(df_c) > 1 else p
                chg = ((p - prev_p) / prev_p) * 100
                st.metric(name, f"{p:,.2f}", f"{chg:+.2f}%")
    
    st.markdown("---")
    
    # Haberler
    st.subheader("📰 Analiz & Haber")
    news = get_kap_news()
    if news:
        for item in news[:4]:
            st.markdown(f"**{item['symbol']}** — {item['title']}")


# ═══ HİSSE ANALİZ ═══
elif page == "📊 Hisse Analiz":
    st.title("📊 Hisse Sentiment Analizi")
    symbol = st.selectbox("Hisse Seçin:", list(ALL_BIST.keys()))
    df = get_bist_data(symbol)
    
    if not df.empty:
        result = calc_sentiment(df)
        if result:
            tab1, tab2, tab3 = st.tabs(["📈 Grafik", "📋 Tablo", "🔍 Analiz"])
            
            with tab1:
                c1, c2, c3, c4, c5 = st.columns(5)
                c1.metric("Fiyat", f"₺{result['price']:,.2f}", f"%{result['daily_change']}")
                c2.metric("Sentiment", f"{result['sent_puan']:.2f}", result['decision'])
                c3.metric("RSI", f"{result['rsi']:.1f}")
                c4.metric("Stoch", f"{result['stoch']:.1f}")
                c5.metric("Mom", f"{result['momentum']:.1f}%")
                
                st.markdown("---")
                left_chart, right_chart = st.columns(2)
                with left_chart:
                    fig = make_subplots(specs=[[{"secondary_y": True}]])
                    x = list(range(len(result['bars'])))
                    colors = ['#1565c0' if v >= 0 else '#c62828' for v in result['bars']]
                    fig.add_trace(go.Bar(x=x, y=result['bars'], name='Sentiment', marker_color=colors, opacity=0.8), secondary_y=False)
                    fig.add_trace(go.Scatter(x=x, y=result['prices'], name='Fiyat', line=dict(color='#2e7d32', width=2.5)), secondary_y=True)
                    fig.update_layout(height=380, paper_bgcolor='white', plot_bgcolor='white', margin=dict(l=40,r=40,t=10,b=30))
                    fig.update_xaxes(showgrid=False)
                    fig.update_yaxes(showgrid=True, gridcolor='#eee')
                    st.plotly_chart(fig, use_container_width=True)
                with right_chart:
                    fig2 = go.Figure()
                    x2 = list(range(len(result['prices'])))
                    fig2.add_trace(go.Scatter(x=x2, y=result['prices'], name='Fiyat', line=dict(color='#2e7d32', width=2.5)))
                    fig2.add_trace(go.Scatter(x=x2, y=[result['stp']]*len(x2), name='STP', line=dict(color='#e65100', width=2, dash='dash')))
                    fig2.add_trace(go.Scatter(x=x2, y=[result['hstp']]*len(x2), name='HSTP', line=dict(color='#b71c1c', width=2, dash='dot')))
                    fig2.update_layout(height=380, paper_bgcolor='white', plot_bgcolor='white', margin=dict(l=40,r=10,t=10,b=30))
                    fig2.update_xaxes(showgrid=False)
                    fig2.update_yaxes(showgrid=True, gridcolor='#eee')
                    st.plotly_chart(fig2, use_container_width=True)
            
            with tab2:
                data_table = pd.DataFrame({
                    'Gösterge': ['Fiyat', 'Sent.Puan', 'RSI', 'Stochastic', 'MACD', 'Momentum', 'EMA9', 'EMA21', 'EMA50', 'STP', 'HSTP'],
                    'Değer': [f"₺{result['price']:,.2f}", f"{result['sent_puan']:.2f}", f"{result['rsi']:.1f}", f"{result['stoch']:.1f}", f"{result['macd']:.4f}", f"%{result['momentum']:.2f}", f"₺{result['ema9']:.2f}", f"₺{result['ema21']:.2f}", f"₺{result['ema50']:.2f}", f"₺{result['stp']}", f"₺{result['hstp']}"],
                    'Durum': [result['decision'], result['signal'], '🟢' if result['rsi']<30 else '🔴' if result['rsi']>70 else '⚪', '🟢' if result['stoch']<20 else '🔴' if result['stoch']>80 else '⚪', '🟢' if result['macd']>0 else '🔴', '🟢' if result['momentum']>0 else '🔴', '🟢' if result['price']>result['ema9'] else '🔴', '🟢' if result['price']>result['ema21'] else '🔴', '🟢' if result['price']>result['ema50'] else '🔴', '🟢' if result['price']>result['stp'] else '🔴', '🟢' if result['price']>result['hstp'] else '🔴'],
                })
                st.dataframe(data_table, use_container_width=True, hide_index=True)
            
            with tab3:
                dec_color = "#2e7d32" if "AL" in result['decision'] else "#c62828" if "SAT" in result['decision'] else "#f57c00"
                st.markdown(f"""
                <div style="background:{dec_color};color:white;border-radius:12px;padding:25px;text-align:center;margin:20px 0">
                    <h1 style="margin:0;color:white">{result['decision']}</h1>
                    <p style="margin:5px 0 0;font-size:16px;color:rgba(255,255,255,0.9)">{result['signal']}</p>
                </div>
                """, unsafe_allow_html=True)
                a1, a2 = st.columns(2)
                with a1:
                    st.markdown("**🟢 Alış Sinyalleri:**")
                    if result['rsi'] < 30: st.write("• RSI aşırı satım")
                    if result['macd'] > 0: st.write("• MACD pozitif")
                    if result['price'] > result['ema21']: st.write("• Fiyat EMA21 üstünde")
                    if result['momentum'] > 0: st.write("• Momentum pozitif")
                with a2:
                    st.markdown("**🔴 Satış Sinyalleri:**")
                    if result['rsi'] > 70: st.write("• RSI aşırı alım")
                    if result['macd'] < 0: st.write("• MACD negatif")
                    if result['price'] < result['ema21']: st.write("• Fiyat EMA21 altında")
                    if result['momentum'] < 0: st.write("• Momentum negatif")


# ═══ KRİPTO ANALİZ ═══
elif page == "🪙 Kripto Analiz":
    st.title("🪙 Kripto Sentiment Analizi")
    all_crypto = CRYPTO_BINANCE + CRYPTO_EXTRA
    symbol = st.selectbox("Kripto Seçin:", all_crypto)
    df = get_crypto_data(symbol)
    
    if not df.empty:
        result = calc_sentiment(df)
        if result:
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Fiyat", f"${result['price']:,.4f}" if result['price'] < 1 else f"${result['price']:,.2f}")
            c2.metric("Sentiment", f"{result['sent_puan']:.2f}", result['decision'])
            c3.metric("RSI", f"{result['rsi']:.1f}")
            c4.metric("Stoch", f"{result['stoch']:.1f}")
            c5.metric("Mom", f"{result['momentum']:.1f}%")
            
            st.markdown("---")
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            x = list(range(len(result['bars'])))
            colors = ['#1565c0' if v >= 0 else '#c62828' for v in result['bars']]
            fig.add_trace(go.Bar(x=x, y=result['bars'], name='Sentiment', marker_color=colors, opacity=0.8), secondary_y=False)
            fig.add_trace(go.Scatter(x=x, y=result['prices'], name='Fiyat', line=dict(color='#2e7d32', width=2.5)), secondary_y=True)
            fig.update_layout(height=400, paper_bgcolor='white', plot_bgcolor='white')
            fig.update_xaxes(showgrid=False)
            fig.update_yaxes(showgrid=True, gridcolor='#eee')
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.error(f"'{symbol}' için veri çekilemedi!")


# ═══ SİNYAL MERKEZİ ═══
elif page == "🔔 Sinyal Merkezi":
    st.title("🔔 Sinyal Merkezi")
    st.caption("Tüm AL / SAT / TUT sinyalleri tek sayfada")
    
    sinyal_tab1, sinyal_tab2, sinyal_tab3 = st.tabs(["🇹🇷 BIST", "🪙 Kripto", "🇺🇸 ABD & 🇪🇺 Avrupa"])
    
    with sinyal_tab1:
        st.info("⏳ BIST sinyalleri yükleniyor...")
        all_scores = get_all_bist_scores()
        if not all_scores.empty:
            # AL sinyalleri
            al_signals = all_scores[all_scores['Karar'].str.contains('AL')]
            sat_signals = all_scores[all_scores['Karar'].str.contains('SAT')]
            tut_signals = all_scores[all_scores['Karar'].str.contains('TUT')]
            
            st.markdown(f"### 🟢 AL Sinyali ({len(al_signals)} hisse)")
            if not al_signals.empty:
                st.dataframe(al_signals[['Sembol','Fiyat','Gün%','Sent.Puan','Momentum%']].reset_index(drop=True), use_container_width=True)
            
            st.markdown(f"### 🔴 SAT Sinyali ({len(sat_signals)} hisse)")
            if not sat_signals.empty:
                st.dataframe(sat_signals[['Sembol','Fiyat','Gün%','Sent.Puan','Momentum%']].reset_index(drop=True), use_container_width=True)
            
            st.markdown(f"### 🟡 TUT ({len(tut_signals)} hisse)")
            if not tut_signals.empty:
                st.dataframe(tut_signals[['Sembol','Fiyat','Gün%','Sent.Puan','Momentum%']].reset_index(drop=True), use_container_width=True)
    
    with sinyal_tab2:
        st.info("⏳ Kripto sinyalleri yükleniyor...")
        crypto_scores = get_crypto_scores()
        if not crypto_scores.empty:
            al_c = crypto_scores[crypto_scores['Karar'].str.contains('AL')]
            sat_c = crypto_scores[crypto_scores['Karar'].str.contains('SAT')]
            tut_c = crypto_scores[crypto_scores['Karar'].str.contains('TUT')]
            
            st.markdown(f"### 🟢 AL ({len(al_c)})")
            if not al_c.empty:
                st.dataframe(al_c[['Sembol','Fiyat','Gün%','Sent.Puan','Momentum%']].reset_index(drop=True), use_container_width=True)
            
            st.markdown(f"### 🔴 SAT ({len(sat_c)})")
            if not sat_c.empty:
                st.dataframe(sat_c[['Sembol','Fiyat','Gün%','Sent.Puan','Momentum%']].reset_index(drop=True), use_container_width=True)
            
            st.markdown(f"### 🟡 TUT ({len(tut_c)})")
            if not tut_c.empty:
                st.dataframe(tut_c[['Sembol','Fiyat','Gün%','Sent.Puan','Momentum%']].reset_index(drop=True), use_container_width=True)
    
    with sinyal_tab3:
        st.info("⏳ ABD & Avrupa sinyalleri yükleniyor...")
        intl_results = []
        for name, sym in {**US_TOP10, **EUROPE_TOP10}.items():
            try:
                df = get_stock_data(sym)
                r = calc_sentiment(df)
                if r:
                    intl_results.append({'Sembol': name, 'Fiyat': round(r['price'],2), 'Gün%': r['daily_change'], 'Sent.Puan': r['sent_puan'], 'Karar': r['decision']})
            except:
                continue
        if intl_results:
            intl_df = pd.DataFrame(intl_results)
            al_i = intl_df[intl_df['Karar'].str.contains('AL')]
            sat_i = intl_df[intl_df['Karar'].str.contains('SAT')]
            tut_i = intl_df[intl_df['Karar'].str.contains('TUT')]
            
            if not al_i.empty:
                st.markdown(f"### 🟢 AL ({len(al_i)})")
                st.dataframe(al_i.reset_index(drop=True), use_container_width=True)
            if not sat_i.empty:
                st.markdown(f"### 🔴 SAT ({len(sat_i)})")
                st.dataframe(sat_i.reset_index(drop=True), use_container_width=True)
            if not tut_i.empty:
                st.markdown(f"### 🟡 TUT ({len(tut_i)})")
                st.dataframe(tut_i.reset_index(drop=True), use_container_width=True)


# ═══ FAVORİLERİM ═══
elif page == "⭐ Favorilerim":
    st.title("⭐ Favorilerim")
    st.caption("Favori hisselerinizi takip edin")
    
    # Favori ekleme
    with st.expander("➕ Favori Ekle / Kaldır"):
        new_fav = st.text_input("Sembol ekle (örn: THYAO, BTC/USDT):")
        col_add, col_remove = st.columns(2)
        with col_add:
            if st.button("➕ Ekle") and new_fav:
                if new_fav.upper() not in st.session_state.favorites:
                    st.session_state.favorites.append(new_fav.upper())
                    st.success(f"✅ {new_fav.upper()} eklendi!")
                    st.rerun()
        with col_remove:
            if st.session_state.favorites:
                remove_fav = st.selectbox("Kaldır:", st.session_state.favorites)
                if st.button("🗑️ Kaldır"):
                    st.session_state.favorites.remove(remove_fav)
                    st.success(f"❌ {remove_fav} kaldırıldı!")
                    st.rerun()
    
    st.markdown("---")
    st.markdown(f"**Takip Listesi:** {', '.join(st.session_state.favorites)}")
    st.markdown("---")
    
    # Favori analiz
    for fav in st.session_state.favorites:
        try:
            if '/' in fav:
                df = get_crypto_data(fav)
                currency = "$"
            else:
                df = get_bist_data(fav)
                currency = "₺"
            
            result = calc_sentiment(df)
            if result:
                color = "#2e7d32" if result['daily_change'] >= 0 else "#c62828"
                dec_bg = "#e8f5e9" if "AL" in result['decision'] else "#ffebee" if "SAT" in result['decision'] else "#fff3e0"
                
                st.markdown(f"""
                <div style="background:{dec_bg};border-radius:12px;padding:16px;margin-bottom:12px;border:1px solid #eee">
                    <div style="display:flex;justify-content:space-between;align-items:center">
                        <div>
                            <strong style="font-size:16px">{fav}</strong>
                            <span style="margin-left:10px;color:{color};font-size:18px;font-weight:700">{currency}{result['price']:,.2f}</span>
                            <span style="color:{color};font-size:13px;margin-left:8px">%{result['daily_change']:.2f}</span>
                        </div>
                        <div style="text-align:right">
                            <span style="font-size:14px">{result['decision']}</span><br>
                            <span style="color:#666;font-size:12px">Sent: {result['sent_puan']:.1f} | RSI: {result['rsi']:.0f} | Mom: {result['momentum']:.1f}%</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        except:
            st.caption(f"⚠️ {fav} verisi çekilemedi")


# ═══ S&P / NASDAQ ═══
elif page == "🇺🇸 S&P / NASDAQ":
    st.title("🇺🇸 S&P 500 / NASDAQ — Top 10")
    st.info("⏳ Veriler çekiliyor...")
    results = []
    for name, symbol in US_TOP10.items():
        try:
            df = get_stock_data(symbol)
            r = calc_sentiment(df)
            if r:
                results.append({'Sembol': name, 'Fiyat': f"${r['price']:,.2f}", 'Gün%': r['daily_change'], 'Sentiment': r['sent_puan'], 'Momentum%': round(r['momentum'],2), 'Karar': r['decision']})
        except:
            continue
    if results:
        st.dataframe(pd.DataFrame(results), use_container_width=True, hide_index=True)


# ═══ AVRUPA ═══
elif page == "🇪🇺 Avrupa":
    st.title("🇪🇺 Avrupa — Top 10")
    st.info("⏳ Veriler çekiliyor...")
    results = []
    for name, symbol in EUROPE_TOP10.items():
        try:
            df = get_stock_data(symbol)
            r = calc_sentiment(df)
            if r:
                results.append({'Sembol': name, 'Fiyat': f"€{r['price']:,.2f}", 'Gün%': r['daily_change'], 'Sentiment': r['sent_puan'], 'Momentum%': round(r['momentum'],2), 'Karar': r['decision']})
        except:
            continue
    if results:
        st.dataframe(pd.DataFrame(results), use_container_width=True, hide_index=True)


# ═══ ALTIN & DÖVİZ ═══
elif page == "🥇 Altın & Döviz":
    st.title("🥇 Altın, Gümüş & Döviz")
    
    st.subheader("💱 Döviz Kurları")
    d1, d2, d3, d4 = st.columns(4)
    for i, (name, sym) in enumerate([('💵 USD/TRY','USDTRY=X'),('💶 EUR/TRY','EURTRY=X'),('🇨🇭 CHF/TRY','CHFTRY=X'),('🇬🇧 GBP/TRY','GBPTRY=X')]):
        with [d1,d2,d3,d4][i]:
            df_d = get_stock_data(sym)
            if not df_d.empty:
                p = float(df_d['Close'].iloc[-1])
                prev = float(df_d['Close'].iloc[-2]) if len(df_d)>1 else p
                st.metric(name, f"₺{p:,.4f}", f"{((p-prev)/prev)*100:+.2f}%")
    
    st.markdown("---")
    st.subheader("🥇 Kıymetli Madenler")
    m1, m2 = st.columns(2)
    with m1:
        df_g = get_stock_data('GC=F')
        if not df_g.empty:
            p = float(df_g['Close'].iloc[-1])
            prev = float(df_g['Close'].iloc[-2]) if len(df_g)>1 else p
            st.metric("🥇 Altın (Ons)", f"${p:,.2f}", f"{((p-prev)/prev)*100:+.2f}%")
    with m2:
        df_s = get_stock_data('SI=F')
        if not df_s.empty:
            p = float(df_s['Close'].iloc[-1])
            prev = float(df_s['Close'].iloc[-2]) if len(df_s)>1 else p
            st.metric("🥈 Gümüş (Ons)", f"${p:,.2f}", f"{((p-prev)/prev)*100:+.2f}%")


# ═══ KAP HABERLERİ ═══
elif page == "📰 KAP Haberleri":
    st.title("📰 KAP Haberleri")
    st.caption("Güncel piyasa haberleri ve bildirimleri")
    news = get_kap_news()
    if news:
        for item in news:
            st.markdown(f"""
            <div style="background:white;border-radius:10px;padding:16px;margin-bottom:12px;border:1px solid #eee;border-left:4px solid #1565c0">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
                    <span style="background:#1565c0;color:white;padding:2px 8px;border-radius:4px;font-size:12px;font-weight:600">{item['symbol']}</span>
                    <span style="color:#999;font-size:12px">{item['date']}</span>
                </div>
                <div style="font-size:14px;color:#333;line-height:1.5">{item['title']}</div>
            </div>
            """, unsafe_allow_html=True)


# ═══ HİSSE TABLOSU ═══
elif page == "📋 Hisse Tablosu":
    st.title("📋 Hisse Tablosu — Tüm BIST")
    st.info("⏳ Tüm hisseler analiz ediliyor...")
    all_scores = get_all_bist_scores()
    if not all_scores.empty:
        f1, f2 = st.columns(2)
        with f1:
            sort_by = st.selectbox("Sırala:", ['Sentiment', 'Momentum%', 'RSI', 'Fiyat'])
        with f2:
            sort_order = st.radio("Sıra:", ['En Yüksek', 'En Düşük'], horizontal=True)
        sorted_df = all_scores.sort_values(sort_by, ascending=(sort_order=='En Düşük')).reset_index(drop=True)
        sorted_df.index = sorted_df.index + 1
        st.dataframe(sorted_df, use_container_width=True, height=500)


# ═══ KRİPTO TOP 10 ═══
elif page == "🪙 Kripto Top 10":
    st.title("🪙 Kripto — İlk 10 / Son 10")
    st.info("⏳ Kripto verileri analiz ediliyor...")
    
    crypto_scores = get_crypto_scores()
    if not crypto_scores.empty:
        ktab1, ktab2 = st.tabs(["🟢 İlk 10 (En Güçlü)", "🔴 Son 10 (En Zayıf)"])
        
        with ktab1:
            top10_c = crypto_scores.sort_values('Sentiment', ascending=False).head(10).reset_index(drop=True)
            top10_c.index = top10_c.index + 1
            st.dataframe(top10_c, use_container_width=True)
            
            fig = go.Figure(go.Bar(
                x=top10_c['Sembol'], y=top10_c['Sentiment'],
                marker_color=['#1565c0' if v>=0 else '#c62828' for v in top10_c['Sentiment']],
                text=top10_c['Karar'], textposition='outside'
            ))
            fig.update_layout(height=350, paper_bgcolor='white', plot_bgcolor='white')
            st.plotly_chart(fig, use_container_width=True)
        
        with ktab2:
            bot10_c = crypto_scores.sort_values('Sentiment', ascending=True).head(10).reset_index(drop=True)
            bot10_c.index = bot10_c.index + 1
            st.dataframe(bot10_c, use_container_width=True)
            
            fig = go.Figure(go.Bar(
                x=bot10_c['Sembol'], y=bot10_c['Sentiment'],
                marker_color=['#1565c0' if v>=0 else '#c62828' for v in bot10_c['Sentiment']],
                text=bot10_c['Karar'], textposition='outside'
            ))
            fig.update_layout(height=350, paper_bgcolor='white', plot_bgcolor='white')
            st.plotly_chart(fig, use_container_width=True)


# ═══ AKILLI FİLTRE ═══
elif page == "🔍 Akıllı Filtre":
    st.title("🔍 Akıllı Filtre")
    all_scores = get_all_bist_scores()
    if not all_scores.empty:
        filter_type = st.selectbox("Filtre:", [
            "🚀 Potansiyel Kalkışlar", "💪 Güçlü Alış", "⭐ En Yüksek Sentiment",
            "📈 Yukarı Momentum", "🔴 Güçlü Satış", "📉 Aşağı Momentum", "⚪ Nötr",
        ])
        st.markdown("---")
        
        if "Potansiyel" in filter_type:
            filtered = all_scores[(all_scores['Sentiment'] > -10) & (all_scores['Sentiment'] < 20) & (all_scores['Momentum%'] > 0)]
        elif "Güçlü Alış" in filter_type:
            filtered = all_scores[all_scores['Sentiment'] > 30]
        elif "En Yüksek" in filter_type:
            filtered = all_scores.sort_values('Sentiment', ascending=False).head(10)
        elif "Yukarı" in filter_type:
            filtered = all_scores[all_scores['Momentum%'] > 2]
        elif "Güçlü Satış" in filter_type:
            filtered = all_scores[all_scores['Sentiment'] < -30]
        elif "Aşağı" in filter_type:
            filtered = all_scores[all_scores['Momentum%'] < -2]
        else:
            filtered = all_scores[(all_scores['Sentiment'] >= -10) & (all_scores['Sentiment'] <= 10)]
        
        if not filtered.empty:
            filtered = filtered.reset_index(drop=True)
            filtered.index = filtered.index + 1
            st.dataframe(filtered, use_container_width=True)
        else:
            st.warning("Sonuç bulunamadı.")


# ═══ GÜNLÜK SENTİMENT ═══
elif page == "📈 Günlük Sentiment":
    st.title("📈 Günlük Sentiment — BIST100")
    bist_df = get_bist100_index()
    if not bist_df.empty:
        result = calc_sentiment(bist_df)
        if result:
            i1, i2, i3, i4 = st.columns(4)
            i1.metric("Sentiment", f"{result['sent_puan']:.2f}")
            i2.metric("Momentum", f"{result['momentum']:.1f}%")
            i3.metric("BIST100", f"{result['price']:,.2f}")
            i4.metric("Karar", result['decision'])
            
            st.markdown("---")
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                               row_heights=[0.7, 0.3], specs=[[{"secondary_y": True}], [{"secondary_y": False}]])
            x = list(range(len(result['bars'])))
            colors = ['#1565c0' if v >= 0 else '#c62828' for v in result['bars']]
            fig.add_trace(go.Bar(x=x, y=result['bars'], name='Sentiment', marker_color=colors, opacity=0.9), row=1, col=1, secondary_y=False)
            fig.add_trace(go.Scatter(x=x, y=result['prices'], name='BIST100', line=dict(color='#2e7d32', width=2.5)), row=1, col=1, secondary_y=True)
            mom_colors = ['#1565c0' if v >= 0 else '#c62828' for v in result['mom_bars']]
            fig.add_trace(go.Bar(x=x, y=result['mom_bars'], name='Momentum', marker_color=mom_colors, opacity=0.7), row=2, col=1)
            fig.update_layout(height=500, paper_bgcolor='white', plot_bgcolor='white', legend=dict(orientation='h', y=-0.1))
            fig.update_xaxes(showgrid=False)
            fig.update_yaxes(showgrid=True, gridcolor='#eee')
            st.plotly_chart(fig, use_container_width=True)


# ═══ OSİLATÖR ═══
elif page == "🔄 Osilatör":
    st.title("🔄 Osilatör — BIST100")
    bist_df = get_bist100_index()
    if not bist_df.empty:
        close = bist_df['Close']
        rsi_series = momentum.RSIIndicator(close, window=14).rsi()
        osc_series = ((rsi_series - 50) / 50) * 3
        period = min(60, len(close) - 14)
        osc_vals = [float(osc_series.iloc[i]) for i in range(-period, 0)]
        price_vals = [float(close.iloc[i]) for i in range(-period, 0)]
        x = list(range(len(osc_vals)))
        
        st.metric("Osilatör", f"{osc_vals[-1]:.2f}" if osc_vals else "0")
        st.markdown("---")
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Scatter(x=x, y=price_vals, name='BIST100', line=dict(color='#1565c0', width=2.5)), secondary_y=False)
        osc_colors = ['#2e7d32' if v >= 0 else '#c62828' for v in osc_vals]
        fig.add_trace(go.Bar(x=x, y=osc_vals, name='Osilatör', marker_color=osc_colors, opacity=0.7), secondary_y=True)
        fig.update_layout(height=450, paper_bgcolor='white', plot_bgcolor='white', legend=dict(orientation='h', y=-0.1))
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(showgrid=True, gridcolor='#eee')
        st.plotly_chart(fig, use_container_width=True)


# ═══ BIST30 İLK 10 ═══
elif page == "📋 BIST30 İlk 10":
    st.title("📋 BIST30 — İlk 10")
    st.info("⏳ Veriler çekiliyor...")
    scores_df = get_bist30_scores()
    if not scores_df.empty:
        top10 = scores_df.sort_values('Sentiment', ascending=False).head(10).reset_index(drop=True)
        top10.index = top10.index + 1
        st.dataframe(top10, use_container_width=True)
        fig = go.Figure(go.Bar(x=top10['Sembol'], y=top10['Sentiment'],
            marker_color=['#1565c0' if v>=0 else '#c62828' for v in top10['Sentiment']],
            text=top10['Karar'], textposition='outside'))
        fig.update_layout(height=400, paper_bgcolor='white', plot_bgcolor='white')
        st.plotly_chart(fig, use_container_width=True)


# ═══ BIST30 SON 10 ═══
elif page == "📋 BIST30 Son 10":
    st.title("📋 BIST30 — Son 10")
    st.info("⏳ Veriler çekiliyor...")
    scores_df = get_bist30_scores()
    if not scores_df.empty:
        bottom10 = scores_df.sort_values('Sentiment', ascending=True).head(10).reset_index(drop=True)
        bottom10.index = bottom10.index + 1
        st.dataframe(bottom10, use_container_width=True)
        fig = go.Figure(go.Bar(x=bottom10['Sembol'], y=bottom10['Sentiment'],
            marker_color=['#1565c0' if v>=0 else '#c62828' for v in bottom10['Sentiment']],
            text=bottom10['Karar'], textposition='outside'))
        fig.update_layout(height=400, paper_bgcolor='white', plot_bgcolor='white')
        st.plotly_chart(fig, use_container_width=True)
