"""Script d'acquisition IMU/GNSS lancé depuis la ligne de commande.

Ce script démarre directement l'acquisition avec les paramètres définis dans le
module config. Le mode GNSS et le chemin du CSV de sortie peuvent être modifiés
avec des arguments de ligne de commande.
"""
import argparse
from config import (
    LSM6DSO_ADDR, ACCEL_RANGE, ACCEL_FREQ,
    GYRO_RANGE, GYRO_FREQ,
    GNSS_DEVICE_ADDR, GNSS_MODES, MODE_GNSS,
    PORT_BUTTON, PORT_LED, MAGNETO_RANGE, MAGNETO_FREQ, MAG_ADDR
)
from core.imu_gps_acquisition import get_imu_gps_data
from utils.CSVHandler import CSVHandler

if __name__ == "__main__":

    # Création du parser
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--mode", "-m",
        type=str,
        choices=GNSS_MODES.keys(),
        default=MODE_GNSS,
        help="Mode GNSS à utiliser"
    )

    parser.add_argument(
        "--save-path", "-s",
        type=str,
        default="data/acquisition_imu_gps.csv",
        help="Chemin du fichier CSV de sauvegarde"
    )

    args = parser.parse_args()

    # Lancement acquisition
    get_imu_gps_data(
        XL_addr=LSM6DSO_ADDR,
        MAG_addr=MAG_ADDR,
        accel_range=ACCEL_RANGE,
        accel_freq=ACCEL_FREQ,
        gyro_range=GYRO_RANGE,
        gyro_freq=GYRO_FREQ,
        magneto_range=MAGNETO_RANGE,
        magneto_freq=MAGNETO_FREQ,
        gnss_addr=GNSS_DEVICE_ADDR,
        gnss_mode=GNSS_MODES[args.mode],
        csv_out=args.save_path)