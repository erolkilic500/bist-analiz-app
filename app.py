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
    "A1CAP", "ACSEL", "ADEL", "ADESE", "ADGYO", "AEFES", "AFYON", "AGESA", "AGHOL", "AGROT", "AGYO", "AHGAZ", "AKBNK", "AKCNS", "AKENR", "AKFGY", "AKFYE", "AKGRT", "AKMGY", "AKSA", "AKSEN", "AKSGY", "AKSUE", "AKYHO", "ALARK", "ALBRK", "ALCAR", "ALCTL", "ALFAS", "ALGYO", "ALKA", "ALKIM", "ALMAD", "ALTNY", "ALVES", "ANELE", "ANGEN", "ANHYT", "ANSGR", "ARASE", "ARCLK", "ARDYZ", "ARENA", "ARSAN", "ARTMS", "ARZUM", "ASELS", "ASGYO", "ASTOR", "ASUZU", "ATAGY", "ATAKP", "ATATP", "ATEKS", "ATLAS", "ATSYH", "AVGYO", "AVHOL", "AVOD", "AVPGY", "AVTUR", "AYCES", "AYDEM", "AYEN", "AYES", "AYGAZ", "AZTEK", "BAGFS", "BAHKM", "BAKAB", "BALAT", "BANVT", "BARMA", "BASCM", "BASGZ", "BAYRK", "BEGYO", "BERA", "BEYAZ", "BFREN", "BIENY", "BIGCH", "BIMAS", "BINBN", "BINHO", "BIOEN", "BIZIM", "BJKAS", "BLCYT", "BMSCH", "BMSTL", "BNTAS", "BOBET", "BORLS", "BORSK", "BOSSA", "BRISA", "BRKO", "BRKSN", "BRKVY", "BRLSM", "BRMEN", "BRSAN", "BRYAT", "BSOKE", "BTCIM", "BUCIM", "BURCE", "BURVA", "BVSAN", "BYDNR", "CANTE", "CASA", "CATES", "CCOLA", "CELHA", "CEMAS", "CEMTS", "CEMZY", "CEOEM", "CIMSA", "CLEBI", "CMBTN", "CMENT", "CONSE", "COSMO", "CRDFA", "CRFSA", "CUSAN", "CVKMD", "CWENE", "DAGHL", "DAGI", "DAPGM", "DARDL", "DENGE", "DERHL", "DERIM", "DESA", "DESPC", "DEVA", "DGATE", "DGGYO", "DGNMO", "DIRIT", "DITAS", "DMRGD", "DMSAS", "DNISI", "DOAS", "DOBUR", "DOCO", "DOFER", "DOGUB", "DOHOL", "DOKTA", "DURDO", "DYOBY", "DZGYO", "EBEBK", "ECILC", "ECZYT", "EDATA", "EDIP", "EFORC", "EGEEN", "EGEPO", "EGGUB", "EGPRO", "EGSER", "EKGYO", "EKIZ", "EKOS", "EKSUN", "ELITE", "EMKEL", "EMNIS", "ENERY", "ENJSA", "ENKAI", "ENSRI", "ENTRA", "EPLAS", "ERBOS", "ERCB", "EREGL", "ERSU", "ESCAR", "ESCOM", "ESEN", "ETILR", "ETYAT", "EUHOL", "EUKYO", "EUPWR", "EUREN", "EUYO", "EYGYO", "FADE", "FENER", "FLAP", "FMIZP", "FONET", "FORMT", "FORTE", "FRIGO", "FROTO", "FZLGY", "GARAN", "GARFA", "GEDIK", "GEDZA", "GENIL", "GENTS", "GEREL", "GESAN", "GIPTA", "GLBMD", "GLCVY", "GLRYH", "GLYHO", "GMTAS", "GOKNR", "GOLTS", "GOODY", "GOZDE", "GRNYO", "GRSEL", "GRTHO", "GSDDE", "GSDHO", "GSRAY", "GUBRF", "GWIND", "GZNMI", "HALKB", "HATEK", "HATSN", "HDFGS", "HEDEF", "HEKTS", "HKTM", "HLGYO", "HOROZ", "HRKET", "HUBVC", "HUNER", "HURGZ", "ICBCT", "ICUGS", "IDGYO", "IEYHO", "IHAAS", "IHEVA", "IHGZT", "IHLAS", "IHLGM", "IHYAY", "IMASM", "INDES", "INFO", "INGRM", "INTEM", "INVEO", "INVES", "IPEKE", "ISATR", "ISBIR", "ISBTR", "ISCTR", "ISDMR", "ISFIN", "ISGSY", "ISGYO", "ISKPL", "ISKUR", "ISMEN", "ISSEN", "ISYAT", "IZENR", "IZFAS", "IZINV", "IZMDC", "JANTS", "KAPLM", "KAREL", "KARSN", "KARTN", "KARYE", "KATMR", "KAYSE", "KBORU", "KCAER", "KCHOL", "KENT", "KERVN", "KERVT", "KFEIN", "KGYO", "KIMMR", "KLGYO", "KLKIM", "KLMSN", "KLNMA", "KLRHO", "KLSER", "KLSYN", "KMPUR", "KNFRT", "KOCMT", "KONKA", "KONTR", "KONYA", "KOPOL", "KORDS", "KOTON", "KOZAA", "KOZAL", "KRDMA", "KRDMB", "KRDMD", "KRGYO", "KRONT", "KRPLS", "KRSTL", "KRTEK", "KRVGD", "KSTUR", "KTLEV", "KTSKR", "KUTPO", "KUVVA", "KUYAS", "KZBGY", "KZGYO", "LIDER", "LIDFA", "LILAK", "LINK", "LKMNH", "LMKDC", "LOGO", "LRSHO", "LUKSK", "LYDHO", "MAALT", "MACKO", "MAGEN", "MAKIM", "MAKTK", "MANAS", "MARBL", "MARKA", "MARTI", "MAVI", "MEDTR", "MEGAP", "MEGMT", "MEKAG", "MEPET", "MERCN", "MERIT", "MERKO", "METRO", "METUR", "MGROS", "MHRGY", "MIATK", "MMCAS", "MNDRS", "MNDTR", "MOBTL", "MOGAN", "MPARK", "MRGYO", "MRSHL", "MSGYO", "MTRKS", "MTRYO", "MZHLD", "NATEN", "NETAS", "NIBAS", "NTGAZ", "NTHOL", "NUGYO", "NUHCM", "OBAMS", "OBASE", "ODAS", "ODINE", "OFSYM", "ONCSM", "ONRYT", "ORCAY", "ORGE", "ORMA", "OSMEN", "OSTIM", "OTKAR", "OTTO", "OYAKC", "OYAYO", "OYLUM", "OYYAT", "OZATD", "OZGYO", "OZKGY", "OZRDN", "OZSUB", "OZYSR", "PAGYO", "PAMEL", "PAPIL", "PARSN", "PASEU", "PATEK", "PCILT", "PEHOL", "PEKGY", "PENGD", "PENTA", "PETKM", "PETUN", "PGSUS", "PHPOL", "PINSU", "PKART", "PKENT", "PLTUR", "PNLSN", "PNSUT", "POLHO", "POLTK", "PRDGS", "PRKAB", "PRKME", "PRZMA", "PSDTC", "PSGYO", "QNBFK", "QNBFL", "QUAGR", "RALYH", "RAYSG", "REEDR", "RGYAS", "RNPOL", "RODRG", "ROYAL", "RTALB", "RUBNS", "RYGYO", "RYSAS", "SAFKR", "SAHOL", "SAMAT", "SANEL", "SANFM", "SANKO", "SARKY", "SASA", "SAYAS", "SDTTR", "SEGMN", "SEGYO", "SEKFK", "SEKUR", "SELEC", "SELGD", "SELVA", "SEYKM", "SILVR", "SISE", "SKBNK", "SKTAS", "SKYLP", "SKYMD", "SMART", "SMRTG", "SMRVA", "SNGYO", "SNICA", "SNKRN", "SNPAM", "SODSN", "SOKE", "SOKM", "SONME", "SRVGY", "SUMAS", "SUNTK", "SURGY", "SUWEN", "TABGD", "TARKM", "TATEN", "TATGD", "TAVHL", "TBORG", "TCELL", "TCKRC", "TDGYO", "TEKTU", "TERA", "TETMT", "TEZOL", "TGSAS", "THYAO", "TKFEN", "TKNSA", "TLMAN", "TMPOL", "TMSN", "TNZTP", "TOASO", "TRCAS", "TRGYO", "TRILC", "TSGYO", "TSKB", "TSPOR", "TTKOM", "TTRAK", "TUCLK", "TUKAS", "TUPRS", "TUREX", "TURGG", "TURSG", "UFUK", "ULAS", "ULKER", "ULUFA", "ULUSE", "ULUUN", "UMPAS", "UNLU", "USAK", "VAKBN", "VAKFN", "VAKKO", "VANGD", "VBTYZ", "VERTU", "VERUS", "VESBE", "VESTL", "VKFYO", "VKGYO", "VKING", "VRGYO", "YAPRK", "YATAS", "YAYLA", "YBTAS", "YEOTK", "YESIL", "YGGYO", "YGYO", "YIGIT", "YKBNK", "YKSLN", "YONGA", "YUNSA", "YYAPI", "YYLGD", "ZEDUR", "ZOREN", "ZRGYO"
]

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

