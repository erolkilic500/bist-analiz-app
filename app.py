import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

st.set_page_config(page_title="BIST 5dk Scalping & Tarama Paneli", layout="wide")

st.title("BIST Scalping, 10 Indikator Puanlama ve BIST 500 Tarayici Paneli")
st.write("Dogrudan Borsa Istanbul verileriyle saf matematiksel ve objektif teknik analiz!")

if 'last_searched_ticker' not in st.session_state:
    st.session_state['last_searched_ticker'] = ""

# --- GENİŞLETİLMİŞ BIST HİSSE LİSTESİ ---
BIST_500_TICKERS = [
    "AKBNK", "ALARK", "ARCLK", "ASELS", "BIMAS", "DOHOL", "EKGYO", "ENKAI", "EREGL", "FROTO",
    "GARAN", "GUBRF", "HALKB", "HEKTS", "ISCTR", "KCHOL", "KONTR", "KOZAL", "KOZAA", "KRDMD",
    "MGROS", "ODAS", "OYAKC", "PETKM", "PGSUS", "SAHOL", "SASA", "SISE", "SKBNK", "TCELL",
    "THYAO", "TKFEN", "TOASO", "TSKB", "TTKOM", "TUPRS", "VAKBN", "VESTL", "YKBNK", "BERA",
    "TGSAS", "CANTE", "ASTOR", "EUPWR", "SMRTG", "ALFAS", "KCAER", "MIATK", "REEDR", "ISMEN",
    "AGHOL", "AHGAZ", "AKFYE", "AKSA", "AKSEN", "ALBRK", "ALGYO", "ALKIM", "ANSGR", "ARASE",
    "ARDYZ", "ARENA", "AYDEM", "BAGFS", "BANVT", "BIOEN", "BOBET", "BRISA", "BUCIM", "CCOLA",
    "CEMTS", "CIMSA", "CWENE", "DEVA", "EGEEN", "EGGUB", "ENJSA", "ERCB", "ESEN", "ETILR", 
    "FONET", "FORMT", "GESAN", "GLYHO", "GWIND", "ICBCT", "IHEVA", "IPEKE", "ISDMR", "ITTFH", 
    "KARYV", "KFEIN", "KMPUR", "KRPLS", "KRVGD", "KTLEV", "LKMNH", "LOGO", "MAVI", "MEDTR", 
    "MHRGY", "MPARK", "NTHOL", "OYYAT", "PAKDM", "PCILT", "PENTA", "PNLSN", "PSGYO", "QUAGR", 
    "RALYH", "RGYAS", "SAYAS", "SDTTR", "SELEC", "SNICA", "SOKM", "TATEN", "TAVHL", "TBORG", 
    "TMSN", "TRGYO", "TSPOR", "TTRAK", "TURSG", "ULKER", "VAKFN", "VBTYZ", "YATAS", "YEOTK", 
    "YYAPI", "ZOREN"
]

tab1, tab2 = st.tabs(["Tek Hisse Detayli Analiz", "BIST Otomatik Tarayici (Top 50)"])

period_options = [
    "1 Dakika", "2 Dakika", "3 Dakika", "5 Dakika", "10 Dakika", "15 Dakika", "30 Dakika", "45 Dakika",
    "1 Saat", "2 Saat", "3 Saat", "4 Saat",
    "1 Günlük", "1 Haftalık", "1 Aylık", "3 Aylık", "6 Aylık", "1 Yıllık"
]

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

