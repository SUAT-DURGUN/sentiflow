"""
SentiFlow Telegram Bot — Sinyal Bildirimleri
"""

import requests
import yfinance as yf
import pandas as pd
from ta import momentum, trend
import ccxt
import time
from datetime import datetime

# Telegram bilgileri
BOT_TOKEN = "8707463842:AAG5Ng2k0oEiW2vxWJdBhOwmVKMFMNvxreM"
CHAT_ID = "8560379317"

# Hisse listesi
WATCHLIST = ['THYAO.IS', 'ASELS.IS', 'GARAN.IS', 'AKBNK.IS', 'YKBNK.IS',
             'EREGL.IS', 'TUPRS.IS', 'PGSUS.IS', 'FROTO.IS', 'KOZAL.IS']


def send_telegram(message):
    """Telegram mesajı gönder."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, data=data)
    except:
        pass


def calc_signal(symbol):
    """Hisse için sinyal hesapla."""
    try:
        df = yf.Ticker(symbol).history(period="3mo", interval="1d")
        if df.empty or len(df) < 20:
            return None
        
        close = df['Close']
        high = df['High']
        low = df['Low']
        price = float(close.iloc[-1])
        prev = float(close.iloc[-2])
        change = ((price - prev) / prev) * 100
        
        rsi_val = float(momentum.RSIIndicator(close, window=14).rsi().iloc[-1])
        macd_val = float(trend.MACD(close).macd_diff().iloc[-1])
        stoch_val = float(momentum.StochasticOscillator(high, low, close).stoch().iloc[-1])
        ema21 = float(close.ewm(span=21).mean().iloc[-1])
        
        score = 0
        if rsi_val < 30: score += 40
        elif rsi_val > 70: score -= 40
        if macd_val > 0: score += 30
        else: score -= 30
        if stoch_val < 20: score += 20
        elif stoch_val > 80: score -= 20
        if price > ema21: score += 10
        else: score -= 10
        
        mom = ((price - float(close.iloc[-6])) / float(close.iloc[-6]) * 100)
        
        if score > 20 and mom > 0:
            decision = "🟢 AL"
        elif score < -20 and mom < 0:
            decision = "🔴 SAT"
        else:
            decision = "🟡 TUT"
        
        name = symbol.replace('.IS', '')
        
        return {
            'name': name, 'price': price, 'change': change,
            'score': score, 'rsi': rsi_val, 'decision': decision,
            'momentum': mom
        }
    except:
        return None


def send_daily_report():
    """Günlük rapor gönder."""
    msg = "🌊 <b>SentiFlow — Günlük Rapor</b>\n"
    msg += f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
    msg += "━━━━━━━━━━━━━━━━━━\n\n"
    
    al_list = []
    sat_list = []
    tut_list = []
    
    for symbol in WATCHLIST:
        result = calc_signal(symbol)
        if result:
            line = f"<b>{result['name']}</b>: ₺{result['price']:.2f} ({result['change']:+.1f}%) | RSI:{result['rsi']:.0f} | {result['decision']}"
            
            if "AL" in result['decision']:
                al_list.append(line)
            elif "SAT" in result['decision']:
                sat_list.append(line)
            else:
                tut_list.append(line)
    
    if al_list:
        msg += "🟢 <b>AL Sinyalleri:</b>\n"
        msg += "\n".join(al_list) + "\n\n"
    
    if sat_list:
        msg += "🔴 <b>SAT Sinyalleri:</b>\n"
        msg += "\n".join(sat_list) + "\n\n"
    
    if tut_list:
        msg += "🟡 <b>TUT:</b>\n"
        msg += "\n".join(tut_list) + "\n\n"
    
    msg += "━━━━━━━━━━━━━━━━━━\n"
    msg += "🌐 sentiflow.streamlit.app"
    
    send_telegram(msg)
    print(f"✅ Rapor gönderildi: {datetime.now()}")


def send_alert(symbol, result):
    """Önemli sinyal uyarısı gönder."""
    msg = f"🚨 <b>SentiFlow UYARI!</b>\n\n"
    msg += f"Sembol: <b>{result['name']}</b>\n"
    msg += f"Fiyat: ₺{result['price']:.2f} ({result['change']:+.1f}%)\n"
    msg += f"Sinyal: {result['decision']}\n"
    msg += f"RSI: {result['rsi']:.0f}\n"
    msg += f"Momentum: %{result['momentum']:.1f}\n"
    msg += f"\n🌐 sentiflow.streamlit.app"
    
    send_telegram(msg)


if __name__ == "__main__":
    print("🌊 SentiFlow Telegram Bot Başlatıldı!")
    print("📡 Günlük rapor gönderiliyor...\n")
    
    # İlk raporu hemen gönder
    send_daily_report()
    
    print("\n✅ Bot çalışıyor! Ctrl+C ile durdur.")
    print("💡 Her 6 saatte bir rapor gönderilecek.\n")
    
    # Her 6 saatte rapor
    while True:
        time.sleep(21600)  # 6 saat
        send_daily_report()
