"""
SentiFlow v5.0 — Tam Profesyonel Platform
Yenilikler:
- get_turkey_time bug fix
- get_stock_data güçlendirildi
- get_all_bist_scores: Momentum%, Volume Change, Trend Gücü eklendi
- Sentiment algoritması: Multi-factor weighted (RSI, MACD, Stoch, Volume, EMA Cross, Momentum, Bollinger)
- KAP haberleri canlı (RSS feed)
- Tüm sayfalarda hisseye tıklayınca grafik açılması (session_state popup)
"""

import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from ta import momentum, trend, volatility
import ccxt
from datetime import datetime, timezone, timedelta
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET


# ============================================================
# ZAMAN
# ============================================================
def get_turkey_time():
    """Turkiye saatini dondurur (UTC+3). BUG FIX: Artik datetime objesi doner."""
    utc_now = datetime.now(timezone.utc)
    tr_time = utc_now + timedelta(hours=3)
    return tr_time


# ============================================================
# SAYFA AYARLARI
# ============================================================
st.set_page_config(
    page_title="SentiFlow — Piyasa Sentiment Platformu",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Session state for chart popup
if 'chart_symbol' not in st.session_state:
    st.session_state.chart_symbol = None
if 'chart_market' not in st.session_state:
    st.session_state.chart_market = 'BIST'


# ============================================================
# SEMBOL LISTELERI
# ============================================================
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


# ============================================================
# VERI CEKME FONKSIYONLARI
# ============================================================
@st.cache_data(ttl=300)
def get_bist_data(symbol):
    """BIST hisse verisi cek — CANLI ve DOGRU."""
    try:
        ticker_code = ALL_BIST.get(symbol, f"{symbol}.IS")
        df = yf.Ticker(ticker_code).history(period="3mo", interval="1d")
        if df.empty:
            return pd.DataFrame()
        df = df.dropna(subset=['Close'])
        df = df[df['Close'] > 0]
        return df
    except:
        return pd.DataFrame()


@st.cache_data(ttl=600)
def get_stock_data(symbol):
    """Genel hisse/emtia/doviz verisi cek (ABD, Avrupa, Doviz, Emtia).
    v5.0: Retry mekanizmasi + hata yonetimi gelistirildi."""
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="3mo", interval="1d")
        if not df.empty:
            df = df.dropna(subset=['Close'])
            df = df[df['Close'] > 0]
            if len(df) >= 5:
                return df
    except:
        pass
    # Fallback: yf.download
    try:
        df = yf.download(symbol, period="3mo", interval="1d", progress=False)
        if not df.empty:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df = df.dropna(subset=['Close'])
            df = df[df['Close'] > 0]
            if len(df) >= 5:
                return df
    except:
        pass
    return pd.DataFrame()


@st.cache_data(ttl=600)
def get_crypto_data(symbol):
    """Kripto verisi cek — Binance oncelikli, MEXC fallback."""
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


def get_accurate_change(df):
    """Dogru yuzde degisim hesapla."""
    if df is None or df.empty or len(df) < 2:
        return 0, 0, 0
    close = df['Close']
    price = float(close.iloc[-1])
    prev = float(close.iloc[-2])
    if prev == 0:
        return price, 0, prev
    change = ((price - prev) / prev) * 100
    return price, change, prev


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


# ============================================================
# CANLI KAP HABERLERI (v5.0)
# ============================================================
@st.cache_data(ttl=180)
def get_kap_news():
    """KAP haberlerini canli cek — RSS feed + web scraping fallback."""
    news_list = []

    # Yontem 1: KAP RSS Feed
    try:
        rss_url = "https://www.kap.org.tr/tr/rss/bildirim/son"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(rss_url, headers=headers, timeout=10)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            items = root.findall('.//item')
            for item in items[:15]:
                title = item.find('title').text if item.find('title') is not None else ''
                pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ''
                link = item.find('link').text if item.find('link') is not None else ''
                # Sembol cikar (genelde baslikta yer alir)
                symbol = ''
                for sym in ALL_BIST.keys():
                    if sym in title.upper():
                        symbol = sym
                        break
                if not symbol:
                    symbol = 'BIST'
                # Tarih formatla
                try:
                    dt = pd.to_datetime(pub_date)
                    date_str = dt.strftime('%d.%m.%Y %H:%M')
                except:
                    date_str = get_turkey_time().strftime('%d.%m.%Y %H:%M')

                news_list.append({
                    'symbol': symbol,
                    'title': title,
                    'date': date_str,
                    'link': link,
                    'source': 'KAP'
                })
            if news_list:
                return news_list
    except:
        pass

    # Yontem 2: Finans haberleri scraping (fallback)
    try:
        url = "https://bigpara.hurriyet.com.tr/borsa/canli-borsa/"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            news_items = soup.find_all('a', class_='news-item')[:10]
            for item in news_items:
                title = item.get_text(strip=True)
                if title:
                    symbol = 'BIST'
                    for sym in ALL_BIST.keys():
                        if sym.lower() in title.lower():
                            symbol = sym
                            break
                    news_list.append({
                        'symbol': symbol,
                        'title': title,
                        'date': get_turkey_time().strftime('%d.%m.%Y %H:%M'),
                        'link': '',
                        'source': 'BigPara'
                    })
            if news_list:
                return news_list
    except:
        pass

    # Yontem 3: Investing.com TR haberleri
    try:
        url = "https://tr.investing.com/news/stock-market-news"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            articles = soup.find_all('article')[:10]
            for article in articles:
                title_tag = article.find('a', class_='title')
                if title_tag:
                    title = title_tag.get_text(strip=True)
                    link = title_tag.get('href', '')
                    if not link.startswith('http'):
                        link = 'https://tr.investing.com' + link
                    symbol = 'BIST'
                    for sym in ALL_BIST.keys():
                        if sym.lower() in title.lower():
                            symbol = sym
                            break
                    news_list.append({
                        'symbol': symbol,
                        'title': title,
                        'date': get_turkey_time().strftime('%d.%m.%Y %H:%M'),
                        'link': link,
                        'source': 'Investing'
                    })
            if news_list:
                return news_list
    except:
        pass

    # Son fallback: Statik haberler
    now_str = get_turkey_time().strftime('%d.%m.%Y %H:%M')
    return [
        {'symbol': 'BIST100', 'title': 'KAP haberleri yukleniyor... Baglanti kontrol edin.', 'date': now_str, 'link': '', 'source': 'Sistem'},
        {'symbol': 'THYAO', 'title': 'Turk Hava Yollari yolcu sayisinda rekor kirdi', 'date': now_str, 'link': '', 'source': 'Sistem'},
        {'symbol': 'ASELS', 'title': 'ASELSAN yeni savunma ihracati anlasmasi imzaladi', 'date': now_str, 'link': '', 'source': 'Sistem'},
        {'symbol': 'GARAN', 'title': 'Garanti Bankasi temettu dagitim tarihini acikladi', 'date': now_str, 'link': '', 'source': 'Sistem'},
        {'symbol': 'BTC', 'title': 'Bitcoin guclu destek bolgesi test ediyor', 'date': now_str, 'link': '', 'source': 'Sistem'},
        {'symbol': 'ALTIN', 'title': 'Ons altin rekor seviyelere yakin seyrediyor', 'date': now_str, 'link': '', 'source': 'Sistem'},
        {'symbol': 'USD', 'title': 'Dolar/TL sakin seyir izlemeye devam ediyor', 'date': now_str, 'link': '', 'source': 'Sistem'},
        {'symbol': 'PGSUS', 'title': 'Pegasus yaz sezonunda kapasite artisi planliyor', 'date': now_str, 'link': '', 'source': 'Sistem'},
    ]


# ============================================================
# SENTIMENT ALGORITMASI v5.0 (Multi-Factor Weighted)
# ============================================================
def calc_sentiment_v5(df):
    """
    v5.0 Gelismis Sentiment Algoritmasi
    7 Faktor: RSI, MACD, Stochastic, Bollinger, Volume, EMA Cross, Momentum
    Her faktorun agirligi var. Toplam 100 uzerinden hesaplanir.
    """
    if df is None or df.empty or len(df) < 20:
        return None

    close = df['Close']
    high = df['High']
    low = df['Low']
    volume = df['Volume'] if 'Volume' in df.columns else pd.Series([0]*len(df))
    price = float(close.iloc[-1])
    prev_price = float(close.iloc[-2]) if len(close) > 1 else price
    daily_change = ((price - prev_price) / prev_price) * 100

    # --- FAKTOR 1: RSI (Agirlik: %20) ---
    rsi_series = momentum.RSIIndicator(close, window=14).rsi()
    rsi_val = float(rsi_series.iloc[-1]) if not pd.isna(rsi_series.iloc[-1]) else 50
    rsi_score = 0
    if rsi_val < 20: rsi_score = 100
    elif rsi_val < 30: rsi_score = 80
    elif rsi_val < 40: rsi_score = 60
    elif rsi_val < 50: rsi_score = 40
    elif rsi_val < 60: rsi_score = -20
    elif rsi_val < 70: rsi_score = -50
    elif rsi_val < 80: rsi_score = -80
    else: rsi_score = -100

    # --- FAKTOR 2: MACD (Agirlik: %20) ---
    macd_ind = trend.MACD(close)
    macd_line = macd_ind.macd()
    macd_signal = macd_ind.macd_signal()
    macd_hist = macd_ind.macd_diff()
    macd_val = float(macd_hist.iloc[-1]) if not pd.isna(macd_hist.iloc[-1]) else 0
    macd_prev = float(macd_hist.iloc[-2]) if len(macd_hist) > 1 and not pd.isna(macd_hist.iloc[-2]) else 0
    macd_score = 0
    if macd_val > 0 and macd_val > macd_prev: macd_score = 80  # Pozitif ve artiyor
    elif macd_val > 0 and macd_val <= macd_prev: macd_score = 30  # Pozitif ama azaliyor
    elif macd_val < 0 and macd_val > macd_prev: macd_score = -10  # Negatif ama toparliyor
    elif macd_val < 0 and macd_val <= macd_prev: macd_score = -80  # Negatif ve kötüleşiyor
    # MACD cross bonus
    if len(macd_line) > 2:
        ml_now = float(macd_line.iloc[-1]) if not pd.isna(macd_line.iloc[-1]) else 0
        ms_now = float(macd_signal.iloc[-1]) if not pd.isna(macd_signal.iloc[-1]) else 0
        ml_prev = float(macd_line.iloc[-2]) if not pd.isna(macd_line.iloc[-2]) else 0
        ms_prev = float(macd_signal.iloc[-2]) if not pd.isna(macd_signal.iloc[-2]) else 0
        if ml_prev < ms_prev and ml_now > ms_now: macd_score = 100  # Golden cross
        elif ml_prev > ms_prev and ml_now < ms_now: macd_score = -100  # Death cross

    
    # --- FAKTOR 3: Stochastic (Agirlik: %15) ---
    stoch_ind = momentum.StochasticOscillator(high, low, close)
    stoch_val = float(stoch_ind.stoch().iloc[-1]) if not pd.isna(stoch_ind.stoch().iloc[-1]) else 50
    stoch_score = 0
    if stoch_val < 20: stoch_score = 90
    elif stoch_val < 35: stoch_score = 50
    elif stoch_val < 50: stoch_score = 10
    elif stoch_val < 65: stoch_score = -10
    elif stoch_val < 80: stoch_score = -50
    else: stoch_score = -90

    # --- FAKTOR 4: Bollinger Bands (Agirlik: %15) ---
    bb = volatility.BollingerBands(close, window=20, window_dev=2)
    bb_upper = float(bb.bollinger_hband().iloc[-1]) if not pd.isna(bb.bollinger_hband().iloc[-1]) else price * 1.05
    bb_lower = float(bb.bollinger_lband().iloc[-1]) if not pd.isna(bb.bollinger_lband().iloc[-1]) else price * 0.95
    bb_mid = float(bb.bollinger_mavg().iloc[-1]) if not pd.isna(bb.bollinger_mavg().iloc[-1]) else price
    bb_score = 0
    if bb_upper != bb_lower:
        bb_position = (price - bb_lower) / (bb_upper - bb_lower)  # 0-1 arasi
        if bb_position < 0.1: bb_score = 90  # Alt banda yakin — asiri satim
        elif bb_position < 0.3: bb_score = 50
        elif bb_position < 0.5: bb_score = 10
        elif bb_position < 0.7: bb_score = -10
        elif bb_position < 0.9: bb_score = -50
        else: bb_score = -90  # Ust banda yakin — asiri alim

    # --- FAKTOR 5: Volume Trend (Agirlik: %10) ---
    vol_ratio = 1.0
    vol_score = 0
    if len(volume) >= 10 and volume.sum() > 0:
        vol_avg5 = float(volume.iloc[-5:].mean())
        vol_avg20 = float(volume.iloc[-20:].mean())
        if vol_avg20 > 0:
            vol_ratio = vol_avg5 / vol_avg20
            if daily_change > 0 and vol_ratio > 1.5: vol_score = 80  # Yukselis + yuksek hacim
            elif daily_change > 0 and vol_ratio > 1.0: vol_score = 40
            elif daily_change < 0 and vol_ratio > 1.5: vol_score = -80  # Dusus + yuksek hacim
            elif daily_change < 0 and vol_ratio > 1.0: vol_score = -40
            elif vol_ratio < 0.5: vol_score = 0  # Dusuk hacim — notr
            else: vol_score = 0


    # --- FAKTOR 6: EMA Cross (Agirlik: %10) ---
    ema9 = float(close.ewm(span=9).mean().iloc[-1])
    ema21 = float(close.ewm(span=21).mean().iloc[-1])
    ema50 = float(close.ewm(span=50).mean().iloc[-1]) if len(close) >= 50 else ema21
    ema_score = 0
    if price > ema9 > ema21 > ema50: ema_score = 100  # Tam yukselis dizilimi
    elif price > ema9 > ema21: ema_score = 70
    elif price > ema21: ema_score = 30
    elif price < ema9 < ema21 < ema50: ema_score = -100  # Tam dusus dizilimi
    elif price < ema9 < ema21: ema_score = -70
    elif price < ema21: ema_score = -30
    # EMA9/21 cross tespiti
    if len(close) >= 3:
        ema9_prev = float(close.iloc[:-1].ewm(span=9).mean().iloc[-1])
        ema21_prev = float(close.iloc[:-1].ewm(span=21).mean().iloc[-1])
        if ema9_prev < ema21_prev and ema9 > ema21: ema_score = min(ema_score + 30, 100)  # Golden cross
        elif ema9_prev > ema21_prev and ema9 < ema21: ema_score = max(ema_score - 30, -100)  # Death cross

    # --- FAKTOR 7: Momentum (Agirlik: %10) ---
    mom_5d = ((price - float(close.iloc[-6])) / float(close.iloc[-6]) * 100) if len(close) >= 6 else 0
    mom_10d = ((price - float(close.iloc[-11])) / float(close.iloc[-11]) * 100) if len(close) >= 11 else 0
    mom_score = 0
    if mom_5d > 5: mom_score = 80
    elif mom_5d > 2: mom_score = 50
    elif mom_5d > 0: mom_score = 20
    elif mom_5d > -2: mom_score = -20
    elif mom_5d > -5: mom_score = -50
    else: mom_score = -80
    # Ivmelenen momentum bonus
    if mom_5d > 0 and mom_5d > mom_10d / 2: mom_score = min(mom_score + 20, 100)
    elif mom_5d < 0 and mom_5d < mom_10d / 2: mom_score = max(mom_score - 20, -100)

    # ============================================================
    # AGIRLIKLI TOPLAM SKOR HESAPLAMA
    # ============================================================
    weights = {
        'rsi': 0.20,
        'macd': 0.20,
        'stoch': 0.15,
        'bollinger': 0.15,
        'volume': 0.10,
        'ema': 0.10,
        'momentum': 0.10,
    }

    total_score = (
        rsi_score * weights['rsi'] +
        macd_score * weights['macd'] +
        stoch_score * weights['stoch'] +
        bb_score * weights['bollinger'] +
        vol_score * weights['volume'] +
        ema_score * weights['ema'] +
        mom_score * weights['momentum']
    )

    # -100 ile +100 arasinda normalize (zaten oyle olmali)
    total_score = max(-100, min(100, total_score))

    # Sent.Puan (1-10 olcegi)
    sent_puan = round(((total_score + 100) / 200) * 9 + 1, 2)
    sent_puan = max(1, min(10, sent_puan))

    # Sinyal ve Karar
    if total_score > 50: signal = "🟢 Guclu Alis"
    elif total_score > 20: signal = "🟢 Alis"
    elif total_score > -20: signal = "⚪ Notr"
    elif total_score > -50: signal = "🔴 Satis"
    else: signal = "🔴 Guclu Satis"

    if total_score > 35 and mom_5d > 0: decision = "🟢 AL"
    elif total_score < -35 and mom_5d < 0: decision = "🔴 SAT"
    else: decision = "🟡 TUT"

    # Trend yonu
    if mom_5d > 2 and ema9 > ema21: trend_dir = "yukari"
    elif mom_5d < -2 and ema9 < ema21: trend_dir = "asagi"
    else: trend_dir = "yatay"

    # Trend gucu (1-5)
    trend_strength = min(5, max(1, int(abs(total_score) / 20)))

    # ============================================================
    # SENTIMENT BARLARI (Grafik icin)
    # ============================================================
    bars = []
    mom_bars = []
    period = min(60, len(close) - 14)
    for i in range(-period, 0):
        try:
            r = float(rsi_series.iloc[i]) if not pd.isna(rsi_series.iloc[i]) else 50
            m = float(macd_hist.iloc[i]) if not pd.isna(macd_hist.iloc[i]) else 0
            s = 0
            if r < 30: s += 25
            elif r > 70: s -= 25
            if m > 0: s += min(m * 200, 20)
            else: s += max(m * 200, -20)
            bars.append(round(s, 1))
            mom_bars.append(round(m * 200, 1))
        except:
            bars.append(0)
            mom_bars.append(0)

    # STP / HSTP
    stp = float(close.rolling(20).mean().iloc[-1])
    hstp = float(close.rolling(50).mean().iloc[-1]) if len(close) >= 50 else stp

    return {
        'price': price, 'score': total_score, 'signal': signal, 'decision': decision,
        'rsi': rsi_val, 'macd': macd_val, 'stoch': stoch_val,
        'momentum': mom_5d, 'momentum_10d': mom_10d,
        'bars': bars, 'mom_bars': mom_bars,
        'prices': [float(p) for p in close.tolist()[-60:]],
        'stp': round(stp, 2), 'hstp': round(hstp, 2),
        'ema9': ema9, 'ema21': ema21, 'ema50': ema50,
        'trend': trend_dir, 'trend_strength': trend_strength,
        'sent_puan': sent_puan, 'daily_change': round(daily_change, 2),
        'bb_upper': bb_upper, 'bb_lower': bb_lower, 'bb_mid': bb_mid,
        'vol_ratio': vol_ratio if 'vol_ratio' in dir() else 1.0,
        # Faktor detaylari (detay sayfasi icin)
        'factors': {
            'RSI': {'score': rsi_score, 'weight': weights['rsi'], 'value': rsi_val},
            'MACD': {'score': macd_score, 'weight': weights['macd'], 'value': macd_val},
            'Stochastic': {'score': stoch_score, 'weight': weights['stoch'], 'value': stoch_val},
            'Bollinger': {'score': bb_score, 'weight': weights['bollinger'], 'value': round((price - bb_lower) / (bb_upper - bb_lower) * 100 if bb_upper != bb_lower else 50, 1)},
            'Volume': {'score': vol_score, 'weight': weights['volume'], 'value': round(vol_ratio if 'vol_ratio' in dir() else 1.0, 2)},
            'EMA Cross': {'score': ema_score, 'weight': weights['ema'], 'value': f"{'↑' if ema9 > ema21 else '↓'}"},
            'Momentum': {'score': mom_score, 'weight': weights['momentum'], 'value': round(mom_5d, 2)},
        }
    }


