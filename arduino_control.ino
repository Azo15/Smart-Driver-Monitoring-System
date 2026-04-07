#include <LiquidCrystal.h>

LiquidCrystal lcd(12, 11, 5, 4, 3, 2);
const int buzzer = 8;
const int pinR = 9;
const int pinG = 10;

void setup() {
  Serial.begin(9600);
  lcd.begin(16, 2);
  pinMode(buzzer, OUTPUT);
  pinMode(pinR, OUTPUT);
  pinMode(pinG, OUTPUT);
  
  lcd.clear();
  lcd.print("Sistem Aktif");
}

void loop() {
  if (Serial.available() > 0) {
    String veri = Serial.readStringUntil('\n'); // Python'dan gelen tam satırı oku
    
    if (veri == "0") { // DURUM NORMAL
      digitalWrite(pinR, LOW);
      digitalWrite(pinG, HIGH);
      noTone(buzzer);
      lcd.clear();
      lcd.print("Sistem Aktif");
      lcd.setCursor(0, 1);
      lcd.print("Yol Acik...    ");
    } 
    else { // TEHLİKE VAR (Gelen veri tehlike adıdır)
      digitalWrite(pinG, LOW);
      // Çakar efekti
      static bool toggle = false;
      digitalWrite(pinR, toggle ? HIGH : LOW);
      toggle = !toggle;
      
      tone(buzzer, 2500);
      lcd.setCursor(0, 0);
      lcd.print("!!! ALERT !!!  ");
      lcd.setCursor(0, 1);
      lcd.print(veri + "          "); // Gelen tehlike adını yaz (UYKU, ESNEME vb.)
    }
  }
}
