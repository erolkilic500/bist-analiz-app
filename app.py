import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

st.set_page_config(page_title="BIST 5dk Teknik Analiz Paneli", layout="wide")

st.title("📈 BIST 5 Dakikalık Scalping ve İndikatör Puanlama Paneli")
st.write("Doğrudan Borsa İstanbul verileriyle saf matematiksel ve objektif teknik analiz!")

if 'last_searched_ticker' not in st.session_state:
    st.session_state['last_searched_ticker'] = ""

col_t, col_m = st.columns(2)
with col_t:
    ticker_input = st.text_input("Hisse Kodu (Örn: THYAO, BERA, BIMAS, TGSAS)", value="TGSAS")
with col_m:
    manual_price_str = st.text_input("Ziraat Canlı Fiyat", value="")
    st.markdown("<p style='font-size:12px; color:#ff4b4b; font-weight:bold; margin-top:-10px; margin-bottom:0px;'>DOĞRU SONUÇ ALMAK İSTİYORSANIZ ZİRAAT/MİDAS VB ARACI KURUMUNDAKİ HİSSENİN ANLIK FİYATINI YAZINIZ</p>", unsafe_allow_html=True)

clean_ticker = ticker_input.strip().upper()
if not clean_ticker.endswith(".IS"):
    clean_ticker += ".IS"

period_options = [
    "1 Dakika", "2 Dakika", "3 Dakika", "5 Dakika", "10 Dakika", "15 Dakika", "30 Dakika", "45 Dakika",
    "1 Saat", "2 Saat", "3 Saat", "4 Saat",
    "1 Günlük", "1 Haftalık", "1 Aylık", "3 Aylık", "6 Aylık", "1 Yıllık"
]

period_choice = st.selectbox("Periyot Seçin", period_options, index=3) # Varsayılan: 5 Dakika

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
    "1 Yıllık": ("3mo", "max")
}

interval, period = interval_map.get(period_choice, ("5m", "1mo"))

