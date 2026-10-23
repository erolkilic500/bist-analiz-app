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
# 💾 KALICI VERİ VE KLASÖR SAKLAMA MEKANİZMASI
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
                if not isinstance(watchlist, list): watchlist = default_watchlist
                portfolio = data.get("portfolio", default_portfolio)
                if not isinstance(portfolio, dict): portfolio = default_portfolio
                images = data.get("images", {})
                if not isinstance(images, dict): images = {}
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
# 🔒 KULLANICI GİRİŞİ (GİRİŞ FORMU VE BUTONU)
# ==============================================================================
USERS = {
    "bist500erol": "2152039",  # Yönetici
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

period_options
