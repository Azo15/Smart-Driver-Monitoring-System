// Proje için LCD kütüphanesini ekliyoruz
#include <LiquidCrystal.h>

// LCD ekranımızın pin bağlantıları (Arduino'ya taktığımız pinler)
LiquidCrystal lcd(12, 11, 5, 4, 3, 2);

// Hangi pinde ne var onları tanımlıyoruz 
const int buzzer = 8; // Alarmımız 8. pinde
const int pinR = 9; // Kırmızı LED'imiz (Tehlike durumu) 9. pinde
const int pinG = 10; // Yeşil LED'imiz (Normal durum) 10. pinde

void setup() {
  // Python koduyla haberleşmek için seri port hızını bilgisayardakiyle (9600) aynı yapıyoruz
  Serial.begin(9600);
  // 16 sütun ve 2 satırlık bir LCD kullandığımızı Arduino'ya söylüyoruz
  lcd.begin(16, 2);
  
  // LED'ler ve buzzer bize çıktı vereceği için OUTPUT yaptık
  pinMode(buzzer, OUTPUT);
  pinMode(pinR, OUTPUT);
  pinMode(pinG, OUTPUT);
  
  // Ekranı temizleyip ilk açılış mesajını yazdırıyoruz
  lcd.clear();
  lcd.print("Sistem Aktif");
}

void loop() {
  // Bilgisayardan (Python'dan) veri gelip gelmediğini kontrol ediyoruz
  if (Serial.available() > 0) {
    // Python'dan gönderilen metni satır sonuna kadar (enter'a basılana kadar) okuyoruz
    String veri = Serial.readStringUntil('\n'); 
    
    // Eğer Python bize "0" gönderdiyse, bu "Her şey normal, sürücü uyanık" demek
    if (veri == "0") { 
      digitalWrite(pinR, LOW); // Kırmızı LED'i kapat
      digitalWrite(pinG, HIGH); // Yeşil LED'i yak (Güvendeyiz)
      noTone(buzzer); // Buzzer'ı sustur
      
      // LCD ekranda normal durumu gösteren hocamıza sunmalık yazılar
      lcd.clear();
      lcd.print("Sistem Aktif");
      lcd.setCursor(0, 1); // İkinci satıra geç 
      lcd.print("Yol Acik...    ");
    } 
    // Eğer 0 gelmediyse, demek ki bir tehlike var (Python hatanın adını gönderiyor)
    else { 
      digitalWrite(pinG, LOW); // Yeşil LED'i kapat (Artık güvende değiliz)
      
      // Dikkat çekmek için Kırmızı LED'i polis çakarı gibi yanıp söndürüyoruz
      static bool toggle = false;
      digitalWrite(pinR, toggle ? HIGH : LOW);
      toggle = !toggle;
      
      // Hocam uyarı olsun diye buzzerı tiz bir seste (2500 Hz) çalıştırıyoruz
      tone(buzzer, 2500);
      
      // LCD ekranın birinci satırında Uyarı yazısı
      lcd.setCursor(0, 0);
      lcd.print("!!! ALERT !!!  ");
      
      // İkinci satırda da hatanın ne olduğunu (UYKU, ESNEME vb.) yazdırıyoruz
      lcd.setCursor(0, 1);
      // Gelen uzunluk değişebileceğinden ekranda önceki yazının kalıntısı kalmasın diye sonuna boşluk ekledik
      lcd.print(veri + "          "); 
    }
  }
}
