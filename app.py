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
                return data.get("watchlist", default_watchlist), data.get("portfolio", default_portfolio), data.get("alerts", {})
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
    price_diff = df['Close'].diff().fillna(0)
    buying_vol = float(df['Volume'][price_diff >= 0].sum())
    buyer_pct = (buying_vol / total_vol) * 100 if total_vol > 0 else 50.0

    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    val_rsi = float((100 - (100 / (1 + (gain / loss)))).iloc[-1])

    ema20 = df['Close'].ewm(span=20, adjust=False).mean()
    ema50 = df['Close'].ewm(span=50, adjust=False).mean()
    
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    macd_line = exp1 - exp2

    return {
        "last_price": last_price, "pivots": pivots, "buyer_pct": buyer_pct,
        "val_rsi": val_rsi, "ema20": ema20, "ema50": ema50, "macd_line": macd_line
    }

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
        st.markdown(f"💰 **Anlık Fiyat:** `{lp:.2f} TL` &nbsp;|&nbsp; 📊 **RSI:** `{res['val_rsi']:.1f}`")

        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1: st.error(f"🔴 **Direnç R1:** {p['r1']:.2f} TL")
        with col_s2: st.info(f"⚪ **Pivot:** {p['pivot']:.2f} TL")
        with col_s3: st.success(f"🟢 **Destek S1:** {p['s1']:.2f} TL")

        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3])
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Fiyat"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=res["ema20"], mode="lines", name="EMA 20", line=dict(color="orange")), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=res["macd_line"], mode="lines", name="MACD", line=dict(color="cyan")), row=2, col=1)
        fig.update_layout(template="plotly_dark", height=550, margin=dict(l=10, r=10, t=30, b=10))
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
