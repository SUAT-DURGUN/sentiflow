"""
SentiFlow v1.3 — Profesyonel Sentiment Analiz Platformu
"""

import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from ta import momentum, trend, volatility
import ccxt
from datetime import datetime

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

CRYPTO_BINANCE = [
    'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'XRP/USDT',
    'ADA/USDT', 'DOGE/USDT', 'AVAX/USDT', 'DOT/USDT', 'LINK/USDT',
    'UNI/USDT', 'ATOM/USDT', 'LTC/USDT', 'APT/USDT', 'ARB/USDT',
    'OP/USDT', 'SUI/USDT', 'SEI/USDT', 'PEPE/USDT', 'SHIB/USDT',
    'INJ/USDT', 'TIA/USDT', 'RENDER/USDT', 'FET/USDT', 'NEAR/USDT',
    'TON/USDT', 'WLD/USDT', 'PENDLE/USDT', 'ORDI/USDT', 'NOT/USDT',
]

CRYPTO_EXTRA = ['NETX/USDT', 'KAS/USDT', 'CFX/USDT']


# ════════════════════════════
# VERİ ÇEKME
# ════════════════════════════

@st.cache_data(ttl=300)
def get_bist_data(symbol):
    yahoo = ALL_BIST.get(symbol, f"{symbol}.IS")
    df = yf.Ticker(yahoo).history(period="6mo", interval="1d")
    return df

@st.cache_data(ttl=300)
def get_crypto_data(symbol):
    try:
        ex = ccxt.binance({'enableRateLimit': True})
        ohlcv = ex.fetch_ohlcv(symbol, '1d', limit=180)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        return df
    except:
        pass
    try:
        ex = ccxt.mexc({'enableRateLimit': True})
        ohlcv = ex.fetch_ohlcv(symbol, '1d', limit=180)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        return df
    except:
        pass
    return pd.DataFrame()

@st.cache_data(ttl=300)
def get_bist100_index():
    df = yf.Ticker("XU100.IS").history(period="6mo", interval="1d")
    return df


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
    
    rsi_series = momentum.RSIIndicator(close, window=14).rsi()
    macd_ind = trend.MACD(close)
    macd_hist = macd_ind.macd_diff()
    macd_line = macd_ind.macd()
    macd_signal = macd_ind.macd_signal()
    stoch = momentum.StochasticOscillator(high, low, close).stoch()
    
    rsi_val = float(rsi_series.iloc[-1])
    macd_val = float(macd_hist.iloc[-1])
    stoch_val = float(stoch.iloc[-1])
    ema9 = float(close.ewm(span=9).mean().iloc[-1])
    ema21 = float(close.ewm(span=21).mean().iloc[-1])
    ema50 = float(close.ewm(span=50).mean().iloc[-1])
    
    # Skor
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
    
    # Günlük sentiment barları
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
    
    # Osilatör
    oscillator = ((rsi_val - 50) / 50) * 3
    
    # STP (basit destek/direnç)
    stp = float(close.rolling(20).mean().iloc[-1])
    hstp = float(close.rolling(50).mean().iloc[-1])
    
    return {
        'price': price, 'score': score, 'signal': signal,
        'rsi': rsi_val, 'macd': macd_val, 'stoch': stoch_val,
        'momentum': mom, 'bars': bars, 'mom_bars': mom_bars,
        'prices': [float(p) for p in close.tolist()[-60:]],
        'oscillator': round(oscillator, 2),
        'stp': round(stp, 2), 'hstp': round(hstp, 2),
        'ema9': ema9, 'ema21': ema21, 'ema50': ema50,
    }


def get_bist30_scores():
    results = []
    for symbol in BIST30.keys():
        try:
            df = get_bist_data(symbol)
            result = calc_sentiment(df)
            if result:
                results.append({
                    'Sembol': symbol,
                    'Fiyat': round(result['price'], 2),
                    'Sentiment': result['score'],
                    'RSI': round(result['rsi'], 1),
                    'Momentum': round(result['momentum'], 2),
                    'Sinyal': result['signal'],
                })
        except:
            continue
    return pd.DataFrame(results)


# ════════════════════════════
# SOL MENÜ
# ════════════════════════════

