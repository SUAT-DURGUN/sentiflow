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


def cmd_dip():
    msg = "🎯 <b>Dip Donusu Adaylari</b>\n\n"
    count = 0
    for symbol in WATCHLIST_BIST:
        r = calc_bist_signal(symbol)
        if r and r['rsi'] < 35 and r['momentum'] < 0:
            msg += f"🎯 <b>{r['name']}</b>: RSI {r['rsi']:.0f} | Mom: {r['momentum']:.1f}%\n"
            count += 1
    if count == 0:
        msg += "Su an belirgin dip donusu adayi yok.\n"
    msg += "\n🌐 sentiflow.streamlit.app"
    send_telegram(msg)


def cmd_top5():
    msg = "🏆 <b>Gunun En Iyileri</b>\n\n"
    results = []
    for symbol in WATCHLIST_BIST:
        r = calc_bist_signal(symbol)
        if r:
            results.append(r)
    results.sort(key=lambda x: x['change'], reverse=True)
    msg += "📈 <b>En Cok Yukselenler:</b>\n"
    for r in results[:5]:
        msg += f"  🟢 {r['name']}: {r['change']:+.1f}%\n"
    msg += "\n📉 <b>En Cok Dusenler:</b>\n"
    for r in results[-5:]:
        msg += f"  🔴 {r['name']}: {r['change']:+.1f}%\n"
    msg += "\n🌐 sentiflow.streamlit.app"
    send_telegram(msg)

def cmd_help():
    msg = "🌊 <b>SentiFlow Bot v3.0</b>\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n\n"
    msg += "📋 <b>KOMUTLAR:</b>\n\n"
    msg += "🎯 /sinyal — Tum al/sat sinyalleri\n"
    msg += "📊 /bist — BIST hisse analiz\n"
    msg += "🪙 /kripto — Kripto detayli analiz\n"
    msg += "🎯 /dip — Dip donusu adaylari\n"
    msg += "🏆 /top5 — Gunun en iyileri/kotuleri\n"
    msg += "📐 /formasyon — OBO, Flama, Cift Dip tespiti\n"
    msg += "📈 /trend — Yukselen/Dusen trendler\n"
    msg += "🌊 /ozet — Gunluk piyasa ozeti\n"
    msg += "🚨 /alarm — Onemli uyarilar\n"
    msg += "/help — Bu menu\n\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    msg += "🌐 sentiflow.streamlit.app\n"
    msg += "⭐ PRO icin: @SentiFlowPro"
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

def cmd_dip():
    """Dip donusu yapabilecek hisseler ve kriptolar."""
    msg = "🎯 <b>DIP DONUSU ADAYLARI</b>\n"
    msg += f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
    
    # BIST Dip Donusu
    msg += "📊 <b>BIST Hisseler:</b>\n"
    bist_dip = 0
    for symbol in WATCHLIST_BIST:
        r = calc_bist_signal(symbol)
        if r and r['rsi'] < 35:
            macd_yon = "↗️" if r.get('macd', 0) > 0 else "↘️"
            msg += f"  🎯 <b>{r['name']}</b>: RSI {r['rsi']:.0f} | {macd_yon} | {r['change']:+.1f}%\n"
            bist_dip += 1
    if bist_dip == 0:
        msg += "  ⚪ Su an belirgin aday yok\n"
    
    # Kripto Dip Donusu
    msg += "\n🪙 <b>Kripto:</b>\n"
    kripto_dip = 0
    for symbol in WATCHLIST_CRYPTO:
        r = calc_crypto_signal(symbol)
        if r and r['rsi'] < 35:
            msg += f"  🎯 <b>{r['name']}</b>: RSI {r['rsi']:.0f} | {r['change']:+.1f}%\n"
            kripto_dip += 1
    if kripto_dip == 0:
        msg += "  ⚪ Su an belirgin aday yok\n"
    
    msg += f"\n💡 <i>RSI 30 alti = asiri satim bolgesi</i>"
    msg += "\n🌐 sentiflow.streamlit.app"
    send_telegram(msg)