if st.button("Teknik Analizi Hesapla"):
    st.session_state['last_searched_ticker'] = clean_ticker
    try:
        with st.spinner(f"{clean_ticker} verileri indiriliyor ve analiz ediliyor..."):
            df = yf.download(clean_ticker, period=period, interval=interval, progress=False)
            
            if df.empty:
                st.error("Hisse verisi bulunamadı. Lütfen geçerli bir hisse kodu girin.")
            else:
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                
                df = df.dropna(subset=['Close', 'High', 'Low', 'Volume', 'Open'])
                
                if df.empty or len(df) < 10:
                    st.error("Seçilen periyot için yeterli teknik veri hesaplanamadı.")
                else:
                    default_yf_price = float(df['Close'].iloc[-1])
                    
                    # DÜZELTME: Min, Max ve Ort değerleri tüm dönemin değil, son mumun (veya son 20 barın scalping aralığının) sınırları olarak alınıyor
                    recent_df = df.tail(20) # Son 20 bar (scalping penceresi)
                    period_min = float(recent_df['Low'].min())
                    period_max = float(recent_df['High'].max())
                    
                    manual_price = 0.0
                    try:
                        if manual_price_str.strip() != "":
                            manual_price = float(manual_price_str.replace(",", "."))
                    except:
                        manual_price = 0.0

                    if manual_price > 0:
                        if manual_price < (period_min * 0.7) or manual_price > (period_max * 1.3):
                            st.warning(f"⚠️ Girilen fiyat hissenin güncel aralığından farklı! Otomatik borsa verisi ({default_yf_price:.2f} TL) kullanıldı.")
                            last_price = default_yf_price
                        else:
                            last_price = manual_price
                    else:
                        last_price = default_yf_price
                    
                    # --- 10 İNDİKATÖR, BİREYSEL PUAN VE DURUM AÇIKLAMALARI ---
                    
                    def get_status_label(score):
                        if score >= 9:
                            return "🟢 **[Çok İyi]**"
                        elif score >= 7:
                            return "🟢 **[Uygun]**"
                        elif score >= 5:
                            return "🟡 **[Nötr]**"
                        else:
                            return "🔴 **[Zayıf / Riskli]**"

                    # 1. RSI (14)
                    delta = df['Close'].diff()
                    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                    rs = gain / loss
                    rsi = 100 - (100 / (1 + rs))
                    val_rsi = float(rsi.iloc[-1])
                    if 40 <= val_rsi <= 70:
                        rsi_signal = f"[ + ] (RSI: {val_rsi:.1f})"
                        rsi_score = 9
                    elif val_rsi < 30:
                        rsi_signal = f"[ + ] ⭐ (RSI: {val_rsi:.1f} Dip Adayı)"
                        rsi_score = 8
                    elif val_rsi > 70:
                        rsi_signal = f"[ - ] ⚠️ (RSI: {val_rsi:.1f} Aşırı Alım)"
                        rsi_score = 4
                    else:
                        rsi_signal = f"[ - ] (RSI: {val_rsi:.1f})"
                        rsi_score = 5

                    # 2. SuperTrend (10, 3)
                    hl2 = (df['High'] + df['Low']) / 2
                    high_low = df['High'] - df['Low']
                    high_close = np.abs(df['High'] - df['Close'].shift())
                    low_close = np.abs(df['Low'] - df['Close'].shift())
                    tr_st = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
                    atr_st = tr_st.rolling(10).mean()
                    upper_band = hl2 + (3 * atr_st)
                    lower_band = hl2 - (3 * atr_st)
                    
                    if df['Close'].iloc[-1] > float(hl2.iloc[-1]):
                        st_signal = f"[ + ] ⭐ (Yükseliş Trendi)"
                        st_score = 10
                    else:
                        st_signal = f"[ - ] ⚠️ (Düşüş Trendi)"
                        st_score = 2

                    # 3. Stochastic
                    low_14 = df['Low'].rolling(14).min()
                    high_14 = df['High'].rolling(14).max()
                    stoch_k = 100 * ((df['Close'] - low_14) / (high_14 - low_14))
                    stoch_d = stoch_k.rolling(3).mean()
                    val_stoch_k = float(stoch_k.iloc[-1])
                    val_stoch_d = float(stoch_d.iloc[-1])
                    if val_stoch_k > val_stoch_d:
                        stoch_signal = f"[ + ] ⭐ (%K: {val_stoch_k:.1f} > %D: {val_stoch_d:.1f})"
                        stoch_score = 10 if val_stoch_k < 80 else 7
                    else:
                        stoch_signal = f"[ - ] ⚠️ (%K: {val_stoch_k:.1f} < %D: {val_stoch_d:.1f})"
                        stoch_score = 3
                    
                    # 4. MACD
                    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
                    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
                    macd_line = exp1 - exp2
                    signal_line = macd_line.ewm(span=9, adjust=False).mean()
                    val_macd = float(macd_line.iloc[-1])
                    val_sig = float(signal_line.iloc[-1])
                    if val_macd > val_sig:
                        macd_signal = f"[ + ] ⭐ (MACD: {val_macd:.2f} > Sig: {val_sig:.2f})"
                        macd_score = 10 if val_macd > 0 else 8
                    else:
                        macd_signal = f"[ - ] ⚠️ (MACD: {val_macd:.2f} < Sig: {val_sig:.2f})"
                        macd_score = 2
                    
                    # 5. Hacim (Volume)
                    vol_current = float(df['Volume'].iloc[-1])
                    vol_ma = float(df['Volume'].rolling(20).mean().iloc[-1]) if len(df) >= 20 else float(df['Volume'].mean())
                    if vol_current > vol_ma:
                        vol_signal = f"[ + ] (Hacim: {vol_current:,.0f} > Ort)"
                        vol_score = 9
                    else:
                        vol_signal = f"[ - ] (Hacim: {vol_current:,.0f} < Ort)"
                        vol_score = 4
                    
                    # 6. OBV
                    obv = (np.sign(df['Close'].diff()) * df['Volume']).fillna(0).cumsum()
                    obv_ma = obv.rolling(10).mean() if len(df) >= 10 else obv.mean()
                    val_obv = float(obv.iloc[-1])
                    val_obv_ma = float(obv_ma.iloc[-1]) if isinstance(obv_ma, pd.Series) else float(obv_ma)
                    if val_obv > val_obv_ma:
                        obv_signal = f"[ + ] (OBV > Ort)"
                        obv_score = 8
                    else:
                        obv_signal = f"[ - ] (OBV < Ort)"
                        obv_score = 4
                    
                    # 7. EMA 20/50
                    ema20 = df['Close'].ewm(span=20, adjust=False).mean()
                    ema50 = df['Close'].ewm(span=50, adjust=False).mean()
                    val_ema20 = float(ema20.iloc[-1])
                    val_ema50 = float(ema50.iloc[-1])
                    if val_ema20 > val_ema50:
                        ema_signal = f"[ + ] ⭐ (EMA20: {val_ema20:.2f} > EMA50: {val_ema50:.2f})"
                        ema_score = 10
                    else:
                        ema_signal = f"[ - ] ⚠️ (EMA20: {val_ema20:.2f} < EMA50: {val_ema50:.2f})"
                        ema_score = 3
                    
                    # 8. TEMA
                    ema_t1 = df['Close'].ewm(span=9).mean()
                    ema_t2 = ema_t1.ewm(span=9).mean()
                    ema_t3 = ema_t2.ewm(span=9).mean()
                    tema = 3 * (ema_t1 - ema_t2) + ema_t3
                    val_tema = float(tema.iloc[-1])
                    if df['Close'].iloc[-1] > val_tema:
                        tema_signal = f"[ + ] (Fiyat > TEMA: {val_tema:.2f})"
                        tema_score = 9
                    else:
                        tema_signal = f"[ - ] (Fiyat < TEMA: {val_tema:.2f})"
                        tema_score = 4
                    
                    # 9. Bollinger Bands (BB)
                    bb_mid = df['Close'].rolling(20).mean() if len(df) >= 20 else df['Close'].mean()
                    val_bb = float(bb_mid.iloc[-1]) if isinstance(bb_mid, pd.Series) else float(bb_mid)
                    bb_std = df['Close'].rolling(20).std() if len(df) >= 20 else df['Close'].std()
                    val_std = float(bb_std.iloc[-1]) if isinstance(bb_std, pd.Series) else float(bb_std)
                    bb_upper = bb_mid + (2 * val_std)
                    bb_lower = bb_mid - (2 * val_std)
                    
                    if df['Close'].iloc[-1] > val_bb:
                        bb_signal = f"[ + ] (Fiyat > BB Ort: {val_bb:.2f})"
                        bb_score = 8
                    else:
                        bb_signal = f"[ - ] (Fiyat < BB Ort: {val_bb:.2f})"
                        bb_score = 4
                    
                    # 10. ATR
                    high_low = df['High'] - df['Low']
                    high_close = np.abs(df['High'] - df['Close'].shift())
                    low_close = np.abs(df['Low'] - df['Close'].shift())
                    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
                    atr = tr.rolling(14).mean()
                    val_atr = float(atr.iloc[-1])
                    atr_ma = atr.rolling(30).mean().iloc[-1] if len(df) >= 30 else atr.mean()
                    if val_atr > float(atr_ma):
                        atr_signal = f"[ + ] (ATR: {val_atr:.2f} Volatiliteli)"
                        atr_score = 7
                    else:
                        atr_signal = f"[ - ] (ATR: {val_atr:.2f} Durgun)"
                        atr_score = 5
                    
                    signals = [rsi_signal, st_signal, macd_signal, ema_signal, stoch_signal, vol_signal, obv_signal, tema_signal, bb_signal, atr_signal]
                    score = sum(1 for s in signals if "[ + ]" in s)
                    
                    if score >= 7:
                        sinyal_text = "GÜÇLÜ AL"
                    elif score >= 5:
                        sinyal_text = "BEKLE"
                    else:
                        sinyal_text = "SAT"

                    stop_loss = last_price * (1 - 0.015)
                    take_profit = last_price * (1 + 0.05)
                    
                    min_val = period_min
                    max_val = period_max
                    ort_val = float(recent_df['Close'].mean())
                    
                    current_time = datetime.now().strftime("%H:%M")
                    
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
                    
                    st.markdown(f"**RSI:** `{rsi_signal}` ➔ **{rsi_score}/10** &nbsp; {get_status_label(rsi_score)}")
                    st.markdown(f"**SuperTrend:** `{st_signal}` ➔ **{st_score}/10** &nbsp; {get_status_label(st_score)}")
                    st.markdown(f"**Stochastic:** `{stoch_signal}` ➔ **{stoch_score}/10** &nbsp; {get_status_label(stoch_score)}")
                    st.markdown(f"**MACD:** `{macd_signal}` ➔ **{macd_score}/10** &nbsp; {get_status_label(macd_score)}")
                    st.markdown(f"**Hacim:** `{vol_signal}` ➔ **{vol_score}/10** &nbsp; {get_status_label(vol_score)}")
                    st.markdown(f"**OBV:** `{obv_signal}` ➔ **{obv_score}/10** &nbsp; {get_status_label(obv_score)}")
                    st.markdown(f"**EMA20/50:** `{ema_signal}` ➔ **{ema_score}/10** &nbsp; {get_status_label(ema_score)}")
                    st.markdown(f"**TEMA:** `{tema_signal}` ➔ **{tema_score}/10** &nbsp; {get_status_label(tema_score)}")
                    st.markdown(f"**Bollinger (BB):** `{bb_signal}` ➔ **{bb_score}/10** &nbsp; {get_status_label(bb_score)}")
                    st.markdown(f"**ATR:** `{atr_signal}` ➔ **{atr_score}/10** &nbsp; {get_status_label(atr_score)}")
                        
                    st.markdown("--------------------------------------------------")
                    st.markdown("**SİNYAL** &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; `" + sinyal_text + "` &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; **Genel Durum :** `" + str(score) + "/10 Olumlu`")
                    st.markdown("--------------------------------------------------")
                    
                    # --- GRAFİK PANELİ ---
                    st.subheader(f"📊 {clean_ticker} 5 Dakikalık İndikatörlü Fiyat ve Osilatör Grafikleri")
                    
                    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.6, 0.2, 0.2])
                    
                    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Mumlar'), row=1, col=1)
                    fig.add_trace(go.Scatter(x=df.index, y=ema20, mode='lines', name='EMA 20', line=dict(color='orange', width=1.2)), row=1, col=1)
                    fig.add_trace(go.Scatter(x=df.index, y=ema50, mode='lines', name='EMA 50', line=dict(color='dodgerblue', width=1.2)), row=1, col=1)
                    fig.add_trace(go.Scatter(x=df.index, y=tema, mode='lines', name='TEMA', line=dict(color='purple', width=1.2)), row=1, col=1)
                    fig.add_trace(go.Scatter(x=df.index, y=bb_upper, mode='lines', name='BB Üst', line=dict(color='gray', width=1, dash='dot')), row=1, col=1)
                    fig.add_trace(go.Scatter(x=df.index, y=bb_lower, mode='lines', name='BB Alt', line=dict(color='gray', width=1, dash='dot'), fill='tonexty', fillcolor='rgba(128,128,128,0.05)'), row=1, col=1)
                    
                    fig.add_trace(go.Scatter(x=df.index, y=macd_line, mode='lines', name='MACD', line=dict(color='cyan', width=1.5)), row=2, col=1)
                    fig.add_trace(go.Scatter(x=df.index, y=signal_line, mode='lines', name='MACD Sinyal', line=dict(color='magenta', width=1.5)), row=2, col=1)
                    
                    fig.add_trace(go.Scatter(x=df.index, y=stoch_k, mode='lines', name='Stoch %K', line=dict(color='yellow', width=1.5)), row=3, col=1)
                    fig.add_trace(go.Scatter(x=df.index, y=stoch_d, mode='lines', name='Stoch %D', line=dict(color='red', width=1.5)), row=3, col=1)
                    
                    fig.update_layout(template="plotly_dark", height=750, margin=dict(l=10, r=10, t=30, b=10))
                    st.plotly_chart(fig, use_container_width=True)
                    
    except Exception as e:
        st.error(f"Bir hata oluştu: {e}")