with st.sidebar:
    st.markdown("## 🌊 SentiFlow")
    st.caption("Piyasa Sentiment Analiz Platformu")
    st.markdown("---")
    
    page = st.radio("📍 Menü", [
        "🏠 Ana Sayfa",
        "📊 Hisse Analiz",
        "🪙 Kripto Analiz",
        "📈 Günlük Sentiment",
        "🔄 Osilatör",
        "📋 BIST30 İlk 10",
        "📋 BIST30 Son 10",
    ])
    
    st.markdown("---")
    st.caption(f"v1.3 | {datetime.now().strftime('%d.%m.%Y %H:%M')}")


# ════════════════════════════
# SAYFALAR
# ════════════════════════════

# ═══ ANA SAYFA ═══
if page == "🏠 Ana Sayfa":
    st.title("🌊 SentiFlow — Dashboard")
    
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        st.subheader("Sentiment Güç İndikatörü")
        bist_df = get_bist100_index()
        if not bist_df.empty:
            bist_result = calc_sentiment(bist_df)
            if bist_result:
                gauge_val = int((bist_result['score'] + 100) / 2)
                gauge_val = max(0, min(100, gauge_val))
                
                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=gauge_val,
                    number={'font': {'size': 50}},
                    gauge={
                        'axis': {'range': [0, 100]},
                        'bar': {'color': '#1e88e5'},
                        'steps': [
                            {'range': [0, 25], 'color': '#ffcdd2'},
                            {'range': [25, 50], 'color': '#fff9c4'},
                            {'range': [50, 75], 'color': '#c8e6c9'},
                            {'range': [75, 100], 'color': '#bbdefb'},
                        ],
                    }
                ))
                fig_gauge.update_layout(height=250, margin=dict(l=20, r=20, t=30, b=10))
                st.plotly_chart(fig_gauge, use_container_width=True)
                
                # Sentiment Özeti
                st.markdown("**Sentiment Özeti:**")
                s1, s2, s3 = st.columns(3)
                s1.metric("Günlük", f"{bist_result['score']}")
                s2.metric("Momentum", f"{bist_result['momentum']:.1f}%")
                s3.metric("Osilatör", f"{bist_result['oscillator']:.2f}")
    
    with col_right:
        st.subheader("BIST100 Endeks")
        if not bist_df.empty:
            price = float(bist_df['Close'].iloc[-1])
            prev = float(bist_df['Close'].iloc[-2])
            change = ((price - prev) / prev) * 100
            
            st.metric("BIST100", f"{price:,.2f}", f"{change:+.2f}%")
            
            # Mini grafik
            fig_mini = go.Figure(go.Scatter(
                y=bist_df['Close'].tolist()[-30:],
                mode='lines', line=dict(color='#00c853' if change >= 0 else '#ff1744', width=2),
                fill='tozeroy', fillcolor='rgba(0,200,83,0.1)' if change >= 0 else 'rgba(255,23,68,0.1)'
            ))
            fig_mini.update_layout(height=200, margin=dict(l=0, r=0, t=0, b=0),
                                  xaxis=dict(visible=False), yaxis=dict(visible=False),
                                  paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_mini, use_container_width=True)
    
    st.markdown("---")
    st.subheader("⚡ Hızlı Bakış — BIST30 Top 5")
    scores = get_bist30_scores()
    if not scores.empty:
        top5 = scores.sort_values('Sentiment', ascending=False).head(5)
        cols = st.columns(5)
        for i, (_, row) in enumerate(top5.iterrows()):
            with cols[i]:
                color = "normal" if row['Sentiment'] > 0 else "inverse"
                st.metric(row['Sembol'], f"₺{row['Fiyat']:.0f}", f"S:{row['Sentiment']}")


