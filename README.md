# 🚗 Smart Driver Monitoring System (AI + IoT)

Bu proje, sürücü güvenliğini artırmak ve trafik kazalarını önlemek amacıyla geliştirilmiş; **Yapay Zeka (Computer Vision)** ve **Gömülü Sistemler (Arduino)** entegrasyonuna sahip hibrit bir takip sistemidir. Sistem, kamera üzerinden aldığı görüntüyü anlık işleyerek 5 farklı tehlike senaryosunu tespit eder ve hem görsel hem sesli uyarı verir.

<img width="1280" height="720" alt="photo_2026-04-25_23-55-05" src="https://github.com/user-attachments/assets/58c812c2-94ef-48b8-adc9-207076cb25ec" />

<img width="1280" height="720" alt="photo_2026-04-26_00-25-17" src="https://github.com/user-attachments/assets/b41e235c-2d15-483a-b667-4d2a23df48c0" />
<img width="1280" height="720" alt="photo_2026-04-26_00-24-48" src="https://github.com/user-attachments/assets/456c7d38-edf9-4988-9b08-7453410d0de8" />
<img width="1295" height="703" alt="image" src="https://github.com/user-attachments/assets/54c66832-f321-400d-804e-dca4c5604417" />



## 🌟 Öne Çıkan Özellikler

Sistem, **MediaPipe Face Mesh** ve **Object Detection** teknolojilerini kullanarak şu senaryoları anlık takip eder:

1.  **Uyku Tespiti (Drowsiness):** Gözlerin 1.2 saniyeden fazla kapalı kalması durumunda kırmızı alarm.
2.  **Esneme Tespiti (Fatigue):** Yorgunluk belirtisi olan ağız hareketlerini takip eder.
3.  **Yana Bakma (Distraction):** Sürücünün yoldan 2.5 saniye boyunca gözünü ayırmasını (sağa/sola bakma) algılar ve **tüm yüz maskesini kırmızıya boyar.**
4.  **Telefon Kullanımı:** Yapay zeka ile araç içinde telefon tespit edildiği an (yüz hareketlerinden bağımsız olarak) en yüksek öncelikli alarmı tetikler.
5.  **Baş Düşmesi:** Uyuyakalma veya bayılma belirtisi olan ani kafa öne düşme hareketlerini yakalar.

## 🛠️ Teknik Altyapı

### Yazılım (Software Stack)
- **Python 3.9+**
- **OpenCV:** Görüntü yakalama ve ön işleme.
- **MediaPipe:** Face Mesh (468 Landmark) ve Nesne Algılama (EfficientDet-Lite0 TFLite).
- **PySerial:** Arduino ile 9600 baud hızında çift yönlü seri haberleşme.

### Donanım (Hardware Stack)
- **Arduino Uno R3**
- **16x2 LCD Ekran:** Anlık durum ve tehlike mesajları (I2C veya paralel).
- **RGB LED:** Durum göstergesi (Yeşil: Güvenli, Kırmızı: Kritik).
- **Buzzer:** Yüksek frekanslı (2500Hz) sesli uyarı.
- **Potansiyometre:** LCD kontrast ayarı.

## 📐 Devre Şeması (Wiring)

Bağlantılar aşağıdaki pin yapısına göre kurulmuştur:

| Bileşen | Arduino Pini | Açıklama |
| :--- | :--- | :--- |
| **LCD RS** | 12 | Veri Seçimi |
| **LCD E** | 11 | Yetkilendirme |
| **LCD D4-D7** | 5, 4, 3, 2 | 4-Bit Veri Yolu |
| **RGB LED (R)** | 9 | Kırmızı Işık (Alarm) |
| **RGB LED (G)** | 10 | Yeşil Işık (Normal) |
| **Buzzer (+)** | 8 | Sesli Uyarı |
| **Potansiyometre** | VO | Kontrast Ayarı |



## 🚀 Kurulum ve Kullanım

1.  **Gereksinimleri Yükleyin:**
    ```bash
    pip install opencv-python mediapipe pyserial
    ```
2.  **Model Dosyasını Hazırlayın:**
    `efficientdet_lite0.tflite` dosyasını indirin, adını `model.tflite` yapın ve projenin `site-packages` klasörüne veya çalışma dizinine ekleyin.
3.  **Arduino Kodunu Yükleyin:**
    `.ino` dosyasını Arduino IDE ile kartınıza flaşlayın.
4.  **Sistemi Başlatın:**
    ```bash
    python yorgunluk_takibi.py
    ```

## 📂 Proje Yapısı
```text
DrowsinessProject/
├── yorgunluk_takibi.py   # Ana Python uygulama kodu
├── arduino_control.ino   # Arduino donanım kontrol kodu
├── model.tflite          # AI Telefon tespit modeli
└── README.md             # Proje dokümantasyonu
```

## Geliştiren: Azo Ismail

## E-posta: ismailazo260@gmail.com

## Kurum: Kırklareli Üniversitesi - Yazılım Mühendisliği
