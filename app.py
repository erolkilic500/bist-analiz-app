import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import json
import os

st.set_page_config(page_title="BIST Pro Terminal & Portfoy Paneli", layout="wide")

DATA_FILE = "user_data.json"

def load_user_data():
    default_watchlist = ["THYAO", "ASELS", "EREGL"]
    default_portfolio = {
        "THYAO": {"cost": 250.00, "lots": 100},
        "ASELS": {"cost": 60.00, "lots": 200}
    }
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return (
                    data.get("watchlist", default_watchlist),
                    data.get("portfolio", default_portfolio),
                    data.get("alerts", {})
                )
        except Exception:
            pass
    return default_watchlist, default_portfolio, {}

def save_user_data():
    try:
        data = {
            "watchlist": st.session_state['watchlist'],
            "portfolio": st.session_state['portfolio'],
            "alerts": st.session_state.get('alerts', {})
        }
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"Kayıt hatası: {e}")

USERS = {"bist500erol": "2152039"}

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🔒 BIST Pro Terminal - Giriş Yap")
    with st.form("login_form"):
        user_input = st.text_input("Kullanıcı Adı")
        pass_input = st.text_input("Şifre", type="password")
        if st.form_submit_button("🚀 Giriş Yap"):
            if user_input.strip() in USERS and USERS[user_input.strip()] == pass_input.strip():
                st.session_state["authenticated"] = True
                st.session_state["username"] = user_input.strip()
                st.rerun()
            else:
                st.error("❌ Hatalı kullanıcı adı veya şifre!")
    st.stop()

saved_w, saved_p, saved_a = load_user_data()
if 'watchlist' not in st.session_state: st.session_state['watchlist'] = saved_w
if 'portfolio' not in st.session_state: st.session_state['portfolio'] = saved_p
if 'alerts' not in st.session_state: st.session_state['alerts'] = saved_a

st.title("BIST Pro Terminal: Portföy & Teknik Analiz Paneli")

BIST_500_TICKERS = [
    "THYAO", "ASELS", "EREGL", "GARAN", "AKBNK", "ISCTR", "KCHOL", "SAHOL", "TUPRS", "BIMAS",
    "ASTOR", "ENJSA", "PGSUS", "TOASO", "FROTO", "ARCLK", "EKGYO", "HEKTS", "SASA", "ODAS"
]

period_options = ["1 Günlük", "1 Haftalık", "1 Aylık", "3 Aylık", "6 Aylık", "1 Yıllık"]
interval_map = {
    "1 Günlük": ("1d", "2y"), "1 Haftalık": ("1wk", "5y"), "1 Aylık": ("1mo", "10y"),
    "3 Aylık": ("3mo", "max"), "6 Aylık": ("3mo", "max"), "1 Yıllık": ("3mo", "max")
}

tab1, tab2, tab3, tab4 = st.tabs(["Tek Hisse Detaylı Analiz", "İzleme Listesi", "Portföyüm", "Tarayıcı"])

def calculate_pivot_levels(df):
    high = float(df['High'].iloc[-2])
    low = float(df['Low'].iloc[-2])
    close = float(df['Close'].iloc[-2])
    pivot = (high + low + close) / 3
    return {
        "pivot": pivot,
        "r1": (2 * pivot) - low, "s1": (2 * pivot) - high,
        "r2": pivot + (high - low), "s2": pivot - (high - low),
        "r3": high + 2 * (pivot - low), "s3": low - 2 * (high - pivot)
    }