tab1, tab2, tab3, tab4 = st.tabs([
    "Tek Hisse Detaylı Analiz", 
    "İzleme Listem (3 Odak Hisse)", 
    "Portföyüm", 
    "BIST Otomatik Tarayıcı"
])

def calculate_pivot_levels(df):
    high = float(df['High'].iloc[-2])
    low = float(df['Low'].iloc[-2])
    close = float(df['Close'].iloc[-2])
    pivot = (high + low + close) / 3
    r1 = (2 * pivot) - low
    s1 = (2 * pivot) - high
    r2 = pivot + (high - low)
    s2 = pivot - (high - low)
    r3 = high + 2 * (pivot - low)
    s3 = low - 2 * (high - pivot)
    return {"pivot": pivot, "r1": r1, "r2": r2, "r3": r3, "s1": s1, "s2": s2, "s3": s3}

def analyze_df(df):
    if df.empty or len(df) < 10:
        return None
    recent_df = df.tail(20)
    last_price = float(df['Close'].iloc[-1])
    pivots = calculate_pivot_levels(df)

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
    
    if 40 <= val_rsi <= 70:
        rsi_sig, rsi_score = f"[ + ] (RSI: {val_rsi:.1f})", 9
    elif val_rsi < 30:
        rsi_sig, rsi_score = f"[ + ] (RSI: {val_rsi:.1f} Dip)", 8
    else:
        rsi_sig, rsi_score = f"[ - ] (RSI: {val_rsi:.1f})", 4

    hl2 = (df['High'] + df['Low']) / 2
    st_trend = df['Close'].iloc[-1] > float(hl2.iloc[-1])
    if st_trend:
        st_sig, st_score = "[ + ] (Yükseliş Trendi)", 10
    else:
        st_sig, st_score = "[ - ] (Düşüş Trendi)", 2

    low_14 = df['Low'].rolling(14).min()
    high_14 = df['High'].rolling(14).max()
    stoch_k = 100 * ((df['Close'] - low_14) / (high_14 - low_14))
    stoch_d = stoch_k.rolling(3).mean()
    val_stoch_k, val_stoch_d = float(stoch_k.iloc[-1]), float(stoch_d.iloc[-1])
    stoch_cross_up = val_stoch_k > val_stoch_d and float(stoch_k.iloc[-2]) <= float(stoch_d.iloc[-2])
    
    if val_stoch_k > val_stoch_d:
        stoch_sig, stoch_score = "[ + ] (%K > %D)", 9
    else:
        stoch_sig, stoch_score = "[ - ] (%K < %D)", 3

    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    macd_line = exp1 - exp2
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    val_macd, val_sig = float(macd_line.iloc[-1]), float(signal_line.iloc[-1])
    
    if val_macd > val_sig:
        macd_sig, macd_score = "[ + ] (MACD Pozitif)", 9
    else:
        macd_sig, macd_score = "[ - ] (MACD Negatif)", 2

    vol_current = float(df['Volume'].iloc[-1])
    vol_ma = float(df['Volume'].rolling(20).mean().iloc[-1]) if len(df) >= 20 else float(df['Volume'].mean())
    vol_high = vol_current > vol_ma
    
    if vol_high:
        vol_sig, vol_score = "[ + ] (Hacim Yüksek)", 9
    else:
        vol_sig, vol_score = "[ - ] (Hacim Düşük)", 4

    obv = (np.sign(df['Close'].diff()) * df['Volume']).fillna(0).cumsum()
    val_obv = float(obv.iloc[-1])
    val_obv_ma = float(obv.rolling(10).mean().iloc[-1]) if len(df) >= 10 else float(obv.mean())
    
    if val_obv > val_obv_ma:
        obv_sig, obv_score = "[ + ] (OBV > Ort)", 8
    else:
        obv_sig, obv_score = "[ - ] (OBV < Ort)", 4

    ema20 = df['Close'].ewm(span=20, adjust=False).mean()
    ema50 = df['Close'].ewm(span=50, adjust=False).mean()
    val_ema20, val_ema50 = float(ema20.iloc[-1]), float(ema50.iloc[-1])
    
    if val_ema20 > val_ema50:
        ema_sig, ema_score = "[ + ] (EMA20 > EMA50)", 10
    else:
        ema_sig, ema_score = "[ - ] (EMA20 < EMA50)", 3

    ema_t1 = df['Close'].ewm(span=9).mean()
    ema_t2 = ema_t1.ewm(span=9).mean()
    ema_t3 = ema_t2.ewm(span=9).mean()
    val_tema = float(tema.iloc[-1]) if 'tema' in locals() else float(df['Close'].iloc[-1])
    
    if last_price > val_tema:
        tema_sig, tema_score = "[ + ] (Fiyat > TEMA)", 9
    else:
        tema_sig, tema_score = "[ - ] (Fiyat < TEMA)", 4

    if len(df) >= 20:
        bb_mid = df['Close'].rolling(20).mean()
        val_bb = float(bb_mid.iloc[-1])
    else:
        val_bb = float(df['Close'].mean())
    
    if last_price > val_bb:
        bb_sig, bb_score = "[ + ] (Fiyat > BB Ort)", 8
    else:
        bb_sig, bb_score = "[ - ] (Fiyat < BB Ort)", 4

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

    signals = [rsi_sig, st_sig, macd_sig, ema_sig, stoch_sig, vol_sig, obv_sig, tema_sig, bb_sig, atr_sig]
    scores = [rsi_score, st_score, stoch_score, macd_score, vol_score, obv_score, ema_score, tema_score, bb_score, atr_score]
    total_positive = sum(1 for s in signals if "[ + ]" in s)
    tech_score_sum = sum(scores)

    return {
        "last_price": last_price,
        "pivots": pivots,
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
            "RSI": (rsi_sig, rsi_score), 
            "SuperTrend": (st_sig, st_score),
            "Stochastic": (stoch_sig, stoch_score), 
            "MACD": (macd_sig, macd_score),
            "Hacim": (vol_sig, vol_score), 
            "OBV": (obv_sig, obv_score),
            "EMA20/50": (ema_sig, ema_score), 
            "TEMA": (tema_sig, tema_score),
            "Bollinger": (bb_sig, bb_score), 
            "ATR": (atr_sig, atr_score)
        },
        "recent_df": recent_df, 
        "ema20": ema20, 
        "ema50": ema50, 
        "tema": ema_t3,
        "macd_line": macd_line, 
        "signal_line": signal_line,
        "stoch_k": stoch_k, 
        "stoch_d": stoch_d
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
            index=12,
            key=f"per_{key_prefix}_{clean_ticker}",
            label_visibility="collapsed"
        )
    with c_time:
        current_time = datetime.now().strftime("%H:%M")
        st.markdown(f"🕒 `{current_time}`")
    with c_sym:
        st.markdown(f"**Hisse:** `{clean_ticker}`")

    interval, period = interval_map.get(selected_period_str, ("1d", "2y"))

    try:
        with st.spinner(f"{clean_ticker} verileri hesaplanıyor..."):
            df = yf.download(clean_ticker, period=period, interval=interval, progress=False)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df = df.dropna(subset=['Close', 'High', 'Low', 'Volume', 'Open'])
            
            res = analyze_df(df)
            if not res:
                st.error("Yeterli teknik veri bulunamadı.")
            else:
                last_price = res["last_price"]
                p = res["pivots"]

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

                st.markdown(f"💰 **Anlık Fiyat:** `{last_price:.2f} TL` &nbsp;|&nbsp; 🎯 **TP (%5):** `{take_profit:.2f}` &nbsp;|&nbsp; 🛑 **Stop-Loss (%1.5):** `{stop_loss:.2f}`")
                
                st.subheader("🛡️ Otomatik Destek & Direnç Seviyeleri (Pivot)")
                col_s1, col_s2, col_s3 = st.columns(3)
                with col_s1:
                    st.error(f"🔴 **R3 (Güçlü Satış):** {p['r3']:.2f} TL\n\n🔴 **R2 (Direnç 2):** {p['r2']:.2f} TL\n\n🔴 **R1 (Direnç 1):** {p['r1']:.2f} TL")
                with col_s2:
                    st.info(f"⚪ **Pivot (Nötr Nokta):** {p['pivot']:.2f} TL\n\n🎯 **Özel Sinyal:** `{action_signal}`")
                with col_s3:
                    st.success(f"🟢 **S1 (Destek 1):** {p['s1']:.2f} TL\n\n🟢 **S2 (Destek 2):** {p['s2']:.2f} TL\n\n🟢 **S3 (Güçlü Alım):** {p['s3']:.2f} TL")

                st.markdown("---")

                with st.expander("🔔 Bu Hisseye Özel Fiyat Alarmı Kur"):
                    c_a1, c_a2, c_a3 = st.columns(3)
                    with c_a1:
                        target_tp = st.number_input("Kâr Al (Satış) Hedefi TL", value=round(p['r1'], 2), key=f"tp_{clean_ticker}")
                    with c_a2:
                        target_sl = st.number_input("Stop-Loss Fiyatı TL", value=round(p['s1'], 2), key=f"sl_{clean_ticker}")
                    with c_a3:
                        st.write("")
                        st.write("")
                        if st.button("🔔 Alarmı Kaydet", key=f"btn_alt_{clean_ticker}"):
                            st.session_state['alerts'][clean_ticker] = {"tp": target_tp, "sl": target_sl}
                            save_user_data()
                            st.success("Fiyat alarmı başarıyla kaydedildi!")

                if clean_ticker in st.session_state['alerts']:
                    alt_data = st.session_state['alerts'][clean_ticker]
                    if last_price >= alt_data['tp']:
                        st.balloons()
                        st.success(f"🚨 **ALARM UYARISI:** {clean_ticker} belirlenen KÂR ALMA hedefine ({alt_data['tp']} TL) ulaştı!")
                    elif last_price <= alt_data['sl']:
                        st.error(f"🚨 **ALARM UYARISI:** {clean_ticker} STOP-LOSS seviyesine ({alt_data['sl']} TL) geriledi!")

                st.subheader("📈 TEKNİK İNDİKATÖR SİNYALLERİ")
                for name, (sig, sc) in res["signals"].items():
                    color_icon = "🟢" if sc >= 7 else ("🟡" if sc >= 5 else "🔴")
                    st.markdown(f"**{name}:** `{sig}` ➔ **{sc}/10** &nbsp; {color_icon} {get_status_label(sc)}")

                st.markdown("---")
                st.markdown(f"⚖️ **PİYASA ALIM / SATIM BASKISI & HACİM ANALİZİ:** `{res['pressure_status']}`")
                st.markdown(f"🟢 **Alıcılar:** `%{res['buyer_pct']:.1f}` &nbsp; | &nbsp; **Lot:** `{res['buying_vol']:,.0f}` &nbsp; | &nbsp; **Hacim:** `₺{res['buyer_tl']:,.2f}`")
                st.markdown(f"🔴 **Satıcılar:** `%{res['seller_pct']:.1f}` &nbsp; | &nbsp; **Lot:** `{res['selling_vol']:,.0f}` &nbsp; | &nbsp; **Hacim:** `₺{res['seller_tl']:,.2f}`")
                st.markdown("---")

                fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.6, 0.2, 0.2])
                fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Mumlar"), row=1, col=1)
                fig.add_hline(y=p['r1'], line_dash="dash", line_color="red", annotation_text="R1 Direnç", row=1, col=1)
                fig.add_hline(y=p['s1'], line_dash="dash", line_color="green", annotation_text="S1 Destek", row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=res["ema20"], mode="lines", name="EMA 20", line=dict(color="orange", width=1.2)), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=res["macd_line"], mode="lines", name="MACD", line=dict(color="cyan", width=1.5)), row=2, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=res["stoch_k"], mode="lines", name="Stoch K", line=dict(color="yellow", width=1.5)), row=3, col=1)
                fig.update_layout(template="plotly_dark", height=650, margin=dict(l=10, r=10, t=30, b=10))
                st.plotly_chart(fig, use_container_width=True, key=f"chart_{key_prefix}_{clean_ticker}_{selected_period_str}")

    except Exception as e:
        st.error(f"Veri yüklenirken veya analiz oluşturulurken hata oluştu: {e}")

