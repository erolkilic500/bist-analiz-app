import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# Sayfa Yapılandırması
st.set_page_config(page_title="BIST Teknik Analiz Paneli", layout="wide")

st.title("📈 BIST Otomatik 8 İndikatör Skorlama ve Grafik Paneli")
st.write("Doğrudan Borsa İstanbul verileriyle saf matematiksel ve objektif teknik analiz!")

# Hisse Kodu ve Canlı Fiyat Girişi Yan Yana
col_t, col_m = st.columns(2)
with col_t:
    ticker_input = st.text_input("Hisse Kodu (Örn: THYAO, BERA, BIMAS)", value="BIMAS")
with col_m:
    manual_price_str = st.text_input("Ziraat Canlı Fiyat", value="")
    st.markdown("<p style='font-size:12px; color:#ff4b4b; font-weight:bold; margin-top:-10px; margin-bottom:0px;'>DOĞRU SONUÇ ALMAK İSTİYORSANIZ ZİRAAT/MİDAS VB ARACI KURUMUNDAKİ HİSSENİN ANLIK FİYATINI YAZINIZ</p>", unsafe_allow_html=True)

clean_ticker = ticker_input.strip().upper()
if not clean_ticker.endswith(".IS"):
    clean_ticker += ".IS"

# Tüm İstenecek Periyot Seçenekleri
period_options = [
    "1 Dakika", "2 Dakika", "3 Dakika", "5 Dakika", "10 Dakika", "15 Dakika", "30 Dakika", "45 Dakika",
    "1 Saat", "2 Saat", "3 Saat", "4 Saat",
    "1 Günlük", "1 Haftalık", "1 Aylık", "3 Aylık", "6 Aylık", "1 Yıllık"
]

period_choice = st.selectbox("Periyot Seçin", period_options, index=3) # Varsayılan: 5 Dakika

# Yahoo Finance İçin Periyot ve Interval (Aralık) Eşleştirmesi
interval_map = {
    "1 Dakika": ("1m", "7d"),
    "2 Dakika": ("2m", "1mo"),
    "3 Dakika": ("2m", "1mo"),
    "5 Dakika": ("5m", "1mo"),
    "10 Dakika": ("5m", "1mo"),
    "15 Dakika": ("15m", "1mo"),
    "30 Dakika": ("30m", "3mo"),
    "45 Dakika": ("15m", "3mo"),
    "1 Saat": ("1h", "6mo"),
    "2 Saat": ("1h", "1y"),
    "3 Saat": ("1h", "1y"),
    "4 Saat": ("1h", "2y"),
    "1 Günlük": ("1d", "2y"),
    "1 Haftalık": ("1wk", "5y"),
    "1 Aylık": ("1mo", "10y"),
    "3 Aylık": ("3mo", "max"),
    "6 Aylık": ("3mo", "max"),
    "1 Yıllık": ("1mo", "max")
}

