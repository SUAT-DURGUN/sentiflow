"""
SentiFlow Telegram Bot v2 — Komut Destekli
"""

import requests
import yfinance as yf
import pandas as pd
from ta import momentum, trend
import ccxt
import time
from datetime import datetime
import json

BOT_TOKEN = "8707463842:AAG5Ng2k0oEiW2vxWJdBhOwmVKMFMNvxreM"
CHAT_ID = "8560379317"

WATCHLIST_BIST = ['THYAO.IS', 'ASELS.IS', 'GARAN.IS', 'AKBNK.IS', 'YKBNK.IS',
                  'EREGL.IS', 'TUPRS.IS', 'PGSUS.IS', 'FROTO.IS', 'KOZAL.IS']

WATCHLIST_CRYPTO = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT', 'BNB/USDT']


def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, data=data)
    except:
        pass


def get_updates(offset=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    params = {"timeout": 30}
    if offset:
        params["offset"] = offset
    try:
        r = requests.get(url, params=params, timeout=35)
        return r.json().get("result", [])
    except:
        return []


def calc_bist_signal(symbol):
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
        if score > 20 and mom > 0: decision = "🟢 AL"
        elif score < -20 and mom < 0: decision = "🔴 SAT"
        else: decision = "🟡 TUT"
        name = symbol.replace('.IS', '')
        return {'name': name, 'price': price, 'change': change, 'score': score, 'rsi': rsi_val, 'decision': decision, 'momentum': mom}
    except:
        return None


def calc_crypto_signal(symbol):
    try:
        ex = ccxt.binance({'enableRateLimit': True})
        ohlcv = ex.fetch_ohlcv(symbol, '1d', limit=90)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
        if len(df) < 20:
            return None
        close = df['Close']
        high = df['High']
        low = df['Low']
        price = float(close.iloc[-1])
        prev = float(close.iloc[-2])
        change = ((price - prev) / prev) * 100
        rsi_val = float(momentum.RSIIndicator(close, window=14).rsi().iloc[-1])
        macd_val = float(trend.MACD(close).macd_diff().iloc[-1])
        score = 0
        if rsi_val < 30: score += 40
        elif rsi_val > 70: score -= 40
        if macd_val > 0: score += 30
        else: score -= 30
        mom = ((price - float(close.iloc[-6])) / float(close.iloc[-6]) * 100)
        if score > 20 and mom > 0: decision = "🟢 AL"
        elif score < -20 and mom < 0: decision = "🔴 SAT"
        else: decision = "🟡 TUT"
        return {'name': symbol, 'price': price, 'change': change, 'score': score, 'rsi': rsi_val, 'decision': decision, 'momentum': mom}
    except:
        return None


def cmd_sinyal():
    msg = "🌊 <b>SentiFlow — Sinyal Raporu</b>\n"
    msg += f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
    msg += "━━━━━━━━━━━━━━━━━━\n\n"
    for symbol in WATCHLIST_BIST:
        r = calc_bist_signal(symbol)
        if r:
            msg += f"{r['decision']} <b>{r['name']}</b>: ₺{r['price']:.2f} ({r['change']:+.1f}%) RSI:{r['rsi']:.0f}\n"
    msg += "\n🌐 sentiflow.streamlit.app"
    send_telegram(msg)


def cmd_bist():
    msg = "🇹🇷 <b>BIST Sentiment</b>\n"
    msg += f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
    al = []
    sat = []
    tut = []
    for symbol in WATCHLIST_BIST:
        r = calc_bist_signal(symbol)
        if r:
            line = f"<b>{r['name']}</b>: ₺{r['price']:.2f} ({r['change']:+.1f}%)"
            if "AL" in r['decision']: al.append(line)
            elif "SAT" in r['decision']: sat.append(line)
            else: tut.append(line)
    if al: msg += "🟢 <b>AL:</b>\n" + "\n".join(al) + "\n\n"
    if sat: msg += "🔴 <b>SAT:</b>\n" + "\n".join(sat) + "\n\n"
    if tut: msg += "🟡 <b>TUT:</b>\n" + "\n".join(tut) + "\n\n"
    send_telegram(msg)


def cmd_kripto():
    msg = "🪙 <b>Kripto Sentiment</b>\n"
    msg += f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
    for symbol in WATCHLIST_CRYPTO:
        r = calc_crypto_signal(symbol)
        if r:
            price_fmt = f"${r['price']:,.4f}" if r['price'] < 1 else f"${r['price']:,.2f}"
            msg += f"{r['decision']} <b>{r['name']}</b>: {price_fmt} ({r['change']:+.1f}%) RSI:{r['rsi']:.0f}\n"
    msg += "\n🌐 sentiflow.streamlit.app"
    send_telegram(msg)


def cmd_help():
    msg = "🌊 <b>SentiFlow Bot Komutlari</b>\n\n"
    msg += "/sinyal — Tum sinyaller\n"
    msg += "/bist — BIST analiz\n"
    msg += "/kripto — Kripto analiz\n"
    msg += "/help — Bu menu\n"
    msg += "\n🌐 sentiflow.streamlit.app"
    send_telegram(msg)

def check_alerts():
    """Buyuk degisimler icin uyari gonder."""
    alerts = []
    for symbol in WATCHLIST_BIST:
        r = calc_bist_signal(symbol)
        if r and (r['change'] > 5 or r['change'] < -5):
            alerts.append(r)
    if alerts:
        msg = "🚨 <b>UYARI! Buyuk Degisim!</b>\n\n"
        for a in alerts:
            msg += f"{'📈' if a['change']>0 else '📉'} <b>{a['name']}</b>: ₺{a['price']:.2f} ({a['change']:+.1f}%)\n"
        msg += "\n🌐 sentiflow.streamlit.app"
        send_telegram(msg)
    return len(alerts)
def check_alerts():
    """Buyuk degisimler icin otomatik uyari."""
    alerts = []
    for symbol in WATCHLIST_BIST:
        r = calc_bist_signal(symbol)
        if r and (r['change'] > 5 or r['change'] < -5):
            alerts.append(r)
    for symbol in WATCHLIST_CRYPTO:
        r = calc_crypto_signal(symbol)
        if r and (r['change'] > 7 or r['change'] < -7):
            alerts.append(r)
    if alerts:
        msg = "🚨 <b>UYARI! Buyuk Degisim!</b>\n\n"
        for a in alerts:
            emoji = "📈" if a['change'] > 0 else "📉"
            msg += f"{emoji} <b>{a['name']}</b>: ({a['change']:+.1f}%) {a['decision']}\n"
        msg += "\n🌐 sentiflow.streamlit.app"
        send_telegram(msg)
        print(f"🚨 {len(alerts)} uyari gonderildi!")

def handle_message(text):
    text = text.lower().strip()
    if text == "/start" or text == "/help":
        cmd_help()
    elif text == "/sinyal":
        cmd_sinyal()
    elif text == "/bist":
        cmd_bist()
    elif text == "/kripto":
        cmd_kripto()
    else:
        send_telegram("Bilinmeyen komut. /help yazin.")


if __name__ == "__main__":
    print("🌊 SentiFlow Telegram Bot v2 Baslatildi!")
    print("Komutlar: /sinyal /bist /kripto /help")
    print("Ctrl+C ile durdur.\n")
    
    # Baslangic mesaji
    send_telegram("🌊 <b>SentiFlow Bot aktif!</b>\n\nKomutlar:\n/sinyal — Tum sinyaller\n/bist — BIST analiz\n/kripto — Kripto analiz\n/help — Yardim")
    
    offset = None
    alert_check = 0
    while True:
        try:
            updates = get_updates(offset)
            for update in updates:
                offset = update["update_id"] + 1
                msg = update.get("message", {})
                text = msg.get("text", "")
                if text:
                    print(f"Komut: {text}")
                    handle_message(text)
            alert_check += 1
            if alert_check >= 900:
                check_alerts()
                alert_check = 0
            time.sleep(2)
        except KeyboardInterrupt:
            print("\nBot durduruldu.")
            break
        except:
            time.sleep(5)