def analyze_df(df):
    """10 Indikator hesaplama ve puanlama motoru"""
    if df.empty or len(df) < 10:
        return None
        
    recent_df = df.tail(20)
    last_price = float(df['Close'].iloc[-1])
    
    # 1. RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    val_rsi = float(rsi.iloc[-1])
    if 40 <= val_rsi <= 70:
        rsi_sig, rsi_score = f"[ + ] (RSI: {val_rsi:.1f})", 9
    elif val_rsi < 30:
        rsi_sig, rsi_score = f"[ + ] ⭐ (RSI: {val_rsi:.1f} Dip Adayi)", 8
    elif val_rsi > 70:
        rsi_sig, rsi_score = f"[ - ] ⚠️ (RSI: {val_rsi:.1f} Asiri Alim)", 4
    else:
        rsi_sig, rsi_score = f"[ - ] (RSI: {val_rsi:.1f})", 5

    # 2. SuperTrend
    hl2 = (df['High'] + df['Low']) / 2
    if df['Close'].iloc[-1] > float(hl2.iloc[-1]):
        st_sig, st_score = "[ + ] ⭐ (Yukselis Trendi)", 10
    else:
        st_sig, st_score = "[ - ] ⚠️ (Dusus Trendi)", 2

    # 3. Stochastic
    low_14 = df['Low'].rolling(14).min()
    high_14 = df['High'].rolling(14).max()
    stoch_k = 100 * ((df['Close'] - low_14) / (high_14 - low_14))
    stoch_d = stoch_k.rolling(3).mean()
    val_stoch_k = float(stoch_k.iloc[-1])
    val_stoch_d = float(stoch_d.iloc[-1])
    if val_stoch_k > val_stoch_d:
        stoch_sig, stoch_score = f"[ + ] ⭐ (%K: {val_stoch_k:.1f} > %D: {val_stoch_d:.1f})", (10 if val_stoch_k < 80 else 7)
    else:
        stoch_sig, stoch_score = f"[ - ] ⚠️ (%K: {val_stoch_k:.1f} < %D: {val_stoch_d:.1f})", 3

    # 4. MACD
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    macd_line = exp1 - exp2
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    val_macd = float(macd_line.iloc[-1])
    val_sig = float(signal_line.iloc[-1])
    if val_macd > val_sig:
        macd_sig, macd_score = f"[ + ] ⭐ (MACD: {val_macd:.2f} > Sig: {val_sig:.2f})", (10 if val_macd > 0 else 8)
    else:
        macd_sig, macd_score = f"[ - ] ⚠️ (MACD: {val_macd:.2f} < Sig: {val_sig:.2f})", 2

    # 5. Hacim
    vol_current = float(df['Volume'].iloc[-1])
    vol_ma = float(df['Volume'].rolling(20).mean().iloc[-1]) if len(df) >= 20 else float(df['Volume'].mean())
    if vol_current > vol_ma:
        vol_sig, vol_score = f"[ + ] (Hacim: {vol_current:,.0f} > Ort)", 9
    else:
        vol_sig, vol_score = f"[ - ] (Hacim: {vol_current:,.0f} < Ort)", 4

    # 6. OBV
    obv = (np.sign(df['Close'].diff()) * df['Volume']).fillna(0).cumsum()
    obv_ma = obv.rolling(10).mean() if len(df) >= 10 else obv.mean()
    val_obv = float(obv.iloc[-1])
    val_obv_ma = float(obv_ma.iloc[-1]) if isinstance(obv_ma, pd.Series) else float(obv_ma)
    if val_obv > val_obv_ma:
        obv_sig, obv_score = "[ + ] (OBV > Ort)", 8
    else:
        obv_sig, obv_score = "[ - ] (OBV < Ort)", 4

    # 7. EMA 20/50
    ema20 = df['Close'].ewm(span=20, adjust=False).mean()
    ema50 = df['Close'].ewm(span=50, adjust=False).mean()
    val_ema20 = float(ema20.iloc[-1])
    val_ema50 = float(ema50.iloc[-1])
    if val_ema20 > val_ema50:
        ema_sig, ema_score = f"[ + ] ⭐ (EMA20: {val_ema20:.2f} > EMA50: {val_ema50:.2f})", 10
    else:
        ema_sig, ema_score = f"[ - ] ⚠️ (EMA20: {val_ema20:.2f} < EMA50: {val_ema50:.2f})", 3

    # 8. TEMA
    ema_t1 = df['Close'].ewm(span=9).mean()
    ema_t2 = ema_t1.ewm(span=9).mean()
    ema_t3 = ema_t2.ewm(span=9).mean()
    tema = 3 * (ema_t1 - ema_t2) + ema_t3
    val_tema = float(tema.iloc[-1])
    if df['Close'].iloc[-1] > val_tema:
        tema_sig, tema_score = f"[ + ] (Fiyat > TEMA: {val_tema:.2f})", 9
    else:
        tema_sig, tema_score = f"[ - ] (Fiyat < TEMA: {val_tema:.2f})", 4

    # 9. Bollinger
    bb_mid = df['Close'].rolling(20).mean() if len(df) >= 20 else df['Close'].mean()
    val_bb = float(bb_mid.iloc[-1]) if isinstance(bb_mid, pd.Series) else float(bb_mid)
    if df['Close'].iloc[-1] > val_bb:
        bb_sig, bb_score = f"[ + ] (Fiyat > BB Ort: {val_bb:.2f})", 8
    else:
        bb_sig, bb_score = f"[ - ] (Fiyat < BB Ort: {val_bb:.2f})", 4

    # 10. ATR
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.rolling(14).mean()
    val_atr = float(atr.iloc[-1])
    atr_ma = atr.rolling(30).mean().iloc[-1] if len(df) >= 30 else atr.mean()
    if val_atr > float(atr_ma):
        atr_sig, atr_score = f"[ + ] (ATR: {val_atr:.2f} Volatiliteli)", 7
    else:
        atr_sig, atr_score = f"[ - ] (ATR: {val_atr:.2f} Durgun)", 5

    signals = [rsi_sig, st_sig, macd_sig, ema_sig, stoch_sig, vol_sig, obv_sig, tema_sig, bb_sig, atr_sig]
    scores = [rsi_score, st_score, stoch_score, macd_score, vol_score, obv_score, ema_score, tema_score, bb_score, atr_score]
    total_positive = sum(1 for s in signals if "[ + ]" in s)
    avg_score = round(np.mean(scores), 1)

    return {
        "last_price": last_price,
        "total_positive": total_positive,
        "avg_score": avg_score,
        "signals": {
            "RSI": (rsi_sig, rsi_score), "SuperTrend": (st_sig, st_score),
            "Stochastic": (stoch_sig, stoch_score), "MACD": (macd_sig, macd_score),
            "Hacim": (vol_sig, vol_score), "OBV": (obv_sig, obv_score),
            "EMA20/50": (ema_sig, ema_score), "TEMA": (tema_sig, tema_score),
            "Bollinger": (bb_sig, bb_score), "ATR": (atr_sig, atr_score)
        },
        "recent_df": recent_df, "ema20": ema20, "ema50": ema50, "tema": tema,
        "macd_line": macd_line, "signal_line": signal_line,
        "stoch_k": stoch_k, "stoch_d": stoch_d
    }

