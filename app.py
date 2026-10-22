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
    st.title("BIST Pro Terminal - Giris Yap")
    st.write("Lutfen devam etmek icin kullanici adi ve sifrenizi giriniz.")
    
    with st.form("login_form"):
        user_input = st.text_input("Kullanici Adi")
        pass_input = st.text_input("Sifre", type="password")
        submit_button = st.form_submit_button("Giris Yap")
        
        if submit_button:
            clean_user = user_input.strip()
            if clean_user in USERS and USERS[clean_user] == pass_input.strip():
                active_device = st.session_state["ACTIVE_SESSIONS"].get(clean_user)
                current_device = st.session_state["device_session_id"]
                
                if active_device and active_device != current_device:
                    st.error("Bu kullanici adi su anda baska bir cihazda aktif! Ayni anda yalnizca tek cihazdan giris yapilabilir.")
                else:
                    st.session_state["ACTIVE_SESSIONS"][clean_user] = current_device
                    st.session_state["authenticated"] = True
                    st.session_state["username"] = clean_user
                    st.success("Giris basarili! Yonlendiriliyorsunuz...")
                    st.rerun()
            else:
                st.error("Hatali kullanici adi veya sifre!")

if not st.session_state["authenticated"]:
    login_form()
    st.stop()

# ==============================================================================
# 🚀 UYGULAMA ANA KODLARI
# ==============================================================================

col_head1, col_head2 = st.columns([0.8, 0.2])
with col_head1:
    st.title("BIST Pro Terminal: Portfoy, Izleme & Analiz Paneli")
with col_head2:
    st.write(f"Kullanici: `{st.session_state['username']}`")
    if st.button("Cikis Yap"):
        curr_user = st.session_state["username"]
        if curr_user in st.session_state["ACTIVE_SESSIONS"]:
            del st.session_state["ACTIVE_SESSIONS"][curr_user]
            
        st.session_state["authenticated"] = False
        st.session_state["username"] = ""
        st.rerun()

st.write("Izleme listenizi ve elinizdeki hisseleri anlik takip edin, tek tikla detayli analize gecin!")

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

# Yerleşik Tab Yapısı (Çakışmaları önler)
tab1, tab2, tab3, tab4 = st.tabs([
    "Tek Hisse Detayli Analiz", 
    "Izleme Listem", 
    "Portfoyum (Aldigim Hisseler)", 
    "BIST Otomatik Tarayici (Top 50)"
])

period_options = [
    "1 Dakika", "2 Dakika", "3 Dakika", "5 Dakika", "10 Dakika", "15 Dakika", "30 Dakika", "45 Dakika",
    "1 Saat", "2 Saat", "3 Saat", "4 Saat",
    "1 Gunluk", "1 Haftalik", "1 Aylik", "3 Aylik", "6 Aylik", "1 Yillik"
]

interval_map = {
    "1 Dakika": ("1m", "7d"), "2 Dakika": ("2m", "1mo"), "3 Dakika": ("2m", "1mo"),
    "5 Dakika": ("5m", "1mo"), "10 Dakika": ("5m", "1mo"), "15 Dakika": ("15m", "1mo"),
    "30 Dakika": ("30m", "3mo"), "45 Dakika": ("15m", "3mo"), "1 Saat": ("1h", "6mo"),
    "2 Saat": ("1h", "1y"), "3 Saat": ("1h", "1y"), "4 Saat": ("1h", "2y"),
    "1 Gunluk": ("1d", "2y"), "1 Haftalik": ("1wk", "5y"), "1 Aylik": ("1mo", "10y"),
    "3 Aylik": ("3mo", "max"), "6 Aylik": ("3mo", "max"), "1 Yillik": ("3mo", "max")
}

