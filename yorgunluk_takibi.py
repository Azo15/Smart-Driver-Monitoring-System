import cv2
import mediapipe as mp
import serial
import time
import os

# ==========================================
# 1. Aşama: Gerekli Kütüphaneler ve Yapay Zeka Modelleri
# ==========================================
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# Telefon kullanıp kullanmadığını anlamak için Object Detection (Nesne Tespiti) modeli
# model.tflite dosyasını proje klasöründe tutmamız gerekiyor.
options = vision.ObjectDetectorOptions(
    base_options=python.BaseOptions(model_asset_path='model.tflite'),
    score_threshold=0.5,
    running_mode=vision.RunningMode.IMAGE)
detector = vision.ObjectDetector.create_from_options(options)

# Yüzdeki noktaları (göz, ağız vb.) bulmak için MediaPipe kütüphanesini ayarlıyoruz.
mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils
face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True, max_num_faces=1)

# ==========================================
# 2. Aşama: Arduino Bağlantısının Kurulması
# ==========================================
try:
    arduino = serial.Serial('COM9', 9600, timeout=0.1)
    time.sleep(2) # Arduino'nun kendine gelip bağlantıyı kurması için bekletiyoruz
    print("Arduino başarıyla bağlandı!")
except:
    arduino = None
    print("Hata! Arduino bulunamadı. Kabloyu taktınız mı veya COM portunu doğru mu yazdık?")

# Kamerayı açıyoruz (0 bilgisayarın kendi kamerasıdır) ve tehlike sürelerini sayacak değişkenleri sıfırlıyoruz
cap = cv2.VideoCapture(0)
timers = {"UYKU": 0, "ESNEME": 0, "YANA BAKMA": 0, "BAS DUSMESI": 0}
alarm_aktif = False

# ==========================================
# 3. Aşama: Sonsuz Döngüde Kameradan Görüntü Alma ve İşleme
# ==========================================
while cap.isOpened():
    success, image = cap.read()
    if not success: break
    h, w, _ = image.shape

    # OpenCV kameradan BGR formatında görüntü alıyor, AI modeli için bunu RGB formatına çevirmemiz lazım
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results_face = face_mesh.process(image_rgb)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image)
    detection_result = detector.detect(mp_image)

    current_alert = None
    yuz_hattı_rengi = (200, 200, 200) # Her şey normalse yüzdeki noktaları gri çizgilerle göstereceğiz

    # --- SENARYO 1: TELEFONLA OYNAMA DURUMU ---
    if detection_result.detections:
        for detection in detection_result.detections:
            if detection.categories[0].category_name in ['cell phone', 'phone']:
                current_alert = "TELEFON VAR!"
                b = detection.bounding_box
                cv2.rectangle(image, (b.origin_x, b.origin_y), (b.origin_x + b.width, b.origin_y + b.height), (0, 0, 255), 3)

    # --- SENARYO 2: YÜZDEKİ NOKTALARA GÖRE YORGUNLUK / YAPAY ZEKA TESPİTİ ---
    if results_face.multi_face_landmarks and not current_alert:
        for face in results_face.multi_face_landmarks:

            # 1. Yana Bakma (Yolla ilgilenmeyip etrafa bakma durumu)
            if abs(face.landmark[454].z - face.landmark[234].z) > 0.075:
                if timers["YANA BAKMA"] == 0: timers["YANA BAKMA"] = time.time()
                if time.time() - timers["YANA BAKMA"] > 2.5:
                    current_alert = "YANA BAKIYOR"
                    yuz_hattı_rengi = (0, 0, 255) # İkaz vermek için yüzündeki haritayı kırmızı yapıyoruz
            else: timers["YANA BAKMA"] = 0

            # 2. Başın Öne Düşmesi (Uyuyakalmak üzere olma)
            if (face.landmark[1].y - face.landmark[10].y) > 0.18:
                if timers["BAS DUSMESI"] == 0: timers["BAS DUSMESI"] = time.time()
                if time.time() - timers["BAS DUSMESI"] > 1.2:
                    current_alert = "BAS DUSMESI"
                    yuz_hattı_rengi = (0, 0, 255)
            else: timers["BAS DUSMESI"] = 0

            # 3. Uyku (Göz Kapama) ve Esneme Kontrolü
            if not current_alert:
                # Gözlerin ne kadar açık olduğuna bakıyoruz (Göz kapakları arası oran hesabı)
                if (face.landmark[145].y - face.landmark[159].y) < 0.012:
                    if timers["UYKU"] == 0: timers["UYKU"] = time.time()
                    if time.time() - timers["UYKU"] > 1.2: current_alert = "UYKU"
                else: timers["UYKU"] = 0

                # Ağzını çok açıp açmadığını hesaplayarak esnemeyi tespit ediyoruz
                if (face.landmark[14].y - face.landmark[13].y) > 0.07:
                    if timers["ESNEME"] == 0: timers["ESNEME"] = time.time()
                    if time.time() - timers["ESNEME"] > 2.0: current_alert = "ESNEME"
                else: timers["ESNEME"] = 0

            # Tespit bitince yüzdeki noktaları videonun üstüne çizdiriyoruz
            mp_drawing.draw_landmarks(image, face, mp_face_mesh.FACEMESH_CONTOURS,
                                      landmark_drawing_spec=None,
                                      connection_drawing_spec=mp_drawing.DrawingSpec(color=yuz_hattı_rengi, thickness=1))

    # ==========================================
    # 4. Aşama: Sonuçları Ekrana Yazdırma ve Arduino'ya Gönderme (Buzzer/LED için)
    # ==========================================
    if current_alert:
        alarm_aktif = True
        # Eğer bir kural ihlali (hata) varsa Arduino'ya hatayı metin olarak gönderiyoruz ki alarm çalsın
        if arduino: arduino.write((current_alert + "\n").encode())
        # Bilgisayar ekranında da tehlike durumunu üst kısımda renkli yazıyla veriyoruz
        cv2.rectangle(image, (0, 0), (w, 60), (0, 0, 0), -1)
        cv2.putText(image, f"ALERT: {current_alert}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
    else:
        # Tehlike durumu bittiyse (örneğin uyanıp tekrar yola bakıyorsa) Arduino'daki alarmı susturmak için '0' yolluyoruz
        if alarm_aktif:
            if arduino: arduino.write(b"0\n")
            alarm_aktif = False
        # Ekranda sürücü uyanık ve güvende olduğunu gösteren "STATUS: AWAKE" bildirim yazısı
        cv2.rectangle(image, (0, 0), (w, 60), (0, 0, 0), -1)
        cv2.putText(image, "STATUS: AWAKE", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    # Proje ekranımızı açıp gösteriyoruz. Klavyeden ESC tuşuna basılırsa program kapanacak
    cv2.imshow('Azo Ismail Smart Monitoring', image)
    if cv2.waitKey(10) & 0xFF == 27: break

# Program bittiğinde kamerayı kapatıp çalışmayı bitiriyoruz
cap.release()
cv2.destroyAllWindows()
if arduino: arduino.close()