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
if 'selected_ticker' not in st.session_state: st.session_state['selected_ticker'] = "THYAO"

st.title("BIST Pro Terminal: Portföy & Teknik Analiz")

BIST_500_TICKERS = ["THYAO", "ASELS", "EREGL", "GARAN", "AKBNK", "ISCTR", "KCHOL", "SAHOL", "TUPRS", "BIMAS"]

tab1, tab2, tab3 = st.tabs(["Tek Hisse Analiz", "Portföyüm", "İzleme Listesi"])

def render_analysis(ticker):
    clean_t = ticker.strip().upper()
    if not clean_t.endswith(".IS"): clean_t += ".IS"
    st.subheader(f"📊 {clean_t} Teknik Analizi")
    try:
        df = yf.download(clean_t, period="6mo", interval="1d", progress=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df = df.dropna()
        if df.empty:
            st.warning("Veri bulunamadı.")
            return
        last_p = float(df['Close'].iloc[-1])
        st.metric("Son Fiyat", f"{last_p:.2f} TL")
        
        fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
        fig.update_layout(template="plotly_dark", height=500)
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Hata: {e}")

with tab1:
    sel = st.selectbox("Hisse Seçin", BIST_500_TICKERS, key="t1_sel")
    render_analysis(sel)

with tab2:
    st.subheader("💼 Portföy Yönetimi")
    for sym, info in st.session_state['portfolio'].items():
        st.write(f"**{sym}** - Maliyet: {info['cost']} TL | Lot: {info['lots']}")

with tab3:
    st.subheader("🎯 İzleme Listesi")
    for sym in st.session_state['watchlist']:
        st.write(f"📌 {sym}")