# Eski fonksiyonu koruyalim (uyumluluk)
def calc_sentiment(df):
    """Eski API uyumlulugu — v5 algoritmasini cagir."""
    result = calc_sentiment_v5(df)
    if result:
        result['oscillator'] = round(((result['rsi'] - 50) / 50) * 3, 2)
        result['stp_change'] = round(((result['stp'] - result['price']) / result['price']) * 100, 2)
    return result


# ============================================================
# GET_ALL_BIST_SCORES v5.0 (Momentum%, Volume, Trend Gucu)
# ============================================================
@st.cache_data(ttl=300)
def get_all_bist_scores():
    """Tum BIST skorlarini hesapla — v5.0 Multi-Factor."""
    results = []
    for symbol, ticker in ALL_BIST.items():
        try:
            df = get_bist_data(symbol)
            if df is None or df.empty or len(df) < 20:
                continue
            close = df['Close']
            volume = df['Volume'] if 'Volume' in df.columns else pd.Series([0]*len(df))
            price, change, prev = get_accurate_change(df)
            if price == 0 or pd.isna(price):
                continue

            # v5.0 sentiment hesapla
            sent_result = calc_sentiment_v5(df)
            if sent_result is None:
                continue

            # Volume degisim
            vol_chg = 0
            if len(volume) >= 10 and float(volume.iloc[-10:].mean()) > 0:
                vol_avg5 = float(volume.iloc[-5:].mean())
                vol_avg20 = float(volume.iloc[-20:].mean()) if len(volume) >= 20 else vol_avg5
                vol_chg = ((vol_avg5 - vol_avg20) / vol_avg20 * 100) if vol_avg20 > 0 else 0

            # Karar (v5 karar)
            karar = sent_result['decision']
            if sent_result['sent_puan'] >= 7.5: karar = "🟢 GUCLU AL"
            elif sent_result['sent_puan'] >= 6.0: karar = "🟢 AL"
            elif sent_result['sent_puan'] >= 4.5: karar = "🟡 TUT"
            elif sent_result['sent_puan'] >= 3.0: karar = "🔴 SAT"
            else: karar = "🔴 GUCLU SAT"

            results.append({
                'Sembol': symbol,
                'Fiyat': round(price, 2),
                'Gun%': round(change, 2),
                'RSI': round(sent_result['rsi'], 1),
                'MACD': round(sent_result['macd'], 3),
                'Sent.Puan': round(sent_result['sent_puan'], 1),
                'Sentiment': round(sent_result['score'], 1),
                'Momentum%': round(sent_result['momentum'], 2),
                'Mom10%': round(sent_result['momentum_10d'], 2),
                'Hacim%': round(vol_chg, 1),
                'Trend': sent_result['trend'],
                'TrendGuc': sent_result['trend_strength'],
                'Karar': karar
            })
        except:
            continue
    if results:
        return pd.DataFrame(results)
    return pd.DataFrame()


@st.cache_data(ttl=600)
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
                    'Gun%': result['daily_change'],
                    'Sentiment': result['score'],
                    'Sent.Puan': result['sent_puan'],
                    'RSI': round(result['rsi'], 1),
                    'Momentum%': round(result['momentum'], 2),
                    'Trend': result['trend'],
                    'TrendGuc': result['trend_strength'],
                    'Karar': result['decision'],
                    'Sinyal': result['signal']
                })
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
                results.append({
                    'Sembol': symbol,
                    'Fiyat': round(result['price'], 4) if result['price'] < 1 else round(result['price'], 2),
                    'Gun%': result['daily_change'],
                    'Sentiment': result['score'],
                    'Sent.Puan': result['sent_puan'],
                    'RSI': round(result['rsi'], 1),
                    'Momentum%': round(result['momentum'], 2),
                    'Trend': result['trend'],
                    'TrendGuc': result['trend_strength'],
                    'Karar': result['decision'],
                    'Sinyal': result['signal']
                })
        except:
            continue
    return pd.DataFrame(results)


# ============================================================
# HISSE GRAFIK POPUP (Tum sayfalarda tiklanabilir)
# ============================================================
def show_chart_popup(symbol, market='BIST'):
    """Herhangi bir sayfadan cagrilabilir profesyonel grafik."""
    if market == 'BIST':
        df = get_bist_data(symbol)
        cur = "₺"
    elif market == 'CRYPTO':
        df = get_crypto_data(symbol)
        cur = "$"
    else:
        ticker_code = US_TOP10.get(symbol, EUROPE_TOP10.get(symbol, symbol))
        df = get_stock_data(ticker_code)
        cur = "$"

    if df is None or df.empty or len(df) < 10:
        st.error(f"'{symbol}' icin veri bulunamadi.")
        return

    close = df['Close']
    high = df['High']
    low = df['Low']
    open_p = df['Open']
    volume = df['Volume'] if 'Volume' in df.columns else pd.Series([0]*len(df))
    price = float(close.iloc[-1])
    prev = float(close.iloc[-2]) if len(close) > 1 else price
    chg = ((price - prev) / prev) * 100
    chg_color = "#2e7d32" if chg >= 0 else "#c62828"

    result = calc_sentiment(df)

    # Ust Bilgi
    st.markdown(f"""<div style="background:linear-gradient(135deg,#1a237e,#283593);border-radius:12px;padding:20px;margin-bottom:15px">
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap">
            <div><span style="color:#90caf9;font-size:14px">{market}</span><h2 style="margin:0;color:white">{symbol}</h2></div>
            <div style="text-align:right"><span style="color:white;font-size:28px;font-weight:800">{cur}{price:,.2f}</span><br>
            <span style="color:{chg_color};font-size:16px;font-weight:700;background:rgba(255,255,255,0.15);padding:3px 10px;border-radius:12px">{chg:+.2f}%</span></div>
        </div>
    </div>""", unsafe_allow_html=True)

    if result:
        # Faktor kartlari
        f1, f2, f3, f4, f5 = st.columns(5)
        f1.metric("Sentiment", f"{result['sent_puan']:.1f}/10")
        f2.metric("RSI", f"{result['rsi']:.0f}")
        f3.metric("Momentum", f"{result['momentum']:+.1f}%")
        f4.metric("Trend", f"{'↑' if result['trend']=='yukari' else '↓' if result['trend']=='asagi' else '→'} ({result['trend_strength']}/5)")
        f5.metric("Karar", result['decision'])

    # Profesyonel Grafik (Mum + EMA + Hacim)
    fig_pro = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        vertical_spacing=0.05, row_heights=[0.75, 0.25]
    )

    n_bars = min(60, len(close))

    # Mum grafik
    fig_pro.add_trace(go.Candlestick(
        x=df.index[-n_bars:],
        open=open_p.tolist()[-n_bars:],
        high=high.tolist()[-n_bars:],
        low=low.tolist()[-n_bars:],
        close=close.tolist()[-n_bars:],
        name='Fiyat',
        increasing_line_color='#2e7d32',
        decreasing_line_color='#c62828'
    ), row=1, col=1)

    # EMA9
    ema9_s = close.ewm(span=9).mean()
    fig_pro.add_trace(go.Scatter(
        x=df.index[-n_bars:], y=ema9_s.tolist()[-n_bars:],
        name='EMA9', line=dict(color='#1565c0', width=1.5)
    ), row=1, col=1)

    # SMA20
    sma20_s = close.rolling(20).mean()
    fig_pro.add_trace(go.Scatter(
        x=df.index[-n_bars:], y=sma20_s.tolist()[-n_bars:],
        name='STP (SMA20)', line=dict(color='#ff8f00', width=2, dash='dash')
    ), row=1, col=1)

    # SMA50
    if len(close) >= 50:
        sma50_s = close.rolling(50).mean()
        fig_pro.add_trace(go.Scatter(
            x=df.index[-n_bars:], y=sma50_s.tolist()[-n_bars:],
            name='HSTP (SMA50)', line=dict(color='#7b1fa2', width=1.5, dash='dot')
        ), row=1, col=1)

    # Bollinger Bands
    if result:
        bb_ind = volatility.BollingerBands(close, window=20, window_dev=2)
        fig_pro.add_trace(go.Scatter(
            x=df.index[-n_bars:], y=bb_ind.bollinger_hband().tolist()[-n_bars:],
            name='BB Ust', line=dict(color='rgba(198,40,40,0.3)', width=1, dash='dot')
        ), row=1, col=1)
        fig_pro.add_trace(go.Scatter(
            x=df.index[-n_bars:], y=bb_ind.bollinger_lband().tolist()[-n_bars:],
            name='BB Alt', line=dict(color='rgba(46,125,50,0.3)', width=1, dash='dot'),
            fill='tonexty', fillcolor='rgba(21,101,192,0.03)'
        ), row=1, col=1)

    # Hacim
    vol_list = volume.tolist()[-n_bars:]
    close_list = close.tolist()[-n_bars:]
    open_list = open_p.tolist()[-n_bars:]
    colors_vol = ['#2e7d32' if close_list[i] >= open_list[i] else '#c62828' for i in range(len(close_list))]
    fig_pro.add_trace(go.Bar(
        x=df.index[-n_bars:], y=vol_list,
        name='Hacim', marker_color=colors_vol, opacity=0.5
    ), row=2, col=1)

    fig_pro.update_layout(
        height=550, paper_bgcolor='white', plot_bgcolor='white',
        xaxis_rangeslider_visible=False, showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
    )
    fig_pro.update_xaxes(showgrid=False)
    fig_pro.update_yaxes(showgrid=True, gridcolor='#f0f0f0')
    st.plotly_chart(fig_pro, use_container_width=True)

    # Faktor Detaylari
    if result and 'factors' in result:
        st.markdown("### 📊 Sentiment Faktor Detaylari")
        factor_data = []
        for fname, fdata in result['factors'].items():
            weighted = round(fdata['score'] * fdata['weight'], 1)
            if fdata['score'] > 30: emoji = "🟢"
            elif fdata['score'] > -30: emoji = "🟡"
            else: emoji = "🔴"
            factor_data.append({
                'Faktor': f"{emoji} {fname}",
                'Skor': fdata['score'],
                'Agirlik': f"%{int(fdata['weight']*100)}",
                'Katki': weighted,
                'Deger': str(fdata['value'])
            })
        st.dataframe(pd.DataFrame(factor_data), use_container_width=True, hide_index=True)


def render_clickable_card(symbol, price, change, sent_puan, karar, market='BIST', key_prefix='card'):
    """Tiklanabilir hisse karti — tiklaninca grafik acar."""
    if change > 0: border = "#2e7d32"; arrow = "📈"
    elif change < 0: border = "#c62828"; arrow = "📉"
    else: border = "#f57c00"; arrow = "➡️"
    chg_color = "#2e7d32" if change >= 0 else "#c62828"
    cur = "₺" if market == 'BIST' else "$"

    st.markdown(f'<div style="border:2px solid {border};border-radius:10px;padding:12px;margin-bottom:8px">'
                f'<div style="font-weight:700;font-size:14px">{arrow} {symbol}</div>'
                f'<div style="color:{chg_color};font-weight:700;font-size:16px;margin-top:4px">{cur}{price:.2f}</div>'
                f'<div style="color:{chg_color};font-size:13px">{change:+.2f}%</div>'
                f'<div style="color:#666;font-size:11px;margin-top:2px">Sent: {sent_puan:.1f} | {karar}</div>'
                f'</div>', unsafe_allow_html=True)

    if st.button(f"📈 Grafik", key=f"{key_prefix}_{symbol}", use_container_width=True):
        st.session_state.chart_symbol = symbol
        st.session_state.chart_market = market
        st.rerun()