def analyze_df(df):
    if df.empty or len(df) < 10:
        return None
        
    recent_df = df.tail(20)
    last_price = float(df['Close'].iloc[-1])
    
    prev_high = float(df['High'].iloc[-2])
    prev_low = float(df['Low'].iloc[-2])
    curr_open = float(df['Open'].iloc[-1])
    
    gap_status = "Normal Acilis"
    if curr_open > prev_high:
        gap_status = "Yukari GAP (Bosluklu Pozitif)"
    elif curr_open < prev_low:
        gap_status = "Asagi GAP (Bosluklu Negatif)"

    # 1. RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    val_rsi = float(rsi.iloc[-1])
    
    if 40 <= val_rsi <= 70:
        rsi_sig, rsi_score = f"[ + ] (RSI: {val_rsi:.1f})", 9
    elif val_rsi < 30:
        rsi_sig, rsi_score = f"[ + ] (RSI: {val_rsi:.1f} Dip Adayi)", 8
    elif val_rsi > 70:
        rsi_sig, rsi_score = f"[ - ] (RSI: {val_rsi:.1f} Asiri Alim)", 4
    else:
        rsi_sig, rsi_score = f"[ - ] (RSI: {val_rsi:.1f})", 5

    # 2. SuperTrend
    hl2 = (df['High'] + df['Low']) / 2
    st_trend = df['Close'].iloc[-1] > float(hl2.iloc[-1])
    st_sig, st_score = ("[ + ] (Yukselis Trendi)", 10) if st_trend else ("[ - ] (Dusus Trendi)", 2)

    # 3. Stochastic
    low_14 = df['Low'].rolling(14).min()
    high_14 = df['High'].rolling(14).max()
    stoch_k = 100 * ((df['Close'] - low_14) / (high_14 - low_14))
    stoch_d = stoch_k.rolling(3).mean()
    val_stoch_k, val_stoch_d = float(stoch_k.iloc[-1]), float(stoch_d.iloc[-1])
    stoch_cross_up = val_stoch_k > val_stoch_d and float(stoch_k.iloc[-2]) <= float(stoch_d.iloc[-2])
    stoch_cross_down = val_stoch_k < val_stoch_d and float(stoch_k.iloc[-2]) >= float(stoch_d.iloc[-2])
    
    if val_stoch_k > val_stoch_d:
        stoch_sig, stoch_score = f"[ + ] (%K: {val_stoch_k:.1f} > %D: {val_stoch_d:.1f})", (10 if val_stoch_k < 80 else 7)
    else:
        stoch_sig, stoch_score = f"[ - ] (%K: {val_stoch_k:.1f} < %D: {val_stoch_d:.1f})", 3

    # 4. MACD
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    macd_line = exp1 - exp2
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    val_macd, val_sig = float(macd_line.iloc[-1]), float(signal_line.iloc[-1])
    if val_macd > val_sig:
        macd_sig, macd_score = f"[ + ] (MACD: {val_macd:.2f} > Sig: {val_sig:.2f})", (10 if val_macd > 0 else 8)
    else:
        macd_sig, macd_score = f"[ - ] (MACD: {val_macd:.2f} < Sig: {val_sig:.2f})", 2

    # 5. Hacim
    vol_current = float(df['Volume'].iloc[-1])
    vol_ma = float(df['Volume'].rolling(20).mean().iloc[-1]) if len(df) >= 20 else float(df['Volume'].mean())
    vol_high = vol_current > vol_ma
    vol_sig, vol_score = (f"[ + ] (Hacim: {vol_current:,.0f} > Ort)", 9) if vol_high else (f"[ - ] (Hacim: {vol_current:,.0f} < Ort)", 4)

    # 6. OBV
    obv = (np.sign(df['Close'].diff()) * df['Volume']).fillna(0).cumsum()
    obv_ma = obv.rolling(10).mean() if len(df) >= 10 else obv.mean()
    val_obv = float(obv.iloc[-1])
    val_obv_ma = float(obv_ma.iloc[-1]) if isinstance(obv_ma, pd.Series) else float(obv_ma)
    obv_sig, obv_score = ("[ + ] (OBV > Ort)", 8) if val_obv > val_obv_ma else ("[ - ] (OBV < Ort)", 4)

    # 7. EMA 20/50
    ema20 = df['Close'].ewm(span=20, adjust=False).mean()
    ema50 = df['Close'].ewm(span=50, adjust=False).mean()
    val_ema20, val_ema50 = float(ema20.iloc[-1]), float(ema50.iloc[-1])
    ema_sig, ema_score = (f"[ + ] (EMA20: {val_ema20:.2f} > EMA50: {val_ema50:.2f})", 10) if val_ema20 > val_ema50 else (f"[ - ] (EMA20: {val_ema20:.2f} < EMA50: {val_ema50:.2f})", 3)

    # 8. TEMA
    ema_t1 = df['Close'].ewm(span=9).mean()
    ema_t2 = ema_t1.ewm(span=9).mean()
    ema_t3 = ema_t2.ewm(span=9).mean()
    tema = 3 * (ema_t1 - ema_t2) + ema_t3
    val_tema = float(tema.iloc[-1])
    tema_sig, tema_score = (f"[ + ] (Fiyat > TEMA: {val_tema:.2f})", 9) if last_price > val_tema else (f"[ - ] (Fiyat < TEMA: {val_tema:.2f})", 4)

    # 9. Bollinger
    bb_mid = df['Close'].rolling(20).mean() if len(df) >= 20 else df['Close'].mean()
    val_bb = float(bb_mid.iloc[-1]) if isinstance(bb_mid, pd.Series) else float(bb_mid)
    bb_sig, bb_score = (f"[ + ] (Fiyat > BB Ort: {val_bb:.2f})", 8) if last_price > val_bb else (f"[ - ] (Fiyat < BB Ort: {val_bb:.2f})", 4)

    # 10. ATR
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.rolling(14).mean()
    val_atr = float(atr.iloc[-1])
    atr_ma = atr.rolling(30).mean().iloc[-1] if len(df) >= 30 else atr.mean()
    atr_sig, atr_score = (f"[ + ] (ATR: {val_atr:.2f} Volatiliteli)", 7) if val_atr > float(atr_ma) else (f"[ - ] (ATR: {val_atr:.2f} Durgun)", 5)

    signals = [rsi_sig, st_sig, macd_sig, ema_sig, stoch_sig, vol_sig, obv_sig, tema_sig, bb_sig, atr_sig]
    scores = [rsi_score, st_score, stoch_score, macd_score, vol_score, obv_score, ema_score, tema_score, bb_score, atr_score]
    total_positive = sum(1 for s in signals if "[ + ]" in s)
    total_score_sum = sum(scores)
    avg_score = round(np.mean(scores), 1)

    action_signal = "NOTR"
    if val_rsi < 35 and stoch_cross_up:
        action_signal = "DIPTEN AL (Dip Donusu)"
    elif val_rsi > 72 and stoch_cross_down:
        action_signal = "TAVANDAN SAT / KAR AL (Asiri Alim)"
    elif last_price > val_bb and not vol_high and val_macd < val_sig:
        action_signal = "BOGA TUZAGI (Dusuk Hacim)"
    elif last_price < val_bb and val_rsi < 35 and vol_high and stoch_cross_up:
        action_signal = "AYI TUZAGI (Silkeleme)"
    elif val_ema20 > val_ema50 and abs(last_price - val_ema20) / last_price < 0.01 and stoch_cross_up:
        action_signal = "ARA AL (Duzeltme Alimi)"
    elif val_ema20 < val_ema50 and abs(last_price - val_ema20) / last_price < 0.01 and stoch_cross_down:
        action_signal = "ARA SAT (Tepki Satisi)"
    elif total_positive >= 8 and total_score_sum >= 75:
        action_signal = "NET AL (Guclu Yukselis)"
    elif total_positive <= 3 or total_score_sum <= 40:
        action_signal = "NET SAT (Dusus Trendi)"
    elif total_positive >= 5:
        action_signal = "BEKLE / IZLE (Notr-Olumlu)"
    else:
        action_signal = "RISKLI / BEKLE"

    comment = f"Hisse {total_score_sum}/100 teknik puana sahiptir. "
    if "AL" in action_signal:
        comment += "Teknik gostergeler momentumun alicilar lehine döndugunu gosteriyor. Stop-Loss seviyesine dikkat edilerek degerlendirilebilir."
    elif "SAT" in action_signal:
        comment += "Asiri satim veya trend bozulmasi emareleri var. Yeni alim riski yuksek, kar realizasyonu dusunulebilir."
    elif "TUZAGI" in action_signal:
        comment += "Hacim ve gosterge uyumsuzlugu mevcut. Yalanci kirilimlara karsi temkinli olunmali."
    else:
        comment += "Indikatorler yatay/kararsiz bir seyir gosteriyor. Net bir kirilim beklenmeli."

    return {
        "last_price": last_price,
        "total_positive": total_positive,
        "total_score_sum": total_score_sum,
        "avg_score": avg_score,
        "action_signal": action_signal,
        "gap_status": gap_status,
        "comment": comment,
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

# --- TAB 1: TEK HİSSE ANALİZİ ---
with tab1:
    col_t, col_m = st.columns(2)
    with col_t:
        ticker_input = st.text_input("Hisse Kodu Girin", value=st.session_state['selected_ticker'].replace(".IS", ""))
    with col_m:
        manual_price_str = st.text_input("Ziraat Canli Fiyat", value="")

    clean_ticker = ticker_input.strip().upper()
    if not clean_ticker.endswith(".IS"):
        clean_ticker += ".IS"

    period_choice = st.selectbox("Periyot Secin", period_options, index=3)
    interval, period = interval_map.get(period_choice, ("5m", "1mo"))

    if st.button("Teknik, GAP & Haber Analizini Baslat") or st.session_state.get('auto_run', False):
        st.session_state['auto_run'] = False
        try:
            with st.spinner(f"{clean_ticker} verileri indiriliyor..."):
                t_obj = yf.Ticker(clean_ticker)
                news_list = t_obj.news

                df = yf.download(clean_ticker, period=period, interval=interval, progress=False)
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                df = df.dropna(subset=['Close', 'High', 'Low', 'Volume', 'Open'])
                
                res = analyze_df(df)
                if not res:
                    st.error("Yeterli teknik veri bulunamadi.")
                else:
                    last_price = res["last_price"]
                    try:
                        if manual_price_str.strip() != "":
                            manual_price = float(manual_price_str.replace(",", "."))
                            if manual_price > 0:
                                last_price = manual_price
                    except:
                        pass

                    stop_loss = last_price * (1 - 0.015)
                    take_profit = last_price * (1 + 0.05)
                    current_time = datetime.now().strftime("%H:%M")

                    st.markdown("---")
                    st.markdown(f"Saat: `{current_time}` | Hisse: `{clean_ticker}` | Alis: `{last_price:.2f}` | TP (%5): `{take_profit:.2f}`")
                    st.markdown(f"Stop-Loss (%1.5): `{stop_loss:.2f}` | GAP Durumu: `{res['gap_status']}`")
                    st.markdown("--------------------------------------------------")

                    st.markdown(f"OZEL SINYAL & AKSIYON: `{res['action_signal']}`")
                    st.markdown(f"TOPLAM TEKNİK PUAN: `{res['total_score_sum']} / 100 Puan` ({res['total_positive']}/10 Olumlu)")
                    st.info(f"SİSTEM VE YAZILIM YORUMU: {res['comment']}")
                    st.markdown("--------------------------------------------------")

                    st.subheader("Hisseyle Ilgili Son Haberler")
                    if news_list:
                        for n in news_list[:4]:
                            title_txt = n.get('title', 'Baslik Yok')
                            publisher_txt = n.get('publisher', 'Haber')
                            link_txt = n.get('link', '#')
                            st.markdown(f"- [{publisher_txt}] [{title_txt}]({link_txt})")
                    else:
                        st.write("Son gunlerde ozel bir haber akisi bulunamadi.")

                    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.6, 0.2, 0.2])
                    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Mumlar"), row=1, col=1)
                    fig.add_trace(go.Scatter(x=df.index, y=res["ema20"], mode="lines", name="EMA 20", line=dict(color="orange", width=1.2)), row=1, col=1)
                    fig.add_trace(go.Scatter(x=df.index, y=res["ema50"], mode="lines", name="EMA 50", line=dict(color="dodgerblue", width=1.2)), row=1, col=1)
                    fig.add_trace(go.Scatter(x=df.index, y=res["macd_line"], mode="lines", name="MACD", line=dict(color="cyan", width=1.5)), row=2, col=1)
                    fig.add_trace(go.Scatter(x=df.index, y=res["signal_line"], mode="lines", name="MACD Sinyal", line=dict(color="magenta", width=1.5)), row=2, col=1)
                    fig.add_trace(go.Scatter(x=df.index, y=res["stoch_k"], mode="lines", name="Stoch K", line=dict(color="yellow", width=1.5)), row=3, col=1)
                    fig.add_trace(go.Scatter(x=df.index, y=res["stoch_d"], mode="lines", name="Stoch D", line=dict(color="red", width=1.5)), row=3, col=1)
                    
                    fig.update_layout(template="plotly_dark", height=650, margin=dict(l=10, r=10, t=30, b=10))
                    st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"Hata olustu: {e}")

# --- TAB 2: İZLEME LİSTEM ---
with tab2:
    st.subheader("Takip Ettigim Hisse Listesi")
    st.write("Asagidaki listeden dilediginiz hisseye basarak aninda detayli analizine gecebilirsiniz.")
    
    cols = st.columns(3)
    for idx, symbol in enumerate(WATCHLIST):
        with cols[idx % 3]:
            st.markdown(f"### {symbol}")
            if st.button(f"{symbol} Analiz Et", key=f"watch_{symbol}"):
                st.session_state['selected_ticker'] = symbol
                st.session_state['auto_run'] = True
                st.success(f"{symbol} seçildi! Üstteki 'Tek Hisse Detaylı Analiz' sekmesine geçebilirsiniz.")

# --- TAB 3: PORTFÖYÜM ---
with tab3:
    st.subheader("Portfoyumdeki (Aldigim) Hisseler")
    st.write("Elin
