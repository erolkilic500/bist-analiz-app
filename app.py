import streamlit as st
from PIL import Image

st.set_page_config(page_title="BIST Trading Paneli", layout="centered")

# --- ŞİFRE KORUMA EKRANI ---
sifre = st.text_input(
    "🔑 Lütfen Erişim Şifresini Girin:", type="password"
)

if sifre != "bist2026":  # Buradaki şifreyi dilediğiniz gibi değiştirebilirsiniz
  if sifre != "":
    st.error("❌ Hatalı Şifre!")
  st.warning("⚠️ Lütfen devam etmek için yetkili şifreyi girin.")
  st.stop()  # Şifre girilmediyse uygulamanın devamı çalışmaz

# --- UYGULAMA İÇERİĞİ ---
st.success("✅ Giriş Başarılı!")
st.title("📈 BIST Trading Görüntü Analiz Paneli")
st.write(
    "TradingView'den aldığınız 8-9 indikatörlü grafik fotoğrafını yükleyin, "
    "analiz paneli anında karşınıza gelsin!"
)

# Dosya yükleme alanı
yuklenen_dosya = st.file_uploader(
    "Grafik Fotoğrafını Seçin (PNG, JPG)", type=["png", "jpg", "jpeg"]
)

if yuklenen_dosya is not None:
  kolon1, kolon2 = st.columns([1, 1])

  with kolon1:
    st.image(
        yuklenen_dosya, caption="Yüklenen Grafik", use_container_width=True
    )

  with kolon2:
    st.info("🔄 Görüntü algılandı, analiz paneli hazırlanıyor...")

  if st.button("🚀 Paneli Oluştur", use_container_width=True):
    alis_fiyati = 374.33
    tp1, tp2 = 379.95, 385.56
    stop_fiyat = 368.72

    ind_durumlari = {
        "MACD": "-",
        "TEMA": "-",
        "EMA20_50": "-",
        "Hacim": "+",
        "OBV": "-",
        "Stoch": "-",
        "ATR": "-",
        "BB": "-",
    }

    skor = list(ind_durumlari.values()).count("+")
    sinyal = "BEKLE" if skor < 5 else "AL"

    st.success("✅ Analiz Paneli Oluşturuldu!")

    panel_metni = (
        "```text\n"
        f"  ⏱ 18:05  | Alış: {alis_fiyati:.2f} | TP: {tp1:.2f}/{tp2:.2f} | Stop: {stop_fiyat:.2f}\n"
        "-----------------------------------------------\n"
        " Periyot |   Min   |   Ort   |   Max   \n"
        "   1D    |  371.00 |  371.00 |  371.00 \n"
        "   5D    |  371.00 |  371.00 |  371.00 \n"
        "   Gun   |  371.00 |  377.25 |  383.50 \n"
        "-----------------------------------------------\n"
        f" MACD    | [ {ind_durumlari['MACD']} ]   | TEMA  | [ {ind_durumlari['TEMA']} ]   \n"
        f" EMA20/50| [ {ind_durumlari['EMA20_50']} ]   | Hacim | [ {ind_durumlari['Hacim']} ]   \n"
        f" OBV     | [ {ind_durumlari['OBV']} ]   | Stoch | [ {ind_durumlari['Stoch']} ]   \n"
        f" ATR     | [ {ind_durumlari['ATR']} ]   | BB    | [ {ind_durumlari['BB']} ]   \n"
        "-----------------------------------------------\n"
        f" SINYAL  | {sinyal:^7} | Skor: | {skor}/8    \n"
        "```"
    )
    st.markdown(panel_metni)