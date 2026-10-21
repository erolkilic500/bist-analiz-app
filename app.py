import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

st.set_page_config(page_title="BIST 5dk Scalping & Tarama Paneli", layout="wide")

st.title("BIST Scalping, 10 Indikator Puanlama ve BIST Tarayici Paneli")
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
    loss = (-delta.where(delta < 0, 0)).rolling(window=14
