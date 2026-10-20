# Otomatik gelen Yahoo son fiyatını değişken olarak tanımlayalım
    default_yf_price = float(df['Close'].iloc[-1])
    
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