# ═══ HİSSE ANALİZ ═══
elif page == "📊 Hisse Analiz":
    st.title("📊 Hisse Sentiment Analizi")
    
    symbol = st.selectbox("Hisse Seçin:", list(ALL_BIST.keys()))
    df = get_bist_data(symbol)
    
    if not df.empty:
        result = calc_sentiment(df)
        if result:
            st.markdown("---")
            col1, col2, col3, col4, col5, col6 = st.columns(6)
            col1.metric("💰 Fiyat", f"₺{result['price']:,.2f}")
            col2.metric("📊 Sent.", f"{result['score']}", result['signal'])
            col3.metric("📉 RSI", f"{result['rsi']:.1f}")
            col4.metric("⚡ Stoch", f"{result['stoch']:.1f}")
            col5.metric("🚀 Mom", f"{result['momentum']:.1f}%")
            col6.metric("🎯 Osil.", f"{result['oscillator']:.2f}")
            
            st.markdown("---")
            
            # Çift grafik (Sentiment Algo gibi)
            left_chart, right_chart = st.columns(2)
            
            with left_chart:
                st.caption(f"📊 {symbol} — Sentiment + Fiyat")
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                                   vertical_spacing=0.08, row_heights=[0.65, 0.35])
                
                x = list(range(len(result['prices'])))
                fig.add_trace(go.Scatter(x=x, y=result['prices'], name='Fiyat',
                                        line=dict(color='#00c853', width=2)), row=1, col=1)
                
                colors = ['#1e88e5' if v >= 0 else '#ff1744' for v in result['bars']]
                fig.add_trace(go.Bar(x=x, y=result['bars'], name='Sentiment',
                                    marker_color=colors, opacity=0.8), row=2, col=1)
                
                fig.update_layout(height=400, showlegend=True, margin=dict(l=40, r=10, t=10, b=30),
                                 paper_bgcolor='white', plot_bgcolor='#fafafa')
                st.plotly_chart(fig, use_container_width=True)
            
            with right_chart:
                st.caption(f"📈 {symbol} — Fiyat + STP/HSTP")
                fig2 = go.Figure()
                
                x2 = list(range(len(result['prices'])))
                fig2.add_trace(go.Scatter(x=x2, y=result['prices'], name='Fiyat',
                                         line=dict(color='#00c853', width=2)))
                # STP çizgisi (20 günlük ortalama)
                stp_line = [result['stp']] * len(x2)
                fig2.add_trace(go.Scatter(x=x2, y=stp_line, name='STP',
                                         line=dict(color='#ff9800', width=1.5, dash='dash')))
                # HSTP çizgisi (50 günlük ortalama)
                hstp_line = [result['hstp']] * len(x2)
                fig2.add_trace(go.Scatter(x=x2, y=hstp_line, name='HSTP',
                                         line=dict(color='#f44336', width=1.5, dash='dot')))
                
                fig2.update_layout(height=400, showlegend=True, margin=dict(l=40, r=10, t=10, b=30),
                                  paper_bgcolor='white', plot_bgcolor='#fafafa')
                st.plotly_chart(fig2, use_container_width=True)
            
            # Detaylar
            with st.expander("📋 Detaylı Göstergeler"):
                d1, d2, d3, d4 = st.columns(4)
                d1.write(f"**EMA 9:** ₺{result['ema9']:.2f}")
                d1.write(f"**EMA 21:** ₺{result['ema21']:.2f}")
                d2.write(f"**EMA 50:** ₺{result['ema50']:.2f}")
                d2.write(f"**STP:** ₺{result['stp']:.2f}")
                d3.write(f"**HSTP:** ₺{result['hstp']:.2f}")
                d3.write(f"**MACD:** {result['macd']:.4f}")
                d4.write(f"**Sinyal:** {result['signal']}")
                d4.write(f"**Osilatör:** {result['oscillator']:.2f}")