# ============================================================
# AI TAHMIN
# ============================================================
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


# ============================================================
# FAVORILER
# ============================================================
if 'favorites' not in st.session_state:
    st.session_state.favorites = ['THYAO', 'ASELS', 'GARAN', 'BTC/USDT']


# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("### 🌊 SentiFlow v5.0")
    st.caption("Multi-Factor Sentiment Platform")
    st.markdown("---")
    page = st.selectbox("Sayfa", [
        "🏠 Ana Sayfa", "📊 Hisse Analiz", "🪙 Kripto Analiz", "🧠 AI Tahmin",
        "🟢 Aktif Degisimler", "📊 Grid Grafik", "🎯 Dip Donusu", "📈 Backtest",
        "📋 Haftalik Rapor", "📐 Fibonacci/Bollinger", "📐 Formasyonlar",
        "📰 AI Gunluk Yorum", "🔴 Divergence", "📊 10 Gun Heatmap",
        "🔔 Sinyal Merkezi", "⭐ Favorilerim", "🔥 Heatmap", "⚔️ Karsilastir",
        "🏆 Gunun En Iyileri", "💼 Portfolyo", "🎯 Destek/Direnc",
        "🕐 Piyasa Saati", "🇺🇸 S&P / NASDAQ", "🇪🇺 Avrupa", "🥇 Altin & Doviz",
        "📰 KAP Haberleri", "📋 Hisse Tablosu", "🪙 Kripto Top 10",
        "🔍 Akilli Filtre", "📈 Gunluk Sentiment", "🔄 Osilator",
        "📋 BIST30 Ilk 10", "📋 BIST30 Son 10"
    ])
    st.markdown("---")
    # Sentiment Ozet (sidebar)
    st.markdown("**📊 Hizli Ozet**")
    try:
        all_s = get_all_bist_scores()
        if not all_s.empty:
            avg = all_s['Sent.Puan'].mean()
            if avg >= 6: st.markdown(f"🟢 Piyasa: **{avg:.1f}** (Pozitif)")
            elif avg >= 4: st.markdown(f"🟡 Piyasa: **{avg:.1f}** (Notr)")
            else: st.markdown(f"🔴 Piyasa: **{avg:.1f}** (Negatif)")
    except:
        pass
    st.markdown("---")
    st.markdown("""<div style="background:linear-gradient(135deg,#ff8f00,#ff6f00);border-radius:10px;padding:12px;text-align:center">
        <div style="font-size:14px;font-weight:700;color:white">⭐ PRO'ya Gec</div>
        <div style="font-size:11px;color:rgba(255,255,255,0.85)">Canli uyari + AI rapor + Oncelikli destek</div>
    </div>""", unsafe_allow_html=True)


# ============================================================
# GRAFIK POPUP (session_state ile)
# ============================================================
if st.session_state.chart_symbol:
    st.markdown("---")
    col_back, col_title = st.columns([1, 5])
    with col_back:
        if st.button("← Geri"):
            st.session_state.chart_symbol = None
            st.rerun()
    with col_title:
        st.markdown(f"### 📈 {st.session_state.chart_symbol} Detay Grafik")
    show_chart_popup(st.session_state.chart_symbol, st.session_state.chart_market)
    st.stop()
# ============================================================
# SAYFA: ANA SAYFA
# ============================================================
if page == "🏠 Ana Sayfa":
    now = get_turkey_time()
    st.markdown(f'<div style="text-align:right;margin-bottom:10px"><span style="background:#2e7d32;color:white;padding:4px 10px;border-radius:12px;font-size:11px;font-weight:600">🟢 CANLI | {now.strftime("%H:%M")}</span></div>', unsafe_allow_html=True)

    # Ust Ticker Bandi
    try:
        xu100 = yf.Ticker("XU100.IS").history(period="2d")
        xu030 = yf.Ticker("XU030.IS").history(period="2d")
        usd_try = yf.Ticker("USDTRY=X").history(period="2d")
        eur_try = yf.Ticker("EURTRY=X").history(period="2d")
        gold = yf.Ticker("GC=F").history(period="2d")
        btc = yf.Ticker("BTC-USD").history(period="2d")
        xu100_price = float(xu100['Close'].iloc[-1]) if not xu100.empty else 0
        xu100_chg = ((float(xu100['Close'].iloc[-1]) - float(xu100['Close'].iloc[-2])) / float(xu100['Close'].iloc[-2]) * 100) if len(xu100) >= 2 else 0
        xu030_price = float(xu030['Close'].iloc[-1]) if not xu030.empty else 0
        xu030_chg = ((float(xu030['Close'].iloc[-1]) - float(xu030['Close'].iloc[-2])) / float(xu030['Close'].iloc[-2]) * 100) if len(xu030) >= 2 else 0
        usd_price = float(usd_try['Close'].iloc[-1]) if not usd_try.empty else 0
        usd_chg = ((float(usd_try['Close'].iloc[-1]) - float(usd_try['Close'].iloc[-2])) / float(usd_try['Close'].iloc[-2]) * 100) if len(usd_try) >= 2 else 0
        eur_price = float(eur_try['Close'].iloc[-1]) if not eur_try.empty else 0
        eur_chg = ((float(eur_try['Close'].iloc[-1]) - float(eur_try['Close'].iloc[-2])) / float(eur_try['Close'].iloc[-2]) * 100) if len(eur_try) >= 2 else 0
        gold_price = float(gold['Close'].iloc[-1]) if not gold.empty else 0
        gold_chg = ((float(gold['Close'].iloc[-1]) - float(gold['Close'].iloc[-2])) / float(gold['Close'].iloc[-2]) * 100) if len(gold) >= 2 else 0
        btc_price = float(btc['Close'].iloc[-1]) if not btc.empty else 0
        btc_chg = ((float(btc['Close'].iloc[-1]) - float(btc['Close'].iloc[-2])) / float(btc['Close'].iloc[-2]) * 100) if len(btc) >= 2 else 0
    except:
        xu100_price = xu100_chg = xu030_price = xu030_chg = usd_price = usd_chg = eur_price = eur_chg = gold_price = gold_chg = btc_price = btc_chg = 0

    def ticker_color(val):
        return "#2e7d32" if val >= 0 else "#c62828"

    st.markdown(f"""<div style="background:#1a237e;border-radius:10px;padding:12px 20px;margin-bottom:20px;display:flex;justify-content:space-around;flex-wrap:wrap;gap:8px">
        <div style="text-align:center"><span style="color:#90caf9;font-size:11px">BIST100</span><br><span style="color:white;font-weight:700">{xu100_price:,.0f}</span> <span style="color:{ticker_color(xu100_chg)};font-size:12px">({xu100_chg:+.1f}%)</span></div>
        <div style="text-align:center"><span style="color:#90caf9;font-size:11px">BIST30</span><br><span style="color:white;font-weight:700">{xu030_price:,.0f}</span> <span style="color:{ticker_color(xu030_chg)};font-size:12px">({xu030_chg:+.1f}%)</span></div>
        <div style="text-align:center"><span style="color:#90caf9;font-size:11px">USD/TRY</span><br><span style="color:white;font-weight:700">{usd_price:.4f}</span> <span style="color:{ticker_color(usd_chg)};font-size:12px">({usd_chg:+.1f}%)</span></div>
        <div style="text-align:center"><span style="color:#90caf9;font-size:11px">EUR/TRY</span><br><span style="color:white;font-weight:700">{eur_price:.4f}</span> <span style="color:{ticker_color(eur_chg)};font-size:12px">({eur_chg:+.1f}%)</span></div>
        <div style="text-align:center"><span style="color:#90caf9;font-size:11px">ALTIN</span><br><span style="color:white;font-weight:700">${gold_price:,.0f}</span> <span style="color:{ticker_color(gold_chg)};font-size:12px">({gold_chg:+.1f}%)</span></div>
        <div style="text-align:center"><span style="color:#90caf9;font-size:11px">BTC</span><br><span style="color:white;font-weight:700">${btc_price:,.0f}</span> <span style="color:{ticker_color(btc_chg)};font-size:12px">({btc_chg:+.1f}%)</span></div>
    </div>""", unsafe_allow_html=True)

    # Piyasa Ozeti Kartlari
    all_scores = get_all_bist_scores()
    if not all_scores.empty:
        all_scores = all_scores.fillna(0)
        greens = len(all_scores[all_scores['Sentiment'] > 10])
        reds = len(all_scores[all_scores['Sentiment'] < -10])
        yellows = len(all_scores) - greens - reds
        avg_sent = all_scores['Sent.Puan'].mean()
        if avg_sent > 6: piyasa_emoji = "🟢"; piyasa_text = "GUCLU"
        elif avg_sent > 4: piyasa_emoji = "🟢"; piyasa_text = "POZITIF"
        elif avg_sent > 3: piyasa_emoji = "🟡"; piyasa_text = "NOTR"
        else: piyasa_emoji = "🔴"; piyasa_text = "NEGATIF"

        st.markdown(f"""<div style="display:flex;gap:12px;margin-bottom:20px;flex-wrap:wrap">
            <div style="flex:1;min-width:140px;background:linear-gradient(135deg,#e8f5e9,#c8e6c9);border-radius:12px;padding:16px;text-align:center;box-shadow:0 2px 8px rgba(0,0,0,0.08)">
                <div style="font-size:28px;font-weight:800;color:#2e7d32">{greens}</div>
                <div style="color:#2e7d32;font-size:13px;font-weight:600">🟢 Yukselen</div>
            </div>
            <div style="flex:1;min-width:140px;background:linear-gradient(135deg,#ffebee,#ffcdd2);border-radius:12px;padding:16px;text-align:center;box-shadow:0 2px 8px rgba(0,0,0,0.08)">
                <div style="font-size:28px;font-weight:800;color:#c62828">{reds}</div>
                <div style="color:#c62828;font-size:13px;font-weight:600">🔴 Dusen</div>
            </div>
            <div style="flex:1;min-width:140px;background:linear-gradient(135deg,#fff8e1,#ffecb3);border-radius:12px;padding:16px;text-align:center;box-shadow:0 2px 8px rgba(0,0,0,0.08)">
                <div style="font-size:28px;font-weight:800;color:#f57c00">{yellows}</div>
                <div style="color:#f57c00;font-size:13px;font-weight:600">🟡 Notr</div>
            </div>
            <div style="flex:1;min-width:140px;background:linear-gradient(135deg,#e3f2fd,#bbdefb);border-radius:12px;padding:16px;text-align:center;box-shadow:0 2px 8px rgba(0,0,0,0.08)">
                <div style="font-size:28px;font-weight:800;color:#1565c0">{piyasa_emoji} {piyasa_text}</div>
                <div style="color:#1565c0;font-size:13px;font-weight:600">Piyasa Durumu</div>
            </div>
        </div>""", unsafe_allow_html=True)

        # BIST30 / BIST70 / BIST100 Sekmeleri
        st.markdown("---")
        bist_tab = st.radio("Endeks:", ["BIST30", "BIST70", "BIST100 (Tumu)"], horizontal=True, key="bist_tab_home")
        if bist_tab == "BIST30": show_symbols = list(BIST30.keys())
        elif bist_tab == "BIST70": show_symbols = list(BIST100_EXTRA.keys())
        else: show_symbols = list(ALL_BIST.keys())

        # Hisse Kartlari — TIKLANABILIR
        cols_per_row = 4
        shown_scores = all_scores[all_scores['Sembol'].isin(show_symbols)].sort_values('Gun%', ascending=False).reset_index(drop=True)
        for i in range(0, min(len(shown_scores), 20), cols_per_row):
            cols = st.columns(cols_per_row)
            for j in range(cols_per_row):
                if i + j < min(len(shown_scores), 20):
                    row = shown_scores.iloc[i + j]
                    with cols[j]:
                        chg = row['Gun%']
                        if chg > 0: border = "#2e7d32"; arrow = "📈"
                        elif chg < 0: border = "#c62828"; arrow = "📉"
                        else: border = "#f57c00"; arrow = "➡️"
                        chg_color = "#2e7d32" if chg >= 0 else "#c62828"
                        st.markdown(f'<div style="border:2px solid {border};border-radius:10px;padding:12px;margin-bottom:4px"><div style="font-weight:700;font-size:14px">{arrow} {row["Sembol"]}</div><div style="color:{chg_color};font-weight:700;font-size:16px;margin-top:4px">₺{row["Fiyat"]:.2f}</div><div style="color:{chg_color};font-size:13px">{chg:+.2f}%</div><div style="color:#666;font-size:11px;margin-top:2px">Sent: {row["Sent.Puan"]:.1f} | {row["Karar"]}</div></div>', unsafe_allow_html=True)
                        if st.button("📈", key=f"home_{row['Sembol']}_{i}_{j}", help="Grafik ac"):
                            st.session_state.chart_symbol = row['Sembol']
                            st.session_state.chart_market = 'BIST'
                            st.rerun()

        # Hisse Detay
        st.markdown("---")
        st.markdown("### 📈 Hisse Detay")
        detail_sym = st.selectbox("Hisse sec:", show_symbols, key="home_detail")
        if detail_sym:
            show_chart_popup(detail_sym, 'BIST')

        # Gunun Yildizlari
        st.markdown("---")
        st.markdown("### ⭐ Gunun Yildizlari")
        top5 = all_scores.sort_values('Gun%', ascending=False).head(5).fillna(0)
        bot5 = all_scores.sort_values('Gun%', ascending=True).head(5).fillna(0)
        col_top, col_bot = st.columns(2)
        with col_top:
            st.markdown("**📈 En Cok Yukselenler**")
            for idx, (_, row) in enumerate(top5.iterrows()):
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.markdown(f'<div style="background:#f1f8e9;border-radius:8px;padding:10px;margin-bottom:6px;display:flex;justify-content:space-between;align-items:center"><span style="font-weight:600">{row["Sembol"]}</span><span style="color:#2e7d32;font-weight:700">{row["Gun%"]:+.2f}%</span></div>', unsafe_allow_html=True)
                with c2:
                    if st.button("📈", key=f"top_{row['Sembol']}_{idx}"):
                        st.session_state.chart_symbol = row['Sembol']
                        st.session_state.chart_market = 'BIST'
                        st.rerun()
        with col_bot:
            st.markdown("**📉 En Cok Dusenler**")
            for idx, (_, row) in enumerate(bot5.iterrows()):
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.markdown(f'<div style="background:#fce4ec;border-radius:8px;padding:10px;margin-bottom:6px;display:flex;justify-content:space-between;align-items:center"><span style="font-weight:600">{row["Sembol"]}</span><span style="color:#c62828;font-weight:700">{row["Gun%"]:+.2f}%</span></div>', unsafe_allow_html=True)
                with c2:
                    if st.button("📈", key=f"bot_{row['Sembol']}_{idx}"):
                        st.session_state.chart_symbol = row['Sembol']
                        st.session_state.chart_market = 'BIST'
                        st.rerun()

        # Dip Donusu Sinyalleri
        st.markdown("---")
        st.markdown("### 🎯 Dip Donusu Sinyalleri")
        dip_list = []
        for symbol in ALL_BIST.keys():
            try:
                df = get_bist_data(symbol)
                if df is not None and not df.empty and len(df) >= 20:
                    close = df['Close']
                    rsi_val = float(momentum.RSIIndicator(close, window=14).rsi().iloc[-1])
                    macd_hist = trend.MACD(close).macd_diff()
                    macd_now = float(macd_hist.iloc[-1])
                    macd_prev = float(macd_hist.iloc[-2])
                    if rsi_val < 35 and macd_now > macd_prev:
                        dip_list.append(f"{symbol} (RSI: {rsi_val:.0f})")
            except:
                continue
        if dip_list:
            st.markdown(f'<div style="background:#e8f5e9;border:1px solid #2e7d32;border-radius:10px;padding:14px"><strong>🎯 {len(dip_list)} hisse dip donusu sinyali veriyor:</strong><br><span style="color:#2e7d32;font-weight:600">{", ".join(dip_list)}</span></div>', unsafe_allow_html=True)
        else:
            st.info("Su an belirgin dip donusu sinyali yok.")

        # Sentiment Pasta
        st.markdown("---")
        st.markdown("### 📊 Piyasa Sentiment Dagilimi")
        fig_pie = go.Figure(data=[go.Pie(labels=['Yukselen', 'Dusen', 'Notr'], values=[greens, reds, yellows], marker_colors=['#2e7d32', '#c62828', '#f57c00'], hole=0.4)])
        fig_pie.update_layout(height=300, paper_bgcolor='white', showlegend=True)
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("---")
    st.caption(f"Son guncelleme: {now.strftime('%d.%m.%Y %H:%M')} | sentiflow.streamlit.app | Yatirim tavsiyesi degildir.")


