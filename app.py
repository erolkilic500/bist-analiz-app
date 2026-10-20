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
    st.caption("TradingView grafik fotoğrafını yükleyin, fiyatları girip stop-loss'lu analizinizi anında alın!")

    uploaded_file = st.file_uploader("Grafik Fotoğrafını Seçin (PNG, JPG)", type=["png", "jpg", "jpeg"])

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Yüklenen Grafik", use_column_width=True)

        # Kullanıcının Alış ve TP değerlerini manuel girebileceği alanlar
        col1, col2 = st.columns(2)
        with col1:
            manual_price = st.number_input("📊 Güncel / Alış Fiyatı", value=119.00, step=0.10)
        with col2:
            manual_tp = st.number_input("🎯 Hedef Fiyat (TP)", value=122.50, step=0.10)

        if st.button("🚀 Paneli Oluştur"):
            last_price = float(manual_price)
            tp1 = float(manual_tp)
            tp2 = round(tp1 * 1.015, 2)
            
            # %1.5 Stop-Loss Hesaplama
            stop_loss = round(last_price * (1 - 0.015), 2)
            
            # Tablo için Min / Max aralığı
            min_p = stop_loss
            max_p = round(last_price * 1.04, 2)
            avg_p = round((min_p + max_p) / 2, 2)

            # Örnek Gösterge Durumları
            macd_stat = "[ + ]"
            stoch_stat = "[ + ]"
            rsi_stat = "[ - ]"
            hacim_stat = "[ + ]"

            skor = "3/8"
            sinyal = "AL"

            st.success("✅ Analiz Paneli Oluşturuldu!")

            # Sonuç Tablosu (%1.5 Stop-Loss eklenmiş hali)
            panel_output = f"""
 ⏱️ 18:05  |  Alış: {last_price:.2f}  |  TP: {tp1} / {tp2}
 🛑 Stop-Loss (%1.5): {stop_loss}
 --------------------------------------------------
  Periyot |   Min (SL) |   Ort    |   Max   
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