def cmd_top5():
    """Gunun en iyi ve en kotu hisseleri."""
    msg = "🏆 <b>GUNUN EN IYILERI / EN KOTULERI</b>\n"
    msg += f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
    
    results = []
    for symbol in WATCHLIST_BIST:
        r = calc_bist_signal(symbol)
        if r:
            results.append(r)
    results.sort(key=lambda x: x['change'], reverse=True)
    
    msg += "📈 <b>En Cok Yukselenler:</b>\n"
    for r in results[:5]:
        msg += f"  🟢 <b>{r['name']}</b>: {r['change']:+.1f}% | ₺{r['price']:.2f}\n"
    
    msg += "\n📉 <b>En Cok Dusenler:</b>\n"
    for r in results[-5:]:
        msg += f"  🔴 <b>{r['name']}</b>: {r['change']:+.1f}% | ₺{r['price']:.2f}\n"
    
    msg += "\n🌐 sentiflow.streamlit.app"
    send_telegram(msg)


def cmd_formasyon():
    """Onemli formasyonlari tespit et."""
    msg = "📐 <b>FORMASYON TESPİTİ</b>\n"
    msg += f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
    
    formasyon_count = 0
    
    # BIST Hisseleri Formasyon
    for symbol in WATCHLIST_BIST:
        try:
            ticker = ALL_BIST.get(symbol, f"{symbol}.IS")
            df = yf.Ticker(ticker).history(period="3mo", interval="1d")
            if df.empty or len(df) < 30:
                continue
            close = df['Close'].tolist()
            high = df['High'].tolist()
            low = df['Low'].tolist()
            price = close[-1]
            n = len(close)
            
            # Cikan Trend
            last10_h = high[-10:]
            last10_l = low[-10:]
            hh = sum(1 for i in range(1, len(last10_h)) if last10_h[i] > last10_h[i-1])
            hl = sum(1 for i in range(1, len(last10_l)) if last10_l[i] > last10_l[i-1])
            if hh >= 7 and hl >= 7:
                msg += f"📈 <b>{symbol}</b>: GUCLU CIKAN TREND ↗️\n"
                formasyon_count += 1
                continue
            
            # Dusen Trend
            lh = sum(1 for i in range(1, len(last10_h)) if last10_h[i] < last10_h[i-1])
            ll = sum(1 for i in range(1, len(last10_l)) if last10_l[i] < last10_l[i-1])
            if lh >= 7 and ll >= 7:
                msg += f"📉 <b>{symbol}</b>: GUCLU DUSEN TREND ↘️\n"
                formasyon_count += 1
                continue
            
            # Cift Dip (Double Bottom)
            if n >= 40:
                first_min = min(close[-40:-20])
                second_min = min(close[-20:])
                diff_pct = abs(first_min - second_min) / first_min * 100
                if diff_pct < 3 and price > (first_min + second_min) / 2 * 1.03:
                    msg += f"🟢 <b>{symbol}</b>: CIFT DIP (Double Bottom) — AL sinyali!\n"
                    formasyon_count += 1
                    continue
            
            # Cift Tepe (Double Top)
            if n >= 40:
                first_max = max(close[-40:-20])
                second_max = max(close[-20:])
                diff_pct = abs(first_max - second_max) / first_max * 100
                if diff_pct < 3 and price < (first_max + second_max) / 2 * 0.97:
                    msg += f"🔴 <b>{symbol}</b>: CIFT TEPE (Double Top) — SAT sinyali!\n"
                    formasyon_count += 1
                    continue
            
            # OBO (Omuz-Bas-Omuz)
            if n >= 30:
                seg = close[-30:]
                left_s = max(seg[0:10])
                head = max(seg[10:20])
                right_s = max(seg[20:30])
                if head > left_s and head > right_s:
                    s_diff = abs(left_s - right_s) / head * 100
                    if s_diff < 5:
                        msg += f"🔴 <b>{symbol}</b>: OBO (Omuz-Bas-Omuz) — DIKKAT!\n"
                        formasyon_count += 1
                        continue
            
            # Flama (Daralan volatilite)
            if n >= 10:
                ranges = [high[-i] - low[-i] for i in range(1, 8)]
                if all(ranges[i] <= ranges[i+1] * 1.1 for i in range(len(ranges)-1)):
                    msg += f"🚩 <b>{symbol}</b>: FLAMA — Patlama yakin! ⚡\n"
                    formasyon_count += 1
                    continue
        except:
            continue
    
    if formasyon_count == 0:
        msg += "⚪ Su an belirgin formasyon tespit edilemedi.\n"
    else:
        msg += f"\n📊 Toplam {formasyon_count} formasyon tespit edildi."
    
    msg += "\n\n🌐 sentiflow.streamlit.app"
    send_telegram(msg)