# ============================================================
# SAYFA: HISSE ANALIZ
# ============================================================
elif page == "📊 Hisse Analiz":
    st.title("📊 Hisse Sentiment Analizi — v5.0")
    symbol = st.selectbox("Hisse Secin:", list(ALL_BIST.keys()))
    df = get_bist_data(symbol)
    if not df.empty:
        result = calc_sentiment(df)
        if result:
            tab1, tab2, tab3, tab4 = st.tabs(["📈 Grafik", "📋 Tablo", "🔍 Analiz", "📊 Faktorler"])
            with tab1:
                show_chart_popup(symbol, 'BIST')
            with tab2:
                data_table = pd.DataFrame({
                    'Gosterge': ['Fiyat', 'Sent.Puan', 'RSI', 'Stoch', 'MACD', 'Momentum 5G', 'Momentum 10G', 'EMA9', 'EMA21', 'EMA50', 'STP', 'HSTP', 'BB Ust', 'BB Alt', 'Trend', 'Trend Gucu'],
                    'Deger': [f"₺{result['price']:,.2f}", f"{result['sent_puan']:.2f}", f"{result['rsi']:.1f}", f"{result['stoch']:.1f}", f"{result['macd']:.4f}", f"%{result['momentum']:.2f}", f"%{result.get('momentum_10d', 0):.2f}", f"₺{result['ema9']:.2f}", f"₺{result['ema21']:.2f}", f"₺{result['ema50']:.2f}", f"₺{result['stp']}", f"₺{result['hstp']}", f"₺{result.get('bb_upper', 0):.2f}", f"₺{result.get('bb_lower', 0):.2f}", result['trend'], f"{result['trend_strength']}/5"],
                    'Durum': [result['decision'], result['signal'], '🟢' if result['rsi']<30 else '🔴' if result['rsi']>70 else '⚪', '🟢' if result['stoch']<20 else '🔴' if result['stoch']>80 else '⚪', '🟢' if result['macd']>0 else '🔴', '🟢' if result['momentum']>0 else '🔴', '🟢' if result.get('momentum_10d',0)>0 else '🔴', '🟢' if result['price']>result['ema9'] else '🔴', '🟢' if result['price']>result['ema21'] else '🔴', '🟢' if result['price']>result['ema50'] else '🔴', '🟢' if result['price']>result['stp'] else '🔴', '🟢' if result['price']>result['hstp'] else '🔴', '🟢' if result['price']<result.get('bb_upper',999) else '🔴', '🟢' if result['price']>result.get('bb_lower',0) else '🔴', '🟢' if result['trend']=='yukari' else '🔴' if result['trend']=='asagi' else '🟡', f"{'🟢' * result['trend_strength']}"]
                })
                st.dataframe(data_table, use_container_width=True, hide_index=True)
            with tab3:
                dec_color = "#2e7d32" if "AL" in result['decision'] else "#c62828" if "SAT" in result['decision'] else "#f57c00"
                st.markdown(f'<div style="background:{dec_color};color:white;border-radius:12px;padding:25px;text-align:center;margin:20px 0"><h1 style="margin:0;color:white">{result["decision"]}</h1><p style="margin:5px 0 0;font-size:16px;color:rgba(255,255,255,0.9)">{result["signal"]} | Trend: {result["trend"]} ({result["trend_strength"]}/5)</p></div>', unsafe_allow_html=True)
                a1, a2 = st.columns(2)
                with a1:
                    st.markdown("**🟢 Alis Sinyalleri:**")
                    if result['rsi'] < 30: st.write("✅ RSI asiri satim bolgesinde")
                    if result['macd'] > 0: st.write("✅ MACD pozitif")
                    if result['price'] > result['ema21']: st.write("✅ Fiyat EMA21 ustunde")
                    if result['price'] > result['ema50']: st.write("✅ Fiyat EMA50 ustunde")
                    if result['momentum'] > 0: st.write("✅ Momentum pozitif")
                    if result['stoch'] < 20: st.write("✅ Stochastic asiri satim")
                    if result['price'] < result.get('bb_lower', 0): st.write("✅ Bollinger alt bandi altinda")
                with a2:
                    st.markdown("**🔴 Satis Sinyalleri:**")
                    if result['rsi'] > 70: st.write("⚠️ RSI asiri alim bolgesinde")
                    if result['macd'] < 0: st.write("⚠️ MACD negatif")
                    if result['price'] < result['ema21']: st.write("⚠️ Fiyat EMA21 altinda")
                    if result['price'] < result['ema50']: st.write("⚠️ Fiyat EMA50 altinda")
                    if result['momentum'] < 0: st.write("⚠️ Momentum negatif")
                    if result['stoch'] > 80: st.write("⚠️ Stochastic asiri alim")
                    if result['price'] > result.get('bb_upper', 99999): st.write("⚠️ Bollinger ust bandi ustunde")
            with tab4:
                st.markdown("### 📊 Multi-Factor Sentiment Detay")
                if 'factors' in result:
                    # Radar chart
                    factor_names = list(result['factors'].keys())
                    factor_scores = [result['factors'][f]['score'] for f in factor_names]
                    fig_radar = go.Figure()
                    fig_radar.add_trace(go.Scatterpolar(
                        r=[max(0, s) for s in factor_scores],
                        theta=factor_names,
                        fill='toself',
                        name='Pozitif',
                        line_color='#2e7d32',
                        fillcolor='rgba(46,125,50,0.2)'
                    ))
                    fig_radar.add_trace(go.Scatterpolar(
                        r=[abs(min(0, s)) for s in factor_scores],
                        theta=factor_names,
                        fill='toself',
                        name='Negatif',
                        line_color='#c62828',
                        fillcolor='rgba(198,40,40,0.2)'
                    ))
                    fig_radar.update_layout(
                        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                        height=400, paper_bgcolor='white'
                    )
                    st.plotly_chart(fig_radar, use_container_width=True)

                    # Faktor tablosu
                    factor_data = []
                    for fname, fdata in result['factors'].items():
                        weighted = round(fdata['score'] * fdata['weight'], 1)
                        bar_width = abs(fdata['score'])
                        if fdata['score'] > 30: emoji = "🟢"
                        elif fdata['score'] > -30: emoji = "🟡"
                        else: emoji = "🔴"
                        factor_data.append({
                            'Faktor': f"{emoji} {fname}",
                            'Ham Skor': fdata['score'],
                            'Agirlik': f"%{int(fdata['weight']*100)}",
                            'Agirlikli Katki': weighted,
                            'Deger': str(fdata['value'])
                        })
                    st.dataframe(pd.DataFrame(factor_data), use_container_width=True, hide_index=True)
                    st.markdown(f"**Toplam Skor:** {result['score']:.1f} / 100")
                    st.markdown(f"**Sent.Puan:** {result['sent_puan']:.2f} / 10")


# ============================================================
# SAYFA: KRIPTO ANALIZ
# ============================================================
elif page == "🪙 Kripto Analiz":
    st.title("🪙 Kripto Sentiment Analizi — v5.0")
    all_crypto = CRYPTO_BINANCE + CRYPTO_EXTRA
    symbol = st.selectbox("Kripto Secin:", all_crypto)
    df = get_crypto_data(symbol)
    if not df.empty:
        result = calc_sentiment(df)
        if result:
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Fiyat", f"${result['price']:,.4f}" if result['price'] < 1 else f"${result['price']:,.2f}")
            c2.metric("Sentiment", f"{result['sent_puan']:.2f}/10", result['decision'])
            c3.metric("RSI", f"{result['rsi']:.1f}")
            c4.metric("Trend", f"{result['trend']} ({result['trend_strength']}/5)")
            c5.metric("Mom", f"{result['momentum']:.1f}%")
            st.markdown("---")
            show_chart_popup(symbol, 'CRYPTO')
    else:
        st.error(f"'{symbol}' icin veri cekilemedi!")


# ============================================================
# SAYFA: AI TAHMIN
# ============================================================
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
                    if rsi_v < 40: ts += 3
                    elif rsi_v > 60: ts -= 3
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
                r1, r2, r3, r4 = st.columns(4)
                r1.metric("Fiyat", f"{r['price']:,.2f}")
                r2.metric("Hedef", f"{r['target_price']:,.2f}", f"%{r['target_pct']}")
                r3.metric("Destek", f"{r['support']:,.2f}")
                r4.metric("Direnc", f"{r['resistance']:,.2f}")
                # Grafik goster
                st.markdown("---")
                if market_ai == "BIST":
                    show_chart_popup(symbol_ai, 'BIST')
                else:
                    show_chart_popup(symbol_ai, 'CRYPTO')
                st.warning("Bu tahmin yatirim tavsiyesi degildir.")
            else:
                st.error("Tahmin yapilamadi.")


# ============================================================
# SAYFA: AKTIF DEGISIMLER
# ============================================================
elif page == "🟢 Aktif Degisimler":
    st.title("🟢 Aktif Degisimler")
    all_scores = get_all_bist_scores()
    if not all_scores.empty:
        greens = all_scores[all_scores['Sentiment'] > 10]
        reds = all_scores[all_scores['Sentiment'] < -10]
        yellows = all_scores[(all_scores['Sentiment'] >= -10) & (all_scores['Sentiment'] <= 10)]
        total = len(all_scores)

        st.markdown(f"""<div style="display:flex;gap:10px;margin-bottom:20px">
            <div style="background:#2e7d32;color:white;padding:8px 16px;border-radius:20px;font-weight:700">{len(greens)}/{total} 🟢</div>
            <div style="background:#c62828;color:white;padding:8px 16px;border-radius:20px;font-weight:700">{len(reds)}/{total} 🔴</div>
            <div style="background:#f9a825;color:white;padding:8px 16px;border-radius:20px;font-weight:700">{len(yellows)}/{total} 🟡</div>
        </div>""", unsafe_allow_html=True)

        filter_type = st.radio("Filtre:", ["Tum", "Yesiller", "Kirmizilar", "Sarilar"], horizontal=True)
        if filter_type == "Yesiller": show_df = greens
        elif filter_type == "Kirmizilar": show_df = reds
        elif filter_type == "Sarilar": show_df = yellows
        else: show_df = all_scores

        if not show_df.empty:
            show_df_sorted = show_df.sort_values('Sentiment', ascending=False).reset_index(drop=True)
            cols_per_row = 3
            for i in range(0, len(show_df_sorted), cols_per_row):
                cols = st.columns(cols_per_row)
                for j in range(cols_per_row):
                    if i + j < len(show_df_sorted):
                        row = show_df_sorted.iloc[i + j]
                        with cols[j]:
                            if row['Sentiment'] > 10: border_color = "#2e7d32"
                            elif row['Sentiment'] < -10: border_color = "#c62828"
                            else: border_color = "#f9a825"
                            chg_color = "#2e7d32" if row['Gun%'] >= 0 else "#c62828"
                            st.markdown(f'<div style="border:2px solid {border_color};border-radius:10px;padding:12px;margin-bottom:4px"><div style="display:flex;justify-content:space-between;align-items:center"><span style="font-weight:700;font-size:15px">{i+j+1}. {row["Sembol"]}</span><span style="color:{chg_color};font-weight:700">%{row["Gun%"]:.2f}</span></div><div style="color:#666;font-size:13px;margin-top:4px">₺{row["Fiyat"]} | Sent: {row["Sent.Puan"]:.1f} | {row["Karar"]}</div></div>', unsafe_allow_html=True)
                            if st.button("📈", key=f"aktif_{row['Sembol']}_{i}_{j}"):
                                st.session_state.chart_symbol = row['Sembol']
                                st.session_state.chart_market = 'BIST'
                                st.rerun()


# ============================================================
# SAYFA: KAP HABERLERI (CANLI v5.0)
# ============================================================
elif page == "📰 KAP Haberleri":
    st.title("📰 KAP Haberleri — Canlı")
    st.caption("Otomatik guncellenen haberler")

    if st.button("🔄 Yenile", type="primary"):
        st.cache_data.clear()
        st.rerun()

    news = get_kap_news()
    for item in news:
        source_color = "#1565c0" if item.get('source') == 'KAP' else "#ff8f00" if item.get('source') == 'BigPara' else "#7b1fa2"
        link_html = f' <a href="{item["link"]}" target="_blank" style="color:#1565c0;font-size:11px">↗ Devami</a>' if item.get('link') else ''
        st.markdown(f'<div style="background:white;border-radius:10px;padding:16px;margin-bottom:12px;border:1px solid #eee;border-left:4px solid {source_color}"><div style="display:flex;justify-content:space-between;margin-bottom:6px"><span style="background:{source_color};color:white;padding:2px 8px;border-radius:4px;font-size:12px">{item["symbol"]}</span><span style="color:#999;font-size:12px">{item["date"]} | {item.get("source", "")}</span></div><div style="font-size:14px;color:#333">{item["title"]}{link_html}</div></div>', unsafe_allow_html=True)

        # Haber sembolune tikla → grafik
        if item['symbol'] in ALL_BIST:
            if st.button(f"📈 {item['symbol']} Grafik", key=f"kap_{item['symbol']}_{item['title'][:20]}"):
                st.session_state.chart_symbol = item['symbol']
                st.session_state.chart_market = 'BIST'
                st.rerun()


# ============================================================
# SAYFA: SINYAL MERKEZI
# ============================================================
elif page == "🔔 Sinyal Merkezi":
    st.title("🔔 Sinyal Merkezi")
    st.caption("Tum AL / SAT / TUT sinyalleri — tikla grafik ac")
    sinyal_tab1, sinyal_tab2, sinyal_tab3 = st.tabs(["BIST", "Kripto", "ABD & Avrupa"])

    with sinyal_tab1:
        all_scores = get_all_bist_scores()
        if not all_scores.empty:
            al_s = all_scores[all_scores['Karar'].str.contains('AL')]
            sat_s = all_scores[all_scores['Karar'].str.contains('SAT')]
            tut_s = all_scores[all_scores['Karar'].str.contains('TUT')]

            st.markdown(f"### 🟢 AL ({len(al_s)})")
            if not al_s.empty:
                st.dataframe(al_s[['Sembol','Fiyat','Gun%','Sent.Puan','Momentum%','Trend','TrendGuc']].reset_index(drop=True), use_container_width=True)
                sel_al = st.selectbox("Grafik ac:", al_s['Sembol'].tolist(), key="sinyal_al")
                if st.button("📈 Grafik Goster", key="sinyal_al_btn"):
                    st.session_state.chart_symbol = sel_al
                    st.session_state.chart_market = 'BIST'
                    st.rerun()

            st.markdown(f"### 🔴 SAT ({len(sat_s)})")
            if not sat_s.empty:
                st.dataframe(sat_s[['Sembol','Fiyat','Gun%','Sent.Puan','Momentum%','Trend','TrendGuc']].reset_index(drop=True), use_container_width=True)

            st.markdown(f"### 🟡 TUT ({len(tut_s)})")
            if not tut_s.empty:
                st.dataframe(tut_s[['Sembol','Fiyat','Gun%','Sent.Puan','Momentum%','Trend','TrendGuc']].reset_index(drop=True), use_container_width=True)

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
                if r: intl_results.append({'Sembol': name, 'Fiyat': round(r['price'],2), 'Gun%': r['daily_change'], 'Sent.Puan': r['sent_puan'], 'Trend': r['trend'], 'Karar': r['decision']})
            except:
                continue
        if intl_results:
            intl_df = pd.DataFrame(intl_results)
            st.dataframe(intl_df, use_container_width=True, hide_index=True)
            sel_intl = st.selectbox("Grafik ac:", [r['Sembol'] for r in intl_results], key="sinyal_intl")
            if st.button("📈 Grafik Goster", key="sinyal_intl_btn"):
                st.session_state.chart_symbol = sel_intl
                st.session_state.chart_market = 'INTL'
                st.rerun()


