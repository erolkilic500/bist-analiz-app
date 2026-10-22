import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import uuid

st.set_page_config(page_title="BIST Pro Terminal & Portfoy Paneli", layout="wide")

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
# 🚀 UYGULAMA ANA KODLARI VE GÜNCELLENMİŞ LİSTELER
# ==============================================================================

if 'selected_ticker' not in st.session_state:
    st.session_state['selected_ticker'] = "THYAO"

if 'scan_results_df' not in st.session_state:
    st.session_state['scan_results_df'] = None
if 'scan_completed_msg' not in st.session_state:
    st.session_state['scan_completed_msg'] = ""

if 'watchlist' not in st.session_state:
    st.session_state['watchlist'] = ["THYAO", "ASELS", "EREGL", "TUPRS", "SASA", "BIMAS"]

if 'portfolio' not in st.session_state:
    st.session_state['portfolio'] = {
        "TGSAS": {"cost": 120.00, "lots": 100},
        "AKBNK": {"cost": 55.50, "lots": 500},
        "GARAN": {"cost": 110.20, "lots": 250},
        "KCHOL": {"cost": 180.00, "lots": 150}
    }

col_head1, col_head2 = st.columns([0.8, 0.2])
with col_head1:
    st.title("BIST Pro Terminal: Portföy, Temel & Teknik Analiz Paneli")
with col_head2:
    st.write(f"👤 `{st.session_state['username']}`")
    if st.button("🚪 Çıkış Yap"):
        curr_user = st.session_state["username"]
        if curr_user in st.session_state["ACTIVE_SESSIONS"]:
            del st.session_state["ACTIVE_SESSIONS"][curr_user]
        st.session_state["authenticated"] = False
        st.session_state["username"] = ""
        st.rerun()

st.write("İzleme listenizi, temelleri güçlü hisseleri ve portföy durumunuzu anlık olarak takip edin.")

BIST_500_TICKERS = sorted([
    "ACSEL", "ADEL", "ADESE", "ADGYO", "AEFES", "AFYON", "AGESA", "AGHOL", "AGROT", "AHGAZ",
    "AKBNK", "AKCNS", "AKFGY", "AKFYE", "AKGRT", "AKMGY", "AKSA", "AKSEN", "AKSGY", "AKSUE",
    "ALARK", "ALBRK", "ALCAR", "ALCTL", "ALFAS", "ALGYO", "ALKA", "ALKIM", "ALMAD", "ALTNY",
    "ARCLK", "ARDYZ", "ASELS", "ASTOR", "ATATP", "AYGAZ", "BAGFS", "BIMAS", "BRSAN", "CANTE",
    "CCOLA", "CWENE", "DOAS", "DOHOL", "EGEEN", "EKGYO", "ENJSA", "ENKAI", "EREGL", "FROTO",
    "GARAN", "GESAN", "GUBRF", "HALKB", "HEKTS", "ISCTR", "KCAER", "KCHOL", "KONTR", "KOZAA",
    "KOZAL", "KRDMD", "MAVI", "MIATK", "MGROS", "ODAS", "OTKAR", "OYAKC", "PETKM", "PGSUS",
    "SAHOL", "SASA", "SISE", "SKBNK", "SOKM", "TABGD", "TCELL", "TGSAS", "THYAO", "TOASO",
    "TUPRS", "ULKER", "VAKBN", "VESBE", "VESTL", "YKBNK", "ZOREN"
])

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