def cmd_trend():
    """Trend analizi — yukselen ve dusen trendler."""
    msg = "📈📉 <b>TREND ANALIZI</b>\n"
    msg += f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
    
    yukselis = []
    dusus = []
    
    for symbol in WATCHLIST_BIST:
        r = calc_bist_signal(symbol)
        if r:
            if r['sent_puan'] > 7 and r['rsi'] > 50 and r['momentum'] > 0:
                yukselis.append(r)
            elif r['sent_puan'] < 3 and r['rsi'] < 40 and r['momentum'] < 0:
                dusus.append(r)
    
    yukselis.sort(key=lambda x: x['sent_puan'], reverse=True)
    dusus.sort(key=lambda x: x['sent_puan'])
    
    msg += "🟢 <b>YUKSELEN TREND:</b>\n"
    if yukselis:
        for r in yukselis[:7]:
            msg += f"  📈 <b>{r['name']}</b>: Sent {r['sent_puan']:.1f} | RSI {r['rsi']:.0f} | {r['change']:+.1f}%\n"
    else:
        msg += "  ⚪ Guclu yukselis trendi yok\n"
    
    msg += "\n🔴 <b>DUSEN TREND:</b>\n"
    if dusus:
        for r in dusus[:7]:
            msg += f"  📉 <b>{r['name']}</b>: Sent {r['sent_puan']:.1f} | RSI {r['rsi']:.0f} | {r['change']:+.1f}%\n"
    else:
        msg += "  ⚪ Guclu dusus trendi yok\n"
    
    msg += "\n🌐 sentiflow.streamlit.app"
    send_telegram(msg)


def cmd_kripto_detay():
    """Kripto detayli analiz."""
    msg = "🪙 <b>KRIPTO DETAYLI ANALIZ</b>\n"
    msg += f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
    
    for symbol in WATCHLIST_CRYPTO:
        r = calc_crypto_signal(symbol)
        if r:
            emoji = "🟢" if "AL" in r['decision'] else "🔴" if "SAT" in r['decision'] else "🟡"
            msg += f"{emoji} <b>{r['name']}</b>\n"
            msg += f"   💰 ${r['price']:,.2f} ({r['change']:+.1f}%)\n"
            msg += f"   📊 RSI: {r['rsi']:.0f} | Sent: {r['sent_puan']:.1f} | {r['decision']}\n\n"
    
    msg += "🌐 sentiflow.streamlit.app"
    send_telegram(msg)


def cmd_ozet():
    """Gunluk piyasa ozeti — en onemli sinyal."""
    msg = "🌊 <b>SENTIFLOW GUNLUK OZET</b>\n"
    msg += f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n\n"
    
    # Genel piyasa durumu
    results = []
    greens = 0
    reds = 0
    for symbol in WATCHLIST_BIST:
        r = calc_bist_signal(symbol)
        if r:
            results.append(r)
            if "AL" in r['decision']: greens += 1
            elif "SAT" in r['decision']: reds += 1
    
    total = len(results)
    yellows = total - greens - reds
    
    msg += f"📊 <b>Piyasa Durumu:</b>\n"
    msg += f"  🟢 AL: {greens}/{total}\n"
    msg += f"  🔴 SAT: {reds}/{total}\n"
    msg += f"  🟡 NOTR: {yellows}/{total}\n\n"
    
    # En guclu sinyal
    if results:
        results.sort(key=lambda x: x['sent_puan'], reverse=True)
        best = results[0]
        worst = results[-1]
        msg += f"⭐ <b>En Guclu:</b> {best['name']} (Sent: {best['sent_puan']:.1f}, {best['change']:+.1f}%)\n"
        msg += f"⚠️ <b>En Zayif:</b> {worst['name']} (Sent: {worst['sent_puan']:.1f}, {worst['change']:+.1f}%)\n\n"
    
    # Dip donusu
    dip_list = [r for r in results if r['rsi'] < 35]
    if dip_list:
        msg += f"🎯 <b>Dip Donusu Adaylari ({len(dip_list)}):</b>\n"
        for r in dip_list[:3]:
            msg += f"  🎯 {r['name']} (RSI: {r['rsi']:.0f})\n"
        msg += "\n"
    
    # Kripto ozet
    msg += "🪙 <b>Kripto:</b>\n"
    for symbol in WATCHLIST_CRYPTO[:5]:
        r = calc_crypto_signal(symbol)
        if r:
            emoji = "🟢" if r['change'] > 0 else "🔴"
            msg += f"  {emoji} {r['name']}: ${r['price']:,.2f} ({r['change']:+.1f}%)\n"
    
    msg += "\n━━━━━━━━━━━━━━━━━━━━"
    msg += "\n🌐 <b>sentiflow.streamlit.app</b>"
    msg += "\n📱 Detayli analiz icin siteyi ziyaret edin!"
    send_telegram(msg)


