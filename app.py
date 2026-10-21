import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# Sayfa Yapılandırması
st.set_page_config(page_title="BIST Teknik Analiz Paneli", layout="centered")

st.title("📈 BIST Otomatik 8 İndikatör Skorlama Paneli")
st.write("Doğrudan Borsa İstanbul verileriyle saf matematiksel ve objektif teknik analiz!")

# Hisse Kodu ve Canlı Fiyat Girişi Yan Yana
col_t, col_m = st.columns(2)
with col_t:
    ticker_input = st.text_input("Hisse Kodu (Örn: THYAO, BERA, BIMAS)", value="BIMAS")
with col_m:
    manual_price_str = st.text_input("Ziraat Canlı Fiyat (İsteğe Bağlı)", value="")

clean_ticker = ticker_input.strip().upper()
if not clean_ticker.endswith(".IS"):
    clean_ticker += ".IS"

period_choice = st.selectbox("Periyot Seçin", ["5 Dakika", "1 Saat", "Günlük"])

# Periyot eşleştirmesi
if period_choice == "5 Dakika":
    interval = "5m"
    period = "5d"
elif period_choice == "1 Saat":
    interval = "1h"
    period = "1mo"
else:
    interval = "1d"
    period = "6mo"

if st.button("Teknik Analizi Hesapla"):
    try:
        with st.spinner("Veriler indiriliyor ve analiz ediliyor..."):
            df = yf.download(clean_ticker, period=period, interval=interval, progress=False)
            
            if df.empty:
                st.error("Hisse verisi bulunamadı. Lütfen geçerli bir hisse kodu girin.")
            else:
                # Çok katmanlı sütun başlığı sorununu çözme
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                
                # Eksik verileri temizleme
                df = df.dropna(subset=['Close', 'High', 'Low', 'Volume'])
                
                if df.empty:
                    st.error("İşlenecek geçerli veri kalmadı.")
                else:
                    # Son geçerli fiyatı çekme
                    default_yf_price = float(df['Close'].iloc[-1])
                    
                    # Manuel fiyat kontrolü
                    try:
                        if manual_price_str.strip() != "":
                            manual_price = float(manual_price_str.replace(",", "."))
                        else:
                            manual_price = 0.0
                    except:
                        manual_price = 0.0

                    if manual_price > 0:
                        last_price = manual_price
                    else:
                        last_price = default_yf_price
                    
                    # --- 8 İNDİKATÖR HESAPLAMA MANTIĞI & YILDIZ (GOLDEN CROSS) KONTROLÜ ---
                    
                    # 1. EMA 20/50 (Kesişim)
                    ema20 = df['Close'].ewm(span=20, adjust=False).mean()
                    ema50 = df['Close'].ewm(span=50, adjust=False).mean()
                    if ema20.iloc[-1] > ema50.iloc[-1]:
                        ema_signal = "[ + ] ⭐"
                    else:
                        ema_signal = "[ - ]"
                    
                    # 2. MACD (Kesişim)
                    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
                    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
                    macd_line = exp1 - exp2
                    signal_line = macd_line.ewm(span=9, adjust=False).mean()
                    if macd_line.iloc[-1] > signal_line.iloc[-1]:
                        macd_signal = "[ + ] ⭐"
                    else:
                        macd_signal = "[ - ]"
                    
                    # 3. TEMA
                    ema1 = df['Close'].ewm(span=9).mean()
                    ema2 = ema1.ewm(span=9).mean()
                    ema3 = ema2.ewm(span=9).mean()
                    tema = 3 * (ema1 - ema2) + ema3
                    tema_signal = "[ + ]" if df['Close'].iloc[-1] > tema.iloc[-1] else "[ - ]"
                    
                    # 4. Hacim
                    vol_current = df['Volume'].iloc[-1]
                    vol_ma = df['Volume'].rolling(20).mean().iloc[-1]
                    vol_signal = "[ + ]" if vol_current > vol_ma else "[ - ]"
                    
                    # 5. OBV
                    obv = (np.sign(df['Close'].diff()) * df['Volume']).fillna(0).cumsum()
                    obv_ma = obv.rolling(10).mean()
                    obv_signal = "[ + ]" if obv.iloc[-1] > obv_ma.iloc[-1] else "[ - ]"
                    
                    # 6. Stochastic (Kesişim)
                    low_14 = df['Low'].rolling(14).min()
                    high_14 = df['High'].rolling(14).max()
                    stoch_k = 100 * ((df['Close'] - low_14) / (high_14 - low_14))
                    stoch_d = stoch_k.rolling(3).mean()
                    if stoch_k.iloc[-1] > stoch_d.iloc[-1]:
                        stoch_signal = "[ + ] ⭐"
                    else:
                        stoch_signal = "[ - ]"
                    
                    # 7. ATR
                    high_low = df['High'] - df['Low']
                    high_close = np.abs(df['High'] - df['Close'].shift())
                    low_close = np.abs(df['Low'] - df['Close'].shift())
                    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
                    atr = tr.rolling(14).mean()
                    atr_signal = "[ + ]" if atr.iloc[-1] > atr.rolling(30).mean().iloc[-1] else "[ - ]"
                    
                    # 8. Bollinger Bands (BB)
                    bb_mid = df['Close'].rolling(20).mean()
                    bb_signal = "[ + ]" if df['Close'].iloc[-1] > bb_mid.iloc[-1] else "[ - ]"
                    
                    # Skorlama (İçinde '+' geçen tüm sinyalleri sayar)
                    signals = [macd_signal, ema_signal, obv_signal, atr_signal, tema_signal, vol_signal, stoch_signal, bb_signal]
                    score = sum(1 for s in signals if "[ + ]" in s)
                    
                    if score >= 6:
                        sinyal_text = "GÜÇLÜ AL"
                    elif score >= 4:
                        sinyal_text = "BEKLE"
                    else:
                        sinyal_text = "SAT"

                    stop_loss = last_price * (1 - 0.015)
                    take_profit = last_price * (1 + 0.05)
                    
                    # Son seansın (bugünkü mumun) min, max ve ortalama değerleri
                    min_val = float(df['Low'].iloc[-1])
                    max_val = float(df['High'].iloc[-1])
                    ort_val = float((df['High'].iloc[-1] + df['Low'].iloc[-1] + df['Close'].iloc[-1]) / 3)
                    
                    current_time = datetime.now().strftime("%H:%M")
                    
                    # --- TABLO FORMATINDA ÇIKTI EKRANI ---
                    st.markdown("---")
                    st.markdown(f"🕒 `{current_time}` &nbsp;|&nbsp; **Alış:** `{last_price:.2f}` &nbsp;|&nbsp; **TP (%5):** `{take_profit:.2f}`")
                    st.markdown(f"🛑 **Stop-Loss (%1.5):** `{stop_loss:.2f}`")
                    st.markdown("--------------------------------------------------")
                    
                    c1, c2, c3, c4 = st.columns(4)
                    with c1:
                        st.write("**Periyot**")
                        st.write(period_choice)
                    with c2:
                        st.write("**Min (SL)**")
                        st.write(f"`{min_val:.2f}`")
                    with c3:
                        st.write("**Ort**")
                        st.write(f"`{ort_val:.2f}`")
                    with c4:
                        st.write("**Max**")
                        st.write(f"`{max_val:.2f}`")
                        
                    st.markdown("--------------------------------------------------")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**MACD** &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; `{macd_signal}`")
                        st.markdown(f"**EMA20/50** &nbsp;&nbsp;&nbsp; `{ema_signal}`")
                        st.markdown(f"**OBV** &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