# ═══ KRİPTO ANALİZ ═══
elif page == "🪙 Kripto Analiz":
    st.title("🪙 Kripto Sentiment Analizi")
    
    all_crypto = CRYPTO_BINANCE + CRYPTO_EXTRA
    symbol = st.selectbox("Kripto Seçin:", all_crypto)
    df = get_crypto_data(symbol)
    
    if not df.empty:
        result = calc_sentiment(df)
        if result:
            st.markdown("---")
            col1, col2, col3, col4, col5, col6 = st.columns(6)
            col1.metric("💰 Fiyat", f"${result['price']:,.4f}" if result['price'] < 1 else f"${result['price']:,.2f}")
            col2.metric("📊 Sent.", f"{result['score']}", result['signal'])
            col3.metric("📉 RSI", f"{result['rsi']:.1f}")
            col4.metric("⚡ Stoch", f"{result['stoch']:.1f}")
            col5.metric("🚀 Mom", f"{result['momentum']:.1f}%")
            col6.metric("🎯 Osil.", f"{result['oscillator']:.2f}")
            
            st.markdown("---")
            
            left_chart, right_chart = st.columns(2)
            
            with left_chart:
                st.caption(f"📊 {symbol} — Sentiment + Fiyat")
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                                   vertical_spacing=0.08, row_heights=[0.65, 0.35])
                
                x = list(range(len(result['prices'])))
                fig.add_trace(go.Scatter(x=x, y=result['prices'], name='Fiyat',
                                        line=dict(color='#00c853', width=2)), row=1, col=1)
                colors = ['#1e88e5' if v >= 0 else '#ff1744' for v in result['bars']]
                fig.add_trace(go.Bar(x=x, y=result['bars'], name='Sentiment',
                                    marker_color=colors, opacity=0.8), row=2, col=1)
                fig.update_layout(height=400, showlegend=True, margin=dict(l=40, r=10, t=10, b=30),
                                 paper_bgcolor='white', plot_bgcolor='#fafafa')
                st.plotly_chart(fig, use_container_width=True)
            
            with right_chart:
                st.caption(f"📈 {symbol} — Fiyat + STP/HSTP")
                fig2 = go.Figure()
                x2 = list(range(len(result['prices'])))
                fig2.add_trace(go.Scatter(x=x2, y=result['prices'], name='Fiyat',
                                         line=dict(color='#00c853', width=2)))
                stp_line = [result['stp']] * len(x2)
                fig2.add_trace(go.Scatter(x=x2, y=stp_line, name='STP',
                                         line=dict(color='#ff9800', width=1.5, dash='dash')))
                hstp_line = [result['hstp']] * len(x2)
                fig2.add_trace(go.Scatter(x=x2, y=hstp_line, name='HSTP',
                                         line=dict(color='#f44336', width=1.5, dash='dot')))
                fig2.update_layout(height=400, showlegend=True, margin=dict(l=40, r=10, t=10, b=30),
                                  paper_bgcolor='white', plot_bgcolor='#fafafa')
                st.plotly_chart(fig2, use_container_width=True)
    else:
        st.error(f"'{symbol}' için veri çekilemedi!")


# ═══ GÜNLÜK SENTİMENT ═══
elif page == "📈 Günlük Sentiment":
    st.title("📈 Günlük Sentiment — BIST100")
    
    bist_df = get_bist100_index()
    if not bist_df.empty:
        result = calc_sentiment(bist_df)
        if result:
            # Bilgi kutusu
            i1, i2, i3, i4 = st.columns(4)
            i1.metric("Sentiment", f"{result['score']}")
            i2.metric("Momentum", f"{result['momentum']:.1f}%")
            i3.metric("BIST100", f"{result['price']:,.2f}")
            i4.metric("Osilatör", f"{result['oscillator']:.2f}")
            
            st.markdown("---")
            
            # Ana grafik (Sentiment Algo tarzı)
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                               vertical_spacing=0.08, row_heights=[0.7, 0.3],
                               specs=[[{"secondary_y": True}], [{"secondary_y": False}]])
            
            x = list(range(len(result['bars'])))
            
            # Sentiment barları
            colors = ['#1e88e5' if v >= 0 else '#ff1744' for v in result['bars']]
            fig.add_trace(go.Bar(x=x, y=result['bars'], name='Sentiment',
                                marker_color=colors, opacity=0.8),
                         row=1, col=1, secondary_y=False)
            
            # Fiyat çizgisi
            fig.add_trace(go.Scatter(x=x, y=result['prices'], name='BIST100',
                                    line=dict(color='#00c853', width=2.5)),
                         row=1, col=1, secondary_y=True)
            
            # Momentum barları
            mom_colors = ['#1e88e5' if v >= 0 else '#ff1744' for v in result['mom_bars']]
            fig.add_trace(go.Bar(x=x, y=result['mom_bars'], name='Momentum',
                                marker_color=mom_colors, opacity=0.7), row=2, col=1)
            
            fig.update_layout(height=500, showlegend=True,
                             legend=dict(orientation='h', y=-0.1),
                             paper_bgcolor='white', plot_bgcolor='#fafafa',
                             margin=dict(l=50, r=20, t=10, b=40))
            fig.update_xaxes(showgrid=False)
            fig.update_yaxes(showgrid=True, gridcolor='#f0f0f0')
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Lejant
            st.caption("🔵 Sentiment | 🟢 BIST100 Endeks | 🔴 Momentum")


