import sys
import os
import threading
import re
import time
from pathlib import Path
import cv2
import mediapipe as mp
import pandas as pd
from flask import Flask, jsonify, render_template, send_from_directory

# Ajustement des chemins système
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Imports de la partie Caméra et Utilitaires
from sensors.CAMERA import Camera
from utils import LED
from core.display import show_frame

# Imports de la partie IMU / GNSS / Traitement
from core.imu_gps_acquisition import get_imu_gps_data, get_imu_gps_long_lat
from core.imu_gps_preprocessing import preprocess_imu_gps_df
from config.constants import LSM6DSO_ADDR, GNSS_DEVICE_ADDR, GNSS_MODES, MAG_ADDR
from config.parameters import (
    ACCEL_RANGE, ACCEL_FREQ, GYRO_RANGE, GYRO_FREQ,
    MODE_GNSS, MAGNETO_RANGE, MAGNETO_FREQ, PORT_LED, DISPLAY_SIZE
)
from IMU_GPS.utils.FiltreKalman import EKF, run_kalman_incremental
from IMU_GPS.utils.correction_erreur_systematique import corriger_biais_imu

# Configuration des chemins
CSV_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'live.csv')
IMAGES_DIR = os.path.join(os.path.dirname(__file__), '..', 'images')
Path(IMAGES_DIR).mkdir(parents=True, exist_ok=True)
Path(os.path.dirname(CSV_PATH)).mkdir(parents=True, exist_ok=True)

CONFIG = (int(ACCEL_RANGE), float(ACCEL_FREQ), int(GYRO_RANGE), float(GYRO_FREQ))

# Variables globales Flask / Suivi
app = Flask(__name__)
all_points = []
last_index = 0
ekf_instance = EKF()
ref_lat = None
ref_lon = None

# Variable de contrôle globale
system_running = True

# Initialisation de MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
)
mp_draw = mp.solutions.drawing_utils


def is_victory_gesture(hand_landmarks):
    """Détecte le geste 'Victory' (index et majeur levés)."""
    index_is_open = hand_landmarks.landmark[8].y < hand_landmarks.landmark[6].y
    middle_is_open = hand_landmarks.landmark[12].y < hand_landmarks.landmark[10].y
    ring_is_closed = hand_landmarks.landmark[16].y > hand_landmarks.landmark[14].y
    pinky_is_closed = hand_landmarks.landmark[20].y > hand_landmarks.landmark[18].y

    if index_is_open and middle_is_open and ring_is_closed and pinky_is_closed:
        return True
    return False


# --- ROUTES FLASK ---

@app.route("/")
def index():
    return render_template("map.html")


@app.route("/data")
def data():
    global last_index, all_points, ekf_instance, ref_lat, ref_lon

    current = all_points[-1] if all_points else None
    
    if not os.path.exists(CSV_PATH):
        return jsonify({"points": all_points, "current": current})

    try:
        df = pd.read_csv(CSV_PATH, on_bad_lines='skip')
    except Exception:
        return jsonify({"points": all_points, "current": current})

    nouvelles = df.iloc[last_index:]
    last_index = len(df)

    if nouvelles.empty:
        return jsonify({"points": all_points, "current": current})

    nouvelles = corriger_biais_imu(nouvelles.copy(), CONFIG)
    df_new = preprocess_imu_gps_df(nouvelles)

    if df_new.empty:
        return jsonify({"points": all_points, "current": current})

    if ref_lat is None:
        first_valid = df_new[df_new['GPS Valid'] == 1].dropna(subset=['Latitude', 'Longitude'])
        if first_valid.empty:
            return jsonify({"points": all_points, "current": current})
        ref_lat = first_valid['Latitude'].iloc[0]
        ref_lon = first_valid['Longitude'].iloc[0]
        ekf_instance = EKF()

    try:
        df_filtered = run_kalman_incremental(df_new, ekf_instance, ref_lat, ref_lon)
    except Exception as e:
        print(f"Kalman n'a pas marché : {e}")
        return jsonify({"points": all_points, "current": current})

    for _, row in df_filtered.iterrows():
        pt = [row["Latitude"], row["Longitude"]]
        all_points.append(pt)

    current = all_points[-1] if all_points else None
    return jsonify({"points": all_points, "current": current})


