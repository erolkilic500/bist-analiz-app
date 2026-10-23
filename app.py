import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import uuid
import json
import os
from PIL import Image

st.set_page_config(page_title="BIST Pro Terminal & Portfoy Paneli", layout="wide")

# ==============================================================================
# 💾 KALICI VERİ VE KLASÖR SAKLAMA MEKANİZMASI (GÜVENLİ YÜKLEME)
# ==============================================================================
DATA_FILE = "user_data.json"
UPLOAD_DIR = "uploaded_images"

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

def load_user_data():
    default_watchlist = ["THYAO", "ASELS", "EREGL", "TUPRS", "SASA", "BIMAS"]
    default_portfolio = {
        "TGSAS": {"cost": 120.00, "lots": 100},
        "AKBNK": {"cost": 55.50, "lots": 500},
        "GARAN": {"cost": 110.20, "lots": 250},
        "KCHOL": {"cost": 180.00, "lots": 150}
    }
    
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                
                watchlist = data.get("watchlist", default_watchlist)
                if not isinstance(watchlist, list):
                    watchlist = default_watchlist
                    
                portfolio = data.get("portfolio", default_portfolio)
                if not isinstance(portfolio, dict):
                    portfolio = default_portfolio
                    
                images = data.get("images", {})
                if not isinstance(images, dict):
                    images = {}
                    
                return watchlist, portfolio, images
        except Exception:
            pass
            
    return default_watchlist, default_portfolio, {}

def save_user_data():
    try:
        data = {
            "watchlist": st.session_state['watchlist'],
            "portfolio": st.session_state['portfolio'],
            "images": st.session_state['saved_images']
        }
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"Veriler kaydedilirken hata oluştu: {e}")