with tab1:
    col_t, col_m = st.columns([0.6, 0.4])
    with col_t:
        current_sel = st.session_state['selected_ticker']
        idx_val = BIST_500_TICKERS.index(current_sel) if current_sel in BIST_500_TICKERS else 0
        ticker_input = st.selectbox(
            "Hisse Seçin veya Kodunu Yazın", 
            options=BIST_500_TICKERS, 
            index=idx_val,
            key="tab1_ticker_select"
        )
        if ticker_input != st.session_state['selected_ticker']:
            st.session_state['selected_ticker'] = ticker_input
    with col_m:
        manual_price_str = st.text_input("Ziraat Canlı Fiyat (İsteğe Bağlı)", value="", key="manual_p_tab1")

    render_stock_analysis(st.session_state['selected_ticker'], key_prefix="tab1", manual_price_input=manual_price_str)

with tab2:
    st.subheader("🎯 3 Odak Hisse İzleme Paneli")
    st.info("Zorlu piyasa koşullarında aynı anda en fazla 3 hisseye odaklanmanız önerilir.")
    with st.expander("➕ Odak Listesini Düzenle"):
        col_ew1, col_ew2 = st.columns(2)
        with col_ew1:
            new_w = st.selectbox("Eklenecek Hisse", options=["Seçiniz..."] + BIST_500_TICKERS, key="new_w_select")
            if st.button("Listeye Ekle", key="add_w_btn"):
                if new_w != "Seçiniz..." and new_w not in st.session_state['watchlist']:
                    if len(st.session_state['watchlist']) >= 3:
                        st.warning("⚠️ Disiplin kuralı: 3 hisseden fazlasını aynı anda izlemek odağı bozar. Lütfen birini çıkarın.")
                    else:
                        st.session_state['watchlist'].append(new_w)
                        save_user_data()
                        st.success(f"{new_w} eklendi!")
                        st.rerun()
        with col_ew2:
            rem_w = st.selectbox("Listeden Çıkarılacak Hisse", ["Seçiniz..."] + st.session_state['watchlist'], key="rem_w_tab")
            if st.button("Seçileni Sil", key="del_w_btn") and rem_w != "Seçiniz...":
                st.session_state['watchlist'].remove(rem_w)
                save_user_data()
                st.success(f"{rem_w} çıkarıldı!")
                st.rerun()

    cols = st.columns(len(st.session_state['watchlist']) if st.session_state['watchlist'] else 1)
    for idx, symbol in enumerate(st.session_state['watchlist']):
        with cols[idx]:
            st.markdown(f"### 📌 {symbol}")
            if st.button(f"🔍 {symbol} Destek/Direnç Analizi", key=f"watch_{symbol}"):
                st.session_state['selected_ticker'] = symbol
                st.rerun()

    if st.session_state.get('selected_ticker'):
        render_stock_analysis(st.session_state['selected_ticker'], key_prefix="tab2")

