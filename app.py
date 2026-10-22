import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import uuid

st.set_page_config(page_title="BIST Pro Terminal & Portföy Paneli", layout="wide")

# ==============================================================================
# 🔒 KULLANICI GİRİŞİ VE TEK CİHAZ KONTROLÜ
# ==============================================================================
USERS = {
    "bist500erol": "2152039",  # Yönetici (Siz)
    "arkadas1": "bist123",
    "arkadas2": "bist456"
}

if "ACTIVE_SESSIONS" not in st.session_state:
    st.session_state["ACTIVE_SESSIONS"] = st.session_state.get("ACTIVE_SESSIONS", {})

if "device_session_id" not in st.session_state:
    st.session_state["device_session_id"] = str(uuid.uuid4())

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""

def login_form():
    st.title("🔒 BIST Pro Terminal - Giriş Yap")
    st.write("Lütfen devam etmek için kullanıcı adı ve şifrenizi giriniz.")
    
    with st.form("login_form"):
        user_input = st.text_input("Kullanıcı Adı")
        pass_input = st.text_input("Şifre", type="password")
        submit_button = st.form_submit_button("Giriş Yap")
        
        if submit_button:
            clean_user = user_input.strip()
            if clean_user in USERS and USERS[clean_user] == pass_input.strip():
                active_device = st.session_state["ACTIVE_SESSIONS"].get(clean_user)
                current_device = st.session_state["device_session_id"]
                
                if active_device and active_device != current_device:
                    st.error("⚠️ Bu kullanıcı adı şu anda başka bir cihazda aktif! Aynı anda yalnızca tek cihazdan giriş yapılabilir.")
                else:
                    st.session_state["ACTIVE_SESSIONS"][clean_user] = current_device
                    st.session_state["authenticated"] = True
                    st.session_state["username"] = clean_user
                    st.success("Giriş başarılı! Yönlendiriliyorsunuz...")
                    st.rerun()
            else:
                st.error("Hatalı kullanıcı adı veya şifre!")

if not st.session_state["authenticated"]:
    login_form()
    st.stop()

# ==============================================================================
# 🚀 UYGULAMA ANA KODLARI & OTOMATİK SEKME YÖNETİMİ
# ==============================================================================

col_head1, col_head2 = st.columns([0.8, 0.2])
with col_head1:
    st.title("BIST Pro Terminal: Portföy, İzleme & Analiz Paneli")
with col_head2:
    st.write(f"👤 **Kullanıcı:** `{st.session_state['username']}`")
    if st.button("🚪 Çıkış Yap"):
        curr_user = st.session_state["username"]
        if curr_user in st.session_state["ACTIVE_SESSIONS"]:
            del st.session_state["ACTIVE_SESSIONS"][curr_user]
            
        st.session_state["authenticated"] = False
        st.session_state["username"] = ""
        st.rerun()

st.write("İzleme listenizi ve elinizdeki hisseleri anlık takip edin, tek tıkla detaylı analize geçin!")

# Dinamik sekme ve hisse yönlendirmeleri
if 'active_tab' not in st.session_state:
    st.session_state['active_tab'] = "🔍 Tek Hisse Detaylı Analiz & Haberler"

if 'selected_ticker' not in st.session_state:
    st.session_state['selected_ticker'] = "THYAO"

if 'scan_results_df' not in st.session_state:
    st.session_state['scan_results_df'] = None
if 'scan_completed_msg' not in st.session_state:
    st.session_state['scan_completed_msg'] = ""

# --- ÖZEL İZLEME VE PORTFÖY LİSTELERİNİZ ---
WATCHLIST = ["THYAO", "ASELS", "EREGL", "TUPRS", "SASA", "BIMAS"]
PORTFOLIO = ["TGSAS", "AKBNK", "GARAN", "KCHOL"]

