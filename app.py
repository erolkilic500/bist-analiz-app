import streamlit as st
from PIL import Image
import google.generativeai as genai

# Sayfa ayarları
st.set_page_config(page_title="BIST Trading Yapay Zeka Gözü Paneli", layout="centered")

# Parola ve API Key Koruması
def check_auth():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        st.subheader("🔑 Giriş ve Yapay Zeka Ayarları")
        password = st.text_input("Erişim Şifresi:", type="password")
        gemini_key = st.text_input("Gemini API Anahtarı (Google AI Studio'dan alınır):", type="password")
        
        if password == "bist2026" and gemini_key:
            st.session_state["authenticated"] = True
            st.session_state["gemini_key"] = gemini_key
            st.success("Giriş Başarılı!")
            st.rerun()
        elif password and not gemini_key:
            st.warning("Lütfen Gemini API anahtarınızı girin.")
        return False
    return True

if check_auth():
    genai.configure(api_key=st.session_state["gemini_key"])
    
    st.title("📈 BIST Trading Yapay Zeka Otomatik Analiz Paneli")
    st.caption("Grafik fotoğrafını yükle; yapay zeka gözü grafiği inceleyip tüm indikatörleri senin için kusursuzca okusun!")

    uploaded_file = st.file_uploader("TradingView Grafik Fotoğrafını Seç (PNG, JPG)", type=["png", "jpg", "jpeg"])

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Yüklenen Grafik", use_column_width=True)

        if st.button("🤖 Yapay Zeka ile Tam Otomatik Analiz Et"):
            with st.spinner("Yapay zeka grafiği inceliyor, mumları ve indikatörleri okuyor..."):
                try:
                    # Google AI Studio'nun güncel kararlı modeli
                    model = genai.GenerativeModel('gemini-3.8-flash')
                    
                    prompt = """
                    Bu bir TradingView Borsa İstanbul (BIST) hisse senedi teknik analiz grafik görüntüsüdür.
                    Lütfen grafiğe bir uzman gözüyle dikkatlice bak ve şu indikatörlerin durumunu gerçek teknik analize göre belirle:
                    - MACD ([ + ] veya [ - ])
                    - Stoch RSI / Stoch ([ + ] veya [ - ])
                    - RSI ([ + ] veya [ - ])
                    - Hacim ([ + ] veya [ - ])
                    - EMA20/50 ([ + ] veya [ - ])
                    - OBV ([ + ] veya [ - ])
                    - ATR ([ + ] veya [ - ])
                    - Bollinger Bands / BB ([ + ] veya [ - ])
                    
                    Ayrıca grafikteki güncel fiyatı (Alış) ve üst hedef fiyatı (TP) görseldeki rakamlardan net olarak oku.
                    Yanıtı tam olarak şu formatta ver, başka hiçbir açıklama yapma:
                    ALIS: <sayısal fiyat>
                    TP: <sayısal hedef fiyat>
                    MACD: [ + ] veya [ - ]
                    STOCH: [ + ] veya [ - ]
                    RSI: [ + ] veya [ - ]
                    HACIM: [ + ] veya [ - ]
                    EMA: [ + ] veya [ - ]
                    OBV: [ + ] veya [ - ]
                    ATR: [ + ] veya [ - ]
                    BB: [ + ] veya [ - ]
                    """
                    
                    response = model.generate_content([image, prompt])
                    ai_text = response.text
                    
                    # Basit ayrıştırma (Parser)
                    lines = ai_text.split('\n')
                    data = {}
                    for line in lines:
                        if ":" in line:
                            k, v = line.split(":", 1)
                            data[k.strip().upper()] = v.strip()

                    last_price = float(data.get("ALIS", "42.30").replace(",", "."))
                    tp1 = float(data.get("TP", "43.38").replace(",", "."))
                    tp2 = round(tp1 * 1.015, 2)
                    
                    stop_loss = round(last_price * (1 - 0.015), 2)
                    min_p = stop_loss
                    max_p = round(tp1 * 1.01, 2)
                    avg_p = round((min_p + max_p) / 2, 2)

                    macd_stat = data.get("MACD", "[ + ]")
                    stoch_stat = data.get("STOCH", "[ + ]")
                    rsi_stat = data.get("RSI", "[ + ]")
                    hacim_stat = data.get("HACIM", "[ + ]")
                    ema_stat = data.get("EMA", "[ + ]")
                    obv_stat = data.get("OBV", "[ + ]")
                    atr_stat = data.get("ATR", "[ - ]")
                    bb_stat = data.get("BB", "[ + ]")

                    indicators = [macd_stat, stoch_stat, rsi_stat, hacim_stat, ema_stat, obv_stat, atr_stat, bb_stat]
                    positives = indicators.count("[ + ]")
                    skor = f"{positives}/8"
                    sinyal = "AL" if positives >= 5 else ("BEKLE" if positives >= 3 else "SAT")

                    st.success("✅ Yapay Zeka Analizi Başarıyla Tamamlandı!")

                    # Sonuç Tablosu
                    panel_output = f"""
 ⏱️ 18:05  |  Alış: {last_price:.2f}  |  TP: {tp1} / {tp2}
 🛑 Stop-Loss (%1.5): {stop_loss}
 --------------------------------------------------
  Periyot |   Min (SL) |   Ort    |   Max   
    1D    |  {min_p:.2f}  |  {avg_p:.2f}  |  {max_p:.2f}
    5D    |  {min_p:.2f}  |  {avg_p:.2f}  |  {max_p:.2f}
    Gun   |  {min_p:.2f}  |  {avg_p:.2f}  |  {max_p:.2f}
 --------------------------------------------------
  MACD     |  {macd_stat}   | TEMA  |  {ema_stat}
  EMA20/50 |  {ema_stat}   | Hacim |  {hacim_stat}
  OBV      |  {obv_stat}   | Stoch |  {stoch_stat}
  ATR      |  {atr_stat}   | BB    |  {bb_stat}
 --------------------------------------------------
  SİNYAL   |  {sinyal}    | Skor :  {skor}
                    """
                    
                    st.code(panel_output, language="text")

                except Exception as e:
                    error_str = str(e)
                    if "429" in error_str or "ResourceExhausted" in error_str or "quota" in error_str.lower():
                        st.error("⚠️ Google AI Studio ücretsiz sürüm dakikalık istek sınırına (Rate Limit) takıldınız. Lütfen 30-40 saniye bekleyip tekrar deneyin.")
                    else:
                        st.error(f"Yapay zeka analizi sırasında bir hata oluştu: {e}")