# ============================================================
# SAYFA: HISSE TABLOSU (Tiklanabilir)
# ============================================================
elif page == "📋 Hisse Tablosu":
    st.title("📋 Hisse Tablosu — v5.0")
    all_scores = get_all_bist_scores()
    if not all_scores.empty:
        f1, f2 = st.columns(2)
        with f1: sort_by = st.selectbox("Sirala:", ['Sent.Puan', 'Sentiment', 'Momentum%', 'Mom10%', 'Hacim%', 'RSI', 'Gun%', 'TrendGuc'])
        with f2: sort_order = st.radio("Sira:", ['En Yuksek', 'En Dusuk'], horizontal=True)
        sorted_df = all_scores.sort_values(sort_by, ascending=(sort_order=='En Dusuk')).reset_index(drop=True)
        sorted_df.index = sorted_df.index + 1
        st.dataframe(sorted_df, use_container_width=True, height=500)

        # Grafik ac
        st.markdown("---")
        sel_tablo = st.selectbox("Hisse sec → Grafik ac:", sorted_df['Sembol'].tolist(), key="tablo_sel")
        if st.button("📈 Grafik Ac", key="tablo_btn", type="primary"):
            st.session_state.chart_symbol = sel_tablo
            st.session_state.chart_market = 'BIST'
            st.rerun()
            
# ============================================================
# SAYFA: GRID GRAFIK
# ============================================================
elif page == "📊 Grid Grafik":
    st.title("📊 Grid Grafik — Coklu Hisse")
    st.caption("6 hisseyi ayni anda izle (Fiyat + STP + HSTP + BB)")
    default_symbols = ['THYAO', 'ASELS', 'GARAN', 'AKBNK', 'EREGL', 'TUPRS']
    selected = st.multiselect("Hisse Sec (max 6):", list(ALL_BIST.keys()), default=default_symbols, max_selections=6)
    if selected:
        cols_per_row = 3 if len(selected) > 3 else len(selected)
        rows_needed = (len(selected) + cols_per_row - 1) // cols_per_row
        for row_i in range(rows_needed):
            cols = st.columns(cols_per_row)
            for col_i in range(cols_per_row):
                idx = row_i * cols_per_row + col_i
                if idx < len(selected):
                    sym = selected[idx]
                    with cols[col_i]:
                        df = get_bist_data(sym)
                        if not df.empty and len(df) >= 20:
                            close = df['Close']
                            price = float(close.iloc[-1])
                            prev = float(close.iloc[-2])
                            chg = ((price - prev) / prev) * 100
                            chg_color = "#2e7d32" if chg >= 0 else "#c62828"
                            fig = go.Figure()
                            fig.add_trace(go.Scatter(y=close.tolist()[-60:], name='Fiyat', line=dict(color='#2e7d32', width=2)))
                            stp_vals = close.rolling(20).mean().tolist()[-60:]
                            fig.add_trace(go.Scatter(y=stp_vals, name='STP', line=dict(color='#ff8f00', width=1.5, dash='dash')))
                            if len(close) >= 50:
                                hstp_vals = close.rolling(50).mean().tolist()[-60:]
                                fig.add_trace(go.Scatter(y=hstp_vals, name='HSTP', line=dict(color='#c62828', width=1.5, dash='dot')))
                            fig.update_layout(height=200, margin=dict(l=5,r=5,t=5,b=5), showlegend=False, paper_bgcolor='white', plot_bgcolor='white')
                            fig.update_xaxes(showticklabels=False, showgrid=False)
                            fig.update_yaxes(showticklabels=False, showgrid=False)
                            st.markdown(f'<div style="text-align:center;font-weight:700;font-size:14px">{sym} <span style="color:{chg_color}">₺{price:.2f} ({chg:+.1f}%)</span></div>', unsafe_allow_html=True)
                            st.plotly_chart(fig, use_container_width=True, key=f"grid_{sym}")
                            if st.button("📈 Detay", key=f"grid_btn_{sym}"):
                                st.session_state.chart_symbol = sym
                                st.session_state.chart_market = 'BIST'
                                st.rerun()


# ============================================================
# SAYFA: DIP DONUSU
# ============================================================
elif page == "🎯 Dip Donusu":
    st.title("🎯 Dip Donusu Yapabilecek Hisseler")
    st.caption("RSI asiri satim + MACD yukari donuyor + Fiyat destek yakininda")
    all_scores = get_all_bist_scores()
    if not all_scores.empty:
        dip_candidates = []
        for symbol in ALL_BIST.keys():
            try:
                df = get_bist_data(symbol)
                if df is not None and not df.empty and len(df) >= 20:
                    close = df['Close']
                    rsi_val = float(momentum.RSIIndicator(close, window=14).rsi().iloc[-1])
                    macd_hist = trend.MACD(close).macd_diff()
                    macd_now = float(macd_hist.iloc[-1])
                    macd_prev = float(macd_hist.iloc[-2])
                    price = float(close.iloc[-1])
                    low20 = float(close.iloc[-20:].min())
                    dist_to_low = ((price - low20) / low20) * 100
                    if rsi_val < 40 and macd_now > macd_prev and dist_to_low < 5:
                        dip_candidates.append({'Sembol': symbol, 'Fiyat': price, 'RSI': round(rsi_val, 1), 'MACD Yon': '📈 Yukari', 'Dip Uzaklik': f"%{dist_to_low:.1f}", 'Guc': round((40 - rsi_val) + (macd_now - macd_prev) * 100, 1)})
            except:
                continue
        if dip_candidates:
            dip_df = pd.DataFrame(dip_candidates).sort_values('Guc', ascending=False)
            st.markdown(f"### 🎯 {len(dip_df)} Adet Dip Donusu Adayi Bulundu!")
            for i, (_, row) in enumerate(dip_df.iterrows()):
                col_info, col_btn = st.columns([5, 1])
                with col_info:
                    st.markdown(f'<div style="background:#e8f5e9;border-left:4px solid #2e7d32;border-radius:8px;padding:14px;margin-bottom:8px"><div style="display:flex;justify-content:space-between;align-items:center"><div><strong style="font-size:16px">{i+1}. {row["Sembol"]}</strong><br><span style="color:#666">₺{row["Fiyat"]:.2f} | RSI: {row["RSI"]} | {row["MACD Yon"]} | Dip: {row["Dip Uzaklik"]}</span></div><div style="background:#2e7d32;color:white;padding:6px 14px;border-radius:20px;font-weight:700">Guc: {row["Guc"]}</div></div></div>', unsafe_allow_html=True)
                with col_btn:
                    if st.button("📈", key=f"dip_{row['Sembol']}_{i}"):
                        st.session_state.chart_symbol = row['Sembol']
                        st.session_state.chart_market = 'BIST'
                        st.rerun()
        else:
            st.info("Su an dip donusu adayi bulunamadi.")


# ============================================================
# SAYFA: BACKTEST
# ============================================================
elif page == "📈 Backtest":
    st.title("📈 Backtest — Sinyal Performansi")
    st.caption("Gecmis sinyallerin basari orani (v5.0 multi-factor)")
    bt_sym = st.selectbox("Hisse:", list(ALL_BIST.keys()), key="bt_sym")
    if st.button("📈 Backtest Yap", type="primary"):
        with st.spinner("Gecmis analiz ediliyor..."):
            df = yf.Ticker(ALL_BIST[bt_sym]).history(period="6mo", interval="1d")
            if not df.empty and len(df) >= 50:
                close = df['Close']
                high = df['High']
                low = df['Low']
                rsi_series = momentum.RSIIndicator(close, window=14).rsi()
                macd_series = trend.MACD(close).macd_diff()
                stoch_series = momentum.StochasticOscillator(high, low, close).stoch()
                signals = []
                for i in range(20, len(close) - 5):
                    rsi_v = float(rsi_series.iloc[i])
                    macd_v = float(macd_series.iloc[i])
                    stoch_v = float(stoch_series.iloc[i]) if not pd.isna(stoch_series.iloc[i]) else 50
                    price_entry = float(close.iloc[i])
                    price_5d = float(close.iloc[min(i+5, len(close)-1)])
                    ret_5d = ((price_5d - price_entry) / price_entry) * 100
                    # v5.0 multi-factor sinyal
                    score = 0
                    if rsi_v < 30: score += 3
                    if macd_v > 0: score += 2
                    if stoch_v < 20: score += 2
                    if rsi_v > 70: score -= 3
                    if macd_v < 0: score -= 2
                    if stoch_v > 80: score -= 2
                    if score >= 5:
                        signals.append({'Tarih': df.index[i].strftime('%d.%m.%Y'), 'Tip': '🟢 AL', 'Giris': round(price_entry, 2), '5 Gun Sonra': round(price_5d, 2), 'Getiri%': round(ret_5d, 2), 'Skor': score})
                    elif score <= -5:
                        signals.append({'Tarih': df.index[i].strftime('%d.%m.%Y'), 'Tip': '🔴 SAT', 'Giris': round(price_entry, 2), '5 Gun Sonra': round(price_5d, 2), 'Getiri%': round(-ret_5d, 2), 'Skor': score})
                if signals:
                    sig_df = pd.DataFrame(signals)
                    total = len(sig_df)
                    win = len(sig_df[sig_df['Getiri%'] > 0])
                    lose = total - win
                    avg_ret = sig_df['Getiri%'].mean()
                    win_rate = (win / total) * 100
                    wr_color = "#2e7d32" if win_rate >= 50 else "#c62828"
                    st.markdown(f'<div style="background:{wr_color};color:white;border-radius:12px;padding:20px;text-align:center;margin-bottom:20px"><h2 style="margin:0;color:white">Basari Orani: %{win_rate:.0f}</h2><p style="color:rgba(255,255,255,0.9)">Toplam {total} sinyal | {win} basarili | {lose} basarisiz | Ort. Getiri: %{avg_ret:.2f}</p></div>', unsafe_allow_html=True)
                    st.dataframe(sig_df, use_container_width=True, hide_index=True)
                    # Grafik
                    st.markdown("---")
                    show_chart_popup(bt_sym, 'BIST')
                else:
                    st.info(f"{bt_sym} icin son 6 ayda guclu sinyal bulunamadi.")
            else:
                st.error("Yeterli veri yok.")