@app.route("/photos")
def photos():
    photos_list = []
    if not os.path.exists(IMAGES_DIR):
        return jsonify([])
    
    for filename in os.listdir(IMAGES_DIR):
        if not filename.endswith(".png"):
            continue
        match = re.match(r"^(-?\d+\.?\d*)_(-?\d+\.?\d*)\.png$", filename)
        if match:
            lat, lon = float(match.group(1)), float(match.group(2))
            photos_list.append({
                "filename": filename,
                "lat": lat,
                "lon": lon
            })
    return jsonify(photos_list)


@app.route("/photo/<filename>")
def serve_photo(filename):
    return send_from_directory(IMAGES_DIR, filename)


def run_flask():
    """Fonction pour lancer Flask en arrière-plan."""
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)


# --- BOUCLE PRINCIPALE (SUR LE THREAD PRINCIPAL) ---

if __name__ == "__main__":
    def stop_condition():
        return not system_running

    # 1. Démarrage du thread d'acquisition IMU + GPS
    acquisition_thread = threading.Thread(
        target=get_imu_gps_data,
        kwargs={
            "XL_addr": LSM6DSO_ADDR,
            "accel_range": ACCEL_RANGE,
            "accel_freq": ACCEL_FREQ,
            "gyro_range": GYRO_RANGE,
            "gyro_freq": GYRO_FREQ,
            "gnss_addr": GNSS_DEVICE_ADDR,
            "gnss_mode": GNSS_MODES[MODE_GNSS],
            "csv_out": CSV_PATH,
            "MAG_addr": MAG_ADDR,
            "magneto_range": MAGNETO_RANGE,
            "magneto_freq": MAGNETO_FREQ,
            "stop_condition": stop_condition,
        },
        daemon=True
    )
    acquisition_thread.start()
    print(f"Acquisition IMU/GPS démarrée → {CSV_PATH}")

    # 2. Démarrage du serveur Flask en tâche de fond
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print("Serveur Flask démarré en arrière-plan : http://localhost:5000")

    # 3. Gestion de la Caméra sur le Thread Principal (évite les fenêtres multiples)
    led = LED(PORT_LED)
    led.on()

    print("Initialisation de la caméra...")
    camera = Camera()
    camera.configure()
    camera.start()
    camera.warmup()

    photo_index = 0
    cooldown_time = 0
    window_name = "Flux Continu Caméra"

    print("Système prêt. Faites le signe 'Victory' (V) ou appuyez sur 'q' pour quitter.")

    try:
        while system_running:
            frame = camera.capture_frame()
            if frame is None:
                time.sleep(0.01)
                continue

            display_frame = frame.copy()

            # Détection MediaPipe
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb_frame)

            gesture_detected = False
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    mp_draw.draw_landmarks(display_frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                    if is_victory_gesture(hand_landmarks):
                        gesture_detected = True

            # Affichage de l'unique fenêtre de flux
            infos = [
                f"Photo index: {photo_index}",
                "Geste attendu: Victory (V)"
            ]
            
            if show_frame(
                display_frame,
                window_name=window_name,
                exit_key="q",
                extra_lines=infos,
                size=DISPLAY_SIZE
            ):
                system_running = False
                break

            # Déclenchement de la photo
            if gesture_detected and time.time() > cooldown_time:
                print(f"Geste détecté ! Capture de la photo {photo_index}...")
                
                led.off()
                time.sleep(0.1)
                led.on()

                # Coordonnées
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

                filename = os.path.join(IMAGES_DIR, f"{latitude}_{longitude}.png")
                camera.save_frame(frame, filename)

                # Effet gel d'image corrigé (SANS recréer de fenêtre)
                freeze_until = time.time() + 3.0
                while time.time() < freeze_until and system_running:
                    show_frame(
                        frame,
                        window_name=window_name,
                        extra_lines=[f"Photo {photo_index} enregistree !", "Apercu..."],
                        size=DISPLAY_SIZE
                    )
                    # Forcer OpenCV à traiter les événements sur la fenêtre existante
                    cv2.waitKey(10)
                    time.sleep(0.05)

                cooldown_time = time.time() + 5.0
                photo_index += 1

            # Un waitKey minimal pour laisser OpenCV respirer et ne pas dupliquer la fenêtre
            if cv2.waitKey(1) & 0xFF == ord('q'):
                system_running = False
                break

    except KeyboardInterrupt:
        print("\nArrêt demandé.")
    finally:
        print("Nettoyage global...")
        system_running = False
        led.off()
        camera.stop()
        led.cleanup()
        hands.close()
        cv2.destroyAllWindows()
        print("Système éteint.")