def analyze_fundamental(ticker_obj, last_price):
    """Şirketin Mali Yapısını, Bilanço Rasyolarını Hızlıca Hesaplar."""
    info = {}
    try:
        info = ticker_obj.info or {}
    except:
        pass
    
    pe_ratio = info.get('trailingPE', info.get('forwardPE', None))
    pb_ratio = info.get('priceToBook', None)
    roe = info.get('returnOnEquity', None)
    current_ratio = info.get('currentRatio', None)
    dividend_yield = info.get('dividendYield', 0.0)
    sector_name = info.get('sector', 'BIST Sektörü')

    # Eğer Cari Oran veya diğer rasyolar gelmediyse hızlı Bilanço denemesi yap
    try:
        if current_ratio is None or pb_ratio is None or pe_ratio is None:
            bs = ticker_obj.balance_sheet
            if not bs.empty:
                # Cari Oran
                if current_ratio is None:
                    ca_idx = [i for i in bs.index if 'Current Assets' in str(i)]
                    cl_idx = [i for i in bs.index if 'Current Liabilities' in str(i)]
                    if ca_idx and cl_idx:
                        ca = float(bs.loc[ca_idx[0]].iloc[0])
                        cl = float(bs.loc[cl_idx[0]].iloc[0])
                        if cl > 0: current_ratio = ca / cl
    except:
        pass

    valuation_status = "Nötr / Makul Değer"
    fund_score = 50 

    if pb_ratio is not None and pe_ratio is not None:
        if pb_ratio < 1.5 and pe_ratio < 10.0:
            valuation_status = "🟢 İSKONTOLU / UCUZ (Düşük F/K ve PD/DD)"
            fund_score += 25
        elif pb_ratio > 4.5 or pe_ratio > 25.0:
            valuation_status = "🔴 PAHALI / AŞIRI DEĞERLENMİŞ"
            fund_score -= 20
        else:
            valuation_status = "🟡 MAKUL DEĞERLİ"
            fund_score += 10
    elif pb_ratio is not None and pb_ratio < 1.0:
        valuation_status = "🟢 İSKONTOLU (Defter Değeri Altında)"
        fund_score += 20

    debt_status = "Sağlıklı Borç Yapısı"
    if current_ratio is not None:
        if current_ratio >= 1.5:
            debt_status = "🟢 Çok Sağlıklı (Cari Oran İyi)"
            fund_score += 15
        elif current_ratio < 1.0:
            debt_status = "🔴 Borç Riski (Cari Oran Düşük)"
            fund_score -= 15

    fund_score = min(max(fund_score, 10), 100)

    return {
        "pe_ratio": pe_ratio,
        "pb_ratio": pb_ratio,
        "roe": roe * 100 if roe else None,
        "current_ratio": current_ratio,
        "dividend_yield": dividend_yield * 100 if dividend_yield else 0.0,
        "sector_name": sector_name if sector_name else "BIST Sektörü",
        "valuation_status": valuation_status,
        "debt_status": debt_status,
        "fund_score": fund_score
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
    stoch_cross_down = val_stoch_k < val_stoch_d and float(stoch_k.iloc[-2]) >= float(stoch_d.iloc[-2])
    
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
        "stoch_cross_down": stoch_cross_down,
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
            except:
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
                except: pass

                fund_res = analyze_fundamental(t_obj, last_price)

                stop_loss = last_price * (1 - 0.015)
                take_profit = last_price * (1 + 0.05)

                hybrid_score = int((res["tech_score_sum"] * 0.6) + (fund_res["fund_score"] * 0.4))

                action_signal = "NÖTR"
                if res["val_rsi"] < 35 and res["stoch_cross_up"] and "UCUZ" in fund_res["valuation_status"]:
                    action_signal = "🚀 DİPTEN AL (Güçlü Temel & Dip Dönüşü)"
                elif "PAHALI" in fund_res["valuation_status"] and res["val_rsi"] > 70:
                    action_signal = "⚠️ TAVANDAN SAT / KÂR AL (Aşırı Değerlenmiş)"
                elif hybrid_score >= 75 and res["buyer_pct"] > 52:
                    action_signal = "🟢 NET AL (Güçlü Temel & Yükseliş Trendi)"
                elif hybrid_score <= 40 or "Borç Riski" in fund_res["debt_status"]:
                    action_signal = "🔴 NET SAT / UZAK DUR (Zayıf Temel veya Düşüş)"
                elif hybrid_score >= 55:
                    action_signal = "🟡 BEKLE / İZLE (Nötr-Pozitif)"
                else:
                    action_signal = "🟠 RİSKLİ / TEMKİNLİ OL"

                comment = f"Hisse hibrit değerlendirmede **{hybrid_score}/100** skora sahiptir. "
                comment += f"Sektör: {fund_res['sector_name']}. Değerleme durumu: {fund_res['valuation_status']}. "
                comment += f"Finansal borçluluk yapısı: {fund_res['debt_status']}."

                st.markdown(f"💰 **Alış:** `{last_price:.2f}` &nbsp;|&nbsp; **TP (%5):** `{take_profit:.2f}` &nbsp;|&nbsp; 🛑 **Stop-Loss (%1.5):** `{stop_loss:.2f}`")
                st.markdown(f"📊 **GAP Durumu:** `{res['gap_status']}`")
                st.markdown("---")

                # TEMEL ANALİZ VE RASYOLAR BÖLÜMÜ
                st.subheader("🏛️ 1. ŞİRKET TEMEL ANALİZİ & RASYOLAR")
                f1, f2, f3, f4 = st.columns(4)
                with f1:
                    st.metric("F/K Oranı", f"{fund_res['pe_ratio']:.2f}" if fund_res['pe_ratio'] else "Veri Yok / Banka")
                    st.metric("Cari Oran (Borç Gücü)", f"{fund_res['current_ratio']:.2f}" if fund_res['current_ratio'] else "N/A")
                with f2:
                    st.metric("PD/DD (Defter Değeri)", f"{fund_res['pb_ratio']:.2f}" if fund_res['pb_ratio'] else "Veri Yok")
                    st.metric("Özkaynak Kârlılığı (ROE)", f"%{fund_res['roe']:.1f}" if fund_res['roe'] else "N/A")
                with f3:
                    st.metric("Temettü Verimi", f"%{fund_res['dividend_yield']:.2f}")
                with f4:
                    st.write(f"🏢 **Sektör:** `{fund_res['sector_name']}`")
                    st.write(f"💎 **Değerleme:** {fund_res['valuation_status']}")
                    st.write(f"🏦 **Borçluluk:** {fund_res['debt_status']}")

                st.markdown("---")

                st.subheader("📈 2. TEKNİK İNDİKATÖR SİNYALLERİ")
                for name, (sig, sc) in res["signals"].items():
                    color_icon = "🟢" if sc >= 7 else ("🟡" if sc >= 5 else "🔴")
                    st.markdown(f"**{name}:** `{sig}` ➔ **{sc}/10** &nbsp; {color_icon} {get_status_label(sc)}")

                st.markdown("---")
                st.markdown(f"⚖️ **PİYASA ALIM / SATIM BASKISI & HACİM ANALİZİ:** `{res['pressure_status']}`")
                st.markdown(f"🟢 **Alıcılar:** `%{res['buyer_pct']:.1f}` &nbsp; | &nbsp; **Lot:** `{res['buying_vol']:,.0f}` &nbsp; | &nbsp; **Hacim:** `₺{res['buyer_tl']:,.2f}`")
                st.markdown(f"🔴 **Satıcılar:** `%{res['seller_pct']:.1f}` &nbsp; | &nbsp; **Lot:** `{res['selling_vol']:,.0f}` &nbsp; | &nbsp; **Hacim:** `₺{res['seller_tl']:,.2f}`")
                st.markdown("---")

                st.markdown(f"🎯 **ÖZEL SİNYAL & AKSİYON:** &nbsp;&nbsp; `{action_signal}`")
                st.markdown(f"🏆 **TOPLAM HİBRİT SKOR (TEMEL + TEKNİK):** &nbsp;&nbsp;&nbsp; `📈 {hybrid_score} / 100 Puan` &nbsp;&nbsp;&nbsp; (Teknik Skor: {res['tech_score_sum']}/100 | Temel Skor: {fund_res['fund_score']}/100)")
                
                st.info(f"🤖 **SİSTEM VE YAZILIM YORUMU:** {comment}")
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
                st.plotly_chart(fig, use_container_width=True, key=f"chart_{key_prefix}_{clean_ticker}_{selected_period_str}")

    except Exception as e:
        st.error(f"Hata oluştu: {e}")

# --- TAB 1: TEK HİSSE ANALİZİ ---
with tab1:
    col_t, col_m = st.columns([0.6, 0.4])
    with col_t:
        ticker_input = st.selectbox(
            "Hisse Seçin veya Kodunu Yazın", 
            options=BIST_500_TICKERS, 
            index=BIST_500_TICKERS.index(st.session_state['selected_ticker']) if st.session_state['selected_ticker'] in BIST_500_TICKERS else 0,
            key="tab1_ticker_select"
        )
    with col_m:
        manual_price_str = st.text_input("Ziraat Canlı Fiyat (İsteğe Bağlı)", value="")

    if st.button("Analizi Başlat"):
        render_stock_analysis(ticker_input, key_prefix="tab1", manual_price_input=manual_price_str)

# --- TAB 2: İZLEME LİSTEM ---
with tab2:
    st.subheader("📌 Takip Ettiğim Hisse Listesi")
    
    with st.expander("➕ İzleme Listesine Yeni Hisse Ekle / Çıkar"):
        col_ew1, col_ew2 = st.columns(2)
        with col_ew1:
            new_w = st.selectbox(
                "Eklenecek Hisse (Yazarak Arayın)", 
                options=["Seçiniz..."] + BIST_500_TICKERS, 
                key="new_w_select"
            )
            if st.button("Listeye Ekle", key="add_w_btn"):
                if new_w != "Seçiniz..." and new_w not in st.session_state['watchlist']:
                    st.session_state['watchlist'].append(new_w)
                    st.success(f"{new_w} izleme listesine eklendi!")
                    st.rerun()
                elif new_w in st.session_state['watchlist']:
                    st.warning("Bu hisse zaten izleme listenizde var.")
        with col_ew2:
            rem_w = st.selectbox("Listeden Çıkarılacak Hisse", ["Seçiniz..."] + st.session_state['watchlist'], key="rem_w_tab")
            if st.button("Seçileni Sil", key="del_w_btn") and rem_w != "Seçiniz...":
                st.session_state['watchlist'].remove(rem_w)
                st.success(f"{rem_w} çıkarıldı!")
                st.rerun()

    st.write("Analiz etmek istediğiniz hisseye tıklayın:")
    cols = st.columns(3)
    for idx, symbol in enumerate(st.session_state['watchlist']):
        with cols[idx % 3]:
            st.markdown(f"### {symbol}")
            if st.button(f"🔍 {symbol} Analiz Et", key=f"watch_{symbol}"):
                st.session_state['selected_ticker'] = symbol

    if st.session_state.get('selected_ticker') and st.session_state['selected_ticker'] in st.session_state['watchlist']:
        render_stock_analysis(st.session_state['selected_ticker'], key_prefix="tab2")

# --- TAB 3: PORTFÖYÜM ---
with tab3:
    st.subheader("💼 Portföyümdeki Hisseler & Anlık Kâr/Zarar Durumu")
    
    with st.expander("➕ Portföye Yeni Hisse Ekle veya Sil"):
        col_ep1, col_ep2, col_ep3, col_ep4 = st.columns([1.5, 1, 1, 1])
        with col_ep1:
            new_p = st.selectbox(
                "Hisse Seçin", 
                options=["Seçiniz..."] + BIST_500_TICKERS, 
                key="new_p_select"
            )
        with col_ep2:
            cost_val = st.text_input("Maliyet (TL) (Boş = Canlı Fiyat)", value="")
        with col_ep3:
            lot_val = st.number_input("Lot Adedi", min_value=1, value=100, step=10)
        with col_ep4:
            st.write("")
            st.write("")
            if st.button("Portföye Ekle", key="add_p_btn"):
                if new_p != "Seçiniz...":
                    parsed_cost = 0.0
                    try:
                        if cost_val.strip() != "":
                            parsed_cost = float(cost_val.replace(",", "."))
                    except: pass
                    
                    if parsed_cost <= 0:
                        try:
                            df_temp = yf.download(f"{new_p}.IS", period="1d", interval="1m", progress=False)
                            if isinstance(df_temp.columns, pd.MultiIndex):
                                df_temp.columns = df_temp.columns.get_level_values(0)
                            parsed_cost = float(df_temp['Close'].dropna().iloc[-1])
                        except:
                            parsed_cost = 0.0

                    st.session_state['portfolio'][new_p] = {
                        "cost": parsed_cost,
                        "lots": int(lot_val)
                    }
                    st.success(f"{new_p} portföye eklendi!")
                    st.rerun()

        st.markdown("---")
        col_del1, col_del2 = st.columns([2, 1])
        with col_del1:
            p_keys = list(st.session_state['portfolio'].keys())
            rem_p = st.selectbox("Portföyden Çıkarılacak Hisse", ["Seçiniz..."] + p_keys, key="rem_p_tab")
        with col_del2:
            st.write("")
            st.write("")
            if st.button("Portföyden Sil", key="del_p_btn") and rem_p != "Seçiniz...":
                del st.session_state['portfolio'][rem_p]
                st.success(f"{rem_p} portföyden çıkarıldı!")
                st.rerun()

    portfolio_data = []
    total_invested = 0.0
    total_current_val = 0.0

    if st.session_state['portfolio']:
        with st.spinner("Portföy canlı fiyatları güncelleniyor..."):
            for sym, info in st.session_state['portfolio'].items():
                t_code = f"{sym}.IS" if not sym.endswith(".IS") else sym
                cost = info["cost"]
                lots = info["lots"]
                
                try:
                    df_p = yf.download(t_code, period="1d", interval="5m", progress=False)
                    if isinstance(df_p.columns, pd.MultiIndex):
                        df_p.columns = df_p.columns.get_level_values(0)
                    curr_price = float(df_p['Close'].dropna().iloc[-1])
                except:
                    curr_price = cost if cost > 0 else 1.0

                if cost <= 0: cost = curr_price

                invested = cost * lots
                current_val = curr_price * lots
                pnl_tl = current_val - invested
                pnl_pct = ((curr_price - cost) / cost) * 100 if cost > 0 else 0.0

                total_invested += invested
                total_current_val += current_val

                portfolio_data.append({
                    "symbol": sym,
                    "cost": cost,
                    "curr_price": curr_price,
                    "lots": lots,
                    "invested": invested,
                    "current_val": current_val,
                    "pnl_tl": pnl_tl,
                    "pnl_pct": pnl_pct
                })

    if total_invested > 0:
        total_pnl_tl = total_current_val - total_invested
        total_pnl_pct = (total_pnl_tl / total_invested) * 100
        
        m_c1, m_c2, m_c3 = st.columns(3)
        with m_c1:
            st.metric("💰 Toplam Anapara (Maliyet)", f"₺{total_invested:,.2f}")
        with m_c2:
            st.metric("📊 Güncel Portföy Değeri", f"₺{total_current_val:,.2f}")
        with m_c3:
            st.metric("📈 Toplam Kâr / Zarar", f"₺{total_