# ============================================================
# SAYFA: HAFTALIK RAPOR
# ============================================================
elif page == "📋 Haftalik Rapor":
    st.title("📋 Haftalik Sentiment Degerlendirmesi")
    all_scores = get_all_bist_scores()
    if not all_scores.empty:
        top7 = all_scores.sort_values('Sent.Puan', ascending=False).head(7)
        bot7 = all_scores.sort_values('Sent.Puan', ascending=True).head(7)
        greens = all_scores[all_scores['Sentiment'] > 10]
        reds = all_scores[all_scores['Sentiment'] < -10]
        yellows = all_scores[(all_scores['Sentiment'] >= -10) & (all_scores['Sentiment'] <= 10)]
        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown("### 🏆 Haftalik Yedili (En Guclu)")
            for i, (_, row) in enumerate(top7.iterrows()):
                st.markdown(f'<div style="background:#e8f5e9;border-radius:8px;padding:10px;margin-bottom:6px;display:flex;justify-content:space-between"><span><strong>{i+1}. {row["Sembol"]}</strong></span><span style="color:#2e7d32;font-weight:700">%{row["Gun%"]:.2f} | Sent: {row["Sent.Puan"]:.1f}</span></div>', unsafe_allow_html=True)
        with col_r:
            st.markdown("### ⚠️ En Zayiflar")
            for i, (_, row) in enumerate(bot7.iterrows()):
                st.markdown(f'<div style="background:#ffebee;border-radius:8px;padding:10px;margin-bottom:6px;display:flex;justify-content:space-between"><span><strong>{i+1}. {row["Sembol"]}</strong></span><span style="color:#c62828;font-weight:700">%{row["Gun%"]:.2f} | Sent: {row["Sent.Puan"]:.1f}</span></div>', unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("### 🤖 AI Haftalik Yorum")
        best = top7.iloc[0]
        worst = bot7.iloc[0]
        avg_sent = all_scores['Sent.Puan'].mean()
        if avg_sent > 6: piyasa_durum = "guclu yukselis trendinde"
        elif avg_sent > 4: piyasa_durum = "pozitif bir seyir izliyor"
        elif avg_sent > 3: piyasa_durum = "notr bir gorunum sergiliyor"
        else: piyasa_durum = "baski altinda"
        yorum = f"**Haftalik Degerlendirme:**\n\nBIST piyasasi bu hafta {piyasa_durum}. "
        yorum += f"Toplam {len(all_scores)} hissenin **{len(greens)} tanesi yesil**, {len(reds)} tanesi kirmizi, {len(yellows)} tanesi sari bolgede.\n\n"
        yorum += f"**Haftanin Yildizi:** {best['Sembol']} (Sent: {best['Sent.Puan']:.1f}, %{best['Gun%']:.2f})\n\n"
        yorum += f"**En Zayif:** {worst['Sembol']} (Sent: {worst['Sent.Puan']:.1f}, %{worst['Gun%']:.2f})\n\n"
        yorum += f"**Ortalama Sentiment:** {avg_sent:.2f}/10"
        st.markdown(yorum)

        # Grafik acma
        st.markdown("---")
        sel_h = st.selectbox("Hisse grafik ac:", all_scores['Sembol'].tolist(), key="hafta_sel")
        if st.button("📈 Grafik", key="hafta_btn"):
            st.session_state.chart_symbol = sel_h
            st.session_state.chart_market = 'BIST'
            st.rerun()


# ============================================================
# SAYFA: FIBONACCI / BOLLINGER
# ============================================================
elif page == "📐 Fibonacci/Bollinger":
    st.title("📐 Fibonacci & Bollinger Bands")
    fib_market = st.radio("Piyasa:", ["BIST", "Kripto"], horizontal=True, key="fib_m")
    if fib_market == "BIST":
        fib_sym = st.selectbox("Hisse:", list(ALL_BIST.keys()), key="fib_sym")
        df_fib = get_bist_data(fib_sym)
        cur = "₺"
    else:
        fib_sym = st.selectbox("Kripto:", CRYPTO_BINANCE + CRYPTO_EXTRA, key="fib_sym_c")
        df_fib = get_crypto_data(fib_sym)
        cur = "$"
    if not df_fib.empty and len(df_fib) >= 20:
        close = df_fib['Close']
        high_max = float(close.max())
        low_min = float(close.min())
        price = float(close.iloc[-1])
        diff = high_max - low_min
        fib_levels = {'%0 (Dip)': low_min, '%23.6': low_min + diff * 0.236, '%38.2': low_min + diff * 0.382, '%50.0': low_min + diff * 0.5, '%61.8': low_min + diff * 0.618, '%78.6': low_min + diff * 0.786, '%100 (Tepe)': high_max}
        bb = volatility.BollingerBands(close, window=20, window_dev=2)
        bb_upper_s = bb.bollinger_hband()
        bb_mid_s = bb.bollinger_mavg()
        bb_lower_s = bb.bollinger_lband()
        st.subheader(f"📐 Fibonacci Seviyeleri — {fib_sym}")
        fib_data = []
        for name, level in fib_levels.items():
            dist = ((level - price) / price) * 100
            fib_data.append({'Seviye': name, 'Fiyat': f"{cur}{level:,.2f}", 'Uzaklik': f"%{dist:+.1f}"})
        st.dataframe(pd.DataFrame(fib_data), use_container_width=True, hide_index=True)
        st.markdown("---")
        st.subheader("📊 Bollinger Bands")
        bb_u = float(bb_upper_s.iloc[-1])
        bb_m = float(bb_mid_s.iloc[-1])
        bb_l = float(bb_lower_s.iloc[-1])
        bb_width = ((bb_u - bb_l) / bb_m) * 100
        b1, b2, b3, b4 = st.columns(4)
        b1.metric("Ust Band", f"{cur}{bb_u:,.2f}")
        b2.metric("Orta", f"{cur}{bb_m:,.2f}")
        b3.metric("Alt Band", f"{cur}{bb_l:,.2f}")
        b4.metric("Bant Genisligi", f"%{bb_width:.1f}")
        if price > bb_u: bb_signal = "🔴 Asiri Alim — Fiyat ust bandin ustunde!"
        elif price < bb_l: bb_signal = "🟢 Asiri Satim — Fiyat alt bandin altinda!"
        else: bb_signal = "⚪ Normal — Fiyat bantlar arasinda."
        st.info(bb_signal)
        st.markdown("---")
        fig_fb = go.Figure()
        x_vals = list(range(min(60, len(close))))
        fig_fb.add_trace(go.Scatter(x=x_vals, y=close.tolist()[-60:], name='Fiyat', line=dict(color='#1565c0', width=2.5)))
        fig_fb.add_trace(go.Scatter(x=x_vals, y=bb_upper_s.tolist()[-60:], name='Ust BB', line=dict(color='#c62828', width=1, dash='dash')))
        fig_fb.add_trace(go.Scatter(x=x_vals, y=bb_mid_s.tolist()[-60:], name='Orta BB', line=dict(color='#f57c00', width=1, dash='dot')))
        fig_fb.add_trace(go.Scatter(x=x_vals, y=bb_lower_s.tolist()[-60:], name='Alt BB', line=dict(color='#2e7d32', width=1, dash='dash')))
        for name, level in fib_levels.items():
            if '%23' in name or '%50' in name or '%61' in name:
                fig_fb.add_hline(y=level, line_dash="dot", line_color="#9e9e9e", annotation_text=name)
        fig_fb.update_layout(height=450, paper_bgcolor='white', plot_bgcolor='white', title=f"{fib_sym} — Fibonacci + Bollinger")
        fig_fb.update_xaxes(showgrid=False)
        fig_fb.update_yaxes(showgrid=True, gridcolor='#eee')
        st.plotly_chart(fig_fb, use_container_width=True)
    else:
        st.error("Yeterli veri yok.")


# ============================================================
# SAYFA: FORMASYONLAR
# ============================================================
elif page == "📐 Formasyonlar":
    st.title("📐 Teknik Formasyonlar")
    st.caption("OBO, Flama, Cikan/Dusen Trend, Bayrak, Cift Dip/Tepe tespiti")
    form_market = st.radio("Piyasa:", ["BIST", "Kripto"], horizontal=True, key="form_m")
    if form_market == "BIST":
        form_sym = st.selectbox("Hisse:", list(ALL_BIST.keys()), key="form_sym")
        df_form = get_bist_data(form_sym)
        cur = "₺"
    else:
        form_sym = st.selectbox("Kripto:", CRYPTO_BINANCE + CRYPTO_EXTRA, key="form_sym_c")
        df_form = get_crypto_data(form_sym)
        cur = "$"
    if not df_form.empty and len(df_form) >= 30:
        close = df_form['Close']
        high = df_form['High']
        low = df_form['Low']
        price = float(close.iloc[-1])
        prices = close.tolist()
        highs = high.tolist()
        lows = low.tolist()
        n = len(prices)
        formasyonlar = []
        # Cikan Trend
        last10_highs = highs[-10:]
        last10_lows = lows[-10:]
        hh_count = sum(1 for i in range(1, len(last10_highs)) if last10_highs[i] > last10_highs[i-1])
        hl_count = sum(1 for i in range(1, len(last10_lows)) if last10_lows[i] > last10_lows[i-1])
        if hh_count >= 6 and hl_count >= 6:
            formasyonlar.append({'Formasyon': '📈 Cikan Trend (Uptrend)', 'Guc': 'Guclu', 'Sinyal': '🟢 AL', 'Aciklama': 'Artan tepeler + artan dipler.'})
        elif hh_count >= 4 and hl_count >= 4:
            formasyonlar.append({'Formasyon': '📈 Cikan Trend (Uptrend)', 'Guc': 'Orta', 'Sinyal': '🟡 TUT', 'Aciklama': 'Hafif yukselis trendi.'})
        # Dusen Trend
        lh_count = sum(1 for i in range(1, len(last10_highs)) if last10_highs[i] < last10_highs[i-1])
        ll_count = sum(1 for i in range(1, len(last10_lows)) if last10_lows[i] < last10_lows[i-1])
        if lh_count >= 6 and ll_count >= 6:
            formasyonlar.append({'Formasyon': '📉 Dusen Trend (Downtrend)', 'Guc': 'Guclu', 'Sinyal': '🔴 SAT', 'Aciklama': 'Azalan tepeler + azalan dipler.'})
        elif lh_count >= 4 and ll_count >= 4:
            formasyonlar.append({'Formasyon': '📉 Dusen Trend (Downtrend)', 'Guc': 'Orta', 'Sinyal': '🟡 DIKKAT', 'Aciklama': 'Hafif dusus trendi.'})
        # OBO
        if n >= 30:
            seg = prices[-30:]
            left_shoulder = max(seg[0:10])
            head = max(seg[10:20])
            right_shoulder = max(seg[20:30])
            if head > left_shoulder and head > right_shoulder:
                shoulder_diff = abs(left_shoulder - right_shoulder) / head * 100
                if shoulder_diff < 5:
                    neckline = min(min(seg[8:12]), min(seg[18:22]))
                    formasyonlar.append({'Formasyon': '🔴 OBO (Omuz-Bas-Omuz)', 'Guc': 'Guclu', 'Sinyal': '🔴 SAT', 'Aciklama': f'Boyun cizgisi: {cur}{neckline:.2f}'})
        # Ters OBO
        if n >= 30:
            seg = prices[-30:]
            left_shoulder = min(seg[0:10])
            head = min(seg[10:20])
            right_shoulder = min(seg[20:30])
            if head < left_shoulder and head < right_shoulder:
                shoulder_diff = abs(left_shoulder - right_shoulder) / abs(head) * 100 if head != 0 else 999
                if shoulder_diff < 5:
                    neckline = max(max(seg[8:12]), max(seg[18:22]))
                    formasyonlar.append({'Formasyon': '🟢 Ters OBO', 'Guc': 'Guclu', 'Sinyal': '🟢 AL', 'Aciklama': f'Boyun cizgisi: {cur}{neckline:.2f}'})
        # Flama
        recent_range = [highs[-i] - lows[-i] for i in range(1, min(11, n))]
        if len(recent_range) >= 8 and all(recent_range[i] <= recent_range[i+1] * 1.1 for i in range(len(recent_range)-1)):
            formasyonlar.append({'Formasyon': '🚩 Flama / Ucgen', 'Guc': 'Orta', 'Sinyal': '⚡ PATLAMA YAKIN', 'Aciklama': 'Volatilite daraliyor.'})
        # Cift Dip
        if n >= 40:
            first_half_min = min(prices[-40:-20])
            second_half_min = min(prices[-20:])
            diff_pct = abs(first_half_min - second_half_min) / max(first_half_min, 0.001) * 100
            if diff_pct < 3 and price > (first_half_min + second_half_min) / 2 * 1.03:
                formasyonlar.append({'Formasyon': '🟢 Cift Dip (Double Bottom)', 'Guc': 'Guclu', 'Sinyal': '🟢 AL', 'Aciklama': 'Iki benzer dip noktasi. Yukselis baslamis olabilir.'})
        # Cift Tepe
        if n >= 40:
            first_half_max = max(prices[-40:-20])
            second_half_max = max(prices[-20:])
            diff_pct = abs(first_half_max - second_half_max) / max(first_half_max, 0.001) * 100
            if diff_pct < 3 and price < (first_half_max + second_half_max) / 2 * 0.97:
                formasyonlar.append({'Formasyon': '🔴 Cift Tepe (Double Top)', 'Guc': 'Guclu', 'Sinyal': '🔴 SAT', 'Aciklama': 'Iki benzer tepe noktasi. Dusus baslamis olabilir.'})
        # Sonuclari goster
        st.markdown(f"### {form_sym} — Tespit Edilen Formasyonlar")
        if formasyonlar:
            for f in formasyonlar:
                if "AL" in f['Sinyal']: bg = "#e8f5e9"; border = "#2e7d32"
                elif "SAT" in f['Sinyal']: bg = "#ffebee"; border = "#c62828"
                else: bg = "#fff3e0"; border = "#f57c00"
                st.markdown(f'<div style="background:{bg};border-left:4px solid {border};border-radius:8px;padding:16px;margin-bottom:10px"><div style="font-size:16px;font-weight:700">{f["Formasyon"]}</div><div style="margin-top:6px;display:flex;gap:10px"><span style="background:{border};color:white;padding:3px 10px;border-radius:12px;font-size:12px">{f["Sinyal"]}</span><span style="background:#eee;padding:3px 10px;border-radius:12px;font-size:12px">Guc: {f["Guc"]}</span></div><div style="color:#555;font-size:13px;margin-top:8px">{f["Aciklama"]}</div></div>', unsafe_allow_html=True)
        else:
            st.info(f"{form_sym} icin su an belirgin bir formasyon tespit edilemedi.")
        # Grafik
        st.markdown("---")
        if form_market == "BIST":
            show_chart_popup(form_sym, 'BIST')
        else:
            show_chart_popup(form_sym, 'CRYPTO')
    else:
        st.error("Yeterli veri yok.")


# ============================================================
# SAYFA: AI GUNLUK YORUM
# ============================================================
elif page == "📰 AI Gunluk Yorum":
    st.title("📰 Gunluk Sentiment Yorumu — v5.0")
    all_scores = get_all_bist_scores()
    if not all_scores.empty:
        greens = len(all_scores[all_scores['Sentiment'] > 10])
        reds = len(all_scores[all_scores['Sentiment'] < -10])
        yellows = len(all_scores) - greens - reds
        avg_sent = all_scores['Sent.Puan'].mean()
        avg_change = all_scores['Gun%'].mean()
        best = all_scores.sort_values('Sent.Puan', ascending=False).iloc[0]
        worst = all_scores.sort_values('Sent.Puan', ascending=True).iloc[0]
        # Trend dagılımı
        yukari_count = len(all_scores[all_scores['Trend'] == 'yukari'])
        asagi_count = len(all_scores[all_scores['Trend'] == 'asagi'])
        yatay_count = len(all_scores[all_scores['Trend'] == 'yatay'])
        # Kartlar
        st.markdown(f"""<div style="display:flex;gap:12px;margin-bottom:20px;flex-wrap:wrap">
            <div style="flex:1;min-width:120px;background:#f8f9fa;border-radius:10px;padding:14px;text-align:center;border-left:4px solid #1565c0">
                <div style="color:#666;font-size:11px">Sentiment</div>
                <div style="font-size:24px;font-weight:700;color:#1565c0">{avg_sent:.2f}</div>
            </div>
            <div style="flex:1;min-width:120px;background:#f8f9fa;border-radius:10px;padding:14px;text-align:center;border-left:4px solid #ff8f00">
                <div style="color:#666;font-size:11px">Ort. Degisim</div>
                <div style="font-size:24px;font-weight:700;color:{'#2e7d32' if avg_change >= 0 else '#c62828'}">{avg_change:+.2f}%</div>
            </div>
            <div style="flex:1;min-width:120px;background:#f8f9fa;border-radius:10px;padding:14px;text-align:center;border-left:4px solid #2e7d32">
                <div style="color:#666;font-size:11px">↑ Yukari Trend</div>
                <div style="font-size:24px;font-weight:700;color:#2e7d32">{yukari_count}</div>
            </div>
            <div style="flex:1;min-width:120px;background:#f8f9fa;border-radius:10px;padding:14px;text-align:center;border-left:4px solid #c62828">
                <div style="color:#666;font-size:11px">↓ Asagi Trend</div>
                <div style="font-size:24px;font-weight:700;color:#c62828">{asagi_count}</div>
            </div>
        </div>""", unsafe_allow_html=True)
        # AI Yorum
        st.markdown("### 🤖 GUNLUK SENTIMENT YORUMU")
        if avg_sent > 6:
            yorum = f"**PIYASA GUCLU POZITIF BOLGEDE ({avg_sent:.2f}/10)**\n\n"
            yorum += f"Toplam {len(all_scores)} hisseden **{greens} tanesi yesil**, {yukari_count} tanesi yukari trendde.\n\n"
            yorum += f"**Gunun Yildizi:** {best['Sembol']} (Sent: {best['Sent.Puan']:.1f})\n\n"
            yorum += f"Momentum pozitif, alislar guclu. Geri cekilmeler alis firsati olabilir."
        elif avg_sent > 4:
            yorum = f"**PIYASA NOTR-POZITIF ({avg_sent:.2f}/10)**\n\n"
            yorum += f"{greens} yesil, {reds} kirmizi, {yellows} notr hisse.\n"
            yorum += f"Trend dagilimi: ↑{yukari_count} / →{yatay_count} / ↓{asagi_count}\n\n"
            yorum += f"**Guclu:** {best['Sembol']} | **Zayif:** {worst['Sembol']}\n\n"
            yorum += "5.00 ustunde kaldikca alislar devam edebilir."
        else:
            yorum = f"**DIKKAT! PIYASA BASKI ALTINDA ({avg_sent:.2f}/10)**\n\n"
            yorum += f"Sadece {greens} hisse yesil. {asagi_count} hisse asagi trendde.\n\n"
            yorum += f"En cok zarar goren: **{worst['Sembol']}** (Sent: {worst['Sent.Puan']:.1f})\n\n"
            yorum += "Temkinli olunmali. Dip donusu sinyalleri takip edilmeli."
        st.markdown(f'<div style="background:#f8f9fa;border-left:4px solid #1565c0;border-radius:8px;padding:20px;font-size:14px;line-height:1.8">{yorum}</div>', unsafe_allow_html=True)
        st.markdown(f"\n📅 **Yayin Tarihi:** {get_turkey_time().strftime('%d.%m.%Y %H:%M')}")
        st.warning("Bu yorum AI tarafindan otomatik olusturulmustur. Yatirim tavsiyesi degildir.")


# ============================================================
# SAYFA: DIVERGENCE
# ============================================================
elif page == "🔴 Divergence":
    st.title("🔴 Divergence (Sapma) Tespiti")
    div_market = st.radio("Piyasa:", ["BIST", "Kripto"], horizontal=True, key="div_m")
    if div_market == "BIST":
        div_sym = st.selectbox("Hisse:", list(ALL_BIST.keys()), key="div_sym")
        df_div = get_bist_data(div_sym)
        cur = "₺"
    else:
        div_sym = st.selectbox("Kripto:", CRYPTO_BINANCE + CRYPTO_EXTRA, key="div_sym_c")
        df_div = get_crypto_data(div_sym)
        cur = "$"
    if not df_div.empty and len(df_div) >= 30:
        close = df_div['Close']
        rsi_series = momentum.RSIIndicator(close, window=14).rsi()
        prices_list = close.tolist()
        rsi_list = rsi_series.tolist()
        price_now = prices_list[-1]
        price_10ago = prices_list[-10]
        rsi_now = rsi_list[-1]
        rsi_10ago = rsi_list[-10]
        divergence_type = None
        if price_now < price_10ago and rsi_now > rsi_10ago:
            divergence_type = "bullish"
        elif price_now > price_10ago and rsi_now < rsi_10ago:
            divergence_type = "bearish"
        if divergence_type == "bullish":
            st.markdown(f'<div style="background:#e8f5e9;border:2px solid #2e7d32;border-radius:12px;padding:20px;text-align:center;margin-bottom:20px"><h2 style="margin:0;color:#2e7d32">🟢 POZITIF SAPMA (Bullish)</h2><p style="color:#333;margin-top:10px">Fiyat dususken RSI yukseliyor — <strong>YUKSELIS sinyali!</strong></p></div>', unsafe_allow_html=True)
        elif divergence_type == "bearish":
            st.markdown(f'<div style="background:#ffebee;border:2px solid #c62828;border-radius:12px;padding:20px;text-align:center;margin-bottom:20px"><h2 style="margin:0;color:#c62828">🔴 NEGATIF SAPMA (Bearish)</h2><p style="color:#333;margin-top:10px">Fiyat yukselirken RSI dususyor — <strong>DUSUS sinyali!</strong></p></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="background:#f5f5f5;border:2px solid #9e9e9e;border-radius:12px;padding:20px;text-align:center;margin-bottom:20px"><h2 style="margin:0;color:#666">⚪ SAPMA YOK</h2><p style="color:#333;margin-top:10px">Fiyat ve RSI uyumlu hareket ediyor.</p></div>', unsafe_allow_html=True)
        d1, d2, d3, d4 = st.columns(4)
        d1.metric("Fiyat", f"{cur}{price_now:,.2f}")
        d2.metric("RSI", f"{rsi_now:.1f}")
        d3.metric("10G Once Fiyat", f"{cur}{price_10ago:,.2f}")
        d4.metric("10G Once RSI", f"{rsi_10ago:.1f}")
        st.markdown("---")
        fig_div = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08, row_heights=[0.6, 0.4])
        x_vals = list(range(len(prices_list[-40:])))
        fig_div.add_trace(go.Scatter(x=x_vals, y=prices_list[-40:], name='Fiyat', line=dict(color='#1565c0', width=2.5)), row=1, col=1)
        fig_div.add_trace(go.Scatter(x=x_vals, y=rsi_list[-40:], name='RSI', line=dict(color='#7b1fa2', width=2)), row=2, col=1)
        fig_div.add_hline(y=70, line_dash="dash", line_color="#c62828", row=2, col=1)
        fig_div.add_hline(y=30, line_dash="dash", line_color="#2e7d32", row=2, col=1)
        if divergence_type:
            fig_div.add_vrect(x0=len(x_vals)-10, x1=len(x_vals)-1, fillcolor="green" if divergence_type=="bullish" else "red", opacity=0.1, row=1, col=1)
            fig_div.add_vrect(x0=len(x_vals)-10, x1=len(x_vals)-1, fillcolor="green" if divergence_type=="bullish" else "red", opacity=0.1, row=2, col=1)
        fig_div.update_layout(height=500, paper_bgcolor='white', plot_bgcolor='white', title=f"{div_sym} — Divergence")
        fig_div.update_xaxes(showgrid=False)
        fig_div.update_yaxes(showgrid=True, gridcolor='#eee')
        st.plotly_chart(fig_div, use_container_width=True)


