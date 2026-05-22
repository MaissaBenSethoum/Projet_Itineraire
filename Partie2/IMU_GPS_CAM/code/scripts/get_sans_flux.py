import time
from pathlib import Path
import threading
import cv2
import mediapipe as mp

from sensors.CAMERA import Camera
from utils import Button, LED
from config import (
    PORT_BUTTON, PORT_LED,
    LSM6DSO_ADDR, ACCEL_RANGE, ACCEL_FREQ,
    GYRO_RANGE, GYRO_FREQ, GNSS_DEVICE_ADDR,
    GNSS_MODES, MODE_GNSS, MAGNETO_RANGE, MAGNETO_FREQ, MAG_ADDR
)
from core.imu_gps_acquisition import get_imu_gps_data, get_imu_gps_long_lat

SAVE_DIR = Path("images")

# Initialisation de MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
)

def is_victory_gesture(hand_landmarks):
    """Détecte le geste 'Victory' (index et majeur levés)."""
    index_is_open = hand_landmarks.landmark[8].y < hand_landmarks.landmark[6].y
    middle_is_open = hand_landmarks.landmark[12].y < hand_landmarks.landmark[10].y
    ring_is_closed = hand_landmarks.landmark[16].y > hand_landmarks.landmark[14].y
    pinky_is_closed = hand_landmarks.landmark[20].y > hand_landmarks.landmark[18].y

    return index_is_open and middle_is_open and ring_is_closed and pinky_is_closed


def get_imu_gps_cam_sans_flux(XL_addr,
                                MAG_addr,
                                accel_range,
                                accel_freq,
                                gyro_range,
                                gyro_freq,
                                magneto_range,
                                magneto_freq,
                                gnss_addr,
                                gnss_mode,
                                stop_event=None):
    """
    Fonction cible pour le thread de capture et détection de geste.
    Prend un threading.Event() pour pouvoir être arrêtée proprement par le code principal.
    """
    led = LED(PORT_LED)
    
    print("[Thread Caméra] Initialisation...")
    led.on()

    camera = Camera()
    camera.configure()
    camera.start()
    camera.warmup()

    SAVE_DIR.mkdir(exist_ok=True)
    index = 0
    cooldown_time = 0 

    # --- Lancement de l'acquisition IMU + GPS en tâche de fond ---
    csv_name = f"data/live.csv"
    
    # Condition d'arrêt partagée avec l'IMU
    def imu_stop_condition():
        return stop_event.is_set()

    imu_gps_thread = threading.Thread(
        target=get_imu_gps_data,
        kwargs={
            "XL_addr": LSM6DSO_ADDR,
            "MAG_addr" : MAG_ADDR,
            "accel_range": ACCEL_RANGE,
            "accel_freq": ACCEL_FREQ,
            "gyro_range": GYRO_RANGE,
            "gyro_freq": GYRO_FREQ,
            "gnss_addr": GNSS_DEVICE_ADDR,
            "gnss_mode": GNSS_MODES[MODE_GNSS],
            "magneto_range" : MAGNETO_RANGE,
            "magneto_freq" : MAGNETO_FREQ,
            "csv_out": csv_name,
            "stop_condition": imu_stop_condition
        },
        daemon=True
    )
    imu_gps_thread.start()

    print("[Thread Caméra] Boucle de détection démarrée (sans affichage).")

    try:
        # La boucle tourne tant que le programme principal ne lève pas le flag d'arrêt
        while not stop_event.is_set():
            # 1. Capture continue en arrière-plan
            frame = camera.capture_frame()

            # 2. Détection par MediaPipe
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb_frame)

            gesture_detected = False
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    if is_victory_gesture(hand_landmarks):
                        gesture_detected = True

            # 3. Traitement du déclenchement photo
            if gesture_detected and time.time() > cooldown_time:
                print(f"[Thread Caméra] Geste détecté ! Capture de la photo {index}...")
                
                # Effet flash LED rapide (non bloquant pour le flux)
                led.off() 
                time.sleep(0.05)
                led.on()
                
                # Récupération GPS
                latitude, longitude = get_imu_gps_long_lat(
                    XL_addr=LSM6DSO_ADDR,
                    MAG_addr=MAG_ADDR,
                    accel_range=ACCEL_RANGE,
                    accel_freq=ACCEL_FREQ,
                    gyro_range=GYRO_RANGE,
                    gyro_freq=GYRO_FREQ,
                    magneto_range=MAGNETO_RANGE,
                    magneto_freq=MAGNETO_FREQ,
                    gnss_addr=GNSS_DEVICE_ADDR,
                    gnss_mode=GNSS_MODES[MODE_GNSS]
                )
                
                filename = SAVE_DIR / f"image_{latitude}_{longitude}.jpg"
                camera.save_frame(frame, str(filename))
                print(f"[Thread Caméra] Image sauvegardée : {filename}")

                cooldown_time = time.time() + 3.0  # Cooldown avant la prochaine détection
                index += 1

            time.sleep(0.01)

    except Exception as e:
        print(f"[Thread Caméra] Erreur rencontrée : {e}")

    finally:
        print("\n[Thread Caméra] Nettoyage et fermeture...")
        if imu_gps_thread.is_alive():
            imu_gps_thread.join(timeout=2.0)
            
        led.off()
        camera.stop()
        led.cleanup()
        hands.close()
        print("[Thread Caméra] Capteurs libérés.")
