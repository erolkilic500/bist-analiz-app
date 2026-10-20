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

if check_password():
    st.title("📈 BIST Trading Görüntü Analiz Paneli")
    st.caption("Grafiği yükleyin, fiyatları ve indikatör durumlarını seçip panelinizi anında oluşturun!")

    uploaded_file = st.file_uploader("Grafik Fotoğrafını Seçin (PNG, JPG)", type=["png", "jpg", "jpeg"])

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Yüklenen Grafik", use_column_width=True)

        # 1. Fiyat ve Hedef Alanı
        st.markdown("### 📊 Fiyat ve Hedef Seviyeleri")
        col1, col2 = st.columns(2)
        with col1:
            manual_price = st.number_input("Alış Fiyatı", value=119.00, step=0.10)
        with col2:
            manual_tp = st.number_input("Hedef Fiyat (TP)", value=122.50, step=0.10)

        # 2. İndikatör Durumlarını Esnek Seçme Alanı
        st.markdown("### ⚙️ İndikatör Durumları (Grafiğe Göre Belirleyin)")
        col3, col4, col5, col6 = st.columns(4)
        
        with col3:
            macd_choice = st.selectbox("MACD", ["[ + ]", "[ - ]"], index=0)
        with col4:
            stoch_choice = st.selectbox("Stoch", ["[ + ]", "[ - ]"], index=0)
        with col5:
            hacim_choice = st.selectbox("Hacim", ["[ + ]", "[ - ]"], index=0)
        with col6:
            rsi_choice = st.selectbox("RSI", ["[ + ]", "[ - ]"], index=1)

        col7, col8, col9, col10 = st.columns(4)
        with col7:
            ema_choice = st.selectbox("EMA20/50", ["[ + ]", "[ - ]"], index=1)
        with col8:
            obv_choice = st.selectbox("OBV", ["[ + ]", "[ - ]"], index=1)
        with col9:
            atr_choice = st.selectbox("ATR", ["[ + ]", "[ - ]"], index=1)
        with col10:
            bb_choice = st.selectbox("BB", ["[ + ]", "[ - ]"], index=1)

        if st.button("🚀 Paneli Oluştur"):
            last_price = float(manual_price)
            tp1 = float(manual_tp)
            tp2 = round(tp1 * 1.015, 2)
            
            # %1.5 Stop-Loss Hesaplama
            stop_loss = round(last_price * (1 - 0.015), 2)
            min_p = stop_loss
            max_p = round(last_price * 1.04, 2)
            avg_p = round((min_p + max_p) / 2, 2)

            # Seçilen indikatörlere göre skor ve sinyal hesaplama
            indicators = [macd_choice, stoch_choice, hacim_choice, rsi_choice, ema_choice, obv_choice, atr_choice, bb_choice]
            positives = indicators.count("[ + ]")
            skor = f"{positives}/8"
            sinyal = "AL" if positives >= 4 else ("BEKLE" if positives >= 2 else "SAT")

            st.success("✅ Analiz Paneli Oluşturuldu!")

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
  MACD     |  {macd_choice}   | TEMA  |  [ - ]
  EMA20/50 |  {ema_choice}   | Hacim |  {hacim_choice}
  OBV      |  {obv_choice}   | Stoch |  {stoch_choice}
  ATR      |  {atr_choice}   | BB    |  {bb_choice}
 --------------------------------------------------
  SİNYAL   |  {sinyal}    | Skor :  {skor}
            """
            
            st.code(panel_output, language="text")
