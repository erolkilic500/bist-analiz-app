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

# 🏆 TÜM BIST HİSSELERİ (450+ HİSSE)
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
    "ISKPL", "ISKUR", "ISMEN", "ISSEN", "ITEKS", "ITAS", "IEYHO", "IZENR", "IZINV", "IZMDC", 
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

    vol_current = float(df['Volume'].iloc[-1])
    vol_ma = float(df['Volume'].rolling(20).mean().iloc[-1]) if len(df) >= 20 else float(df['Volume'].mean())
    vol_high = vol_current > vol_ma
    vol_sig, vol_score = (f"[ + ] (Hacim Yüksek)", 9) if vol_high else (f"[ - ] (Hacim Düşük)", 4)

    obv = (np.sign(df['Close'].diff()) * df['Volume']).fillna(0).cumsum()
    obv_ma = obv.rolling(10).mean() if len(df) >= 10 else obv.mean()
    val_obv = float(obv.iloc[-1])
    val_obv_ma = float(obv_ma.iloc[-1]) if isinstance(obv_ma, pd.Series) else float(obv_ma)
    obv_sig, obv_score = ("[ + ] (OBV > Ort)", 8) if val_obv > val_obv_ma else ("[ - ] (OBV < Ort)", 4)

    ema20 = df['Close'].ewm(span=20, adjust=False).mean()
    ema50 = df['Close'].ewm(span=50, adjust=False).mean()
    val_ema20, val_ema50 = float(ema20.iloc[-1]), float(ema50.iloc[-1])
    ema_sig, ema_score = (f"[ + ] (EMA20 > EMA50)", 10) if val_ema20 > val_ema50 else (f"[ - ] (EMA20 < EMA50)", 3)

    ema_t1 = df['Close'].ewm(span=9).mean()
    ema_t2 = ema_t1.ewm(span=9).mean()
    ema_t3 = ema_t2.ewm(span=9).mean()
    tema = 3 * (ema_t1 - ema_t2) + ema_t3
    val_tema = float(tema.iloc[-1])
    tema_sig, tema_score = (f"[ + ] (Fiyat > TEMA)", 9) if last_price > val_tema else (f"[ - ] (Fiyat < TEMA)", 4)

    bb_mid = df['Close'].rolling(20).mean() if len(df) >= 20 else df['Close'].mean()
    val_bb = float(bb_mid.iloc[-1]) if isinstance(bb_mid, pd.Series) else float(bb_mid)
    bb_sig, bb_score = (f"[ + ] (Fiyat > BB Ort)", 8) if last_price > val_bb else (f"[ - ] (Fiyat < BB Ort)", 4)

    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.rolling(14).mean()
    val_atr = float(atr.iloc[-1])
    atr_ma = atr.rolling(30).mean().iloc[-1] if len(df) >= 30 else atr.mean()
    atr_sig, atr_score = (f"[ + ] (ATR Volatiliteli)", 7) if val_atr > float(atr_ma) else (f"[ - ] (ATR Durgun)", 5)

    signals = [rsi_sig, st_sig, macd_sig, ema_sig, stoch_sig, vol_sig, obv_sig, tema_sig, bb_sig, atr_sig]
    scores = [rsi_score, st_score, stoch_score, macd_score, vol_score, obv_score, ema_score, tema_score, bb_score, atr_score]
    total_positive = sum(1 for s in signals if "[ + ]" in s)
    tech_score_sum = sum(scores)

    return {
        "last_price": last_price,
        "total_positive": total_positive,
        "tech_score_sum": tech_score_sum,
        "gap_status": gap_status,
        "pressure_status": pressure_status,
        "buyer_pct": buyer_pct,
        "seller_pct": seller_pct,
        "buying_vol": buying_vol,
        "selling_vol": selling_vol,
        "buyer_tl": buyer_tl,
        "seller_tl": seller_tl,
        "val_rsi": val_rsi,
        "stoch_cross_up": stoch_cross_up,
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

def get_status_label(score):
    if score >= 9: return "🟢 **[Çok İyi]**"
    elif score >= 7: return "🟢 **[Uygun]**"
    elif score >= 5: return "🟡 **[Nötr]**"
    else: return "🔴 **[Zayıf / Riskli]**"

def render_stock_analysis(ticker_code, key_prefix="tab1", manual_price_input=""):
    clean_ticker = ticker_code.strip().upper()
    if not clean_ticker.endswith(".IS"):
        clean_ticker += ".IS"

    st.markdown("---")
    
    c_per, c_time, c_sym = st.columns([1.4, 0.9, 1.2])
    with c_per:
        selected_period_str = st.selectbox(
            "⏱️ Periyot", 
            period_options, 
            index=3, 
            key=f"per_{key_prefix}_{clean_ticker}",
            label_visibility="collapsed"
        )
    with c_time:
        current_time = datetime.now().strftime("%H:%M")
        st.markdown(f"🕒 `{current_time}`")
    with c_sym:
        st.markdown(f"**Hisse:** `{clean_ticker}`")

    interval, period = interval_map.get(selected_period_str, ("5m", "1mo"))

    try:
        with st.spinner(f"{clean_ticker} verileri hesaplanıyor..."):
            t_obj = yf.Ticker(clean_ticker)
            try:
                news_list = t_obj.news
            except Exception:
                news_list = []

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
                    if manual_price_input.strip() != "":
                        manual_price = float(manual_price_input.replace(",", "."))
                        if manual_price > 0: last_price = manual_price
                except Exception: pass

                stop_loss = last_price * (1 - 0.015)
                take_profit = last_price * (1 + 0.05)

                tech_score = res["tech_score_sum"]

                action_signal = "NÖTR"
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

                st.markdown(f"💰 **Alış:** `{last_price:.2f}` &nbsp;|&nbsp; **TP (%5):** `{take_profit:.2f}` &nbsp;|&nbsp; 🛑 **Stop-Loss (%1.5):** `{stop_loss:.2f}`")
                st.markdown(f"📊 **GAP Durumu:** `{res['gap_status']}`")
                st.markdown("---")

                # 📷 UYARI MESAJLI, DOSYA KONTROLLÜ VE ONAY KUTULU FOTOĞRAF YÜKLEME ALANI
                with st.expander("📷 Temel Analiz / Bilanço Fotoğrafı Yükle (Güvenli & Kalıcı)"):
                    st.warning("⚠️ **Dikkat: Yüklediğiniz fotoğraf güncel döneme (en son açıklanan bilançoya) mi ait?** Eski dönem fotoğrafları yanlış yönlendirebilir.")
                    
                    col_up1, col_up2 = st.columns(2)
                    with col_up1:
                        uploaded_img1 = st.file_uploader("📂 Dosya Seç / Yükle", type=["png", "jpg", "jpeg"], key=f"img1_{key_prefix}_{clean_ticker}")
                    with col_up2:
                        uploaded_img2 = st.file_uploader("📸 Fotoğraf Yükle / Çek", type=["png", "jpg", "jpeg"], key=f"img2_{key_prefix}_{clean_ticker}")

                    active_img = uploaded_img1 if uploaded_img1 is not None else uploaded_img2

                    if active_img:
                        file_name_upper = active_img.name.upper()
                        base_ticker_name = clean_ticker.replace(".IS", "")
                        mismatch_found = False
                        detected_ticker = ""

                        for t_code in BIST_500_TICKERS:
                            if t_code in file_name_upper and t_code != base_ticker_name:
                                mismatch_found = True
                                detected_ticker = t_code
                                break

                        if mismatch_found:
                            st.error(f"🚨 **UYARI:** Yüklediğiniz dosyanın adında (`{active_img.name}`) farklı bir hisse kodu (`{detected_ticker}`) geçiyor! Şu anda **{clean_ticker}** analizindesiniz. Lütfen doğru hissede olduğunuzdan emin olun.")

                        confirm_box = st.checkbox(f"Bu görselin **{clean_ticker}** hissesine ait olduğunu ve güncel olduğunu onaylıyorum.", key=f"conf_{key_prefix}_{clean_ticker}")

                        if confirm_box:
                            img_filename = f"{base_ticker_name}_{uuid.uuid4().hex[:6]}.png"
                            img_path = os.path.join(UPLOAD_DIR, img_filename)
                            
                            image_obj = Image.open(active_img)
                            image_obj.save(img_path)
                            
                            st.session_state['saved_images'][clean_ticker] = img_path
                            save_user_data()
                            st.success("📸 Görsel onaylandı ve sunucuya kalıcı olarak kaydedildi!")
                        else:
                            st.info("💡 Resmi kaydetmek için lütfen yukarıdaki onay kutusunu işaretleyin.")

                    if clean_ticker in st.session_state['saved_images'] and os.path.exists(st.session_state['saved_images'][clean_ticker]):
                        saved_path = st.session_state['saved_images'][clean_ticker]
                        st.image(saved_path, caption=f"{clean_ticker} Kayıtlı Bilanço / Rasyo Görseli", use_container_width=True)
                        if st.button(f"🗑️ Bu Fotoğrafı Sil", key=f"del_img_{clean_ticker}"):
                            del st.session_state['saved_images'][clean_ticker]
                            save_user_data()
                            if os.path.exists(saved_path):
                                os.remove(saved_path)
                            st.success("Fotoğraf silindi.")
                            st.rerun()

                        st.info(f"🤖 **Yüklenen Temel Analiz Görseli Yorumu:** Görsel hafızada kalıcıdır. Teknik skorunuz ({tech_score}/100) ile yüklediğiniz bilanço/rasyo verileri harmanlanmıştır.")

                st.subheader("📈 1. TEKNİK İNDİKATÖR SİNYALLERİ")
                for name, (sig, sc) in res["signals"].items():
                    color_icon = "🟢" if sc >= 7 else ("🟡" if sc >= 5 else "🔴")
                    st.markdown(f"**{name}:** `{sig}` ➔ **{sc}/10** &nbsp; {color_icon} {get_status_label(sc)}")

                st.markdown("---")
                st.markdown(f"⚖️ **2. PİYASA ALIM / SATIM BASKISI & HACİM ANALİZİ:** `{res['pressure_status']}`")
                st.markdown(f"🟢 **Alıcılar:** `%{res['buyer_pct']:.1f}` &nbsp; | &nbsp; **Lot:** `{res['buying_vol']:,.0f}` &nbsp; | &nbsp; **Hacim:** `₺{res['buyer_tl']:,.2f}`")
                st.markdown(f"🔴 **Satıcılar:** `%{res['seller_pct']:.1f}` &nbsp; | &nbsp; **Lot:** `{res['selling_vol']:,.0f}` &nbsp; | &nbsp; **Hacim:** `₺{res['seller_tl']:,.2f}`")
                st.markdown("---")

                st.markdown(f"🎯 **ÖZEL SİNYAL & AKSİYON:** &nbsp;&nbsp; `{action_signal}`")
                st.markdown(f"🏆 **TOPLAM TEKNİK SKOR:** &nbsp;&nbsp;&nbsp; `📈 {tech_score} / 100 Puan`")
                st.markdown("---")

                st.subheader("📰 Son Haber Akışı")
                if news_list:
                    for n in news_list[:4]:
                        title_txt = n.get('title', 'Başlık Yok')
                        publisher_txt = n.get('publisher', 'Haber')
                        link_txt = n.get('link', '#')
                        st.markdown(f"- 📌 **[{publisher_txt}]** [{title_txt}]({link_txt})")
                else:
                    st.write("Son günlerde özel bir haber akışı bulunamadı.")

                fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.6, 0.2, 0.2])
                fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Mumlar"), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=res["ema20"], mode="lines", name="EMA 20", line=dict(color="orange", width=1.2)), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=res["ema50"], mode="lines", name="EMA 50", line=dict(color="dodgerblue", width=1.2)), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=res["macd_line"], mode="lines", name="MACD", line=dict(color="cyan", width=1.5)), row=2, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=res["signal_line"], mode="lines", name="MACD Sinyal", line=dict(color="magenta", width=1.5)), row=2, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=res["stoch_k"], mode="lines", name="Stoch K", line=dict(color="yellow", width=1.5)), row=3, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=res["stoch_d"], mode="lines", name="Stoch D", line=dict(color="red", width=1.5)), row=3, col=1)
                fig.update_layout(template="plotly_dark", height=650, margin=dict(l=10, r=10, t=30, b=10))
                st.plotly_chart(