# ============================================================
# SAYFA: 10 GUN HEATMAP
# ============================================================
elif page == "📊 10 Gun Heatmap":
    st.title("📊 10 Gunluk Performans Heatmap")
    hm_scores = get_bist30_scores()
    if not hm_scores.empty:
        symbols_to_show = hm_scores['Sembol'].tolist()[:15]
        heatmap_data = []
        for sym in symbols_to_show:
            try:
                df_hm = get_bist_data(sym)
                if not df_hm.empty and len(df_hm) >= 11:
                    close = df_hm['Close']
                    daily_returns = []
                    for i in range(-10, 0):
                        ret = ((float(close.iloc[i]) - float(close.iloc[i-1])) / float(close.iloc[i-1])) * 100
                        daily_returns.append(round(ret, 1))
                    heatmap_data.append({'Sembol': sym, 'returns': daily_returns})
            except:
                continue
        if heatmap_data:
            for item in heatmap_data:
                cols = st.columns([1.5] + [1]*10 + [0.5])
                with cols[0]:
                    st.markdown(f"**{item['Sembol']}**")
                for i, ret in enumerate(item['returns']):
                    with cols[i+1]:
                        if ret >= 2: bg = "#1b5e20"; color = "white"
                        elif ret >= 0.5: bg = "#66bb6a"; color = "white"
                        elif ret >= 0: bg = "#c8e6c9"; color = "#333"
                        elif ret >= -0.5: bg = "#ffcdd2"; color = "#333"
                        elif ret >= -2: bg = "#ef5350"; color = "white"
                        else: bg = "#b71c1c"; color = "white"
                        st.markdown(f'<div style="background:{bg};color:{color};text-align:center;padding:4px;border-radius:4px;font-size:11px;font-weight:600">{ret:+.1f}%</div>', unsafe_allow_html=True)
                with cols[11]:
                    if st.button("📈", key=f"hm10_{item['Sembol']}"):
                        st.session_state.chart_symbol = item['Sembol']
                        st.session_state.chart_market = 'BIST'
                        st.rerun()


# ============================================================
# SAYFA: FAVORILERIM
# ============================================================
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
    for idx, fav in enumerate(st.session_state.favorites):
        try:
            if '/' in fav:
                df = get_crypto_data(fav)
                cur = "$"; market = 'CRYPTO'
            else:
                df = get_bist_data(fav)
                cur = "₺"; market = 'BIST'
            result = calc_sentiment(df)
            if result:
                color = "#2e7d32" if result['daily_change'] >= 0 else "#c62828"
                dec_bg = "#e8f5e9" if "AL" in result['decision'] else "#ffebee" if "SAT" in result['decision'] else "#fff3e0"
                col_fav, col_btn = st.columns([5, 1])
                with col_fav:
                    st.markdown(f'<div style="background:{dec_bg};border-radius:12px;padding:16px;margin-bottom:8px;border:1px solid #eee"><div style="display:flex;justify-content:space-between;align-items:center"><div><strong>{fav}</strong> <span style="color:{color};font-size:18px;font-weight:700">{cur}{result["price"]:,.2f}</span> <span style="color:{color};font-size:13px">%{result["daily_change"]:.2f}</span></div><div>{result["decision"]} | Sent: {result["sent_puan"]:.1f} | Trend: {result["trend"]}</div></div></div>', unsafe_allow_html=True)
                with col_btn:
                    if st.button("📈", key=f"fav_{fav}_{idx}"):
                        st.session_state.chart_symbol = fav
                        st.session_state.chart_market = market
                        st.rerun()
        except:
            pass


# ============================================================
# SAYFA: HEATMAP
# ============================================================
elif page == "🔥 Heatmap":
    st.title("🔥 Heatmap — BIST Isi Haritasi")
    all_scores = get_all_bist_scores()
    if not all_scores.empty:
        sorted_s = all_scores.sort_values('Gun%', ascending=False)
        cols_per_row = 6
        rows_data = [sorted_s.iloc[i:i+cols_per_row] for i in range(0, len(sorted_s), cols_per_row)]
        for row_idx, row_data in enumerate(rows_data):
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
                        st.markdown(f'<div style="background:{bg};color:white;border-radius:8px;padding:10px;text-align:center;margin-bottom:4px;min-height:70px"><div style="font-weight:700;font-size:13px">{row["Sembol"]}</div><div style="font-size:16px;font-weight:800">{pct:+.1f}%</div><div style="font-size:11px">₺{row["Fiyat"]}</div></div>', unsafe_allow_html=True)
                        if st.button("📈", key=f"hm_{row['Sembol']}_{row_idx}_{i}"):
                            st.session_state.chart_symbol = row['Sembol']
                            st.session_state.chart_market = 'BIST'
                            st.rerun()


# ============================================================
# SAYFA: KARSILASTIR
# ============================================================
elif page == "⚔️ Karsilastir":
    st.title("⚔️ Hisse Karsilastirma")
    col1, col2 = st.columns(2)
    with col1: sym1 = st.selectbox("1. Hisse:", list(ALL_BIST.keys()), index=0)
    with col2: sym2 = st.selectbox("2. Hisse:", list(ALL_BIST.keys()), index=1)
    if st.button("⚔️ Karsilastir", type="primary"):
        df1 = get_bist_data(sym1)
        df2 = get_bist_data(sym2)
        r1 = calc_sentiment(df1)
        r2 = calc_sentiment(df2)
        if r1 and r2:
            c1, c2 = st.columns(2)
            with c1:
                dc = "#2e7d32" if "AL" in r1['decision'] else "#c62828" if "SAT" in r1['decision'] else "#f57c00"
                st.markdown(f'<div style="background:{dc};color:white;border-radius:12px;padding:20px;text-align:center"><h2 style="margin:0;color:white">{sym1}</h2><p style="font-size:24px;color:white">₺{r1["price"]:,.2f}</p><p style="color:rgba(255,255,255,0.9)">{r1["decision"]} | Trend: {r1["trend"]}</p></div>', unsafe_allow_html=True)
            with c2:
                dc = "#2e7d32" if "AL" in r2['decision'] else "#c62828" if "SAT" in r2['decision'] else "#f57c00"
                st.markdown(f'<div style="background:{dc};color:white;border-radius:12px;padding:20px;text-align:center"><h2 style="margin:0;color:white">{sym2}</h2><p style="font-size:24px;color:white">₺{r2["price"]:,.2f}</p><p style="color:rgba(255,255,255,0.9)">{r2["decision"]} | Trend: {r2["trend"]}</p></div>', unsafe_allow_html=True)
            st.markdown("---")
            compare_data = pd.DataFrame({
                'Gosterge': ['Fiyat', 'Gun%', 'Sent.Puan', 'RSI', 'Stoch', 'Momentum%', 'MACD', 'Trend', 'Trend Gucu', 'EMA21', 'Karar'],
                sym1: [f"₺{r1['price']:,.2f}", f"%{r1['daily_change']:.2f}", f"{r1['sent_puan']:.2f}", f"{r1['rsi']:.1f}", f"{r1['stoch']:.1f}", f"%{r1['momentum']:.2f}", f"{r1['macd']:.4f}", r1['trend'], f"{r1['trend_strength']}/5", f"₺{r1['ema21']:.2f}", r1['decision']],
                sym2: [f"₺{r2['price']:,.2f}", f"%{r2['daily_change']:.2f}", f"{r2['sent_puan']:.2f}", f"{r2['rsi']:.1f}", f"{r2['stoch']:.1f}", f"%{r2['momentum']:.2f}", f"{r2['macd']:.4f}", r2['trend'], f"{r2['trend_strength']}/5", f"₺{r2['ema21']:.2f}", r2['decision']]
            })
            st.dataframe(compare_data, use_container_width=True, hide_index=True)
            # Normalize grafik
            fig = go.Figure()
            prices1 = [p / r1['prices'][0] * 100 for p in r1['prices']]
            prices2 = [p / r2['prices'][0] * 100 for p in r2['prices']]
            fig.add_trace(go.Scatter(y=prices1, name=sym1, line=dict(color='#1565c0', width=2.5)))
            fig.add_trace(go.Scatter(y=prices2, name=sym2, line=dict(color='#c62828', width=2.5)))
            fig.update_layout(height=350, title="Performans Karsilastirma (Normalize)", paper_bgcolor='white', plot_bgcolor='white')
            st.plotly_chart(fig, use_container_width=True)


# ============================================================
# SAYFA: GUNUN EN IYILERI
# ============================================================
elif page == "🏆 Gunun En Iyileri":
    st.title("🏆 Gunun En Iyileri / En Kotuleri")
    all_scores = get_all_bist_scores()
    if not all_scores.empty:
        gtab1, gtab2 = st.tabs(["📈 En Cok Yukselenler", "📉 En Cok Dusenler"])
        with gtab1:
            top5 = all_scores.sort_values('Gun%', ascending=False).head(5).reset_index(drop=True)
            for i, (_, row) in enumerate(top5.iterrows()):
                medal = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][i]
                col_info, col_btn = st.columns([5, 1])
                with col_info:
                    st.markdown(f'<div style="background:#e8f5e9;border-radius:10px;padding:14px;margin-bottom:8px;display:flex;justify-content:space-between;align-items:center"><div><span style="font-size:20px">{medal}</span> <strong style="font-size:16px">{row["Sembol"]}</strong></div><div style="text-align:right"><span style="color:#2e7d32;font-size:18px;font-weight:700">+%{row["Gun%"]:.2f}</span><br><span style="color:#666;font-size:13px">₺{row["Fiyat"]} | {row["Karar"]}</span></div></div>', unsafe_allow_html=True)
                with col_btn:
                    if st.button("📈", key=f"gunbest_{row['Sembol']}_{i}"):
                        st.session_state.chart_symbol = row['Sembol']
                        st.session_state.chart_market = 'BIST'
                        st.rerun()
        with gtab2:
            bot5 = all_scores.sort_values('Gun%', ascending=True).head(5).reset_index(drop=True)
            for i, (_, row) in enumerate(bot5.iterrows()):
                medal = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][i]
                col_info, col_btn = st.columns([5, 1])
                with col_info:
                    st.markdown(f'<div style="background:#ffebee;border-radius:10px;padding:14px;margin-bottom:8px;display:flex;justify-content:space-between;align-items:center"><div><span style="font-size:20px">{medal}</span> <strong style="font-size:16px">{row["Sembol"]}</strong></div><div style="text-align:right"><span style="color:#c62828;font-size:18px;font-weight:700">{row["Gun%"]:.2f}%</span><br><span style="color:#666;font-size:13px">₺{row["Fiyat"]} | {row["Karar"]}</span></div></div>', unsafe_allow_html=True)
                with col_btn:
                    if st.button("📈", key=f"gunworst_{row['Sembol']}_{i}"):
                        st.session_state.chart_symbol = row['Sembol']
                        st.session_state.chart_market = 'BIST'
                        st.rerun()


# ============================================================
# SAYFA: PORTFOLYO
# ============================================================
elif page == "💼 Portfolyo":
    st.title("💼 Portfolyo Takibi")
    if 'portfolio' not in st.session_state:
        st.session_state.portfolio = []
    with st.expander("➕ Hisse Ekle"):
        p_col1, p_col2, p_col3 = st.columns(3)
        with p_col1: p_sym = st.selectbox("Sembol:", list(ALL_BIST.keys()), key="port_sym")
        with p_col2: p_lot = st.number_input("Lot:", min_value=1, value=100, key="port_lot")
        with p_col3: p_cost = st.number_input("Alis Fiyati (₺):", min_value=0.01, value=10.0, step=0.01, key="port_cost")
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
            # Grafik ac
            sel_port = st.selectbox("Grafik ac:", [p['Sembol'] for p in port_data], key="port_chart")
            if st.button("📈 Grafik", key="port_chart_btn"):
                st.session_state.chart_symbol = sel_port
                st.session_state.chart_market = 'BIST'
                st.rerun()
        if st.button("🗑️ Portfolyoyu Temizle"):
            st.session_state.portfolio = []
            st.rerun()
    else:
        st.info("Henuz hisse eklenmedi.")


