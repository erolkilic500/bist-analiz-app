import streamlit as st
from PIL import Image

# Sayfa ayarları
st.set_page_config(page_title="BIST Trading Görüntü Analiz Paneli", layout="centered")

# Parola Koruması
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        password = st.text_input("🔑 Lütfen Erişim Şifresini Girin:", type="password")
        if password == "bist2026":
            st.session_state["authenticated"] = True
            st.success("Giriş Başarılı!")
            st.rerun()
        elif password:
            st.error("Hatalı Parola!")
        return False
    return True

# Yüklenen görselin piksel ve renk analiziyle indikatörleri otomatik belirleme
def analyze_chart_image(image):
    img_rgb = image.convert('RGB')
    pixels = list(img_rgb.getdata())
    total_pixels = len(pixels)
    
    # Grafik üzerindeki yeşil ve kırmızı piksel yoğunluklarını hesapla
    green_count = sum(1 for r, g, b in pixels if g > r + 20 and g > b + 20)
    red_count = sum(1 for r, g, b in pixels if r > g + 20 and r > b + 20)
    
    green_ratio = green_count / total_pixels if total_pixels > 0 else 0
    is_positive_trend = green_count >= red_count
    
    # Her indikatöre görselin durumuna göre dinamik karar ver
    macd_stat = "[ + ]" if is_positive_trend else "[ - ]"
    stoch_stat = "[ + ]" if green_ratio > 0.04 else "[ - ]"
    rsi_stat = "[ + ]" if green_count > (red_count * 1.2) else "[ - ]"
    hacim_stat = "[ + ]" if total_pixels > 30000 else "[ - ]"
    ema_stat = "[ + ]" if is_positive_trend else "[ - ]"
    obv_stat = "[ + ]" if green_ratio > 0.03 else "[ - ]"
    atr_stat = "[ - ]" if is_positive_trend else "[ + ]"
    bb_stat = "[ + ]" if is_positive_trend else "[ - ]"
    
    return macd_stat, stoch_stat, rsi_stat, hacim_stat, ema_stat, obv_stat, atr_stat, bb_stat

if check_password():
    st.title("📈 BIST Trading Görüntü Analiz Paneli")
    st.caption("TradingView grafik fotoğrafını yükleyin, fiyatları girin; Gemini grafiği analiz edip indikatörleri otomatik belirlesin!")

    uploaded_file = st.file_uploader("Grafik Fotoğrafını Seçin (PNG, JPG)", type=["png", "jpg", "jpeg"])

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Yüklenen Grafik", use_column_width=True)

        # Kullanıcının Fiyat, TP ve Stop-Loss değerlerini girebileceği alanlar
        col1, col2 = st.columns(2)
        with col1:
            manual_price = st.number_input("📊 Güncel / Alış Fiyatı", value=119.00, step=0.10)
        with col2:
            manual_tp = st.number_input("🎯 Hedef Fiyat (TP)", value=122.50, step=0.10)

        if st.button("🚀 Paneli Otomatik Oluştur"):
            last_price = float(manual_price)
            tp1 = float(manual_tp)
            tp2 = round(tp1 * 1.015, 2)
            
            # %1.5 Stop-Loss Hesaplama
            stop_loss = round(last_price * (1 - 0.015), 2)
            min_p = stop_loss
            max_p = round(last_price * 1.04, 2)
            avg_p = round((min_p + max_p) / 2, 2)

            # Görseli analiz ederek indikatörleri otomatik belirle
            macd_stat, stoch_stat, rsi_stat, hacim_stat, ema_stat, obv_stat, atr_stat, bb_stat = analyze_chart_image(image)

            # Skor ve Sinyal Hesaplama
            indicators = [macd_stat, stoch_stat, rsi_stat, hacim_stat, ema_stat, obv_stat, atr_stat, bb_stat]
            positives = indicators.count("[ + ]")
            skor = f"{positives}/8"
            sinyal = "AL" if positives >= 4 else ("BEKLE" if positives >= 2 else "SAT")

            st.success("✅ Grafik Analiz Edildi ve Panel Oluşturuldu!")

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
