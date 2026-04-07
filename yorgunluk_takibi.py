import cv2
import mediapipe as mp
import serial
import time

# --- MODELLERİ ÇAĞIRMA ---
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# model.tflite dosyasının site-packages içinde olduğunu varsayıyoruz
options = vision.ObjectDetectorOptions(
    base_options=python.BaseOptions(model_asset_path='model.tflite'),
    score_threshold=0.5,
    running_mode=vision.RunningMode.IMAGE)
detector = vision.ObjectDetector.create_from_options(options)

# Yüz Takibi
mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils
face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True, max_num_faces=1)

# --- ARDUINO BAĞLANTISI (COM9) ---
try:
    arduino = serial.Serial('COM9', 9600, timeout=0.1)
    time.sleep(2)
    print("Donanim Baglantisi Kuruldu!")
except:
    arduino = None
    print("Arduino Baglanamadi!")

cap = cv2.VideoCapture(0)
# Sayaçlara "BAŞ DÜŞMESİ" eklendi
timers = {"UYKU": 0, "ESNEME": 0, "YANA BAKMA": 0, "BAS DUSMESI": 0}
alarm_aktif = False

while cap.isOpened():
    success, image = cap.read()
    if not success: break
    h, w, _ = image.shape

    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results_face = face_mesh.process(image_rgb)

    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image)
    detection_result = detector.detect(mp_image)

    current_alert = None
    yuz_hattı_rengi = (200, 200, 200)  # Normal gri çizgiler

    # 1. TELEFON TESPİTİ
    if detection_result.detections:
        for detection in detection_result.detections:
            if detection.categories[0].category_name in ['cell phone', 'phone']:
                current_alert = "TELEFON VAR!"
                b = detection.bounding_box
                cv2.rectangle(image, (b.origin_x, b.origin_y), (b.origin_x + b.width, b.origin_y + b.height),
                              (0, 0, 255), 3)

    # 2. YÜZ ANALİZİ
    if results_face.multi_face_landmarks and not current_alert:
        for face in results_face.multi_face_landmarks:

            # --- YANA BAKMA ---
            if abs(face.landmark[454].z - face.landmark[234].z) > 0.075:
                if timers["YANA BAKMA"] == 0: timers["YANA BAKMA"] = time.time()
                if time.time() - timers["YANA BAKMA"] > 2.5:
                    current_alert = "YANA BAKIYOR"
                    yuz_hattı_rengi = (0, 0, 255)  # Yüzü kırmızı yap
            else:
                timers["YANA BAKMA"] = 0

            # --- BAŞ DÜŞMESİ (YENİ EKLENDİ) ---
            # Burun ucu ve alın arasındaki dikey mesafe kontrolü
            if (face.landmark[1].y - face.landmark[10].y) > 0.18:
                if timers["BAS DUSMESI"] == 0: timers["BAS DUSMESI"] = time.time()
                if time.time() - timers["BAS DUSMESI"] > 1.2:
                    current_alert = "BAS DUSMESI"
                    yuz_hattı_rengi = (0, 0, 255)
            else:
                timers["BAS DUSMESI"] = 0

            if not current_alert:
                # --- UYKU ---
                if (face.landmark[145].y - face.landmark[159].y) < 0.012:
                    if timers["UYKU"] == 0: timers["UYKU"] = time.time()
                    if time.time() - timers["UYKU"] > 1.2: current_alert = "UYKU"
                else:
                    timers["UYKU"] = 0

                # --- ESNEME ---
                if (face.landmark[14].y - face.landmark[13].y) > 0.07:
                    if timers["ESNEME"] == 0: timers["ESNEME"] = time.time()
                    if time.time() - timers["ESNEME"] > 2.0: current_alert = "ESNEME"
                else:
                    timers["ESNEME"] = 0

            # Yüz hatlarını çiz
            mp_drawing.draw_landmarks(image, face, mp_face_mesh.FACEMESH_CONTOURS,
                                      landmark_drawing_spec=None,
                                      connection_drawing_spec=mp_drawing.DrawingSpec(color=yuz_hattı_rengi,
                                                                                     thickness=1))

    # ARDUINO GÜNCELLEME
    if current_alert:
        alarm_aktif = True
        if arduino: arduino.write((current_alert + "\n").encode())
        cv2.rectangle(image, (0, 0), (w, 60), (0, 0, 0), -1)  # Siyah şerit
        cv2.putText(image, f"ALERT: {current_alert}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
    else:
        if alarm_aktif:
            if arduino: arduino.write(b"0\n")
            alarm_aktif = False
        cv2.rectangle(image, (0, 0), (w, 60), (0, 0, 0), -1)  # Siyah şerit
        cv2.putText(image, "STATUS: AWAKE", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    cv2.imshow('Azo Ismail Smart Monitoring', image)
    if cv2.waitKey(10) & 0xFF == 27: break

cap.release()
cv2.destroyAllWindows()