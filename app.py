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
UPLOAD_DIR = "uploaded_images"

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

def load_user_data():
    default_watchlist = ["THYAO", "ASELS", "EREGL"]
    default_portfolio = {
        "TGSAS": {"cost": 120.00, "lots": 100},
        "AKBNK": {"cost": 55.50, "lots": 500}
    }
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                watchlist = data.get("watchlist", default_watchlist)
                if not isinstance(watchlist, list): watchlist = default_watchlist
                portfolio = data.get("portfolio", default_portfolio)
                if not isinstance(portfolio, dict): portfolio = default_portfolio
                images = data.get("images", {})
                if not isinstance(images, dict): images = {}
                alerts = data.get("alerts", {})
                if not isinstance(alerts, dict): alerts = {}
                return watchlist, portfolio, images, alerts
        except Exception:
            pass
    return default_watchlist, default_portfolio, {}, {}

def save_user_data():
    try:
        data = {
            "watchlist": st.session_state['watchlist'],
            "portfolio": st.session_state['portfolio'],
            "images": st.session_state['saved_images'],
            "alerts": st.session_state.get('alerts', {})
        }
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"Veriler kaydedilirken hata oluştu: {e}")

USERS = {
    "bist500erol": "2152039",
    "arkadas1": "bist123",
    "arkadas2": "bist456"
}

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""

if not st.session_state["authenticated"]:
    st.title("🔒 BIST Pro Terminal - Giriş Yap")
    st.write("Lütfen devam etmek için kullanıcı adı ve şifrenizi giriniz.")
    with st.form("login_form_secure"):
        user_input = st.text_input("Kullanıcı Adı")
        pass_input = st.text_input("Şifre", type="password")
        submit_button = st.form_submit_button("🚀 Giriş Yap")
        if submit_button:
            clean_user = user_input.strip()
            clean_pass = pass_input.strip()
            if clean_user in USERS and USERS[clean_user] == clean_pass:
                st.session_state["authenticated"] = True
                st.session_state["username"] = clean_user
                st.success("Giriş başarılı! Yönlendiriliyorsunuz...")
                st.rerun()
            else:
                st.error("❌ Hatalı kullanıcı adı veya şifre!")
    st.stop()

saved_watchlist, saved_portfolio, saved_images, saved_alerts = load_user_data()

if 'watchlist' not in st.session_state:
    st.session_state['watchlist'] = saved_watchlist
if 'portfolio' not in st.session_state:
    st.session_state['portfolio'] = saved_portfolio
if 'saved_images' not in st.session_state:
    st.session_state['saved_images'] = saved_images
if 'alerts' not in st.session_state:
    st.session_state['alerts'] = saved_alerts
if 'selected_ticker' not in st.session_state:
    st.session_state['selected_ticker'] = "THYAO"
if 'scan_results_df' not in st.session_state:
    st.session_state['scan_results_df'] = None
if 'scan_completed_msg' not in st.session_state:
    st.session_state['scan_completed_msg'] = ""

col_head1, col_head2 = st.columns([0.8, 0.2])
with col_head1:
    st.title("BIST Pro Terminal: Portföy, Hacim & Teknik Analiz Paneli")
with col_head2:
    st.write(f"👤 `{st.session_state['username']}`")
    if st.button("🚪 Çıkış Yap"):
        st.session_state["authenticated"] = False
        st.session_state["username"] = ""
        st.rerun()

BIST_500_TICKERS = [
    "A1CAP", "ACSEL", "ADEL", "ADESE", "ADGYO", "AEFES", "AFYON", "AGESA", "AGHOL", "AGROT", "AGYO", "AHGAZ", "AKBNK", "AKCNS", "AKENR", "AKFGY", "AKFYE", "AKGRT", "AKMGY", "AKSA", "AKSEN", "AKSGY", "AKSUE", "AKYHO", "ALARK", "ALBRK", "ALCAR", "ALCTL", "ALFAS", "ALGYO", "ALKA", "ALKIM", "ALMAD", "ALTNY", "ALVES", "ANELE", "ANGEN", "ANHYT", "ANSGR", "ARASE", "ARCLK", "ARDYZ", "ARENA", "ARSAN", "ARTMS", "ARZUM", "ASELS", "ASGYO", "ASTOR", "ASUZU", "ATAGY", "ATAKP", "ATATP", "ATEKS", "ATLAS", "ATSYH", "AVGYO", "AVHOL", "AVOD", "AVPGY", "AVTUR", "AYCES", "AYDEM", "AYEN", "AYES", "AYGAZ", "AZTEK", "BAGFS", "BAHKM", "BAKAB", "BALAT", "BANVT", "BARMA", "BASCM", "BASGZ", "BAYRK", "BEGYO", "BERA", "BEYAZ", "BFREN", "BIENY", "BIGCH", "BIMAS", "BINBN", "BINHO", "BIOEN", "BIZIM", "BJKAS", "BLCYT", "BMSCH", "BMSTL", "BNTAS", "BOBET", "BORLS", "BORSK", "BOSSA", "BRISA", "BRKO", "BRKSN", "BRKVY", "BRLSM", "BRMEN", "BRSAN", "BRYAT", "BSOKE", "BTCIM", "BUCIM", "BURCE", "BURVA", "BVSAN", "BYDNR
