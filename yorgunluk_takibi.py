import cv2
import mediapipe as mp
import serial
import time
import os

# ==========================================
# BÖLÜM 1: AI MODELLERİNİN YAPILANDIRILMASI
# ==========================================
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# Telefon Tespiti (Object Detection) Ayarları
# NOT: model.tflite dosyası site-packages veya çalışma dizininde olmalıdır.
options = vision.ObjectDetectorOptions(
    base_options=python.BaseOptions(model_asset_path='model.tflite'),
    score_threshold=0.5,
    running_mode=vision.RunningMode.IMAGE)
detector = vision.ObjectDetector.create_from_options(options)

# Yüz Takibi ve Landmark (Yüz Noktaları) Ayarları
mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils
face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True, max_num_faces=1)

# ==========================================
# BÖLÜM 2: DONANIM (ARDUINO) BAĞLANTISI
# ==========================================
try:
    arduino = serial.Serial('COM9', 9600, timeout=0.1)
    time.sleep(2) # Bağlantı kararlılığı için bekleme
    print("Donanim Baglantisi Kuruldu!")
except:
    arduino = None
    print("Arduino Baglanamadi! Portu kontrol edin.")

# Kamera ve Değişken Başlatma
cap = cv2.VideoCapture(0)
timers = {"UYKU": 0, "ESNEME": 0, "YANA BAKMA": 0, "BAS DUSMESI": 0}
alarm_aktif = False

# ==========================================
# BÖLÜM 3: ANA DÖNGÜ VE GÖRÜNTÜ İŞLEME
# ==========================================
while cap.isOpened():
    success, image = cap.read()
    if not success: break
    h, w, _ = image.shape

    # Görüntüleri AI modellerinin anlayacağı formatlara çevir
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results_face = face_mesh.process(image_rgb)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image)
    detection_result = detector.detect(mp_image)

    current_alert = None
    yuz_hattı_rengi = (200, 200, 200) # Normal durum: Gri çizgiler

    # --- SENARYO 1: TELEFON TESPİTİ ---
    if detection_result.detections:
        for detection in detection_result.detections:
            if detection.categories[0].category_name in ['cell phone', 'phone']:
                current_alert = "TELEFON VAR!"
                b = detection.bounding_box
                cv2.rectangle(image, (b.origin_x, b.origin_y), (b.origin_x + b.width, b.origin_y + b.height), (0, 0, 255), 3)

    # --- SENARYO 2: YÜZ ANALİZİ VE ANOMALİ TESPİTİ ---
    if results_face.multi_face_landmarks and not current_alert:
        for face in results_face.multi_face_landmarks:

            # A. YANA BAKMA (Dikkat Dağınıklığı)
            if abs(face.landmark[454].z - face.landmark[234].z) > 0.075:
                if timers["YANA BAKMA"] == 0: timers["YANA BAKMA"] = time.time()
                if time.time() - timers["YANA BAKMA"] > 2.5:
                    current_alert = "YANA BAKIYOR"
                    yuz_hattı_rengi = (0, 0, 255) # Tehlike: Kırmızı yüz maskesi
            else: timers["YANA BAKMA"] = 0

            # B. BAŞ DÜŞMESİ (Yorgunluk/Bayılma)
            if (face.landmark[1].y - face.landmark[10].y) > 0.18:
                if timers["BAS DUSMESI"] == 0: timers["BAS DUSMESI"] = time.time()
                if time.time() - timers["BAS DUSMESI"] > 1.2:
                    current_alert = "BAS DUSMESI"
                    yuz_hattı_rengi = (0, 0, 255)
            else: timers["BAS DUSMESI"] = 0

            # C. UYKU VE ESNEME TESPİTİ
            if not current_alert:
                # Göz açıklığı kontrolü
                if (face.landmark[145].y - face.landmark[159].y) < 0.012:
                    if timers["UYKU"] == 0: timers["UYKU"] = time.time()
                    if time.time() - timers["UYKU"] > 1.2: current_alert = "UYKU"
                else: timers["UYKU"] = 0

                # Ağız açıklığı kontrolü
                if (face.landmark[14].y - face.landmark[13].y) > 0.07:
                    if timers["ESNEME"] == 0: timers["ESNEME"] = time.time()
                    if time.time() - timers["ESNEME"] > 2.0: current_alert = "ESNEME"
                else: timers["ESNEME"] = 0

            # Yüz ağını (Face Mesh) ekrana çiz
            mp_drawing.draw_landmarks(image, face, mp_face_mesh.FACEMESH_CONTOURS,
                                      landmark_drawing_spec=None,
                                      connection_drawing_spec=mp_drawing.DrawingSpec(color=yuz_hattı_rengi, thickness=1))

    # ==========================================
    # BÖLÜM 4: ALARM YÖNETİMİ VE ÇIKTI
    # ==========================================
    if current_alert:
        alarm_aktif = True
        # Arduino'ya veriyi gönder (LCD ve Buzzer için)
        if arduino: arduino.write((current_alert + "\n").encode())
        # Ekranda görsel uyarı oluştur
        cv2.rectangle(image, (0, 0), (w, 60), (0, 0, 0), -1)
        cv2.putText(image, f"ALERT: {current_alert}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
    else:
        # Tehlike bittiğinde Arduino'yu sıfırla
        if alarm_aktif:
            if arduino: arduino.write(b"0\n")
            alarm_aktif = False
        # Normal durum göstergesi
        cv2.rectangle(image, (0, 0), (w, 60), (0, 0, 0), -1)
        cv2.putText(image, "STATUS: AWAKE", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    # Pencereyi göster (ESC tuşu ile çıkış)
    cv2.imshow('Azo Ismail Smart Monitoring', image)
    if cv2.waitKey(10) & 0xFF == 27: break

# Kaynakları serbest bırak
cap.release()
cv2.destroyAllWindows()
if arduino: arduino.close()