# ═══ OSİLATÖR ═══
elif page == "🔄 Osilatör":
    st.title("🔄 Osilatör — BIST100")
    
    bist_df = get_bist100_index()
    if not bist_df.empty:
        close = bist_df['Close']
        rsi_series = momentum.RSIIndicator(close, window=14).rsi()
        
        # Osilatör serisini hesapla
        oscillator_series = ((rsi_series - 50) / 50) * 3
        
        # Son 60 gün
        period = min(60, len(close) - 14)
        osc_vals = [float(oscillator_series.iloc[i]) for i in range(-period, 0)]
        price_vals = [float(close.iloc[i]) for i in range(-period, 0)]
        x = list(range(len(osc_vals)))
        
        # Bilgi
        current_osc = osc_vals[-1] if osc_vals else 0
        st.metric("Osilatör Değeri", f"{current_osc:.2f}")
        
        st.markdown("---")
        
        # Grafik
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Endeks çizgisi
        fig.add_trace(go.Scatter(x=x, y=price_vals, name='BIST100',
                                line=dict(color='#1e88e5', width=2)), secondary_y=False)
        
        # Osilatör barları
        osc_colors = ['#00c853' if v >= 0 else '#ff1744' for v in osc_vals]
        fig.add_trace(go.Bar(x=x, y=osc_vals, name='Osilatör',
                            marker_color=osc_colors, opacity=0.6), secondary_y=True)
        
        fig.update_layout(height=450, showlegend=True,
                         legend=dict(orientation='h', y=-0.1),
                         paper_bgcolor='white', plot_bgcolor='#fafafa',
                         margin=dict(l=50, r=50, t=10, b=40))
        
        st.plotly_chart(fig, use_container_width=True)
        st.caption("🔵 BIST100 Endeks | 🟢🔴 Osilatör (pozitif = yükseliş, negatif = düşüş)")


# ═══ BIST30 İLK 10 ═══
elif page == "📋 BIST30 İlk 10":
    st.title("📋 BIST30 — En Güçlü 10 Hisse")
    st.info("⏳ Veriler çekiliyor... (ilk seferde 1-2 dakika sürebilir)")
    
    scores_df = get_bist30_scores()
    if not scores_df.empty:
        top10 = scores_df.sort_values('Sentiment', ascending=False).head(10).reset_index(drop=True)
        top10.index = top10.index + 1
        st.dataframe(top10, use_container_width=True)
        
        st.markdown("---")
        st.subheader("📊 Sentiment Sıralaması")
        fig = go.Figure(go.Bar(
            x=top10['Sembol'], y=top10['Sentiment'],
            marker_color=['#1e88e5' if v >= 0 else '#ff1744' for v in top10['Sentiment']],
            text=top10['Sinyal'], textposition='outside'
        ))
        fig.update_layout(height=400, paper_bgcolor='white', plot_bgcolor='#fafafa')
        st.plotly_chart(fig, use_container_width=True)


# ═══ BIST30 SON 10 ═══
elif page == "📋 BIST30 Son 10":
    st.title("📋 BIST30 — En Zayıf 10 Hisse")
    st.info("⏳ Veriler çekiliyor...")
    
    scores_df = get_bist30_scores()
    if not scores_df.empty:
        bottom10 = scores_df.sort_values('Sentiment', ascending=True).head(10).reset_index(drop=True)
        bottom10.index = bottom10.index + 1
        st.dataframe(bottom10, use_container_width=True)
        
        st.markdown("---")
        st.subheader("📊 Sentiment Sıralaması")
        fig = go.Figure(go.Bar(
            x=bottom10['Sembol'], y=bottom10['Sentiment'],
            marker_color=['#1e88e5' if v >= 0 else '#ff1744' for v in bottom10['Sentiment']],
            text=bottom10['Sinyal'], textposition='outside'
        ))
        fig.update_layout(height=400, paper_bgcolor='white', plot_bgcolor='#fafafa')
        st.plotly_chart(fig, use_container_width=True)
