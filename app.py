# Gerçek Piyasa Verileri (O güne ait High, Low ve Kapanış/Ortalama)
                    actual_low = float(low.iloc[-1])
                    actual_high = float(high.iloc[-1])
                    actual_close = float(close.iloc[-1])
                    
                    # Eğer hacimli ağırlıklı ortalama hesaplamak istersek yaklaşık close/ortalama, 
                    # ya da doğrudan o mumun medyan/ortalama fiyatı:
                    actual_avg = round((actual_high + actual_low) / 2, 3) # veya borsa A.Ort. mantığı

                    last_price = actual_close
                    tp1 = round(last_price * 1.025, 2)
                    tp2 = round(last_price * 1.04, 2)
                    stop_loss = round(last_price * 0.985, 2)
                    
                    # Tabloda borsa ekranındakiyle birebir görünmesi için:
                    min_p = actual_low
                    max_p = actual_high
                    avg_p = actual_avg
