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
    st.markdown("<p style='font-size:11px; color:#ff4b4b; margin-top:-10px; margin-bottom:0px;'><b>⚠️ DİKKAT:</b> Canlı fiyatı doğru giriniz, aksi halde sonuçlar yanlış çıkar!</p>", unsafe_allow_html=True)

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
                    
                    # --- 8 İNDİKATÖR HESAPLAMA VE AÇIKLAMALI DEĞERLERİ ---
                    
                    # 1. EMA 20/50
                    ema20 = df['Close'].ewm(span=20, adjust=False).mean()
                    ema50 = df['Close'].ewm(span=50, adjust=False).mean()
                    val_ema20 = float(ema20.iloc[-1])
                    val_ema50 = float(ema50.iloc[-1])
                    if val_ema20 > val_ema50:
                        ema_signal = f"[ + ] ⭐ (EMA20: {val_ema20:.2f} > EMA50: {val_ema50:.2f})"
                    else:
                        ema_signal = f"[ - ] ⚠️ (EMA20: {val_ema20:.2f} < EMA50: {val_ema50:.2f})"
                    
                    # 2. MACD
                    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
                    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
                    macd_line = exp1 - exp2
                    signal_line = macd_line.ewm(span=9, adjust=False).mean()
                    val_macd = float(macd_line.iloc[-1])
                    val_sig = float(signal_line.iloc[-1])
                    if val_macd > val_sig:
                        macd_signal = f"[ + ] ⭐ (MACD: {val_macd:.2f} > Sinyal: {val_sig:.2f})"
                    else:
                        macd_signal = f"[ - ] ⚠️ (MACD: {val_macd:.2f} < Sinyal: {val_sig:.2f})"
                    
                    # 3. TEMA
                    ema1 = df['Close'].ewm(span=9).mean()
                    ema2 = ema1.ewm(span=9).mean()
                    ema3 = ema2.ewm(span=9).mean()
                    tema = 3 * (ema1 - ema2) + ema3
                    val_tema = float(tema.iloc[-1])
                    if df['Close'].iloc[-1] > val_tema:
                        tema_signal = f"[ + ] (Fiyat > TEMA: {val_tema:.2f})"
                    else:
                        tema_signal = f"[ - ] (Fiyat < TEMA: {val_tema:.2f})"
                    
                    # 4. Hacim
                    vol_current = float(df['Volume'].iloc[-1])
                    vol_ma = float(df['Volume'].rolling(20).mean().iloc[-1])
                    if vol_current > vol_ma:
                        vol_signal = f"[ + ] (Hacim: {vol_current:,.0f} > Ort)"
                    else:
                        vol_signal = f"[ - ] (Hacim: {vol_current:,.0f} < Ort)"
                    
                    # 5. OBV
                    obv = (np.sign(df['Close'].diff()) * df['Volume']).fillna(0).cumsum()
                    obv_ma = obv.rolling(10).mean()
                    val_obv = float(obv.iloc[-1])
                    val_obv_ma = float(obv_ma.iloc[-1])
                    if val_obv > val_obv_ma:
                        obv_signal = f"[ + ] (OBV > OBV Ort)"
                    else:
                        obv_signal = f"[ - ] (OBV < OBV Ort)"
                    
                    # 6. Stochastic
                    low_14 = df['Low'].rolling(14).min()
                    high_14 = df['High'].rolling(14).max()
                    stoch_k = 100 * ((df['Close'] - low_14) / (high_14 - low_14))
                    stoch_d = stoch_k.rolling(3).mean()
                    val_stoch_k = float(stoch_k.iloc[-1])
                    val_stoch_d = float(stoch_d.iloc[-1])
                    if val_stoch_k > val_stoch_d:
                        stoch_signal = f"[ + ] ⭐ (%K: {val_stoch_k:.1f} > %D: {val_stoch_d:.1f})"
                    else:
                        stoch_signal = f"[ - ] ⚠️ (%K: {val_stoch_k:.1f} < %D: {val_stoch_d:.1f})"
                    
                    # 7. ATR
                    high_low = df['High'] - df['Low']
                    high_close = np.abs(df['High'] - df['Close'].shift())
                    low_close = np.abs(df['Low'] - df['Close'].shift())
                    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
                    atr = tr.rolling(14).mean()
                    val_atr = float(atr.iloc[-1])
                    val_atr_ma = float(atr.rolling(30).mean().iloc[-1])
                    if val_atr > val_atr_ma:
                        atr_signal = f"[ + ] (ATR: {val_atr:.2f} > Volatiliteli)"
                    else:
                        atr_signal = f"[ - ] (ATR: {val_atr:.2f} < Durgun)"
                    
                    # 8. Bollinger Bands (BB)
                    bb_mid = df['Close'].rolling(20).mean()
                    val_bb = float(bb_mid.iloc[-1])
                    if df['Close'].iloc[-1] > val_bb:
                        bb_signal = f"[ + ] (Fiyat > BB Orta: {val_bb:.2f})"
                    else:
                        bb_signal = f"[ - ] (Fiyat < BB Orta: {val_bb:.2f})"
                    
                    # Skorlama
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
                    
                    # Son seansın min, max ve ortalama değerleri
                    min_val = float(df['Low'].iloc[-1])
                    max_val = float(df['High'].iloc[-1])
                    ort_val = float((df['High'].iloc[-1] + df['Low'].iloc[-1] + df['Close'].iloc[-1]) / 3)
                    
                    current_time = datetime.now().strftime("%H:%M")
                    
                    # --- TABLO FORMATINDA ÇIKTI EKRANI ---
                    st.markdown("---")
                    st.markdown("🕒 `" + current_time + "` &nbsp;|&nbsp; **Alış:** `" + f"{last_price:.2f}" + "` &nbsp;|&nbsp; **TP (%5):** `" + f"{take_profit:.2f}" + "`")
                    st.markdown("🛑 **Stop-Loss (%1.5):** `" + f"{stop_loss:.2f}" + "`")
                    st.markdown("--------------------------------------------------")
                    
                    c1, c2, c3, c4 = st.columns(4)
                    with c1:
                        st.write("**Periyot**")
                        st.write(period_choice)
                    with c2:
                        st.write("**Min (SL)**")
                        st.write("`" + f"{min_val:.2f}" + "`")
                    with c3:
                        st.write("**Ort**")
                        st.write("`" + f"{ort_val:.2f}" + "`")
                    with c4:
                        st.write("**Max**")
                        st.write("`" + f"{max_val:.2f}" + "`")
                        
                    st.markdown("--------------------------------------------------")
                    
                    # Alt alta net görünüm için indikatör satırları
                    st.markdown("**MACD:** `" + macd_signal + "`")
                    st.markdown("**EMA20/50:** `" + ema_signal + "`")
                    st.markdown("**TEMA:** `" + tema_signal + "`")
                    st.markdown("**Stochastic:** `" + stoch_signal + "`")
                    st.markdown("**Hacim:** `" + vol_signal + "`")
                    st.markdown("**OBV:** `" + obv_signal + "`")
                    st.markdown("**ATR:** `" + atr_signal + "`")
                    st.markdown("**Bollinger (BB):** `" + bb_signal + "`")
                        
                    st.markdown("--------------------------------------------------")
                    st.markdown("**SİNYAL** &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; `" + sinyal_text + "` &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; **Skor :** `" + str(score) + "/8`")
                    st.markdown("--------------------------------------------------")
                    st.caption("⭐ **Not:** Yıldız simgesi pozitif kesişimi (Golden Cross), ⚠️ simgesi ise negatif kesişimi (Death Cross) gösterir.")
                    
                    # --- EĞİTİM VE İNDİKATÖR ANLAMLARI BÖLÜMÜ ---
                    with st.expander("📚 İndikatör Değerleri ve Anlamları (Eğitim Rehberi)"):
                        st.markdown("""
                        - **EMA20/50 (Üstel Hareketli Ortalama):** 20 periyotluk ortalamanın 50 periyotluk ortalama üzerindeki konumunu ölçer. EMA20'nin EMA50'yi yukarı kesmesi pozitif trend onayıdır.
                        - **MACD:** Fiyat momentumunu gösterir. Sıfırın üzerinde pozitif kesişim boğa piyasasına, sıfırın altında kalması ise ayı piyasasına işaret eder.
                        - **TEMA (Üçlü Üstel Ort.):** Gecikmeyi en aza indiren hızlı ortalamadır. Fiyatın TEMA değerinin üzerinde olması kısa vadeli güçlü yükseliş ivmesini gösterir.
                        - **Hacim (Volume):** Son mummaki işlem adedidir. Hacmin 20 günlük ortalamasının üzerinde olması, gerçekleşen hareketin büyük yatırımcılarca desteklendiğini gösterir.
                        - **OBV (Denge İşlem Hacmi):** Para giriş-çıkışını ölçer. OBV değerinin ortalamasının üzerine çıkması, hisseye taze para girişi olduğunu gösterir.
                        - **Stochastic (Oscillator):** 0-100 arasında değer alır. 20 seviyesi altı aşırı satış (fırsat), 80 üzeri aşırı alım bölgesidir. K çizgisinin D çizgisini yukarı kesmesi al sinyalidir.
                        - **ATR (Ortalama Gerçek Aralık):** Hissenin oynaklığını (volatilitesini) ölçer. ATR değerinin yükselmesi hissede sert hareketlerin yaklaştığını gösterir.
                        - **BB (Bollinger Bandı Orta Çizgisi):** Hissenin 20 periyotluk basit ortalamasıdır. Fiyatın bant ortasının üzerinde kalması yükseliş trendinin devam ettiğini doğrular.
                        """)
                    
    except Exception as e:
        st.error(f"Bir hata oluştu: {e}")
