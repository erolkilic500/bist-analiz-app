import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# Sayfa ayarları
st.set_page_config(page_title="BIST Teknik Analiz ve Skorlama Paneli", layout="centered")

# Basit Şifre Koruması
def check_auth():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        st.subheader("🔑 BIST Panel Girişi")
        password = st.text_input("Erişim Şifresi:", type="password")
        
        if password == "bist2026":
            st.session_state["authenticated"] = True
            st.success("Giriş Başarılı!")
            st.rerun()
        elif password:
            st.error("Hatalı Şifre!")
        return False
    return True

if check_auth():
    st.title("📈 BIST Otomatik 8 İndikatör Skorlama Paneli")
    st.caption("Google AI bağımlılığı olmadan, doğrudan Borsa İstanbul verileriyle saf matematiksel ve objektif teknik analiz!")

    # Hisse Seçimi
    col1, col2 = st.columns([2, 1])
    with col1:
        ticker_input = st.text_input("Hisse Kodu (Örn: THYAO, BERA, EREGL, GARAN)", value="THYAO").upper().strip()
    with col2:
        interval = st.selectbox("Periyot", ["1d", "60m", "30m"], index=0)

    if st.button("🚀 Teknik Analizi Hesapla"):
        symbol = ticker_input if ticker_input.endswith(".IS") else f"{ticker_input}.IS"
        
        with st.spinner(f"{symbol} için veriler çekiliyor ve 8 indikatör hesaplanıyor..."):
            try:
                # Veri Çekme (Yahoo Finance)
                df = yf.download(symbol, period="60d", interval=interval, progress=False)
                
                if df.empty or len(df) < 30:
                    st.error("Yeterli veri bulunamadı. Lütfen geçerli bir BIST hisse kodu girin (Örn: THYAO).")
                else:
                    # MultiIndex sütun yapılarını düzeltme
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(0)

                    close = df['Close']
                    high = df['High']
                    low = df['Low']
                    volume = df['Volume']

                    # --- 1. MACD (12, 26, 9) ---
                    exp1 = close.ewm(span=12, adjust=False).mean()
                    exp2 = close.ewm(span=26, adjust=False).mean()
                    macd_line = exp1 - exp2
                    signal_line = macd_line.ewm(span=9, adjust=False).mean()
                    cond_macd = macd_line.iloc[-1] > signal_line.iloc[-1]

                    # --- 2. TEMA (9) ---
                    ema1 = close.ewm(span=9, adjust=False).mean()
                    ema2 = ema1.ewm(span=9, adjust=False).mean()
                    ema3 = ema2.ewm(span=9, adjust=False).mean()
                    tema = 3 * (ema1 - ema2) + ema3
                    cond_tema = close.iloc[-1] > tema.iloc[-1]

                    # --- 3. EMA 20 / 50 ---
                    ema20 = close.ewm(span=20, adjust=False).mean()
                    ema50 = close.ewm(span=50, adjust=False).mean()
                    cond_ema = ema20.iloc[-1] > ema50.iloc[-1]

                    # --- 4. Hacim > SMA 20 ---
                    vol_sma = volume.rolling(window=20).mean()
                    cond_vol = volume.iloc[-1] > vol_sma.iloc[-1]

                    # --- 5. OBV & OBV SMA ---
                    obv = (np.sign(close.diff()) * volume).fillna(0).cumsum()
                    obv_sma = obv.rolling(window=10).mean()
                    cond_obv = obv.iloc[-1] > obv_sma.iloc[-1]

                    # --- 6. Stoch RSI ---
                    delta = close.diff()
                    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                    rs = gain / loss
                    rsi = 100 - (100 / (1 + rs))
                    stoch_rsi = (rsi - rsi.rolling(14).min()) / (rsi.rolling(14).max() - rsi.rolling(14).min())
                    stoch_k = stoch_rsi.rolling(3).mean() * 100
                    stoch_d = stoch_k.rolling(3).mean()
                    cond_stoch = stoch_k.iloc[-1] > stoch_d.iloc[-1]

                    # --- 7. ATR (14) ---
                    tr1 = high - low
                    tr2 = abs(high - close.shift())
                    tr3 = abs(low - close.shift())
                    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
                    atr = tr.rolling(14).mean()
                    cond_atr = (high.iloc[-1] - low.iloc[-1]) > (atr.iloc[-1] * 0.5)

                    # --- 8. Bollinger Bands (20, 2) ---
                    bb_basis = close.rolling(20).mean()
                    bb_std = close.rolling(20).std()
                    bb_upper = bb_basis + (bb_std * 2)
                    bb_lower = bb_basis - (bb_std * 2)
                    cond_bb = (close.iloc[-1] > bb_lower.iloc[-1]) and (close.iloc[-1] < bb_upper.iloc[-1])

                    # Skorlama
                    indicators = [cond_macd, cond_tema, cond_ema, cond_vol, cond_obv, cond_stoch, cond_atr, cond_bb]
                    positives = sum(indicators)
                    skor = f"{positives}/8"
                    sinyal = "AL" if positives >= 5 else ("BEKLE" if positives >= 3 else "SAT")

                    # Gerçek Piyasa Verileri (Borsa Ekranı ile Birebir)
                    actual_low = float(low.iloc[-1])
                    actual_high = float(high.iloc[-1])
                    actual_close = float(close.iloc[-1])
                    actual_avg = round((actual_high + actual_low) / 2, 2)

                    last_price = actual_close
                    tp1 = round(last_price * 1.025, 2)
                    tp2 = round(last_price * 1.04, 2)
                    stop_loss = round(last_price * 0.985, 2)
                    
                    min_p = actual_low
                    max_p = actual_high
                    avg_p = actual_avg

                    # Metinsel Durumlar
                    macd_stat = "[ + ]" if cond_macd else "[ - ]"
                    tema_stat = "[ + ]" if cond_tema else "[ - ]"
                    ema_stat = "[ + ]" if cond_ema else "[ - ]"
                    hacim_stat = "[ + ]" if cond_vol else "[ - ]"
                    obv_stat = "[ + ]" if cond_obv else "[ - ]"
                    stoch_stat = "[ + ]" if cond_stoch else "[ - ]"
                    atr_stat = "[ + ]" if cond_atr else "[ - ]"
                    bb_stat = "[ + ]" if cond_bb else "[ - ]"

                    current_time_str = datetime.now().strftime("%H:%M")

                    st.success("✅ Saf Matematiksel Analiz Başarıyla Tamamlandı!")

                    # Sonuç Paneli
                    panel_output = f"""
 ⏱️ {current_time_str}  |  Alış: {last_price:.2f}  |  TP: {tp1} / {tp2}
 🛑 Stop-Loss (%1.5): {stop_loss}
 --------------------------------------------------
  Periyot |   Min (SL) |   Ort    |   Max   
    1D    |  {min_p:.2f}  |  {avg_p:.2f}  |  {max_p:.2f}
    5D    |  {min_p:.2f}  |  {avg_p:.2f}  |  {max_p:.2f}
    Gun   |  {min_p:.2f}  |  {avg_p:.2f}  |  {max_p:.2f}
 --------------------------------------------------
  MACD     |  {macd_stat}   | TEMA  |  {tema_stat}
  EMA20/50 |  {ema_stat}   | Hacim |  {hacim_stat}
  OBV      |  {obv_stat}   | Stoch |  {stoch_stat}
  ATR      |  {atr_stat}   | BB    |  {bb_stat}
 --------------------------------------------------
  SİNYAL   |  {sinyal}    | Skor :  {skor}
                    """
                    
                    st.code(panel_output, language="text")

            except Exception as e:
                st.error(f"Analiz sırasında bir hata oluştu: {e}")