# --- SEKME 1: TEK HİSSE ANALİZİ ---
with tab1:
    col_t, col_m = st.columns(2)
    with col_t:
        ticker_input = st.text_input("Hisse Kodu (Örn: THYAO, BERA, BIMAS, TGSAS)", value="TGSAS")
    with col_m:
        manual_price_str = st.text_input("Ziraat Canlı Fiyat", value="")
        st.markdown("<p style='font-size:12px; color:#ff4b4b; font-weight:bold; margin-top:-10px; margin-bottom:0px;'>DOĞRU SONUÇ ALMAK İSTİYORSANIZ ANLIK FİYATI YAZINIZ</p>", unsafe_allow_html=True)

    clean_ticker = ticker_input.strip().upper()
    if not clean_ticker.endswith(".IS"):
        clean_ticker += ".IS"

    period_choice = st.selectbox("Periyot Seçin", period_options, index=3)
    interval, period = interval_map.get(period_choice, ("5m", "1mo"))

    if st.button("Teknik Analizi Hesapla"):
        st.session_state['last_searched_ticker'] = clean_ticker
        try:
            with st.spinner(f"{clean_ticker} verileri indiriliyor..."):
                df = yf.download(clean_ticker, period=period, interval=interval, progress=False)
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                df = df.dropna(subset=['Close', 'High', 'Low', 'Volume', 'Open'])
                
                res = analyze_df(df)
                if not res:
                    st.error("Yeterli teknik veri bulunamadı.")
                else:
                    last_price = res["last_price"]
                    try:
                        if manual_price_str.strip() != "":
                            manual_price = float(manual_price_str.replace(",", "."))
                            if manual_price > 0: last_price = manual_price
                    except: pass

                    period_min = float(res["recent_df"]['Low'].min())
                    period_max = float(res["recent_df"]['High'].max())
                    ort_val = float(res["recent_df"]['Close'].mean())

                    stop_loss = last_price * (1 - 0.015)
                    take_profit = last_price * (1 + 0.05)
                    current_time = datetime.now().strftime("%H:%M")

                    st.markdown("---")
                    st.markdown(f"🕒 `{current_time}` &nbsp;|&nbsp; **Alış:** `{last_price:.2f}` &nbsp;|&nbsp; **TP (%5):** `{take_profit:.2f}`")
                    st.markdown(f"🛑 **Stop-Loss (%1.5):** `{stop_loss:.2f}`")
                    st.markdown("--------------------------------------------------")

                    c1, c2, c3, c4 = st.columns(4)
                    c1.write("**Periyot**\n" + period_choice)
                    c2.write(f"**Min (SL)**\n`{period_min:.2f}`")
                    c3.write(f"**Ort**\n`{ort_val:.2f}`")
                    c4.write(f"**Max**\n`{period_max:.2f}`")

                    st.markdown("--------------------------------------------------")
                    def get_status_label(score):
                        if score >= 9: return "🟢 **[Çok İyi]**"
                        elif score >= 7: return "🟢 **[Uygun]**"
                        elif score >= 5: return "🟡 **[Nötr]**"
                        else: return "🔴 **[Zayıf / Riskli]**"

                    for name, (sig, sc) in res["signals"].items():
                        st.markdown(f"**{name}:** `{sig}` ➔ **{sc}/10** &nbsp; {get_status_label(sc)}")

                    sinyal_text = "GÜÇLÜ AL" if res["total_positive"] >= 7 else ("BEKLE" if res["total_positive"] >= 5 else "SAT")
                    st.markdown("--------------------------------------------------")
                    st.markdown(f"**SİNYAL** &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; `{sinyal_text}` &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; **Genel Durum :** `{res['total_positive']}/10 Olumlu`")
                    st.markdown("--------------------------------------------------")

                    # Grafikler
                    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.6, 0.2, 0.2])
                    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Mumlar'), row=1, col=1)
                    fig.add_trace(go.Scatter(x=df.index, y=res["ema20"], mode='lines', name='EMA 20', line=dict(color='orange', width=1.2)), row=1, col=1)
                    fig.add_trace(go.Scatter(x=df.index, y=res["ema50"], mode='lines', name='EMA 5