# ==============================================================================
# 🔒 KULLANICI GİRİŞİ VE TEK CİHAZ KONTROLÜ
# ==============================================================================
USERS = {
    "bist500erol": "2152039",  # Yönetici
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
# 🚀 UYGULAMA ANA KODLARI VE KALICI LİSTELER
# ==============================================================================

saved_watchlist, saved_portfolio, saved_images = load_user_data()

if 'watchlist' not in st.session_state:
    st.session_state['watchlist'] = saved_watchlist

if 'portfolio' not in st.session_state:
    st.session_state['portfolio'] = saved_portfolio

if 'saved_images' not in st.session_state:
    st.session_state['saved_images'] = saved_images

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
        curr_user = st.session_state["username"]
        if curr_user in st.session_state["ACTIVE_SESSIONS"]:
            del st.session_state["ACTIVE_SESSIONS"][curr_user]
        st.session_state["authenticated"] = False
        st.session_state["username"] = ""
        st.rerun()

st.write("İzleme listenizi, anlık para giriş/çıkışlarını ve portföy durumunuzu canlı takip edin.")

# 🏆 TÜM BIST HİSSELERİ
BIST_500_TICKERS = sorted(list(set([
    "AAVT", "ABOD", "ACSEL", "ADEL", "ADESE", "ADGYO", "AEFES", "AFYON", "AGESA", "AGHOL", 
    "AGROT", "AHGAZ", "AKBNK", "AKCNS", "AKENR", "AKFGY", "AKFYE", "AKGRT", "AKMGY", "AKSA", 
    "AKSEN", "AKSGY", "AKSUE", "AKTV", "ALARK", "ALBRK", "ALCAR", "ALCTL", "ALFAS", "ALGYO", 
    "ALKA", "ALKIM", "ALMAD", "ALTNY", "ALVES", "ANELE", "ANGEN", "ANHYT", "ANSGR", "ARASE", 
    "ARCLK", "ARDYZ", "ARENA", "ARSAN", "ARTMS", "ARZUM", "ASELS", "ASGYO", "ASTOR", "ASUZU", 
    "ATAGY", "ATATP", "ATEKS", "ATSYH", "ATLAS", "AVGYO", "AVHOL", "AVOD", "AYCES", "AYDEM", 
    "AYGAZ", "AZTEK", "BAGFS", "BAKAB", "BALAT", "BANVT", "BARMA", "BASCM", "BASGZ", "BAYRK", 
    "BEGYO", "BERA", "BEYAZ", "BFREN", "BIENP", "BIGCHEFS", "BIMAS", "BINHO", "BIOEN", "BIZIM", 
    "BJKAS", "BLCYT", "BMSCH", "BMSTL", "BNTAS", "BOBET", "BORAV", "BORSK", "BOSSA", "BRISA", 
    "BRKO", "BRKSN", "BRKVY", "BRSAN", "BRYAT", "BSOKE", "BTCIM", "BUCIM", "BURCE", "BURVA", 
    "BVSAN", "BYDNR", "CANTE", "CASA", "CATES", "CCOLA", "CELHA", "CEMAS", "CEMTS", "CMBTN", 
    "CMENT", "CONSE", "COSMO", "CRDFA", "CRFSA", "CUSAN", "CVKMD", "CWENE", "DAGI", "DAGHL", 
    "DAPGM", "DARDL", "DGATE", "DGGYO", "DGNMO", "DIRIT", "DITAS", "DMRGD", "DMSAS", "DOAS", 
    "DOBUR", "DOCTA", "DOHOL", "DOKTA", "DURDO", "DYOBY", "DZGYO", "EBEBK", "ECILC", "ECZYT", 
    "EDATA", "EDIP", "EGEEN", "EGEPO", "EGGUB", "EGPRO", "EGSER", "EKIZ", "EKGYO", "EKOS", 
    "EKSUN", "ELITE", "EMKEL", "EMNIS", "ENJSA", "ENKAI", "ENSRI", "EPLAS", "ERCB", "EREGL", 
    "ERSU", "ESCAR", "ESEN", "ETILR", "ETYAT", "EUHOL", "EUKYO", "EUPWR", "EUREK", "EURO", 
    "EYGYO", "FADE", "FENER", "FLAP", "FMIZP", "FONET", "FORTE", "FORMT", "FRIGO", "FROTO", 
    "FZLGY", "GARAN", "GARFA", "GEDIK", "GEDZA", "GENIL", "GENTS", "GEREL", "GESAN", "GIPTA", 
    "GLBMD", "GLYHO", "GLCVY", "GMTAS", "GOKNR", "GOLTS", "GOODY", "GOZDE", "GRNYO", "GRTRK", 
    "GSDHO", "GSDEVR", "GSDDE", "GUBRF", "GWIND", "GZNMI", "HALKB", "HATEK", "HATSN", "HEKTS", 
    "HKTM", "HLGYO", "HUBVC", "HUNER", "HURGZ", "ICBCT", "ICUGS", "IDEAS", "IDGYO", "IEYHO", 
    "IHAAS", "IHEVA", "IHGZT", "IHLGM", "IHYAY", "IMASM", "INDES", "INFO", "INGRM", "INTEM", 
    "INVEO", "INVES", "IPEKE", "ISATR", "ISBTR", "ISCTR", "ISDMR", "ISFIN", "ISGSY", "ISGYO", 
    "ISKPL", "ISKUR", "ISMEN", "ISSEN", "ITEKS", "ITAS", "IZENR", "IZINV", "IZMDC", 
    "JANTS", "KAPLM", "KARYE", "KATMR", "KAYSE", "KBORU", "KCAER", "KCHOL", "KENT", "KRTEK", 
    "KFEIN", "KLMSN", "KLNMA", "KLRXO", "KLSER", "KLYSN", "KMEPU", "KMPUR", "KNFRT", "KONTR", 
    "KONYA", "KORDS", "KOZAA", "KOZAL", "KRDMA", "KRDMB", "KRDMD", "KRGYO", "KRONT", "KRPLS", 
    "KRSTL", "KRTEK", "KRVGD", "KSTUR", "KTLEV", "KTSKR", "KUYAŞ", "KZTGY", "KZGYO", "LIDER", 
    "LKMNH", "LMKDC", "LOGIN", "LNKAC", "LORAS", "LUKSK", "MAALT", "MACKO", "MAKIM", "MAKTK", 
    "MANAS", "MARKA", "MAVI", "MEDTR", "MEGAP", "MEGMT", "MEPET", "MERCN", "MERIT", "MERKO", 
    "METRO", "METUR", "MHRGY", "MIATK", "MGROS", "MKGYO", "MPARK", "MRGYO", "MRSHL", "MSGYO", 
    "MTRKS", "MTRYO", "MZHLD", "NATEN", "NETAS", "NIBAS", "NTGAZ", "NTHOL", "NUGYO", "NUHCM", 
    "OBAMS", "OBASE", "ODAS", "OFSYM", "ONCSM", "ORCA", "ORGE", "ORMA", "OSTIM", "OTKAR", 
    "OTTO", "OYAKC", "OATEK", "OYLUM", "OZMGD", "OZKGY", "OZRDN", "OZSUB", "PAGYO", "PAMEL", 
    "PAPIL", "PARSN", "PASEU", "PCILT", "PEKGY", "PENGD", "PENTA", "PETKM", "PETUN", "PGSUS", 
    "PINSU", "PKART", "PKENT", "PLTUR", "PNLSN", "PNSUT", "POLHO", "POLTK", "PRDGS", "PRKAB", 
    "PRKME", "PRZMA", "PSDTC", "PSGYO", "QNBFB", "QNBFK", "QUAGR", "RALYH", "RAYSG", "REEDR", 
    "RNPOL", "RODRG", "ROYAL", "RTALB", "RUBNS", "RYGYO", "RYSAS", "SAHOL", "SAMAT", "SANEL", 
    "SANFM", "SANGS", "SANKO", "SARKY", "SASA", "SAYAS", "SDTTR", "SEGMN", "SEKFK", "SEKUR", 
    "SELEC", "SELVA", "SEYKM", "SILVR", "SISE", "SKBNK", "SKTAS", "SKYMD", "SMART", "SMAO", 
    "SMRTG", "SMCGY", "SNGYO", "SNICA", "SNKRN", "SOKE", "SOKM", "SONME", "SRVGY", "SUMAS", 
    "SUNTK", "SURGY", "SUWEN", "TATEN", "TATGD", "TAVHL", "TBORG", "TCAR", "TCELL", "TCKRC", 
    "TDGYO", "TEKTU", "TERA", "TETMT", "TGSAS", "THYAO", "TKFEN", "TKNSA", "TLMAN", "TMPOL", 
    "TMSN", "TOASO", "TRGYO", "TLREF", "TNZTP", "TRCAS", "TRILC", "TSKB", "TSPOR", "TTKOM", 
    "TTRAK", "TUCLK", "TUKAS", "TUPRS", "TUREKS", "TURSG", "UFUK", "ULAS", "ULKER", "UNLU", 
    "USAK", "VAKBN", "VAKFN", "VAKKO", "VANGD", "VBTYZ", "VESBE", "VESTL", "VKFYO", "VKGYO", 
    "VKING", "YAPRK", "YATAS", "YAYLA", "YGGYO", "YGYO", "YEOTK", "YINCO", "YITAT", "YKBNK", 
    "YUASA", "YYLGD", "YONGA", "YUNSA", "YYAPI", "ZEDUR", "ZELVE", "ZRGYO", "ZOREN"
])))

tab1, tab2, tab3, tab4 = st.tabs([
    "Tek Hisse Detaylı Analiz", 
    "İzleme Listem", 
    "Portföyüm", 
    "BIST Otomatik Tarayıcı"
])

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
    if curr_open > prev_high:
        gap_status = "🟢 Yukarı GAP (Boşluklu Pozitif)"
    elif curr_open < prev_low:
        gap_status = "🔴 Aşağı GAP (Boşluklu Negatif)"

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

    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    val_rsi = float(rsi.iloc[-1])
    
    rsi_sig, rsi_score = (f"[ + ] (RSI: {val_rsi:.1f})", 9) if 40 <= val_rsi <= 70 else ((f"[ + ] (RSI: {val_rsi:.1f} Dip)", 8) if val_rsi < 30 else (f"[ - ] (RSI: {val_rsi:.1f})", 4))

    hl2 = (df['High'] + df['Low']) / 2
    st_trend = df['Close'].iloc[-1] > float(hl2.iloc[-1])
    st_sig, st_score = ("[ + ] (Yükseliş Trendi)", 10) if st_trend else ("[ - ] (Düşüş Trendi)", 2)

    low_14 = df['Low'].rolling(14).min()
    high_14 = df['High'].rolling(14).max()
    stoch_k = 100 * ((df['Close'] - low_14) / (high_14 - low_14))
    stoch_d = stoch_k.rolling(3).mean()
    val_stoch_k, val_stoch_d = float(stoch_k.iloc[-1]), float(stoch_d.iloc[-1])
    stoch_cross_up = val_stoch_k > val_stoch_d and float(stoch_k.iloc[-2]) <= float(stoch_d.iloc[-2])
    
    stoch_sig, stoch_score = (f"[ + ] (%K > %D)", 9) if val_stoch_k > val_stoch_d else (f"[ - ] (%K < %D)", 3)

    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    macd_line = exp1 - exp2
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    val_macd, val_sig = float(macd_line.iloc[-1]), float(signal_line.iloc[-1])
    macd_sig, macd_score = (f"[ + ] (MACD Pozitif)", 9) if val_macd > val_sig else (f"[ - ] (MACD Negatif)", 2)