with tab3:
    st.subheader("💼 Portföyümdeki Hisseler & Anlık Kâr/Zarar Durumu")
    with st.expander("➕ Portföye Yeni Hisse Ekle veya Sil"):
        col_ep1, col_ep2, col_ep3, col_ep4 = st.columns([1.5, 1, 1, 1])
        with col_ep1:
            new_p = st.selectbox("Hisse Seçin", options=["Seçiniz..."] + BIST_500_TICKERS, key="new_p_select")
        with col_ep2:
            cost_val = st.text_input("Maliyet (TL)", value="", key="cost_val_in")
        with col_ep3:
            lot_val = st.number_input("Lot Adedi", min_value=1, value=100, step=10, key="lot_val_in")
        with col_ep4:
            st.write("")
            st.write("")
            if st.button("Portföye Ekle", key="add_p_btn"):
                if new_p != "Seçiniz...":
                    parsed_cost = 0.0
                    try:
                        if cost_val.strip() != "":
                            parsed_cost = float(cost_val.replace(",", "."))
                    except Exception: pass
                    st.session_state['portfolio'][new_p] = {"cost": parsed_cost, "lots": int(lot_val)}
                    save_user_data()
                    st.success(f"{new_p} portföye eklendi!")
                    st.rerun()

    portfolio_data = []
    total_invested = 0.0
    total_current_val = 0.0

    if st.session_state['portfolio']:
        with st.spinner("Portföy canlı fiyatları güncelleniyor..."):
            for sym, info in st.session_state['portfolio'].items():
                t_code = f"{sym}.IS" if not sym.endswith(".IS") else sym
                cost = info.get("cost", 0.0)
                lots = info.get("lots", 100)
                try:
                    df_p = yf.download(t_code, period="1d", interval="5m", progress=False)
                    if isinstance(df_p.columns, pd.MultiIndex):
                        df_p.columns = df_p.columns.get_level_values(0)
                    curr_price = float(df_p['Close'].dropna().iloc[-1])
                except Exception:
                    curr_price = cost if cost > 0 else 1.0

                if cost <= 0: cost = curr_price

                invested = cost * lots
                current_val = curr_price * lots
                pnl_tl = current_val - invested
                pnl_pct = ((curr_price - cost) / cost) * 100 if cost > 0 else 0.0

                total_invested += invested
                total_current_val += current_val

                portfolio_data.append({
                    "symbol": sym, "cost": cost, "curr_price": curr_price,
                    "lots": lots, "invested": invested, "current_val": current_val,
                    "pnl_tl": pnl_tl, "pnl_pct": pnl_pct
                })

    if total_invested > 0:
        total_pnl_tl = total_current_val - total_invested
        total_pnl_pct = (total_pnl_tl / total_invested) * 100
        m_c1, m_c2, m_c3 = st.columns(3)
        with m_c1: st.metric("💰 Toplam Anapara", f"₺{total_invested:,.2f}")
        with m_c2: st.metric("📊 Güncel Değer", f"₺{total_current_val:,.2f}")
        with m_c3: st.metric("📈 Kâr / Zarar", f"₺{total_pnl_tl:,.2f}", f"{total_pnl_pct:+.2f}%")
        st.markdown("---")

    cols_p = st.columns(2)
    for idx, item in enumerate(portfolio_data):
        sym = item["symbol"]
        pnl_color = "🟢" if item["pnl_pct"] >= 0 else "🔴"
        with cols_p[idx % 2]:
            st.markdown(f"### {pnl_color} {sym}")
            st.markdown(f"**Maliyet:** `{item['cost']:.2f} TL` | **Fiyat:** `{item['curr_price']:.2f} TL` | **Lot:** `{item['lots']:,}`")
            st.markdown(f"**Kâr/Zarar:** `%{item['pnl_pct']:+.2f}` (`₺{item['pnl_tl']:+,.2f}`)")
            if st.button(f"📊 {sym} Analizi Gör", key=f"port_{sym}"):
                st.session_state['selected_ticker'] = sym
                st.rerun()
            st.markdown("---")

    if st.session_state.get('selected_ticker'):
        render_stock_analysis(st.session_state['selected_ticker'], key_prefix="tab3")

