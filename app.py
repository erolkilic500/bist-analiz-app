import streamlit as st
from PIL import Image

# Sayfa ayarları
st.set_page_config(page_title="BIST Trading Analiz Paneli", layout="centered")

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
    st.title("📈 BIST Trading Akıllı Analiz Paneli")
    st.caption("Grafik fotoğrafını yükleyin, fiyatları girin ve dilediğiniz indikatör durumunu esnekçe yönetin!")

    uploaded_file = st.file_uploader("Grafik Fotoğrafını Seçin (PNG, JPG)", type=["png", "jpg", "jpeg"])

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Yüklenen Grafik", use_column_width=True)

        # 1. Fiyat ve Hedef Alanı
        st.markdown("### 📊 Fiyat, TP ve Stop-Loss Seviyeleri")
        col1, col2, col3 = st.columns(3)
        with col1:
            manual_price = st.number_input("Alış Fiyatı", value=42.30, step=0.01)
        with col2:
            manual_tp = st.number_input("Hedef Fiyat (TP)", value=43.38, step=0.01)
        with col3:
            sl_orani = st.slider("Stop-Loss %", value=1.5, step=0.1)

        # 2. İndikatör Durumları (Otomatik Taslak + Manuel Esneklik Kontrolü)
        st.markdown("### ⚙️ İndikatör Durumları (İstediğinizi Tek Tuşla Değiştirin)")
        
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            macd_choice = st.selectbox("MACD", ["[ + ]", "[ - ]"], index=0)
        with c2:
            stoch_choice = st.selectbox("Stoch RSI", ["[ + ]", "[ - ]"], index=0)
        with c3:
            rsi_choice = st.selectbox("RSI", ["[ + ]", "[ - ]"], index=0)
        with c4:
            hacim_choice = st.selectbox("Hacim", ["[ + ]", "[ - ]"], index=0)

        c5, c6, c7, c8 = st.columns(4)
        with c5:
            ema_choice = st.selectbox("EMA20/50", ["[ + ]", "[ - ]"], index=0)
        with c6:
            obv_choice = st.selectbox("OBV", ["[ + ]", "[ - ]"], index=0)
        with c7:
            atr_choice = st.selectbox("ATR", ["[ + ]", "[ - ]"], index=1)
        with c8:
            bb_choice = st.selectbox("Bollinger (BB)", ["[ + ]", "[ - ]"], index=0)

        if st.button("🚀 Paneli Oluştur"):
            last_price = float(manual_price)
            tp1 = float(manual_tp)
            tp2 = round(tp1 * 1.015, 2)
            
            # Stop-Loss Hesaplama
            stop_loss = round(last_price * (1 - (sl_orani / 100)), 2)
            min_p = stop_loss
            max_p = round(tp1 * 1.01, 2)
            avg_p = round((min_p + max_p) / 2, 2)

            # Skor ve Sinyal Hesaplama
            indicators = [macd_choice, stoch_choice, rsi_choice, hacim_choice, ema_choice, obv_choice, atr_choice, bb_choice]
            positives = indicators.count("[ + ]")
            skor = f"{positives}/8"
            sinyal = "AL" if positives >= 5 else ("BEKLE" if positives >= 3 else "SAT")

            st.success("✅ Analiz Paneli Başarıyla Oluşturuldu!")

            # Sonuç Tablosu
            panel_output = f"""
 ⏱️ 18:05  |  Alış: {last_price:.2f}  |  TP: {tp1} / {tp2}
 🛑 Stop-Loss (%{sl_orani}): {stop_loss}
 --------------------------------------------------
  Periyot |   Min (SL) |   Ort    |   Max   
    1D    |  {min_p:.2f}  |  {avg_p:.2f}  |  {max_p:.2f}
    5D    |  {min_p:.2f}  |  {avg_p:.2f}  |  {max_p:.2f}
    Gun   |  {min_p:.2f}  |  {avg_p:.2f}  |  {max_p:.2f}
 --------------------------------------------------
  MACD     |  {macd_choice}   | TEMA  |  {ema_choice}
  EMA20/50 |  {ema_choice}   | Hacim |  {hacim_choice}
  OBV      |  {obv_choice}   | Stoch |  {stoch_choice}
  ATR      |  {atr_choice}   | BB    |  {bb_choice}
 --------------------------------------------------
  SİNYAL   |  {sinyal}    | Skor :  {skor}
            """
            
            st.code(panel_output, language="text")
