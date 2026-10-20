import streamlit as st
import yfinance as yf
# (Diğer importlar ve mevcut kodlarınız burada yer alıyor...)

st.title("Borsa İstanbul Teknik Analiz ve Skorlama Paneli")

# Hisse kodu ve periyot seçimleri...
ticker_input = st.text_input("Hisse Kodu (Örn: THYAO, BERA, EREGL)", value="THYAO")
period_choice = st.selectbox("Periyot Seçin", ["5 Dakika", "1 Saat", "Günlük"])

if st.button("Teknik Analizi Hesapla"):
    # Hisse verisini Yahoo Finance'ten çekme (Mevcut kodunuz)
    # ...
    
    # ---------------------------------------------------------
    # YENİ EKLENEN: Ziraat Trader / Anlık Manuel Fiyat Girişi
    # ---------------------------------------------------------
    st.markdown("---")
    st.subheader("⚡ Canlı Fiyat Entegrasyonu (İsteğe Bağlı)")
    
    # Otomatik gelen Yahoo son fiyatını varsayılan (value) olarak gösterelim ki referans olsun
    default_yf_price = float(df['Close'].iloc[-1])
    
    manual_price = st.number_input(
        "Ziraat Trader Anlık Fiyatını Girin (Değiştirmek istemiyorsanız aynı bırakın veya 0 yapın):", 
        value=default_yf_pop := default_yf_price, 
        step=0.10, 
        format="%.2f"
    )
    
    # Fiyat belirleme mantığı
    if manual_price > 0:
        last_price = manual_price
        st.success(f"✅ İşlemler aktif olarak girdiğiniz **{last_price:.2f} TL** canlı fiyata göre hesaplanıyor.")
    else:
        last_price = default_yf_price
        st.info(f"ℹ️ Yahoo Finance fiyatı kullanılıyor: {last_price:.2f} TL")
    
    # Stop-Loss (%1.5) ve Kar Al - TP (%5) Hesaplamaları
    stop_loss = last_price * (1 - 0.015)
    take_profit = last_price * (1 + 0.05)
    
    # Sonuçların ekrana yazdırılması
    st.markdown(f"**Alış / Baz Fiyat:** {last_price:.2f} TL")
    st.markdown(f"**Stop-Loss (%1.5):** {stop_loss:.2f} TL")
    st.markdown(f"**TP / Kar Al (%5):** {take_profit:.2f} TL")
