import sys
import os
import re
import threading
import pandas as pd
from flask import Flask, jsonify, render_template, send_from_directory

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from scripts.get_sans_flux import get_imu_gps_cam_sans_flux
from core.imu_gps_preprocessing import preprocess_imu_gps_df
from config.constants import LSM6DSO_ADDR, GNSS_DEVICE_ADDR, GNSS_MODES,MAG_ADDR
from config.parameters import (
    ACCEL_RANGE, ACCEL_FREQ, GYRO_RANGE, GYRO_FREQ,
    MODE_GNSS, MAGNETO_RANGE, MAGNETO_FREQ
)
from utils.FiltreKalman import EKF, run_kalman_incremental
from utils.correction_erreur_systematique import corriger_biais_imu

CSV_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'live.csv')
IMAGES_DIR = os.path.join(os.path.dirname(__file__), '..', 'images')

CONFIG = (int(ACCEL_RANGE), float(ACCEL_FREQ), int(GYRO_RANGE), float(GYRO_FREQ))

app = Flask(__name__)

all_points = []
last_index = 0
ekf_instance = EKF()
ref_lat = None
ref_lon = None
stop_event = threading.Event()

@app.route("/")
def index():
    return render_template("map.html")


@app.route("/data")
def data():
    """fonction qui qui recupère les données du csv, les traite avec le Kalman et les retourne au client
    Qui les affiches sur la carte qui est dans map.html
    """
    global last_index, all_points, ekf_instance, ref_lat, ref_lon

    current = all_points[-1] if all_points else None
    
    if not os.path.exists(CSV_PATH):
        return jsonify({"points": all_points, "current": current})

    try:
        df = pd.read_csv(CSV_PATH, on_bad_lines='skip')
    except Exception:
        return jsonify({"points": all_points, "current": current})

    nouvelles = df.iloc[last_index:]

    if nouvelles.empty:
        return jsonify({"points": all_points, "current": current})

    try:
        nouvelles = corriger_biais_imu(nouvelles.copy(), CONFIG)
        df_new = preprocess_imu_gps_df(nouvelles)
    except Exception as e:
        print(f"Prétraitement échoué : {e}")
        return jsonify({"points": all_points, "current": current})

    last_index = len(df)

    if df_new.empty:
        return jsonify({"points": all_points, "current": current})

    if ref_lat is None:
        first_valid = df_new[df_new['GPS Valid'] == 1].dropna(subset=['Latitude', 'Longitude'])
        if first_valid.empty:
            return jsonify({"points": all_points, "current": current})
        ref_lat = first_valid['Latitude'].iloc[0]
        ref_lon = first_valid['Longitude'].iloc[0]
        ekf_instance = EKF()  # repart de zéro avec P, v, theta propres

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
    """Retourne la liste des photos avec leurs coordonnées extraites du nom de fichier."""
    photos = []
    if not os.path.exists(IMAGES_DIR):
        return jsonify([])
    
    for filename in os.listdir(IMAGES_DIR):
        if not filename.endswith(".jpg"):
            continue
        match = re.match(r"^image_(-?\d+\.?\d*)_(-?\d+\.?\d*)\.jpg$", filename)
        if match:
            lat, lon = float(match.group(1)), float(match.group(2))
            photos.append({
                "filename": filename,
                "lat": lat,
                "lon": lon
            })
    
    return jsonify(photos)

@app.route("/photo/<filename>")
def serve_photo(filename):
    """Sert une image individuelle."""
    return send_from_directory(IMAGES_DIR, filename)

if __name__ == "__main__":
    acq_thread = threading.Thread(
        target=get_imu_gps_cam_sans_flux,
        kwargs={
            "XL_addr":        LSM6DSO_ADDR,
            "accel_range":    ACCEL_RANGE,
            "accel_freq":     ACCEL_FREQ,
            "gyro_range":     GYRO_RANGE,
            "gyro_freq":      GYRO_FREQ,
            "gnss_addr":      GNSS_DEVICE_ADDR,
            "gnss_mode":      GNSS_MODES[MODE_GNSS],
            "MAG_addr":       MAG_ADDR,
            "magneto_range":  MAGNETO_RANGE,
            "magneto_freq":   MAGNETO_FREQ,
            "stop_event":     stop_event,
        },
        daemon=True,
    )
    acq_thread.start()
    print("Serveur : http://0.0.0.0:5000")

    app.run(host="0.0.0.0", port=5000, debug=False)