interval, period = interval_map.get(period_choice, ("5m", "1mo"))

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
                df = df.dropna(subset=['Close', 'High', 'Low', 'Volume', 'Open'])
                
                if df.empty or len(df) < 5:
                    st.error("Seçilen periyot için yeterli teknik veri hesaplanamadı.")
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
                    ema_t1 = df['Close'].ewm(span=9).mean()
                    ema_t2 = ema_t1.ewm(span=9).mean()
                    ema_t3 = ema_t2.ewm(span=9).mean()
                    tema = 3 * (ema_t1 - ema_t2) + ema_t3
                    val_tema = float(tema.iloc[-1])
                    if df['Close'].iloc[-1] > val_tema:
                        tema_signal = f"[ + ] (Fiyat > TEMA: {val_tema:.2f})"
                    else:
                        tema_signal = f"[ - ] (Fiyat < TEMA: {val_tema:.2f})"
                    
                    # 4. Hacim
                    vol_current = float(df['Volume'].iloc[-1])
                    vol_ma = float(df['Volume'].rolling(20).mean().iloc[-1]) if len(df) >= 20 else float(df['Volume'].mean())
                    if vol_current > vol_ma:
                        vol_signal = f"[ + ] (Hacim: {vol_current:,.0f} > Ort)"
                    else:
                        vol_signal = f"[ - ] (Hacim: {vol_current:,.0f} < Ort)"
                    
                    # 5. OBV
                    obv = (np.sign(df['Close'].diff()) * df['Volume']).fillna(0).cumsum()
                    obv_ma = obv.rolling(10).mean() if len(df) >= 10 else obv.mean()
                    val_obv = float(obv.iloc[-1])
                    val_obv_ma = float(obv_ma.iloc[-1]) if isinstance(obv_ma, pd.Series) else float(obv_ma)
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
                    atr_ma = atr.rolling(30).mean().iloc[-1] if len(df) >= 30 else atr.mean()
                    if val_atr > float(atr_ma):
                        atr_signal = f"[ + ] (ATR: {val_atr:.2f} > Volatiliteli)"
                    else:
                        atr_signal = f"[ - ] (ATR: {val_atr:.2f} < Durgun)"
                    
                    # 8. Bollinger Bands (BB)
                    bb_mid = df['Close'].rolling(20).mean() if len(df) >= 20 else df['Close'].mean()
                    val_bb = float(bb_mid.iloc[-1]) if isinstance(bb_mid, pd.Series) else float(bb_mid)
                    bb_std = df['Close'].rolling(20).std() if len(df) >= 20 else df['Close'].std()
                    val_std = float(bb_std.iloc[-1]) if isinstance(bb_std, pd.Series) else float(bb_std)
                    bb_upper = bb_mid + (2 * val_std)
                    bb_lower = bb_mid - (2 * val_std)
                    
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
                        st.write("`" + f"{max_val:.2f}`")
                        
                    st.markdown("--------------------------------------------------")
                    
                    # İndikatör satırları
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
                    
                    # --- PROFESYONEL ÇOKLU PANEL GRAFİK (SUBPLOTS) ---
                    st.subheader("📊 Profesyonel İndikatörlü Fiyat ve Osilatör Grafikleri")
                    
                    # 3 Satırlı Alt Alta Grafik Paneli (1. Fiyat/Bollinger/EMA/TEMA, 2. MACD, 3. Stochastic)
                    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, 
                                        vertical_spacing=0.05, 
                                        row_heights=[0.6, 0.2, 0.2])
                    
                    # 1. Panel: Fiyat Mumları, Bollinger Bantları, EMA 20/50 ve TEMA
                    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Mumlar'), row=1, col=1)
                    fig.add_trace(go.Scatter(x=df.index, y=ema20, mode='lines', name='EMA 20', line=dict(color='orange', width=1.2)), row=1, col=1)
                    fig.add_trace(go.Scatter(x=df.index, y=ema50, mode='lines', name='EMA 50', line=dict(color='dodgerblue', width=1.2)), row=1, col=1)
                    fig.add_trace(go.Scatter(x=df.index, y=tema, mode='lines', name='TEMA', line=dict(color='purple', width=1.2)), row=1, col=1)
                    fig.add_trace(go.Scatter(x=df.index, y=bb_upper, mode='lines', name='BB Üst', line=dict(color='gray', width=1, dash='dot')), row=1, col=1)
                    fig.add_trace(go.Scatter(x=df.index, y=bb_lower, mode='lines', name='BB Alt', line=dict(color='gray', width=1, dash='dot'), fill='tonexty', fillcolor='rgba(128,128,128,0.05)'), row=1, col=1)
                    
                    # 2. Panel: MACD ve Sinyal Çizgisi
                    fig.add_trace(go.Scatter(x=df.index, y=macd_line, mode='lines', name='MACD', line=dict(color='cyan', width=1.5)), row=2, col=1)
                    fig.add_trace(go.Scatter(x=df.index, y=signal_line, mode='lines', name='MACD Sinyal', line=dict(color='magenta', width=1.5)), row=2, col=1)
                    
                    # 3. Panel: Stochastic (%K ve %D)
                    fig.add_trace(go.Scatter(x=df.index, y=stoch_k, mode='lines', name='Stoch %K', line=dict(color='yellow', width=1.5)), row=3, col=1)
                    fig.add_trace(go.Scatter(x=df.index, y=stoch_d, mode='lines', name='Stoch %D', line=dict(color='red', width=1.5)), row=3, col=1)
                    
                    fig.update_layout(
                        template="plotly_dark",
                        height=750,
                        margin=dict(l=10, r=10, t=30, b=10),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
