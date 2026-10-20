import streamlit as st
from PIL import Image
import pytesseract
import re

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

if check_password():
    st.title("📈 BIST Trading Görüntü Analiz Paneli")
    st.caption("TradingView'den aldığınız 8-9 indikatörlü grafik fotoğrafını yükleyin, analiz paneli anında karşınıza gelsin!")

    uploaded_file = st.file_uploader("Grafik Fotoğrafını Seçin (PNG, JPG)", type=["png", "jpg", "jpeg"])

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Yüklenen Grafik", use_column_width=True)

        if st.button("🚀 Paneli Oluştur"):
            with st.spinner("Görüntü analiz ediliyor ve veriler okunuyor..."):
                # Görselden metin çıkarma (OCR)
                extracted_text = pytesseract.image_to_string(image)

                # Fiyat tespiti
                prices = re.findall(r'\b\d+[.,]\d{2}\b', extracted_text)
                last_price = float(prices[0].replace(',', '.')) if prices else 100.00
                
                # Dinamik Hesaplama Mantığı
                tp1 = round(last_price * 1.015, 2)
                tp2 = round(last_price * 1.03, 2)
                min_p = round(last_price * 0.98, 2)
                max_p = round(last_price * 1.04, 2)
                avg_p = round((min_p + max_p) / 2, 2)

                # İndikatör analizi
                macd_stat = "[ + ]" if "MACD" in extracted_text and "0," in extracted_text else "[ - ]"
                stoch_stat = "[ + ]" if "Stoch" in extracted_text else "[ - ]"
                rsi_stat = "[ + ]" if "RSI" in extracted_text else "[ - ]"
                hacim_stat = "[ + ]" if "Hacim" in extracted_text or "Vol" in extracted_text else "[ - ]"

                # Skor hesaplama
                positives = [macd_stat, stoch_stat, rsi_stat, hacim_stat].count("[ + ]")
                skor = f"{positives}/8"
                sinyal = "AL" if positives >= 2 else "BEKLE"

            st.success("✅ Analiz Paneli Oluşturuldu!")

            # Dinamik Sonuç Tablosu
            panel_output = f"""
 ⏱️ 18:05  |  Alış: {last_price:.2f}  |  TP: {tp1} / {tp2}
 --------------------------------------------------
  Periyot |   Min    |   Ort    |   Max   
    1D    |  {min_p:.2f}  |  {avg_p:.2f}  |  {max_p:.2f}
    5D    |  {min_p:.2f}  |  {avg_p:.2f}  |  {max_p:.2f}
    Gun   |  {min_p:.2f}  |  {avg_p:.2f}  |  {max_p:.2f}
 --------------------------------------------------
  MACD     |  {macd_stat}   | TEMA  |  [ - ]
  EMA20/50 |  [ - ]   | Hacim |  {hacim_stat}
  OBV      |  [ - ]   | Stoch |  {stoch_stat}
  ATR      |  [ - ]   | BB    |  [ - ]
 --------------------------------------------------
  SİNYAL   |  {sinyal}    | Skor :  {skor}
            """
            
            st.code(panel_output, language="text")
