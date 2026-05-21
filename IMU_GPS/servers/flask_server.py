import sys
import os
import threading
import json
import pandas as pd
from flask import Flask, jsonify, render_template, send_from_directory

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core.imu_gps_acquisition import get_imu_gps_data
from core.imu_gps_preprocessing import preprocess_imu_gps_df
from config.constants import LSM6DSO_ADDR, GNSS_DEVICE_ADDR, GNSS_MODES,MAG_ADDR
from config.parameters import (
    ACCEL_RANGE, ACCEL_FREQ, GYRO_RANGE, GYRO_FREQ,
    MODE_GNSS, MAGNETO_RANGE, MAGNETO_FREQ
)
from IMU_GPS.utils.FiltreKalman import EKF, run_kalman,run_kalman_incremental
from IMU_GPS.utils.correction_erreur_systematique import corriger_biais_imu

CSV_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'live.csv')
PHOTOS_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'photos') 
PHOTOS_JSON = os.path.join(os.path.dirname(__file__), '..', 'data', 'photos.json') 
 
CONFIG = (int(ACCEL_RANGE), float(ACCEL_FREQ), int(GYRO_RANGE), float(GYRO_FREQ))

app = Flask(__name__)

all_points = []
last_index = 0
ekf_instance = EKF()
ref_lat = None
ref_lon = None
last_ekf_row = None

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
        df = pd.read_csv(CSV_PATH)
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
        ekf_instance.x[0] = 0.0
        ekf_instance.x[1] = 0.0

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
    """Retourne la liste des photos avec leurs coordonnées."""
    if not os.path.exists(PHOTOS_JSON):
        return jsonify([])
    try:
        with open(PHOTOS_JSON, 'r') as f:
            return jsonify(json.load(f))
    except Exception as e:
        print(f"Erreur lecture photos.json : {e}")
        return jsonify([])

@app.route("/photo/<filename>")
def serve_photo(filename):
    """Sert une image individuelle."""
    return send_from_directory(PHOTOS_DIR, filename)

if __name__ == "__main__":
    acquisition = threading.Thread(
        target=get_imu_gps_data,
        kwargs={
            "XL_addr":        LSM6DSO_ADDR,
            "accel_range":    ACCEL_RANGE,
            "accel_freq":     ACCEL_FREQ,
            "gyro_range":     GYRO_RANGE,
            "gyro_freq":      GYRO_FREQ,
            "gnss_addr":      GNSS_DEVICE_ADDR,
            "gnss_mode":      GNSS_MODES[MODE_GNSS],
            "csv_out":        CSV_PATH,
            "MAG_addr":       MAG_ADDR,
            "magneto_range":  MAGNETO_RANGE,
            "magneto_freq":   MAGNETO_FREQ,
            "stop_condition": None,
        },
        daemon=True
    )
    acquisition.start()
    print(f"Acquisition démarrée → {CSV_PATH}")
    print("Serveur : http://0.0.0.0:5000")

    app.run(host="0.0.0.0", port=5000, debug=False)