# ============================================================
# SAYFA: DESTEK / DIRENC
# ============================================================
elif page == "🎯 Destek/Direnc":
    st.title("🎯 Destek / Direnc Seviyeleri")
    dd_market = st.radio("Piyasa:", ["BIST", "Kripto"], horizontal=True, key="dd_m")
    if dd_market == "BIST":
        dd_sym = st.selectbox("Hisse:", list(ALL_BIST.keys()), key="dd_sym")
        df_dd = get_bist_data(dd_sym)
        cur = "₺"
    else:
        dd_sym = st.selectbox("Kripto:", CRYPTO_BINANCE + CRYPTO_EXTRA, key="dd_sym_c")
        df_dd = get_crypto_data(dd_sym)
        cur = "$"
    if not df_dd.empty and len(df_dd) >= 20:
        close = df_dd['Close']
        high = df_dd['High']
        low = df_dd['Low']
        price = float(close.iloc[-1])
        pivot = (float(high.iloc[-1]) + float(low.iloc[-1]) + price) / 3
        r1_pivot = 2 * pivot - float(low.iloc[-1])
        s1_pivot = 2 * pivot - float(high.iloc[-1])
        r2_pivot = pivot + (float(high.iloc[-1]) - float(low.iloc[-1]))
        s2_pivot = pivot - (float(high.iloc[-1]) - float(low.iloc[-1]))
        sma20 = float(close.rolling(20).mean().iloc[-1])
        sma50 = float(close.rolling(50).mean().iloc[-1]) if len(close) >= 50 else sma20
        st.markdown(f'<div style="background:linear-gradient(135deg,#e3f2fd,#f8f9fa);border-radius:12px;padding:20px;text-align:center;margin-bottom:20px"><h2 style="margin:0;color:#1565c0">{dd_sym}</h2><h1 style="margin:5px 0;color:#333">{cur}{price:,.2f}</h1></div>', unsafe_allow_html=True)
        p1, p2, p3, p4, p5 = st.columns(5)
        p1.metric("R2", f"{cur}{r2_pivot:,.2f}")
        p2.metric("R1", f"{cur}{r1_pivot:,.2f}")
        p3.metric("Pivot", f"{cur}{pivot:,.2f}")
        p4.metric("S1", f"{cur}{s1_pivot:,.2f}")
        p5.metric("S2", f"{cur}{s2_pivot:,.2f}")
        st.markdown("---")
        fig_dd = go.Figure()
        fig_dd.add_trace(go.Scatter(y=close.tolist()[-60:], name='Fiyat', line=dict(color='#1565c0', width=2.5)))
        fig_dd.add_hline(y=r1_pivot, line_dash="dash", line_color="#c62828", annotation_text="R1")
        fig_dd.add_hline(y=s1_pivot, line_dash="dash", line_color="#2e7d32", annotation_text="S1")
        fig_dd.add_hline(y=pivot, line_dash="dot", line_color="#f57c00", annotation_text="Pivot")
        fig_dd.add_hline(y=sma20, line_dash="dot", line_color="#7b1fa2", annotation_text="SMA20")
        fig_dd.update_layout(height=400, paper_bgcolor='white', plot_bgcolor='white', title="Fiyat + Destek/Direnc")
        fig_dd.update_xaxes(showgrid=False)
        fig_dd.update_yaxes(showgrid=True, gridcolor='#eee')
        st.plotly_chart(fig_dd, use_container_width=True)


# ============================================================
# SAYFA: PIYASA SAATI
# ============================================================
elif page == "🕐 Piyasa Saati":
    st.title("🕐 Piyasa Saati")
    now = get_turkey_time()
    hour = now.hour
    weekday = now.weekday()
    markets = [
        {"name": "🇹🇷 BIST (Istanbul)", "open": 10, "close": 18, "tz": 3},
        {"name": "🇺🇸 NYSE (New York)", "open": 9, "close": 16, "tz": -4},
        {"name": "🇺🇸 NASDAQ", "open": 9, "close": 16, "tz": -4},
        {"name": "🇬🇧 LSE (Londra)", "open": 8, "close": 16, "tz": 1},
        {"name": "🇩🇪 XETRA (Frankfurt)", "open": 9, "close": 17, "tz": 2},
        {"name": "🇯🇵 TSE (Tokyo)", "open": 9, "close": 15, "tz": 9},
        {"name": "🇭🇰 HKEX (Hong Kong)", "open": 9, "close": 16, "tz": 8},
        {"name": "🪙 Kripto", "open": 0, "close": 24, "tz": 0},
    ]
    for m in markets:
        local_hour = (hour + m['tz'] - 3) % 24
        if m['name'] == "🪙 Kripto":
            is_open = True
        elif weekday >= 5:
            is_open = False
        else:
            is_open = m['open'] <= local_hour < m['close']
        status = "🟢 ACIK" if is_open else "🔴 KAPALI"
        status_bg = "#e8f5e9" if is_open else "#ffebee"
        hours_text = f"{m['open']:02d}:00 - {m['close']:02d}:00" if m['close'] != 24 else "7/24"
        st.markdown(f'<div style="background:{status_bg};border-radius:10px;padding:14px;margin-bottom:8px;display:flex;justify-content:space-between;align-items:center"><div><strong>{m["name"]}</strong><br><span style="color:#666;font-size:12px">{hours_text} (Yerel)</span></div><div style="font-size:16px;font-weight:700">{status}</div></div>', unsafe_allow_html=True)
    st.caption(f"Sunucu Saati: {now.strftime('%d.%m.%Y %H:%M')} (UTC+3)")


# ============================================================
# SAYFA: S&P / NASDAQ
# ============================================================
elif page == "🇺🇸 S&P / NASDAQ":
    st.title("🇺🇸 S&P 500 / NASDAQ — Top 10")
    results = []
    for name, symbol in US_TOP10.items():
        try:
            df = get_stock_data(symbol)
            r = calc_sentiment(df)
            if r: results.append({'Sembol': name, 'Fiyat': f"${r['price']:,.2f}", 'Gun%': r['daily_change'], 'Sent.Puan': r['sent_puan'], 'Momentum%': round(r['momentum'],2), 'Trend': r['trend'], 'Karar': r['decision']})
        except:
            continue
    if results:
        st.dataframe(pd.DataFrame(results), use_container_width=True, hide_index=True)
        sel_us = st.selectbox("Grafik ac:", [r['Sembol'] for r in results], key="us_sel")
        if st.button("📈 Grafik", key="us_btn"):
            st.session_state.chart_symbol = sel_us
            st.session_state.chart_market = 'INTL'
            st.rerun()


# ============================================================
# SAYFA: AVRUPA
# ============================================================
elif page == "🇪🇺 Avrupa":
    st.title("🇪🇺 Avrupa — Top 10")
    results = []
    for name, symbol in EUROPE_TOP10.items():
        try:
            df = get_stock_data(symbol)
            r = calc_sentiment(df)
            if r: results.append({'Sembol': name, 'Fiyat': f"€{r['price']:,.2f}", 'Gun%': r['daily_change'], 'Sent.Puan': r['sent_puan'], 'Momentum%': round(r['momentum'],2), 'Trend': r['trend'], 'Karar': r['decision']})
        except:
            continue
    if results:
        st.dataframe(pd.DataFrame(results), use_container_width=True, hide_index=True)
        sel_eu = st.selectbox("Grafik ac:", [r['Sembol'] for r in results], key="eu_sel")
        if st.button("📈 Grafik", key="eu_btn"):
            st.session_state.chart_symbol = sel_eu
            st.session_state.chart_market = 'INTL'
            st.rerun()


# ============================================================
# SAYFA: ALTIN & DOVIZ
# ============================================================
elif page == "🥇 Altin & Doviz":
    st.title("🥇 Altin, Gumus & Doviz")
    st.subheader("Doviz Kurlari")
    d1, d2, d3, d4 = st.columns(4)
    doviz_list = [('USD/TRY','USDTRY=X'),('EUR/TRY','EURTRY=X'),('CHF/TRY','CHFTRY=X'),('GBP/TRY','GBPTRY=X')]
    for i, (name, sym) in enumerate(doviz_list):
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
            st.metric("🥇 Altin (Ons)", f"${p:,.2f}", f"{((p-prev)/prev)*100:+.2f}%")
    with m2:
        df_s = get_stock_data('SI=F')
        if not df_s.empty:
            p = float(df_s['Close'].iloc[-1])
            prev = float(df_s['Close'].iloc[-2]) if len(df_s)>1 else p
            st.metric("🥈 Gumus (Ons)", f"${p:,.2f}", f"{((p-prev)/prev)*100:+.2f}%")


# ============================================================
# SAYFA: KRIPTO TOP 10
# ============================================================
elif page == "🪙 Kripto Top 10":
    st.title("🪙 Kripto Top 10")
    crypto_scores = get_crypto_scores()
    if not crypto_scores.empty:
        ktab1, ktab2 = st.tabs(["🟢 Ilk 10", "🔴 Son 10"])
        with ktab1:
            top10_c = crypto_scores.sort_values('Sent.Puan', ascending=False).head(10).reset_index(drop=True)
            top10_c.index = top10_c.index + 1
            st.dataframe(top10_c, use_container_width=True)
            sel_c = st.selectbox("Grafik:", top10_c['Sembol'].tolist(), key="ct_sel")
            if st.button("📈 Grafik", key="ct_btn"):
                st.session_state.chart_symbol = sel_c
                st.session_state.chart_market = 'CRYPTO'
                st.rerun()
        with ktab2:
            bot10_c = crypto_scores.sort_values('Sent.Puan', ascending=True).head(10).reset_index(drop=True)
            bot10_c.index = bot10_c.index + 1
            st.dataframe(bot10_c, use_container_width=True)


# ============================================================
# SAYFA: AKILLI FILTRE
# ============================================================
elif page == "🔍 Akilli Filtre":
    st.title("🔍 Akilli Filtre — v5.0")
    all_scores = get_all_bist_scores()
    if not all_scores.empty:
        filter_type = st.selectbox("Filtre:", [
            "Potansiyel Kalkislar", "Guclu Alis", "En Yuksek Sentiment",
            "Yukari Trend + Momentum", "Guclu Satis", "Asagi Momentum",
            "Yuksek Hacim Artisi", "Notr (Bekle)"
        ])
        st.markdown("---")
        if "Potansiyel" in filter_type:
            filtered = all_scores[(all_scores['Sentiment'] > -10) & (all_scores['Sentiment'] < 30) & (all_scores['Momentum%'] > 0) & (all_scores['Trend'] != 'asagi')]
        elif "Guclu Alis" in filter_type:
            filtered = all_scores[all_scores['Sent.Puan'] >= 7]
        elif "En Yuksek" in filter_type:
            filtered = all_scores.sort_values('Sent.Puan', ascending=False).head(10)
        elif "Yukari Trend" in filter_type:
            filtered = all_scores[(all_scores['Trend'] == 'yukari') & (all_scores['Momentum%'] > 1)]
        elif "Guclu Satis" in filter_type:
            filtered = all_scores[all_scores['Sent.Puan'] <= 3]
        elif "Asagi" in filter_type:
            filtered = all_scores[all_scores['Momentum%'] < -2]
        elif "Hacim" in filter_type:
            filtered = all_scores[all_scores['Hacim%'] > 30].sort_values('Hacim%', ascending=False)
        else:
            filtered = all_scores[(all_scores['Sent.Puan'] >= 4) & (all_scores['Sent.Puan'] <= 6)]

        if not filtered.empty:
            st.dataframe(filtered.reset_index(drop=True), use_container_width=True)
            sel_f = st.selectbox("Grafik ac:", filtered['Sembol'].tolist(), key="filtre_sel")
            if st.button("📈 Grafik", key="filtre_btn"):
                st.session_state.chart_symbol = sel_f
                st.session_state.chart_market = 'BIST'
                st.rerun()
        else:
            st.warning("Sonuc bulunamadi.")


# ============================================================
# SAYFA: GUNLUK SENTIMENT
# ============================================================
elif page == "📈 Gunluk Sentiment":
    st.title("📈 Gunluk Sentiment — BIST100")
    bist_df = get_bist100_index()
    if not bist_df.empty:
        result = calc_sentiment(bist_df)
        if result:
            i1, i2, i3, i4 = st.columns(4)
            i1.metric("Sentiment", f"{result['sent_puan']:.2f}/10")
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


# ============================================================
# SAYFA: OSILATOR
# ============================================================
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
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Scatter(x=x, y=price_vals, name='BIST100', line=dict(color='#1565c0', width=2.5)), secondary_y=False)
        osc_colors = ['#2e7d32' if v >= 0 else '#c62828' for v in osc_vals]
        fig.add_trace(go.Bar(x=x, y=osc_vals, name='Osilator', marker_color=osc_colors, opacity=0.7), secondary_y=True)
        fig.update_layout(height=450, paper_bgcolor='white', plot_bgcolor='white', legend=dict(orientation='h', y=-0.1))
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(showgrid=True, gridcolor='#eee')
        st.plotly_chart(fig, use_container_width=True)


# ============================================================
# SAYFA: BIST30 ILK 10
# ============================================================
elif page == "📋 BIST30 Ilk 10":
    st.title("📋 BIST30 — Ilk 10")
    scores_df = get_bist30_scores()
    if not scores_df.empty:
        top10 = scores_df.sort_values('Sent.Puan', ascending=False).head(10).reset_index(drop=True)
        top10.index = top10.index + 1
        st.dataframe(top10, use_container_width=True)
        fig = go.Figure(go.Bar(x=top10['Sembol'], y=top10['Sentiment'], marker_color=['#1565c0' if v>=0 else '#c62828' for v in top10['Sentiment']], text=top10['Karar'], textposition='outside'))
        fig.update_layout(height=400, paper_bgcolor='white', plot_bgcolor='white')
        st.plotly_chart(fig, use_container_width=True)
        sel_b30 = st.selectbox("Grafik:", top10['Sembol'].tolist(), key="b30t_sel")
        if st.button("📈 Grafik", key="b30t_btn"):
            st.session_state.chart_symbol = sel_b30
            st.session_state.chart_market = 'BIST'
            st.rerun()


# ============================================================
# SAYFA: BIST30 SON 10
# ============================================================
elif page == "📋 BIST30 Son 10":
    st.title("📋 BIST30 — Son 10")
    scores_df = get_bist30_scores()
    if not scores_df.empty:
        bottom10 = scores_df.sort_values('Sent.Puan', ascending=True).head(10).reset_index(drop=True)
        bottom10.index = bottom10.index + 1
        st.dataframe(bottom10, use_container_width=True)
        fig = go.Figure(go.Bar(x=bottom10['Sembol'], y=bottom10['Sentiment'], marker_color=['#1565c0' if v>=0 else '#c62828' for v in bottom10['Sentiment']], text=bottom10['Karar'], textposition='outside'))
        fig.update_layout(height=400, paper_bgcolor='white', plot_bgcolor='white')
        st.plotly_chart(fig, use_container_width=True)
        sel_b30b = st.selectbox("Grafik:", bottom10['Sembol'].tolist(), key="b30b_sel")
        if st.button("📈 Grafik", key="b30b_btn"):
            st.session_state.chart_symbol = sel_b30b
            st.session_state.chart_market = 'BIST'
            st.rerun()


# ============================================================
# FOOTER
# ============================================================
st.markdown("---")
st.markdown(f"""<div style="text-align:center;padding:20px;color:#999">
    <div style="font-size:14px;font-weight:600">🌊 SentiFlow v5.0</div>
    <div style="font-size:11px;margin-top:4px">Multi-Factor Sentiment Analiz Platformu | 7 Faktor Agirlikli Sistem</div>
    <div style="font-size:11px;margin-top:2px">© 2025 SentiFlow. Yatirim tavsiyesi degildir.</div>
    <div style="font-size:10px;margin-top:4px;color:#bbb">Son guncelleme: {get_turkey_time().strftime('%d.%m.%Y %H:%M')} UTC+3</div>
</div>""", unsafe_allow_html=True)