def cmd_alarm():
    """Onemli uyarilar — buyuk degisimler."""
    msg = "🚨 <b>ONEMLI UYARILAR</b>\n"
    msg += f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
    
    alarm_count = 0
    
    # BIST alarmlari
    for symbol in WATCHLIST_BIST:
        r = calc_bist_signal(symbol)
        if r:
            if r['change'] > 5:
                msg += f"🚀 <b>{r['name']}</b>: +%{r['change']:.1f} SERT YUKSELIS!\n"
                alarm_count += 1
            elif r['change'] < -5:
                msg += f"💥 <b>{r['name']}</b>: %{r['change']:.1f} SERT DUSUS!\n"
                alarm_count += 1
            elif r['rsi'] > 80:
                msg += f"⚠️ <b>{r['name']}</b>: RSI {r['rsi']:.0f} — ASIRI ALIM!\n"
                alarm_count += 1
            elif r['rsi'] < 20:
                msg += f"💎 <b>{r['name']}</b>: RSI {r['rsi']:.0f} — ASIRI SATIM!\n"
                alarm_count += 1
    
    # Kripto alarmlari
    for symbol in WATCHLIST_CRYPTO:
        r = calc_crypto_signal(symbol)
        if r:
            if r['change'] > 7:
                msg += f"🚀 <b>{r['name']}</b>: +%{r['change']:.1f} SERT YUKSELIS!\n"
                alarm_count += 1
            elif r['change'] < -7:
                msg += f"💥 <b>{r['name']}</b>: %{r['change']:.1f} SERT DUSUS!\n"
                alarm_count += 1
    
    if alarm_count == 0:
        msg += "✅ Su an onemli bir alarm yok. Piyasa sakin.\n"
    
    msg += "\n🌐 sentiflow.streamlit.app"
    send_telegram(msg)

def handle_message(text):
    text = text.strip().lower()
    if text == "/start" or text == "/help":
        cmd_help()
    elif text == "/sinyal":
        cmd_sinyal()
    elif text == "/bist":
        cmd_bist()
    elif text == "/kripto":
        cmd_kripto_detay()
    elif text == "/dip":
        cmd_dip()
    elif text == "/top5":
        cmd_top5()
    elif text == "/formasyon":
        cmd_formasyon()
    elif text == "/trend":
        cmd_trend()
    elif text == "/ozet":
        cmd_ozet()
    elif text == "/alarm":
        cmd_alarm()
    else:
        msg = "🌊 <b>SentiFlow Bot</b>\n\n"
        msg += "Komut bulunamadi. /help yazarak komutlari gorebilirsin."
        send_telegram(msg)


if __name__ == "__main__":
    print("🌊 SentiFlow Telegram Bot v2 Baslatildi!")
    print("Komutlar: /sinyal /bist /kripto /help")
    print("Ctrl+C ile durdur.\n")
    
    # Baslangic mesaji
    send_telegram("🌊 <b>SentiFlow Bot aktif!</b>\n\nKomutlar:\n/sinyal — Tum sinyaller\n/bist — BIST analiz\n/kripto — Kripto analiz\n/help — Yardim")
    
        offset = None
    alert_check = 0
    daily_sent = False
    while True:
        try:
            # Gunluk otomatik ozet (09:30)
            now = datetime.now()
            if now.hour == 9 and now.minute >= 30 and now.minute < 33 and not daily_sent:
                cmd_ozet()
                daily_sent = True
                print(f"📊 Gunluk ozet gonderildi: {now.strftime('%H:%M')}")
            if now.hour == 10:
                daily_sent = False
            
            updates = get_updates(offset)
            for update in updates:
                offset = update["update_id"] + 1
                msg = update.get("message", {})
                text = msg.get("text", "")
                if text:
                    print(f"Komut: {text}")
                    handle_message(text)
            
            # Her 30 dakikada alarm kontrol
            alert_check += 1
            if alert_check >= 900:
                check_alerts()
                alert_check = 0
            
            time.sleep(2)
        except KeyboardInterrupt:
            print("\nBot durduruldu.")
            break
        except Exception as e:
            print(f"Hata: {e}")
            time.sleep(5)
 