# --- BIST 500 HİSSE LİSTESİ ---
BIST_500_TICKERS = [
    "ACSEL", "ADEL", "ADESE", "ADGYO", "AEFES", "AFYON", "AGESA", "AGHOL", "AGROT", "AHGAZ",
    "AKBNK", "AKCNS", "AKFGY", "AKFYE", "AKGRT", "AKMGY", "AKSA", "AKSEN", "AKSGY", "AKSUE",
    "ALARK", "ALBRK", "ALCAR", "ALCTL", "ALFAS", "ALGYO", "ALKA", "ALKIM", "ALMAD", "ALTNY",
    "ARCLK", "ARDYZ", "ASELS", "ASTOR", "ATATP", "AYGAZ", "BAGFS", "BIMAS", "BRSAN", "CANTE",
    "CCOLA", "CWENE", "DOAS", "DOHOL", "EGEEN", "EKGYO", "ENJSA", "ENKAI", "EREGL", "FROTO",
    "GARAN", "GESAN", "GUBRF", "HALKB", "HEKTS", "ISCTR", "KCAER", "KCHOL", "KONTR", "KOZAA",
    "KOZAL", "KRDMD", "MAVI", "MIATK", "MGROS", "ODAS", "OTKAR", "OYAKC", "PETKM", "PGSUS",
    "SAHOL", "SASA", "SISE", "SKBNK", "SOKM", "TABGD", "TCELL", "TGSAS", "THYAO", "TOASO",
    "TUPRS", "ULKER", "VAKBN", "VESBE", "VESTL", "YKBNK", "ZOREN"
]

# Dinamik Menü / Sekme Seçimi
tabs = [
    "🔍 Tek Hisse Detaylı Analiz & Haberler", 
    "📌 İzleme Listem", 
    "💼 Portföyüm (Aldığım Hisseler)", 
    "🚀 BIST Otomatik Tarayıcı (Top 50)"
]

selected_tab = st.radio("Sayfa Seçiniz:", tabs, index=tabs.index(st.session_state['active_tab']), horizontal=True)
st.session_state['active_tab'] = selected_tab

period_options = [
    "1 Dakika", "2 Dakika", "3 Dakika", "5 Dakika", "10 Dakika", "15 Dakika", "30 Dakika", "45 Dakika",
    "1 Saat", "2 Saat", "3 Saat", "4 Saat",
    "1 Günlük", "1 Haftalık", "1 Aylık", "3 Aylık", "6 Aylık", "1 Yıllık"
]

interval_map = {
    "1 Dakika": ("1m", "7d"), "2 Dakika": ("2m", "1mo"), "3 Dakika": ("2m", "1mo"),
    "5 Dakika": ("5m", "1mo"), "10 Dakika": ("5m", "1mo"), "15 Dakika": ("15m", "1mo"),
    "30 Dakika": ("30m", "3mo"), "45 Dakika": ("15m", "3mo"), "1 Saat": ("1h", "6mo"),
    "2 Saat": ("1h", "1y"), "3 Saat": ("1h", "1y"), "4 Saat": ("1h", "2y"),
    "1 Günlük": ("1d", "2y"), "1 Haftalık": ("1wk", "5y"), "1 Aylık": ("1mo", "10y"),
    "3 Aylık": ("3mo", "max"), "6 Aylık": ("3mo", "max"), "1 Yıllık": ("3mo", "max")
}

def analyze_df(df):
    if df.empty or len(df) < 10:
        return None
        
    recent_df = df.tail(20)
    last_price = float(df['Close'].iloc[-1])
    
    prev_high = float(df['High'].iloc[-2])
    prev_low = float(df['Low'].iloc[-2])
    curr_open = float(df['Open'].iloc[-1])
    
    gap_status = "Normal Açılış"
    if curr_open > prev_high: gap_status = "🟢 Yukarı GAP (Boşluklu Pozitif)"
    elif curr_open < prev_low: gap_status = "🔴 Aşağı GAP (Boşluklu Negatif)"

    # 1. RSI
    delta = df['Close'].diff()