with tab4:
    st.subheader("🔍 BIST Otomatik Teknik Tarayıcı")
    st.info("TradingView'da belirlediğiniz teknik filtre kriterlerine uygun hisseleri otomatik tarar.")
    if st.button("🚀 BIST Taramasını Başlat", key="start_scan_btn"):
        results = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        total_stocks = len(BIST_500_TICKERS)
        for i, sym in enumerate(BIST_500_TICKERS):
            status_text.text(f"Taranıyor... ({i+1}/{total_stocks}) - {sym}")
            progress_bar.progress((i + 1) / total_stocks)
            t_code = f"{sym}.IS" if not sym.endswith(".IS") else sym
            try:
                df_scan = yf.download(t_code, period="3mo", interval="1d", progress=False)
                if isinstance(df_scan.columns, pd.MultiIndex):
                    df_scan.columns = df_scan.columns.get_level_values(0)
                df_scan = df_scan.dropna(subset=['Close', 'High', 'Low', 'Volume', 'Open'])
                if len(df_scan) < 30:
                    continue
                close = df_scan['Close']
                high = df_scan['High']
                low = df_scan['Low']
                volume = df_scan['Volume']
                open_p = df_scan['Open']
                
                avg_vol = volume.iloc[-20:].mean()
                if not (1_000_000 <= avg_vol <= 50_000_000):
                    continue
                delta = close.diff()
                gain = (delta.where(delta > 0, 0)).rolling(14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                rs = gain / loss
                rsi14 = 100 - (100 / (1 + rs))
                val_rsi14 = float(rsi14.iloc[-1])
                if not (45 <= val_rsi14 <= 65):
                    continue
                gain7 = (delta.where(delta > 0, 0)).rolling(7).mean()
                loss7 = (-delta.where(delta < 0, 0)).rolling(7).mean()
                rs7 = gain7 / loss7
                rsi7 = 100 - (100 / (1 + rs7))
                val_rsi7 = float(rsi7.iloc[-1])
                if val_rsi7 >= 70:
                    continue
                hma9 = close.rolling(9).mean()
                if float(hma9.iloc[-1]) >= float(close.iloc[-1]):
                    continue
                if float(open_p.iloc[-1]) >= float(close.iloc[-1]):
                    continue
                pivots = calculate_pivot_levels(df_scan)
                if pivots['pivot'] >= float(close.iloc[-1]):
                    continue
                results.append({
                    "Hisse": sym,
                    "Fiyat (TL)": round(float(close.iloc[-1]), 2),
                    "RSI(14)": round(val_rsi14, 1),
                    "RSI(7)": round(val_rsi7, 1),
                    "Hacim (Ort)": f"{int(avg_vol):,}"
                })
            except Exception:
                continue
        progress_bar.empty()
        status_text.empty()
        st.session_state['scan_results_df'] = pd.DataFrame(results)
        st.session_state['scan_completed_msg'] = f"Tarama tamamlandı! Kriterlere uyan {len(results)} hisse bulundu."
        st.rerun()

    if st.session_state['scan_completed_msg']:
        st.success(st.session_state['scan_completed_msg'])

    if st.session_state['scan_results_df'] is not None and not st.session_state['scan_results_df'].empty:
        st.dataframe(st.session_state['scan_results_df'], use_container_width=True)
    elif st.session_state['scan_results_df'] is not None:
        st.warning("Belirttiğiniz tüm teknik filtrelere aynı anda uyan hisse bulunamadı.")
