import cv2
import mediapipe as mp
import serial
import time
import os

# ==========================================
# YAPILANDIRMA: YAPAY ZEKA MODELLERİNİN BAŞLATILMASI
# ==========================================
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# Nesne Tespiti (Telefon Saptama) Konfigürasyonu
# Lütfen dikkat: model.tflite dosyasının çalışma ortamında ya da site-packages dizininde yer aldığından emin olunuz.
options = vision.ObjectDetectorOptions(
    base_options=python.BaseOptions(model_asset_path='model.tflite'),
    score_threshold=0.5,
    running_mode=vision.RunningMode.IMAGE)
detector = vision.ObjectDetector.create_from_options(options)

# Yüz İzleme ve Landmark (Yüz Hatları) Çıkarım Konfigürasyonu
mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils
face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True, max_num_faces=1)

# ==========================================
# DONANIM: MİKRODENETLEYİCİ (ARDUINO) SERİ HABERLEŞME BAĞLANTISI
# ==========================================
try:
    arduino = serial.Serial('COM9', 9600, timeout=0.1)
    time.sleep(2) # Bağlantının stabilizasyonu için bekleme süresi
    print("Sistem Mesajı: Donanım bağlantısı başarıyla kuruldu.")
except:
    arduino = None
    print("Hata Durumu: Arduino ile bağlantı sağlanamadı. Lütfen COM port konfigürasyonunu kontrol ediniz.")

# Kamera Modülü ve Zamanlayıcı Değişkenlerinin İlklendirilmesi
cap = cv2.VideoCapture(0)
timers = {"UYKU": 0, "ESNEME": 0, "YANA BAKMA": 0, "BAS DUSMESI": 0}
alarm_aktif = False

# ==========================================
# SİSTEM İŞLEYİŞİ: ANA GÜVENLİK DÖNGÜSÜ VE GÖRÜNTÜ İŞLEME ADIMLARI
# ==========================================
while cap.isOpened():
    success, image = cap.read()
    if not success: break
    h, w, _ = image.shape

    # Görüntü matrislerinin yapay zeka modelleri için uygun formatlara dönüştürülmesi
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results_face = face_mesh.process(image_rgb)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image)
    detection_result = detector.detect(mp_image)

    current_alert = None
    yuz_hattı_rengi = (200, 200, 200) # Olağan durum göstergesi: Gri referans çizgileri

    # --- ANALİZ 1: MOBİL CİHAZ (TELEFON) KULLANIM TESPİTİ ---
    if detection_result.detections:
        for detection in detection_result.detections:
            if detection.categories[0].category_name in ['cell phone', 'phone']:
                current_alert = "TELEFON VAR!"
                b = detection.bounding_box
                cv2.rectangle(image, (b.origin_x, b.origin_y), (b.origin_x + b.width, b.origin_y + b.height), (0, 0, 255), 3)

    # --- ANALİZ 2: YÜZ GEOMETRİSİ ANALİZİ VE ANOMALİ SAPTAMASI ---
    if results_face.multi_face_landmarks and not current_alert:
        for face in results_face.multi_face_landmarks:

            # Kriter A: Sürücünün Yola Odaklanmama (Dikkat Dağınıklığı) Durumu
            if abs(face.landmark[454].z - face.landmark[234].z) > 0.075:
                if timers["YANA BAKMA"] == 0: timers["YANA BAKMA"] = time.time()
                if time.time() - timers["YANA BAKMA"] > 2.5:
                    current_alert = "YANA BAKIYOR"
                    yuz_hattı_rengi = (0, 0, 255) # Risk durumu göstergesi: Kırmızı referans çizgileri
            else: timers["YANA BAKMA"] = 0

            # Kriter B: Dikey Eksen Altında Baş Düşmesi (Aşırı Yorgunluk Eğilimi)
            if (face.landmark[1].y - face.landmark[10].y) > 0.18:
                if timers["BAS DUSMESI"] == 0: timers["BAS DUSMESI"] = time.time()
                if time.time() - timers["BAS DUSMESI"] > 1.2:
                    current_alert = "BAS DUSMESI"
                    yuz_hattı_rengi = (0, 0, 255)
            else: timers["BAS DUSMESI"] = 0

            # Kriter C: Uyuklama ve Esneme (Fiziksel Yorgunluk) Belirtilerinin Saptanması
            if not current_alert:
                # Göz kapakları arası mesafe (Açıklık Oranı) analizi
                if (face.landmark[145].y - face.landmark[159].y) < 0.012:
                    if timers["UYKU"] == 0: timers["UYKU"] = time.time()
                    if time.time() - timers["UYKU"] > 1.2: current_alert = "UYKU"
                else: timers["UYKU"] = 0

                # Ağız bölgesi açıklık oranının izlenmesi
                if (face.landmark[14].y - face.landmark[13].y) > 0.07:
                    if timers["ESNEME"] == 0: timers["ESNEME"] = time.time()
                    if time.time() - timers["ESNEME"] > 2.0: current_alert = "ESNEME"
                else: timers["ESNEME"] = 0

            # Yüz topolojisinin (Face Mesh) görselleştirilmesi
            mp_drawing.draw_landmarks(image, face, mp_face_mesh.FACEMESH_CONTOURS,
                                      landmark_drawing_spec=None,
                                      connection_drawing_spec=mp_drawing.DrawingSpec(color=yuz_hattı_rengi, thickness=1))

    # ==========================================
    # UYARI SİSTEMİ: ALARM YÖNETİMİ VE BİLGİLENDİRME ÇIKTILARI
    # ==========================================
    if current_alert:
        alarm_aktif = True
        # Donanıma uyarı sinyalinin iletilmesi (Harici LED, Buzzer vb. için)
        if arduino: arduino.write((current_alert + "\n").encode())
        # Kullanıcı arayüzünde (Ekranda) görsel uyarı oluşturulması
        cv2.rectangle(image, (0, 0), (w, 60), (0, 0, 0), -1)
        cv2.putText(image, f"ALERT: {current_alert}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
    else:
        # Risk faktörü ortadan kalktığında donanım sinyallerinin sıfırlanması
        if alarm_aktif:
            if arduino: arduino.write(b"0\n")
            alarm_aktif = False
        # Olağan seyrin (Sürücü Dikkatli) arayüzde gösterimi
        cv2.rectangle(image, (0, 0), (w, 60), (0, 0, 0), -1)
        cv2.putText(image, "STATUS: AWAKE", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    # İzleme penceresinin render edilmesi (Durdurmak için: ESC tuşu)
    cv2.imshow('Azo Ismail Smart Monitoring', image)
    if cv2.waitKey(10) & 0xFF == 27: break

# Sistem kaynaklarının serbest bırakılması ve bağlantıların sonlandırılması
cap.release()
cv2.destroyAllWindows()
if arduino: arduino.close()