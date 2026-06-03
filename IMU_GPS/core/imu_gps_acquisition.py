"""Acquisition synchronisée des données IMU, magnétomètre et GNSS.

Ce module initialise les capteurs, lit périodiquement les mesures et peut les
enregistrer dans un fichier CSV. Il est utilisé par les scripts d'acquisition
manuelle ou par bouton.
"""

import time
import os

from sensors.IMU import initialize_sensors, read_IMU
from sensors.GNSS import GNSS
from utils.CSVHandler import CSVHandler


def get_imu_gps_data(
    XL_addr,
    MAG_addr,
    accel_range,
    accel_freq,
    gyro_range,
    gyro_freq,
    magneto_range,
    magneto_freq,
    gnss_addr,
    gnss_mode,
    csv_out=None,
    stop_condition=None):
    """Lance une acquisition continue des données IMU, magnétomètre et GNSS.

    Parameters
    ----------
    XL_addr : int
        Adresse I2C du capteur LSM6DSO utilisé pour l'accéléromètre et le gyroscope.
    MAG_addr : int
        Adresse I2C du magnétomètre LIS3MDL.
    accel_range : int
        Plage de mesure de l'accéléromètre, en g.
    accel_freq : float
        Fréquence d'échantillonnage de l'accéléromètre, en Hz.
    gyro_range : int
        Plage de mesure du gyroscope, en degrés par seconde.
    gyro_freq : float
        Fréquence d'échantillonnage du gyroscope, en Hz.
    magneto_range : int
        Plage de mesure du magnétomètre, en gauss.
    magneto_freq : float
        Fréquence d'échantillonnage du magnétomètre, en Hz.
    gnss_addr : int
        Adresse I2C du module GNSS.
    gnss_mode : int
        Mode de fonctionnement du module GNSS.
    csv_out : str, optional
        Chemin du fichier CSV de sortie. Si None, les données ne sont pas enregistrées.
    stop_condition : callable, optional
        Fonction sans argument qui retourne True quand l'acquisition doit s'arrêter.

    Notes
    -----
    L'acquisition est cadencée avec la fréquence minimale des trois capteurs IMU,
    afin d'éviter de lire plus vite que le capteur le plus lent.
    """

    interval = 1 / min(accel_freq, gyro_freq, magneto_freq)

    save_csv = False
    if csv_out is not None:
        save_csv = True

        if not csv_out.endswith(".csv"):
            csv_out += ".csv"

        directory = os.path.dirname(csv_out)
        if directory != "":
            os.makedirs(directory, exist_ok=True)

        record = CSVHandler(csv_out)
        record.create_csv_with_header([
            "Timestamp", "UTC",
            "Latitude", "Longitude", "Altitude",
            "Nb Satellites", "GPS Valid",
            "Fix Quality", "Fix Type",
            "HDOP", "VDOP", "PDOP",
            "SOG_ms", "COG",
            "Accel X", "Accel Y", "Accel Z",
            "Gyro X", "Gyro Y", "Gyro Z",
            "Magneto X", "Magneto Y", "Magneto Z"
        ])

    # Initialisation IMU + magnétomètre
    initialize_sensors(
        XL_addr,
        MAG_addr,
        accel_range,
        accel_freq,
        gyro_range,
        gyro_freq,
        magneto_range,
        magneto_freq)

    # Initialisation GNSS
    gnss = GNSS(1, gnss_addr)
    gnss.initialisation(gnss_mode)

    print("Acquisition IMU + GNSS démarrée.")
    print("Bouton ou Ctrl+C pour arrêter.")

    try:
        while stop_condition is None or not stop_condition():
            start_time = time.time()
            timestamp = time.time()

            accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z, magneto_x, magneto_y, magneto_z = read_IMU(
                XL_addr,
                MAG_addr,
                accel_range,
                gyro_range,
                magneto_range
            )

            gnss.update()

            if gnss.reception_ok:
                gps_valid = 1
                utc = str(gnss.utc)
                latitude = gnss.latitude.coordinates_DD
                longitude = gnss.longitude.coordinates_DD
                altitude = gnss.altitude
                nb_satellites = gnss.number_satellites
            else:
                gps_valid = 0
                utc = ""
                latitude = ""
                longitude = ""
                altitude = ""
                nb_satellites = gnss.number_satellites

            if save_csv:
                record.append_row([
                    timestamp,
                    utc,
                    latitude,
                    longitude,
                    altitude,
                    nb_satellites,
                    gps_valid,
                    gnss.fix_quality,
                    gnss.fix_type,
                    gnss.HDOP,
                    gnss.VDOP,
                    gnss.PDOP,
                    gnss.SOG_ms,
                    gnss.COG,
                    accel_x,
                    accel_y,
                    accel_z,
                    gyro_x,
                    gyro_y,
                    gyro_z,
                    magneto_x,
                    magneto_y,
                    magneto_z
                ])

            elapsed_time = time.time() - start_time
            time_to_sleep = max(0, interval - elapsed_time)
            time.sleep(time_to_sleep)

    except KeyboardInterrupt:
        print("Arrêt du programme.")