def analyze_df(df):
    if df.empty or len(df) < 10:
        return None
    last_price = float(df['Close'].iloc[-1])
    pivots = calculate_pivot_levels(df)

    total_vol = float(df['Volume'].sum())
    total_tl_vol = float((df['Close'] * df['Volume']).sum())
    price_diff = df['Close'].diff().fillna(0)
    buying_vol = float(df['Volume'][price_diff >= 0].sum())
    selling_vol = float(df['Volume'][price_diff < 0].sum())

    buyer_pct = (buying_vol / total_vol) * 100 if total_vol > 0 else 50.0
    seller_pct = (selling_vol / total_vol) * 100 if total_vol > 0 else 50.0
    buyer_tl = total_tl_vol * (buyer_pct / 100)
    seller_tl = total_tl_vol * (seller_pct / 100)

    if buyer_pct > 55:
        pressure_status = "🟢 GÜÇLÜ ALICI BASKISI (Para Girişi Var)"
    elif buyer_pct > 50:
        pressure_status = "🟢 HAFİF ALICILI (Dengeli / Pozitif)"
    elif seller_pct > 55:
        pressure_status = "🔴 GÜÇLÜ SATICI BASKISI (Para Çıkışı Var)"
    else:
        pressure_status = "🟡 HAFİF SATICILI (Dengeli / Negatif)"

    # 1. RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    val_rsi = float((100 - (100 / (1 + rs))).iloc[-1])
    if 40 <= val_rsi <= 70:
        rsi_sig, rsi_score = f"[ + ] (RSI: {val_rsi:.1f})", 9
    elif val_rsi < 30:
        rsi_sig, rsi_score = f"[ + ] (RSI: {val_rsi:.1f} Dip)", 8
    else:
        rsi_sig, rsi_score = f"[ - ] (RSI: {val_rsi:.1f})", 4

    # 2. SuperTrend (Basitleştirilmiş HL2)
    hl2 = (df['High'] + df['Low']) / 2
    if last_price > float(hl2.iloc[-1]):
        st_sig, st_score = "[ + ] (Yükseliş Trendi)", 10
    else:
        st_sig, st_score = "[ - ] (Düşüş Trendi)", 2

    # 3. Stochastic
    low_14 = df['Low'].rolling(14).min()
    high_14 = df['High'].rolling(14).max()
    stoch_k = 100 * ((df['Close'] - low_14) / (high_14 - low_14))
    stoch_d = stoch_k.rolling(3).mean()
    val_k, val_d = float(stoch_k.iloc[-1]), float(stoch_d.iloc[-1])
    stoch_cross_up = val_k > val_d and float(stoch_k.iloc[-2]) <= float(stoch_d.iloc[-2])
    if val_k > val_d:
        stoch_sig, stoch_score = "[ + ] (%K > %D)", 9
    else:
        stoch_sig, stoch_score = "[ - ] (%K < %D)", 3

    # 4. MACD
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    macd_line = exp1 - exp2
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    if float(macd_line.iloc[-1]) > float(signal_line.iloc[-1]):
        macd_sig, macd_score = "[ + ] (MACD Pozitif)", 9
    else:
        macd_sig, macd_score = "[ - ] (MACD Negatif)", 2

    # 5. Hacim
    vol_curr = float(df['Volume'].iloc[-1])
    vol_ma = float(df['Volume'].rolling(20).mean().iloc[-1]) if len(df) >= 20 else float(df['Volume'].mean())
    if vol_curr > vol_ma:
        vol_sig, vol_score = "[ + ] (Hacim Yüksek)", 9
    else:
        vol_sig, vol_score = "[ - ] (Hacim Düşük)", 4

    # 6. OBV
    obv = (np.sign(df['Close'].diff()) * df['Volume']).fillna(0).cumsum()
    val_obv = float(obv.iloc[-1])
    val_obv_ma = float(obv.rolling(10).mean().iloc[-1]) if len(df) >= 10 else float(obv.mean())
    if val_obv > val_obv_ma:
        obv_sig, obv_score = "[ + ] (OBV > Ort)", 8
    else:
        obv_sig, obv_score = "[ - ] (OBV < Ort)", 4

    # 7. EMA 20/50
    ema20 = df['Close'].ewm(span=20, adjust=False).mean()
    ema50 = df['Close'].ewm(span=50, adjust=False).mean()
    if float(ema20.iloc[-1]) > float(ema50.iloc[-1]):
        ema_sig, ema_score = "[ + ] (EMA20 > EMA50)", 10
    else:
        ema_sig, ema_score = "[ - ] (EMA20 < EMA50)", 3

    # 8. TEMA
    ema_t1 = df['Close'].ewm(span=9).mean()
    ema_t2 = ema_t1.ewm(span=9).mean()
    ema_t3 = ema_t2.ewm(span=9).mean()
    tema = 3 * (ema_t1 - ema_t2) + ema_t3
    if last_price > float(tema.iloc[-1]):
        tema_sig, tema_score = "[ + ] (Fiyat > TEMA)", 9
    else:
        tema_sig, tema_score = "[ - ] (Fiyat < TEMA)", 4

    # 9. Bollinger
    bb_mid = df['Close'].rolling(20).mean()
    val_bb = float(bb_mid.iloc[-1]) if len(df) >= 20 else float(df['Close'].mean())
    if last_price > val_bb:
        bb_sig, bb_score = "[ + ] (Fiyat > BB Ort)", 8
    else:
        bb_sig, bb_score = "[ - ] (Fiyat < BB Ort)", 4

    # 10. ATR
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.rolling(14).mean()
    val_atr = float(atr.iloc[-1])
    atr_ma = float(atr.rolling(30).mean().iloc[-1]) if len(df) >= 30 else float(atr.mean())
    if val_atr > atr_ma:
        atr_sig, atr_score = "[ + ] (ATR Volatiliteli)", 7
    else:
        atr_sig, atr_score = "[ - ] (ATR Durgun)", 5

    scores = [rsi_score, st_score, stoch_score, macd_score, vol_score, obv_score, ema_score, tema_score, bb_score, atr_score]

    return {
        "last_price": last_price, "pivots": pivots,
        "tech_score_sum": sum(scores), "pressure_status": pressure_status,
        "buyer_pct": buyer_pct, "seller_pct": seller_pct,
        "buying_vol": buying_vol, "selling_vol": selling_vol,
        "buyer_tl": buyer_tl, "seller_tl": seller_tl,
        "val_rsi": val_rsi, "stoch_cross_up": stoch_cross_up,
        "signals": {
            "RSI": (rsi_sig, rsi_score), "SuperTrend": (st_sig, st_score),
            "Stochastic": (stoch_sig, stoch_score), "MACD": (macd_sig, macd_score),
            "Hacim": (vol_sig, vol_score), "OBV": (obv_sig, obv_score),
            "EMA20/50": (ema_sig, ema_score), "TEMA": (tema_sig, tema_score),
            "Bollinger": (bb_sig, bb_score), "ATR": (atr_sig, atr_score)
        },
        "ema20": ema20, "macd_line": macd_line, "signal_line": signal_line, "stoch_k": stoch_k
    }

