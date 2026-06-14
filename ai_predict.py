"""
SentiFlow AI — Basit Tahmin Modeli
Geçmiş verilere dayalı trend tahmini
"""

import yfinance as yf
import pandas as pd
import numpy as np
from ta import momentum, trend


def predict_trend(symbol, period="6mo"):
    """
    Basit AI tahmin modeli.
    Son 5 günlük pattern'e göre gelecek 3 gün tahmini.
    """
    try:
        df = yf.Ticker(symbol).history(period=period, interval="1d")
        if df.empty or len(df) < 50:
            return None
        
        close = df['Close']
        
        # Göstergeler
        rsi = momentum.RSIIndicator(close, window=14).rsi()
        macd = trend.MACD(close)
        macd_hist = macd.macd_diff()
        ema9 = close.ewm(span=9).mean()
        ema21 = close.ewm(span=21).mean()
        ema50 = close.ewm(span=50).mean()
        
        # Son değerler
        price = float(close.iloc[-1])
        rsi_val = float(rsi.iloc[-1])
        macd_val = float(macd_hist.iloc[-1])
        
        # Pattern analizi (son 5 gün)
        last5 = close.iloc[-5:]
        returns = last5.pct_change().dropna()
        avg_return = float(returns.mean())
        volatility = float(returns.std())
        
        # Trend gücü
        trend_strength = 0
        
        # RSI bazlı
        if rsi_val < 30:
            trend_strength += 3  # Dönüş beklenir
        elif rsi_val > 70:
            trend_strength -= 3  # Düşüş beklenir
        elif rsi_val > 50:
            trend_strength += 1
        else:
            trend_strength -= 1
        
        # MACD bazlı
        if macd_val > 0:
            prev_macd = float(macd_hist.iloc[-2])
            if macd_val > prev_macd:
                trend_strength += 2  # Güçleniyor
            else:
                trend_strength += 1
        else:
            prev_macd = float(macd_hist.iloc[-2])
            if macd_val < prev_macd:
                trend_strength -= 2  # Zayıflıyor
            else:
                trend_strength -= 1
        
        # EMA bazlı
        if float(ema9.iloc[-1]) > float(ema21.iloc[-1]):
            trend_strength += 1
        else:
            trend_strength -= 1
        
        if price > float(ema50.iloc[-1]):
            trend_strength += 1
        else:
            trend_strength -= 1
        
        # Momentum bazlı
        if avg_return > 0.005:
            trend_strength += 2
        elif avg_return < -0.005:
            trend_strength -= 2
        
        # Tahmin
        if trend_strength >= 4:
            prediction = "📈 Güçlü Yükseliş"
            confidence = min(85, 60 + trend_strength * 3)
            target_pct = round(avg_return * 300 + 1.5, 1)
        elif trend_strength >= 2:
            prediction = "📈 Hafif Yükseliş"
            confidence = min(75, 55 + trend_strength * 3)
            target_pct = round(avg_return * 200 + 0.5, 1)
        elif trend_strength <= -4:
            prediction = "📉 Güçlü Düşüş"
            confidence = min(85, 60 + abs(trend_strength) * 3)
            target_pct = round(avg_return * 300 - 1.5, 1)
        elif trend_strength <= -2:
            prediction = "📉 Hafif Düşüş"
            confidence = min(75, 55 + abs(trend_strength) * 3)
            target_pct = round(avg_return * 200 - 0.5, 1)
        else:
            prediction = "➡️ Yatay"
            confidence = 50
            target_pct = round(avg_return * 100, 1)
        
        target_price = round(price * (1 + target_pct / 100), 2)
        
        # Destek / Direnç seviyeleri
        support = round(float(close.iloc[-20:].min()), 2)
        resistance = round(float(close.iloc[-20:].max()), 2)
        
        return {
            'prediction': prediction,
            'confidence': confidence,
            'target_pct': target_pct,
            'target_price': target_price,
            'trend_strength': trend_strength,
            'support': support,
            'resistance': resistance,
            'volatility': round(volatility * 100, 2),
            'price': price,
        }
    except:
        return None


if __name__ == "__main__":
    # Test
    result = predict_trend("THYAO.IS")
    if result:
        print(f"THYAO Tahmin: {result['prediction']}")
        print(f"Güven: %{result['confidence']}")
        print(f"Hedef: ₺{result['target_price']} (%{result['target_pct']})")
        print(f"Destek: ₺{result['support']} | Direnç: ₺{result['resistance']}")
