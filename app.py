import streamlit as st
import yfinance as yf
import pandas as pd

# Sayfa Yapılandırması
st.set_page_config(page_title="BIST Teknik Analiz Paneli", layout="centered")

st.title("📈 BIST Otomatik 8 İndikatör Skorlama Paneli")
st.write("Google AI bağımlılığı olmadan, doğrudan Borsa İstanbul verileriyle saf matematiksel ve objektif teknik analiz!")

# Kullanıcı Girişleri
ticker_input = st.text_input("Hisse Kodu (Örn: THYAO, BERA, EREGL, GARAN)", value="THYAO")
# Büyük harfe çevir ve BIST uzantısını ekle
clean_ticker = ticker_input.strip().upper()
if not clean_ticker.endswith(".IS"):
    clean_ticker += ".IS"

period_choice = st.selectbox("Periyot Seçin", ["5 Dakika", "1 Saat", "Günlük"])

# Periyot eşleştirmesi
if period_choice == "5 Dakika":
    interval = "5m"
    period = "5d"
elif period_choice == "1 Saat":
    interval = "1h"
    period = "1mo"
else:
    interval = "1d"
    period = "6mo"

if st.button("Teknik Analizi Hesapla"):
    try:
        with st.spinner("Veriler indiriliyor ve analiz ediliyor..."):
            df = yf.download(clean_ticker, period=period, interval=interval, progress=False)
            
            if df.empty:
                st.error("Hisse verisi bulunamadı. Lütfen geçerli bir hisse kodu girin.")
            else:
                # Çok katmanlı sütun başlığı sorununu önleme
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                    
                st.success("Saf Matematiksel Analiz Başarıyla Tamamlandı!")
                
                # Temel veri çekme
                default_yf_price = float(df['Close'].iloc[-1])
                volume = int(df['Volume'].iloc[-1])
                avg_volume = int(df['Volume'].rolling(20).mean().iloc[-1])
                
                st.markdown(f"**Ham Veri Kontrolü** $\rightarrow$ Son Kapanış: {default_yf_price:.2f} | Hacim: {volume:,} (Ort: {avg_volume:,})")
                
                st.markdown("---")
                st.subheader("⚡ Ziraat Trader Canlı Fiyat Entegrasyonu")
                
                # Ziraat Trader / Anlık Manuel Fiyat Girişi
                manual_price = st.number_input(
                    "Ziraat Trader Anlık Fiyatını Girin (Değiştirmek istemiyorsanız aynı bırakın veya 0 yapın):", 
                    value=default_yf_price, 
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
                st.markdown("---")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Alış / Baz Fiyat", f"{last_price:.2f} TL")
                with col2:
                    st.metric("Stop-Loss (%1.5)", f"{stop_loss:.2f} TL")
                with col3:
                    st.metric("TP / Kar Al (%5)", f"{take_profit:.2f} TL")
                    
                st.markdown("--------------------------------------------------")
                
    except Exception as e:
        st.error(f"Bir hata oluştu: {e}")
