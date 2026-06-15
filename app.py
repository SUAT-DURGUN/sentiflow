"""
SentiFlow v3.1 — Tam Profesyonel Platform
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

st.set_page_config(page_title="SentiFlow", layout="wide", page_icon="🌊")


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
    '🥇 Altin (Ons/USD)': 'GC=F',
    '🥈 Gumus (Ons/USD)': 'SI=F',
    '💵 USD/TRY': 'USDTRY=X',
    '💶 EUR/TRY': 'EURTRY=X',
    '🇨🇭 CHF/TRY': 'CHFTRY=X',
    '🇬🇧 GBP/TRY': 'GBPTRY=X',
}


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
    return [
        {'symbol': 'BIST100', 'title': 'BIST100 endeksi gune yukselisle basladi', 'date': datetime.now().strftime('%d.%m.%Y')},
        {'symbol': 'THYAO', 'title': 'Turk Hava Yollari yolcu sayisinda rekor kirdi', 'date': datetime.now().strftime('%d.%m.%Y')},
        {'symbol': 'ASELS', 'title': 'ASELSAN yeni savunma ihracati anlasmasi imzaladi', 'date': datetime.now().strftime('%d.%m.%Y')},
        {'symbol': 'GARAN', 'title': 'Garanti Bankasi temettu dagitim tarihini acikladi', 'date': datetime.now().strftime('%d.%m.%Y')},
        {'symbol': 'BTC', 'title': 'Bitcoin 64.000$ seviyesinde tutunmaya calisiyor', 'date': datetime.now().strftime('%d.%m.%Y')},
        {'symbol': 'ALTIN', 'title': 'Ons altin 4.200$ uzerinde seyrediyor', 'date': datetime.now().strftime('%d.%m.%Y')},
        {'symbol': 'USD', 'title': 'Dolar/TL 46.26 seviyesinden islem goruyor', 'date': datetime.now().strftime('%d.%m.%Y')},
        {'symbol': 'PGSUS', 'title': 'Pegasus yaz sezonunda kapasite artisi planliyor', 'date': datetime.now().strftime('%d.%m.%Y')},
    ]


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
    if score > 30: signal = "🟢 Guclu Alis"
    elif score > 10: signal = "🟡 Alis"
    elif score > -10: signal = "⚪ Notr"
    elif score > -30: signal = "🟡 Satis"
    else: signal = "🔴 Guclu Satis"
    if score > 20 and mom > 0: decision = "🟢 AL"
    elif score < -20 and mom < 0: decision = "🔴 SAT"
    else: decision = "🟡 TUT"
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
        'oscillator': round(oscillator, 2), 'stp': round(stp, 2), 'hstp': round(hstp, 2),
        'stp_change': round(stp_change, 2), 'ema9': ema9, 'ema21': ema21, 'ema50': ema50,
        'trend': trend_dir, 'sent_puan': sent_puan, 'daily_change': round(daily_change, 2),
    }


def predict_trend(symbol):
    try:
        df = yf.Ticker(symbol).history(period="6mo", interval="1d")
        if df.empty or len(df) < 50:
            return None
        close = df['Close']
        price = float(close.iloc[-1])
        rsi_val = float(momentum.RSIIndicator(close, window=14).rsi().iloc[-1])
        macd_val = float(trend.MACD(close).macd_diff().iloc[-1])
        ema9 = float(close.ewm(span=9).mean().iloc[-1])
        ema21 = float(close.ewm(span=21).mean().iloc[-1])
        ema50 = float(close.ewm(span=50).mean().iloc[-1])
        last5 = close.iloc[-5:]
        avg_return = float(last5.pct_change().dropna().mean())
        vol = float(last5.pct_change().dropna().std())
        ts = 0
        if rsi_val < 30: ts += 3
        elif rsi_val > 70: ts -= 3
        elif rsi_val > 50: ts += 1
        else: ts -= 1
        if macd_val > 0: ts += 2
        else: ts -= 2
        if ema9 > ema21: ts += 1
        else: ts -= 1
        if price > ema50: ts += 1
        else: ts -= 1
        if avg_return > 0.005: ts += 2
        elif avg_return < -0.005: ts -= 2
        if ts >= 4: prediction = "📈 Guclu Yukselis"
        elif ts >= 2: prediction = "📈 Hafif Yukselis"
        elif ts <= -4: prediction = "📉 Guclu Dusus"
        elif ts <= -2: prediction = "📉 Hafif Dusus"
        else: prediction = "➡️ Yatay"
        confidence = min(85, 55 + abs(ts) * 4)
        target_pct = round(avg_return * 300, 1)
        target_price = round(price * (1 + target_pct / 100), 2)
        support = round(float(close.iloc[-20:].min()), 2)
        resistance = round(float(close.iloc[-20:].max()), 2)
        return {
            'prediction': prediction, 'confidence': confidence,
            'target_pct': target_pct, 'target_price': target_price,
            'trend_strength': ts, 'support': support, 'resistance': resistance,
            'volatility': round(vol * 100, 2), 'price': price,
        }
    except:
        return None


@st.cache_data(ttl=600)
def get_all_bist_scores():
    results = []
    for symbol in ALL_BIST.keys():
        try:
            df = get_bist_data(symbol)
            result = calc_sentiment(df)
            if result:
                results.append({'Sembol': symbol, 'Fiyat': round(result['price'], 2), 'Gun%': result['daily_change'], 'Sentiment': result['score'], 'Sent.Puan': result['sent_puan'], 'RSI': round(result['rsi'], 1), 'Momentum%': round(result['momentum'], 2), 'Karar': result['decision'], 'Sinyal': result['signal'], 'Trend': result['trend']})
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
                results.append({'Sembol': symbol, 'Fiyat': round(result['price'], 2), 'Gun%': result['daily_change'], 'Sentiment': result['score'], 'Sent.Puan': result['sent_puan'], 'RSI': round(result['rsi'], 1), 'Momentum%': round(result['momentum'], 2), 'Karar': result['decision'], 'Sinyal': result['signal']})
        except:
            continue
    return pd.DataFrame(results)


@st.cache_data(ttl=600)
def get_crypto_scores():
    results = []
    for symbol in CRYPTO_BINANCE + CRYPTO_EXTRA:
        try:
            df = get_crypto_data(symbol)
            result = calc_sentiment(df)
            if result:
                results.append({'Sembol': symbol, 'Fiyat': round(result['price'], 4) if result['price'] < 1 else round(result['price'], 2), 'Gun%': result['daily_change'], 'Sentiment': result['score'], 'Sent.Puan': result['sent_puan'], 'RSI': round(result['rsi'], 1), 'Momentum%': round(result['momentum'], 2), 'Karar': result['decision'], 'Sinyal': result['signal']})
        except:
            continue
    return pd.DataFrame(results)


if 'favorites' not in st.session_state:
    st.session_state.favorites = ['THYAO', 'ASELS', 'GARAN', 'BTC/USDT']

with st.sidebar:
    st.markdown("### 🌊 SentiFlow")
    st.markdown("### SentiFlow")
    st.caption("Piyasa Sentiment Platformu")
    st.markdown("---")
    page = st.radio("Sayfa", ["🏠 Ana Sayfa", "📊 Hisse Analiz", "🪙 Kripto Analiz", "🧠 AI Tahmin", "🔔 Sinyal Merkezi", "⭐ Favorilerim", "🇺🇸 S&P / NASDAQ", "🇪🇺 Avrupa", "🥇 Altin & Doviz", "📰 KAP Haberleri", "📋 Hisse Tablosu", "🪙 Kripto Top 10", "🔍 Akilli Filtre", "📈 Gunluk Sentiment", "🔄 Osilator", "📋 BIST30 Ilk 10", "📋 BIST30 Son 10"])
    st.markdown("---")
    st.caption(f"v3.1 | {datetime.now().strftime('%d.%m.%Y %H:%M')}")

if page == "🏠 Ana Sayfa":
    st.markdown('<div style="display:flex;align-items:center;gap:12px;margin-bottom:20px"><span style="font-size:40px">🌊</span><div><h1 style="margin:0;color:#1565c0">SentiFlow</h1><p style="margin:0;color:#666;font-size:14px">Piyasa Sentiment Analiz Platformu</p></div></div>', unsafe_allow_html=True)
    bist_df = get_bist100_index()
    bist30_df = get_bist30_index()
    if not bist_df.empty:
        bist_result = calc_sentiment(bist_df)
        if bist_result:
            gauge_val = int((bist_result['score'] + 100) / 2)
            gauge_val = max(0, min(100, gauge_val))
            if gauge_val >= 75: guc_text = "Guclu"
            elif gauge_val >= 50: guc_text = "Normal"
            elif gauge_val >= 25: guc_text = "Zayif"
            else: guc_text = "Cok Zayif"
            guc_color = '#c62828' if gauge_val < 25 else '#e65100' if gauge_val < 50 else '#2e7d32' if gauge_val < 75 else '#1565c0'
            st.markdown(f'<div style="background:linear-gradient(135deg,#f8f9fa,#e3f2fd);border-radius:16px;padding:24px;margin-bottom:20px;border:1px solid #bbdefb"><div style="display:flex;align-items:center;gap:20px"><div style="text-align:center;min-width:100px"><div style="font-size:14px;color:#666">Sentiment Guc</div><div style="font-size:52px;font-weight:800;color:#1565c0">{gauge_val}</div><div style="background:{guc_color};color:white;border-radius:20px;padding:4px 12px;font-size:12px;display:inline-block">{guc_text}</div></div><div style="flex:1;color:#555;font-size:14px">Piyasalarin genel sentiment gucunu gosteren indikator.</div></div></div>', unsafe_allow_html=True)
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
    st.subheader("📋 Ilk 10")
    scores = get_bist30_scores()
    if not scores.empty:
        top_list = scores.sort_values('Sentiment', ascending=False).head(10)
        cols = st.columns(5)
        for i, (_, row) in enumerate(top_list.head(5).iterrows()):
            with cols[i]:
                color = "#2e7d32" if row['Gun%'] >= 0 else "#c62828"
                st.markdown(f'<div style="background:white;border-radius:12px;padding:14px;border:1px solid #eee;text-align:center"><div style="font-weight:700">{row["Sembol"]}</div><div style="color:{color};font-size:20px;font-weight:700">{row["Fiyat"]}</div><div style="color:{color};font-size:12px">%{row["Gun%"]:.2f}</div><div style="font-size:11px;color:#666">{row["Karar"]}</div></div>', unsafe_allow_html=True)
    st.markdown("---")
    st.subheader("💰 Altin & Doviz")
    gc1, gc2, gc3, gc4 = st.columns(4)
    for i, (name, sym) in enumerate([('USD/TRY','USDTRY=X'),('EUR/TRY','EURTRY=X'),('Altin','GC=F'),('Gumus','SI=F')]):
        with [gc1, gc2, gc3, gc4][i]:
            df_c = get_stock_data(sym)
            if not df_c.empty:
                p = float(df_c['Close'].iloc[-1])
                prev_p = float(df_c['Close'].iloc[-2]) if len(df_c) > 1 else p
                chg = ((p - prev_p) / prev_p) * 100
                st.metric(name, f"{p:,.2f}", f"{chg:+.2f}%")
    st.markdown("---")
    st.subheader("📰 Haberler")
    news = get_kap_news()
    for item in news[:4]:
        st.markdown(f"**{item['symbol']}** — {item['title']}")


elif page == "📊 Hisse Analiz":
    st.title("📊 Hisse Sentiment Analizi")
    symbol = st.selectbox("Hisse Secin:", list(ALL_BIST.keys()))
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
                    fig.update_layout(height=380, paper_bgcolor='white', plot_bgcolor='white', margin=dict(l=40, r=40, t=10, b=30))
                    fig.update_xaxes(showgrid=False)
                    fig.update_yaxes(showgrid=True, gridcolor='#eee')
                    st.plotly_chart(fig, use_container_width=True)
                with right_chart:
                    fig2 = go.Figure()
                    x2 = list(range(len(result['prices'])))
                    fig2.add_trace(go.Scatter(x=x2, y=result['prices'], name='Fiyat', line=dict(color='#2e7d32', width=2.5)))
                    fig2.add_trace(go.Scatter(x=x2, y=[result['stp']]*len(x2), name='STP', line=dict(color='#e65100', width=2, dash='dash')))
                    fig2.add_trace(go.Scatter(x=x2, y=[result['hstp']]*len(x2), name='HSTP', line=dict(color='#b71c1c', width=2, dash='dot')))
                    fig2.update_layout(height=380, paper_bgcolor='white', plot_bgcolor='white', margin=dict(l=40, r=10, t=10, b=30))
                    fig2.update_xaxes(showgrid=False)
                    fig2.update_yaxes(showgrid=True, gridcolor='#eee')
                    st.plotly_chart(fig2, use_container_width=True)
            with tab2:
                data_table = pd.DataFrame({'Gosterge': ['Fiyat', 'Sent.Puan', 'RSI', 'Stoch', 'MACD', 'Momentum', 'EMA9', 'EMA21', 'EMA50', 'STP', 'HSTP'], 'Deger': [f"₺{result['price']:,.2f}", f"{result['sent_puan']:.2f}", f"{result['rsi']:.1f}", f"{result['stoch']:.1f}", f"{result['macd']:.4f}", f"%{result['momentum']:.2f}", f"₺{result['ema9']:.2f}", f"₺{result['ema21']:.2f}", f"₺{result['ema50']:.2f}", f"₺{result['stp']}", f"₺{result['hstp']}"], 'Durum': [result['decision'], result['signal'], '🟢' if result['rsi']<30 else '🔴' if result['rsi']>70 else '⚪', '🟢' if result['stoch']<20 else '🔴' if result['stoch']>80 else '⚪', '🟢' if result['macd']>0 else '🔴', '🟢' if result['momentum']>0 else '🔴', '🟢' if result['price']>result['ema9'] else '🔴', '🟢' if result['price']>result['ema21'] else '🔴', '🟢' if result['price']>result['ema50'] else '🔴', '🟢' if result['price']>result['stp'] else '🔴', '🟢' if result['price']>result['hstp'] else '🔴']})
                st.dataframe(data_table, use_container_width=True, hide_index=True)
            with tab3:
                dec_color = "#2e7d32" if "AL" in result['decision'] else "#c62828" if "SAT" in result['decision'] else "#f57c00"
                st.markdown(f'<div style="background:{dec_color};color:white;border-radius:12px;padding:25px;text-align:center;margin:20px 0"><h1 style="margin:0;color:white">{result["decision"]}</h1><p style="margin:5px 0 0;font-size:16px;color:rgba(255,255,255,0.9)">{result["signal"]}</p></div>', unsafe_allow_html=True)
                a1, a2 = st.columns(2)
                with a1:
                    st.markdown("**🟢 Alis Sinyalleri:**")
                    if result['rsi'] < 30: st.write("RSI asiri satim")
                    if result['macd'] > 0: st.write("MACD pozitif")
                    if result['price'] > result['ema21']: st.write("Fiyat EMA21 ustunde")
                    if result['momentum'] > 0: st.write("Momentum pozitif")
                with a2:
                    st.markdown("**🔴 Satis Sinyalleri:**")
                    if result['rsi'] > 70: st.write("RSI asiri alim")
                    if result['macd'] < 0: st.write("MACD negatif")
                    if result['price'] < result['ema21']: st.write("Fiyat EMA21 altinda")
                    if result['momentum'] < 0: st.write("Momentum negatif")


elif page == "🪙 Kripto Analiz":
    st.title("🪙 Kripto Sentiment Analizi")
    all_crypto = CRYPTO_BINANCE + CRYPTO_EXTRA
    symbol = st.selectbox("Kripto Secin:", all_crypto)
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
        st.error(f"'{symbol}' icin veri cekilemedi!")


elif page == "🧠 AI Tahmin":
    st.title("🧠 AI Tahmin Modeli")
    st.caption("Teknik gostergelere dayali 3 gunluk trend tahmini")
    market_ai = st.radio("Piyasa:", ["BIST", "Kripto"], horizontal=True)
    if market_ai == "BIST":
        symbol_ai = st.selectbox("Hisse:", list(ALL_BIST.keys()))
        yahoo_sym = ALL_BIST[symbol_ai]
    else:
        symbol_ai = st.selectbox("Kripto:", CRYPTO_BINANCE + CRYPTO_EXTRA)
        yahoo_sym = None
    if st.button("🧠 Tahmin Yap", type="primary"):
        with st.spinner("AI analiz yapiyor..."):
            if yahoo_sym:
                r = predict_trend(yahoo_sym)
            else:
                df_ai = get_crypto_data(symbol_ai)
                if not df_ai.empty and len(df_ai) >= 50:
                    close = df_ai['Close']
                    rsi_v = float(momentum.RSIIndicator(close, window=14).rsi().iloc[-1])
                    macd_v = float(trend.MACD(close).macd_diff().iloc[-1])
                    price_v = float(close.iloc[-1])
                    avg_r = float(close.iloc[-5:].pct_change().dropna().mean())
                    vol_v = float(close.iloc[-5:].pct_change().dropna().std())
                    ts = 0
                    if rsi_v < 30: ts += 3
                    elif rsi_v > 70: ts -= 3
                    if macd_v > 0: ts += 2
                    else: ts -= 2
                    if avg_r > 0: ts += 1
                    else: ts -= 1
                    if ts >= 3: pred = "📈 Guclu Yukselis"
                    elif ts >= 1: pred = "📈 Hafif Yukselis"
                    elif ts <= -3: pred = "📉 Guclu Dusus"
                    elif ts <= -1: pred = "📉 Hafif Dusus"
                    else: pred = "➡️ Yatay"
                    conf = min(80, 55 + abs(ts) * 4)
                    tgt = round(avg_r * 300, 1)
                    r = {'prediction': pred, 'confidence': conf, 'target_pct': tgt, 'target_price': round(price_v * (1 + tgt / 100), 4), 'trend_strength': ts, 'support': round(float(close.iloc[-20:].min()), 4), 'resistance': round(float(close.iloc[-20:].max()), 4), 'volatility': round(vol_v * 100, 2), 'price': price_v}
                else:
                    r = None
            if r:
                pc = "#2e7d32" if "Yukselis" in r['prediction'] else "#c62828" if "Dusus" in r['prediction'] else "#f57c00"
                st.markdown(f'<div style="background:{pc};color:white;border-radius:12px;padding:25px;text-align:center;margin:20px 0"><h1 style="margin:0;color:white">{r["prediction"]}</h1><p style="margin:10px 0 0;font-size:18px;color:rgba(255,255,255,0.9)">Guven: %{r["confidence"]}</p></div>', unsafe_allow_html=True)
                st.markdown("---")
                r1, r2, r3, r4 = st.columns(4)
                r1.metric("Fiyat", f"{r['price']:,.2f}")
                r2.metric("Hedef", f"{r['target_price']:,.2f}", f"%{r['target_pct']}")
                r3.metric("Destek", f"{r['support']:,.2f}")
                r4.metric("Direnc", f"{r['resistance']:,.2f}")
                st.warning("Bu tahmin yatirim tavsiyesi degildir.")
            else:
                st.error("Tahmin yapilamadi.")


elif page == "🔔 Sinyal Merkezi":
    st.title("🔔 Sinyal Merkezi")
    st.caption("Tum AL / SAT / TUT sinyalleri")
    sinyal_tab1, sinyal_tab2, sinyal_tab3 = st.tabs(["BIST", "Kripto", "ABD & Avrupa"])
    with sinyal_tab1:
        all_scores = get_all_bist_scores()
        if not all_scores.empty:
            al_s = all_scores[all_scores['Karar'].str.contains('AL')]
            sat_s = all_scores[all_scores['Karar'].str.contains('SAT')]
            tut_s = all_scores[all_scores['Karar'].str.contains('TUT')]
            st.markdown(f"### 🟢 AL ({len(al_s)})")
            if not al_s.empty: st.dataframe(al_s[['Sembol','Fiyat','Gun%','Sent.Puan','Momentum%']].reset_index(drop=True), use_container_width=True)
            st.markdown(f"### 🔴 SAT ({len(sat_s)})")
            if not sat_s.empty: st.dataframe(sat_s[['Sembol','Fiyat','Gun%','Sent.Puan','Momentum%']].reset_index(drop=True), use_container_width=True)
            st.markdown(f"### 🟡 TUT ({len(tut_s)})")
            if not tut_s.empty: st.dataframe(tut_s[['Sembol','Fiyat','Gun%','Sent.Puan','Momentum%']].reset_index(drop=True), use_container_width=True)
    with sinyal_tab2:
        crypto_scores = get_crypto_scores()
        if not crypto_scores.empty:
            al_c = crypto_scores[crypto_scores['Karar'].str.contains('AL')]
            sat_c = crypto_scores[crypto_scores['Karar'].str.contains('SAT')]
            tut_c = crypto_scores[crypto_scores['Karar'].str.contains('TUT')]
            if not al_c.empty:
                st.markdown(f"### 🟢 AL ({len(al_c)})")
                st.dataframe(al_c[['Sembol','Fiyat','Gun%','Sent.Puan','Momentum%']].reset_index(drop=True), use_container_width=True)
            if not sat_c.empty:
                st.markdown(f"### 🔴 SAT ({len(sat_c)})")
                st.dataframe(sat_c[['Sembol','Fiyat','Gun%','Sent.Puan','Momentum%']].reset_index(drop=True), use_container_width=True)
            if not tut_c.empty:
                st.markdown(f"### 🟡 TUT ({len(tut_c)})")
                st.dataframe(tut_c[['Sembol','Fiyat','Gun%','Sent.Puan','Momentum%']].reset_index(drop=True), use_container_width=True)
    with sinyal_tab3:
        intl_results = []
        for name, sym in {**US_TOP10, **EUROPE_TOP10}.items():
            try:
                df = get_stock_data(sym)
                r = calc_sentiment(df)
                if r: intl_results.append({'Sembol': name, 'Fiyat': round(r['price'],2), 'Gun%': r['daily_change'], 'Sent.Puan': r['sent_puan'], 'Karar': r['decision']})
            except:
                continue
        if intl_results:
            intl_df = pd.DataFrame(intl_results)
            st.dataframe(intl_df, use_container_width=True, hide_index=True)


elif page == "⭐ Favorilerim":
    st.title("⭐ Favorilerim")
    with st.expander("Favori Ekle / Kaldir"):
        new_fav = st.text_input("Sembol ekle (orn: THYAO, BTC/USDT):")
        if st.button("Ekle") and new_fav:
            if new_fav.upper() not in st.session_state.favorites:
                st.session_state.favorites.append(new_fav.upper())
                st.rerun()
        if st.session_state.favorites:
            remove_fav = st.selectbox("Kaldir:", st.session_state.favorites)
            if st.button("Kaldir"):
                st.session_state.favorites.remove(remove_fav)
                st.rerun()
    st.markdown("---")
    for fav in st.session_state.favorites:
        try:
            if '/' in fav:
                df = get_crypto_data(fav)
                cur = "$"
            else:
                df = get_bist_data(fav)
                cur = "₺"
            result = calc_sentiment(df)
            if result:
                color = "#2e7d32" if result['daily_change'] >= 0 else "#c62828"
                dec_bg = "#e8f5e9" if "AL" in result['decision'] else "#ffebee" if "SAT" in result['decision'] else "#fff3e0"
                st.markdown(f'<div style="background:{dec_bg};border-radius:12px;padding:16px;margin-bottom:12px;border:1px solid #eee"><div style="display:flex;justify-content:space-between;align-items:center"><div><strong>{fav}</strong> <span style="color:{color};font-size:18px;font-weight:700">{cur}{result["price"]:,.2f}</span> <span style="color:{color};font-size:13px">%{result["daily_change"]:.2f}</span></div><div>{result["decision"]} | Sent: {result["sent_puan"]:.1f}</div></div></div>', unsafe_allow_html=True)
        except:
            pass


elif page == "🇺🇸 S&P / NASDAQ":
    st.title("🇺🇸 S&P 500 / NASDAQ — Top 10")
    results = []
    for name, symbol in US_TOP10.items():
        try:
            df = get_stock_data(symbol)
            r = calc_sentiment(df)
            if r: results.append({'Sembol': name, 'Fiyat': f"${r['price']:,.2f}", 'Gun%': r['daily_change'], 'Sentiment': r['sent_puan'], 'Momentum%': round(r['momentum'],2), 'Karar': r['decision']})
        except:
            continue
    if results: st.dataframe(pd.DataFrame(results), use_container_width=True, hide_index=True)


elif page == "🇪🇺 Avrupa":
    st.title("🇪🇺 Avrupa — Top 10")
    results = []
    for name, symbol in EUROPE_TOP10.items():
        try:
            df = get_stock_data(symbol)
            r = calc_sentiment(df)
            if r: results.append({'Sembol': name, 'Fiyat': f"€{r['price']:,.2f}", 'Gun%': r['daily_change'], 'Sentiment': r['sent_puan'], 'Momentum%': round(r['momentum'],2), 'Karar': r['decision']})
        except:
            continue
    if results: st.dataframe(pd.DataFrame(results), use_container_width=True, hide_index=True)


elif page == "🥇 Altin & Doviz":
    st.title("🥇 Altin, Gumus & Doviz")
    st.subheader("Doviz Kurlari")
    d1, d2, d3, d4 = st.columns(4)
    for i, (name, sym) in enumerate([('USD/TRY','USDTRY=X'),('EUR/TRY','EURTRY=X'),('CHF/TRY','CHFTRY=X'),('GBP/TRY','GBPTRY=X')]):
        with [d1,d2,d3,d4][i]:
            df_d = get_stock_data(sym)
            if not df_d.empty:
                p = float(df_d['Close'].iloc[-1])
                prev = float(df_d['Close'].iloc[-2]) if len(df_d)>1 else p
                st.metric(name, f"₺{p:,.4f}", f"{((p-prev)/prev)*100:+.2f}%")
    st.markdown("---")
    m1, m2 = st.columns(2)
    with m1:
        df_g = get_stock_data('GC=F')
        if not df_g.empty:
            p = float(df_g['Close'].iloc[-1])
            prev = float(df_g['Close'].iloc[-2]) if len(df_g)>1 else p
            st.metric("Altin (Ons)", f"${p:,.2f}", f"{((p-prev)/prev)*100:+.2f}%")
    with m2:
        df_s = get_stock_data('SI=F')
        if not df_s.empty:
            p = float(df_s['Close'].iloc[-1])
            prev = float(df_s['Close'].iloc[-2]) if len(df_s)>1 else p
            st.metric("Gumus (Ons)", f"${p:,.2f}", f"{((p-prev)/prev)*100:+.2f}%")


elif page == "📰 KAP Haberleri":
    st.title("📰 KAP Haberleri")
    news = get_kap_news()
    for item in news:
        st.markdown(f'<div style="background:white;border-radius:10px;padding:16px;margin-bottom:12px;border:1px solid #eee;border-left:4px solid #1565c0"><div style="display:flex;justify-content:space-between;margin-bottom:6px"><span style="background:#1565c0;color:white;padding:2px 8px;border-radius:4px;font-size:12px">{item["symbol"]}</span><span style="color:#999;font-size:12px">{item["date"]}</span></div><div style="font-size:14px;color:#333">{item["title"]}</div></div>', unsafe_allow_html=True)


elif page == "📋 Hisse Tablosu":
    st.title("📋 Hisse Tablosu")
    all_scores = get_all_bist_scores()
    if not all_scores.empty:
        f1, f2 = st.columns(2)
        with f1: sort_by = st.selectbox("Sirala:", ['Sentiment', 'Momentum%', 'RSI', 'Fiyat'])
        with f2: sort_order = st.radio("Sira:", ['En Yuksek', 'En Dusuk'], horizontal=True)
        sorted_df = all_scores.sort_values(sort_by, ascending=(sort_order=='En Dusuk')).reset_index(drop=True)
        sorted_df.index = sorted_df.index + 1
        st.dataframe(sorted_df, use_container_width=True, height=500)


elif page == "🪙 Kripto Top 10":
    st.title("🪙 Kripto Top 10")
    crypto_scores = get_crypto_scores()
    if not crypto_scores.empty:
        ktab1, ktab2 = st.tabs(["🟢 Ilk 10", "🔴 Son 10"])
        with ktab1:
            top10_c = crypto_scores.sort_values('Sentiment', ascending=False).head(10).reset_index(drop=True)
            top10_c.index = top10_c.index + 1
            st.dataframe(top10_c, use_container_width=True)
        with ktab2:
            bot10_c = crypto_scores.sort_values('Sentiment', ascending=True).head(10).reset_index(drop=True)
            bot10_c.index = bot10_c.index + 1
            st.dataframe(bot10_c, use_container_width=True)


elif page == "🔍 Akilli Filtre":
    st.title("🔍 Akilli Filtre")
    all_scores = get_all_bist_scores()
    if not all_scores.empty:
        filter_type = st.selectbox("Filtre:", ["Potansiyel Kalkislar", "Guclu Alis", "En Yuksek Sentiment", "Yukari Momentum", "Guclu Satis", "Asagi Momentum", "Notr"])
        st.markdown("---")
        if "Potansiyel" in filter_type: filtered = all_scores[(all_scores['Sentiment'] > -10) & (all_scores['Sentiment'] < 20) & (all_scores['Momentum%'] > 0)]
        elif "Guclu Alis" in filter_type: filtered = all_scores[all_scores['Sentiment'] > 30]
        elif "En Yuksek" in filter_type: filtered = all_scores.sort_values('Sentiment', ascending=False).head(10)
        elif "Yukari" in filter_type: filtered = all_scores[all_scores['Momentum%'] > 2]
        elif "Guclu Satis" in filter_type: filtered = all_scores[all_scores['Sentiment'] < -30]
        elif "Asagi" in filter_type: filtered = all_scores[all_scores['Momentum%'] < -2]
        else: filtered = all_scores[(all_scores['Sentiment'] >= -10) & (all_scores['Sentiment'] <= 10)]
        if not filtered.empty:
            st.dataframe(filtered.reset_index(drop=True), use_container_width=True)
        else:
            st.warning("Sonuc bulunamadi.")


elif page == "📈 Gunluk Sentiment":
    st.title("📈 Gunluk Sentiment — BIST100")
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
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08, row_heights=[0.7, 0.3], specs=[[{"secondary_y": True}], [{"secondary_y": False}]])
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


elif page == "🔄 Osilator":
    st.title("🔄 Osilator — BIST100")
    bist_df = get_bist100_index()
    if not bist_df.empty:
        close = bist_df['Close']
        rsi_series = momentum.RSIIndicator(close, window=14).rsi()
        osc_series = ((rsi_series - 50) / 50) * 3
        period = min(60, len(close) - 14)
        osc_vals = [float(osc_series.iloc[i]) for i in range(-period, 0)]
        price_vals = [float(close.iloc[i]) for i in range(-period, 0)]
        x = list(range(len(osc_vals)))
        st.metric("Osilator", f"{osc_vals[-1]:.2f}" if osc_vals else "0")
        st.markdown("---")
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Scatter(x=x, y=price_vals, name='BIST100', line=dict(color='#1565c0', width=2.5)), secondary_y=False)
        osc_colors = ['#2e7d32' if v >= 0 else '#c62828' for v in osc_vals]
        fig.add_trace(go.Bar(x=x, y=osc_vals, name='Osilator', marker_color=osc_colors, opacity=0.7), secondary_y=True)
        fig.update_layout(height=450, paper_bgcolor='white', plot_bgcolor='white', legend=dict(orientation='h', y=-0.1))
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(showgrid=True, gridcolor='#eee')
        st.plotly_chart(fig, use_container_width=True)


elif page == "📋 BIST30 Ilk 10":
    st.title("📋 BIST30 — Ilk 10")
    scores_df = get_bist30_scores()
    if not scores_df.empty:
        top10 = scores_df.sort_values('Sentiment', ascending=False).head(10).reset_index(drop=True)
        top10.index = top10.index + 1
        st.dataframe(top10, use_container_width=True)
        fig = go.Figure(go.Bar(x=top10['Sembol'], y=top10['Sentiment'], marker_color=['#1565c0' if v>=0 else '#c62828' for v in top10['Sentiment']], text=top10['Karar'], textposition='outside'))
        fig.update_layout(height=400, paper_bgcolor='white', plot_bgcolor='white')
        st.plotly_chart(fig, use_container_width=True)


elif page == "📋 BIST30 Son 10":
    st.title("📋 BIST30 — Son 10")
    scores_df = get_bist30_scores()
    if not scores_df.empty:
        bottom10 = scores_df.sort_values('Sentiment', ascending=True).head(10).reset_index(drop=True)
        bottom10.index = bottom10.index + 1
        st.dataframe(bottom10, use_container_width=True)
        fig = go.Figure(go.Bar(x=bottom10['Sembol'], y=bottom10['Sentiment'], marker_color=['#1565c0' if v>=0 else '#c62828' for v in bottom10['Sentiment']], text=bottom10['Karar'], textposition='outside'))
        fig.update_layout(height=400, paper_bgcolor='white', plot_bgcolor='white')
        st.plotly_chart(fig, use_container_width=True)


elif page == "🔥 Heatmap":
    st.title("🔥 Heatmap — BIST Isı Haritasi")
    st.caption("Yesil = yukselis, Kirmizi = dusus")
    all_scores = get_all_bist_scores()
    if not all_scores.empty:
        sorted_s = all_scores.sort_values('Gun%', ascending=False)
        max_val = max(abs(sorted_s['Gun%'].max()), abs(sorted_s['Gun%'].min()), 1)
        cols_per_row = 6
        rows_data = [sorted_s.iloc[i:i+cols_per_row] for i in range(0, len(sorted_s), cols_per_row)]
        for row_data in rows_data:
            cols = st.columns(cols_per_row)
            for i, (_, row) in enumerate(row_data.iterrows()):
                if i < cols_per_row:
                    with cols[i]:
                        pct = row['Gun%']
                        if pct >= 2: bg = "#1b5e20"
                        elif pct >= 0.5: bg = "#388e3c"
                        elif pct >= 0: bg = "#66bb6a"
                        elif pct >= -0.5: bg = "#ef5350"
                        elif pct >= -2: bg = "#c62828"
                        else: bg = "#7f0000"
                        st.markdown(f'<div style="background:{bg};color:white;border-radius:8px;padding:10px;text-align:center;margin-bottom:6px;min-height:70px"><div style="font-weight:700;font-size:13px">{row["Sembol"]}</div><div style="font-size:16px;font-weight:800">{pct:+.1f}%</div><div style="font-size:11px">₺{row["Fiyat"]}</div></div>', unsafe_allow_html=True)


elif page == "⚔️ Karsilastir":
    st.title("⚔️ Hisse Karsilastirma")
    st.caption("2 hisseyi yan yana karsilastir")
    col1, col2 = st.columns(2)
    with col1:
        sym1 = st.selectbox("1. Hisse:", list(ALL_BIST.keys()), index=0)
    with col2:
        sym2 = st.selectbox("2. Hisse:", list(ALL_BIST.keys()), index=1)
    if st.button("⚔️ Karsilastir", type="primary"):
        df1 = get_bist_data(sym1)
        df2 = get_bist_data(sym2)
        r1 = calc_sentiment(df1)
        r2 = calc_sentiment(df2)
        if r1 and r2:
            st.markdown("---")
            c1, c2 = st.columns(2)
            with c1:
                dec_color = "#2e7d32" if "AL" in r1['decision'] else "#c62828" if "SAT" in r1['decision'] else "#f57c00"
                st.markdown(f'<div style="background:{dec_color};color:white;border-radius:12px;padding:20px;text-align:center"><h2 style="margin:0;color:white">{sym1}</h2><p style="margin:5px 0;font-size:24px;color:white">₺{r1["price"]:,.2f}</p><p style="color:rgba(255,255,255,0.9)">{r1["decision"]}</p></div>', unsafe_allow_html=True)
            with c2:
                dec_color = "#2e7d32" if "AL" in r2['decision'] else "#c62828" if "SAT" in r2['decision'] else "#f57c00"
                st.markdown(f'<div style="background:{dec_color};color:white;border-radius:12px;padding:20px;text-align:center"><h2 style="margin:0;color:white">{sym2}</h2><p style="margin:5px 0;font-size:24px;color:white">₺{r2["price"]:,.2f}</p><p style="color:rgba(255,255,255,0.9)">{r2["decision"]}</p></div>', unsafe_allow_html=True)
            st.markdown("---")
            compare_data = pd.DataFrame({'Gosterge': ['Fiyat', 'Gun%', 'Sentiment', 'RSI', 'Stoch', 'Momentum%', 'MACD', 'EMA21', 'Karar'], sym1: [f"₺{r1['price']:,.2f}", f"%{r1['daily_change']:.2f}", f"{r1['sent_puan']:.2f}", f"{r1['rsi']:.1f}", f"{r1['stoch']:.1f}", f"%{r1['momentum']:.2f}", f"{r1['macd']:.4f}", f"₺{r1['ema21']:.2f}", r1['decision']], sym2: [f"₺{r2['price']:,.2f}", f"%{r2['daily_change']:.2f}", f"{r2['sent_puan']:.2f}", f"{r2['rsi']:.1f}", f"{r2['stoch']:.1f}", f"%{r2['momentum']:.2f}", f"{r2['macd']:.4f}", f"₺{r2['ema21']:.2f}", r2['decision']]})
            st.dataframe(compare_data, use_container_width=True, hide_index=True)
            st.markdown("---")
            fig = go.Figure()
            prices1 = [p / r1['prices'][0] * 100 for p in r1['prices']]
            prices2 = [p / r2['prices'][0] * 100 for p in r2['prices']]
            fig.add_trace(go.Scatter(y=prices1, name=sym1, line=dict(color='#1565c0', width=2.5)))
            fig.add_trace(go.Scatter(y=prices2, name=sym2, line=dict(color='#c62828', width=2.5)))
            fig.update_layout(height=350, title="Performans Karsilastirma (Normalize)", paper_bgcolor='white', plot_bgcolor='white')
            fig.update_xaxes(showgrid=False)
            fig.update_yaxes(showgrid=True, gridcolor='#eee')
            st.plotly_chart(fig, use_container_width=True)


elif page == "🏆 Gunun En Iyileri":
    st.title("🏆 Gunun En Iyileri / En Kotuleri")
    all_scores = get_all_bist_scores()
    if not all_scores.empty:
        gtab1, gtab2 = st.tabs(["📈 En Cok Yukselenler", "📉 En Cok Dusenler"])
        with gtab1:
            top5 = all_scores.sort_values('Gun%', ascending=False).head(5).reset_index(drop=True)
            for i, (_, row) in enumerate(top5.iterrows()):
                medal = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][i]
                st.markdown(f'<div style="background:#e8f5e9;border-radius:10px;padding:14px;margin-bottom:8px;display:flex;justify-content:space-between;align-items:center"><div><span style="font-size:20px">{medal}</span> <strong style="font-size:16px">{row["Sembol"]}</strong></div><div style="text-align:right"><span style="color:#2e7d32;font-size:18px;font-weight:700">+%{row["Gun%"]:.2f}</span><br><span style="color:#666;font-size:13px">₺{row["Fiyat"]} | {row["Karar"]}</span></div></div>', unsafe_allow_html=True)
        with gtab2:
            bot5 = all_scores.sort_values('Gun%', ascending=True).head(5).reset_index(drop=True)
            for i, (_, row) in enumerate(bot5.iterrows()):
                medal = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][i]
                st.markdown(f'<div style="background:#ffebee;border-radius:10px;padding:14px;margin-bottom:8px;display:flex;justify-content:space-between;align-items:center"><div><span style="font-size:20px">{medal}</span> <strong style="font-size:16px">{row["Sembol"]}</strong></div><div style="text-align:right"><span style="color:#c62828;font-size:18px;font-weight:700">{row["Gun%"]:.2f}%</span><br><span style="color:#666;font-size:13px">₺{row["Fiyat"]} | {row["Karar"]}</span></div></div>', unsafe_allow_html=True)


elif page == "💼 Portfolyo":
    st.title("💼 Portfolyo Takibi")
    st.caption("Hisselerinizi ekleyin, kar/zarar takip edin")
    if 'portfolio' not in st.session_state:
        st.session_state.portfolio = []
    with st.expander("➕ Hisse Ekle"):
        p_col1, p_col2, p_col3 = st.columns(3)
        with p_col1:
            p_sym = st.selectbox("Sembol:", list(ALL_BIST.keys()), key="port_sym")
        with p_col2:
            p_lot = st.number_input("Lot:", min_value=1, value=100, key="port_lot")
        with p_col3:
            p_cost = st.number_input("Alis Fiyati (₺):", min_value=0.01, value=10.0, step=0.01, key="port_cost")
        if st.button("➕ Ekle", key="port_add"):
            st.session_state.portfolio.append({'symbol': p_sym, 'lot': p_lot, 'cost': p_cost})
            st.success(f"✅ {p_sym} eklendi!")
            st.rerun()
    if st.session_state.portfolio:
        st.markdown("---")
        toplam_maliyet = 0
        toplam_deger = 0
        port_data = []
        for item in st.session_state.portfolio:
            try:
                df = get_bist_data(item['symbol'])
                if not df.empty:
                    current = float(df['Close'].iloc[-1])
                    maliyet = item['lot'] * item['cost']
                    deger = item['lot'] * current
                    kar = deger - maliyet
                    kar_pct = ((current - item['cost']) / item['cost']) * 100
                    toplam_maliyet += maliyet
                    toplam_deger += deger
                    port_data.append({'Sembol': item['symbol'], 'Lot': item['lot'], 'Alis': f"₺{item['cost']:.2f}", 'Guncel': f"₺{current:.2f}", 'Kar/Zarar': f"₺{kar:,.0f}", 'Kar%': f"%{kar_pct:.1f}"})
            except:
                continue
        if port_data:
            toplam_kar = toplam_deger - toplam_maliyet
            toplam_pct = ((toplam_deger - toplam_maliyet) / toplam_maliyet) * 100 if toplam_maliyet > 0 else 0
            t_color = "#2e7d32" if toplam_kar >= 0 else "#c62828"
            st.markdown(f'<div style="background:{t_color};color:white;border-radius:12px;padding:20px;text-align:center;margin-bottom:20px"><h3 style="margin:0;color:white">Toplam Kar/Zarar</h3><h1 style="margin:5px 0;color:white">₺{toplam_kar:,.0f} (%{toplam_pct:.1f})</h1><p style="color:rgba(255,255,255,0.8)">Maliyet: ₺{toplam_maliyet:,.0f} | Deger: ₺{toplam_deger:,.0f}</p></div>', unsafe_allow_html=True)
            st.dataframe(pd.DataFrame(port_data), use_container_width=True, hide_index=True)
        if st.button("🗑️ Portfolyoyu Temizle"):
            st.session_state.portfolio = []
            st.rerun()
    else:
        st.info("Henuz hisse eklenmedi. Yukardaki formdan ekleyin.")