def get_status_label(score):
    if score >= 9: return "🟢 **[Çok İyi]**"
    elif score >= 7: return "🟢 **[Uygun]**"
    elif score >= 5: return "🟡 **[Nötr]**"
    else: return "🔴 **[Zayıf / Riskli]**"

def render_stock_analysis(ticker_code, key_p="t1"):
    clean_ticker = ticker_code.strip().upper()
    if not clean_ticker.endswith(".IS"):
        clean_ticker += ".IS"

    st.markdown("---")
    c_per, c_time, c_sym = st.columns([1.4, 0.9, 1.2])
    with c_per:
        selected_period_str = st.selectbox("Periyot", period_options, index=0, key=f"per_{key_p}_{clean_ticker}")
    with c_time:
        st.markdown(f"🕒 `{datetime.now().strftime('%H:%M')}`")
    with c_sym:
        st.markdown(f"**Hisse:** `{clean_ticker}`")

    interval, period = interval_map.get(selected_period_str, ("1d", "2y"))

    try:
        df = yf.download(clean_ticker, period=period, interval=interval, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.dropna(subset=['Close', 'High', 'Low', 'Volume', 'Open'])

        res = analyze_df(df)
        if not res:
            st.warning("Yeterli veri bulunamadı.")
            return

        lp = res["last_price"]
        p = res["pivots"]
        tech_score = res["tech_score_sum"]

        if res["val_rsi"] < 35 and res["stoch_cross_up"]:
            action_signal = "🚀 DİPTEN AL (Dip Dönüş Sinyali)"
        elif tech_score >= 75 and res["buyer_pct"] > 52:
            action_signal = "🟢 NET AL (Güçlü Yükseliş Trendi)"
        elif tech_score <= 40:
            action_signal = "🔴 NET SAT / UZAK DUR (Zayıf Trend)"
        elif tech_score >= 55:
            action_signal = "🟡 BEKLE / İZLE (Nötr-Pozitif)"
        else:
            action_signal = "🟠 RİSKLİ / TEMKİNLİ OL"

        st.markdown(f"💰 **Anlık Fiyat:** `{lp:.2f} TL` &nbsp;|&nbsp; 🏆 **Genel Teknik Puan:** `{tech_score}/100` &nbsp;|&nbsp; 🎯 **Sinyal:** `{action_signal}`")

        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1: st.error(f"🔴 **R3:** {p['r3']:.2f} | **R2:** {p['r2']:.2f} | **R1:** {p['r1']:.2f} TL")
        with col_s2: st.info(f"⚪ **Pivot:** {p['pivot']:.2f} TL")
        with col_s3: st.success(f"🟢 **S1:** {p['s1']:.2f} | **S2:** {p['s2']:.2f} | **S3:** {p['s3']:.2f} TL")

        st.subheader("📈 10 PARAMETRELİ TEKNİK İNDİKATÖR DEĞERLENDİRMESİ")
        for name, (sig, sc) in res["signals"].items():
            st.markdown(f"**{name}:** `{sig}` ➔ **{sc}/10** &nbsp; {get_status_label(sc)}")

        st.markdown("---")
        st.markdown(f"⚖️ **PİYASA ALIM / SATIM BASKISI:** `{res['pressure_status']}`")
        st.markdown(f"🟢 **Alıcılar:** `%{res['buyer_pct']:.1f}` (`₺{res['buyer_tl']:,.0f}`) &nbsp;|&nbsp; 🔴 **Satıcılar:** `%{res['seller_pct']:.1f}` (`₺{res['seller_tl']:,.0f}`)")

        fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.6, 0.2, 0.2])
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Fiyat"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=res["ema20"], mode="lines", name="EMA 20", line=dict(color="orange", width=1.5)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=res["macd_line"], mode="lines", name="MACD", line=dict(color="cyan", width=1.5)), row=2, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=res["signal_line"], mode="lines", name="Sinyal", line=dict(color="magenta", width=1.2)), row=2, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=res["stoch_k"], mode="lines", name="Stoch %K", line=dict(color="yellow", width=1.5)), row=3, col=1)
        fig.update_layout(template="plotly_dark", height=750, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig, use_container_width=True, key=f"chart_{key_p}_{clean_ticker}")

    except Exception as e:
        st.error(f"Grafik yüklenirken hata: {e}")

with tab1:
    st.subheader("Tek Hisse Detaylı Analiz")
    sel_t1 = st.selectbox("Hisse Seçin", BIST_500_TICKERS, key="main_ticker_selectbox")
    render_stock_analysis(sel_t1, key_p="tab1")

with tab2:
    st.subheader("🎯 İzleme Listesi")
    for sym in st.session_state['watchlist']:
        render_stock_analysis(sym, key_p=f"watch_{sym}")

with tab3:
    st.subheader("💼 Portföyüm")
    for sym, info in st.session_state['portfolio'].items():
        st.write(f"**{sym}** - Maliyet: {info['cost']} TL | Lot: {info['lots']}")

with tab4:
    st.subheader("🔍 BIST Otomatik Tarayıcı")
    if st.button("Taramayı Başlat"):
        st.info("Tarama modülü aktif.")
