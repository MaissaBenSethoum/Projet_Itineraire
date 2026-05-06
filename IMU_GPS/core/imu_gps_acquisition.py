import time
import os

from sensors.IMU import initialize_sensors, read_IMU
from sensors.GNSS import GNSS
from utils import CSVHandler


def get_imu_gps_data(
    XL_addr,
    accel_range,
    accel_freq,
    gyro_range,
    gyro_freq,
    gnss_addr,
    gnss_mode,
    csv_out=None):
    """
    Fait l'acquisition simultanée des données IMU et GNSS.

    Arguments :
    - XL_addr : adresse I2C de l'IMU
    - accel_range : plage de mesure de l'accéléromètre
    - accel_freq : fréquence de l'accéléromètre
    - gyro_range : plage de mesure du gyroscope
    - gyro_freq : fréquence du gyroscope
    - gnss_addr : adresse I2C du module GNSS
    - gnss_mode : mode GNSS utilisé
    - csv_out : chemin du fichier CSV de sortie
    """

    # Intervalle d'acquisition basé sur la fréquence IMU
    interval = 1 / min(accel_freq, gyro_freq)

    # Création CSV
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
            "Timestamp", "UTC", "Latitude","Longitude","Altitude", "Nb Satellites", "GPS Valid",
            "Accel X","Accel Y","Accel Z","Gyro X","Gyro Y","Gyro Z"])

    # Initialisation IMU
    initialize_sensors(XL_addr,accel_range,accel_freq,gyro_range,gyro_freq)

    # Initialisation GNSS
    gnss = GNSS(1, gnss_addr)
    gnss.initialisation(gnss_mode)

    print("Acquisition IMU + GNSS démarrée.")
    print("Ctrl+C pour arrêter.")

    try:
        while True:
            start_time = time.time()
            timestamp = time.time()

            # Lecture IMU
            accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z = read_IMU(
                XL_addr,
                accel_range,
                gyro_range)

            # Lecture GNSS
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

            # Sauvegarde CSV
            if save_csv:
                record.append_row([
                    timestamp,
                    utc,
                    latitude,
                    longitude,
                    altitude,
                    nb_satellites,
                    gps_valid,
                    accel_x,
                    accel_y,
                    accel_z,
                    gyro_x,
                    gyro_y,
                    gyro_z
                ])

            # Affichage console
            print("--------------------------------------------------")
            print(f"Timestamp : {timestamp:.3f}")
            print(f"GPS valid : {gps_valid}")
            print(f"Latitude : {latitude}")
            print(f"Longitude : {longitude}")
            print(f"Satellites : {nb_satellites}")
            print(f"Accel : X={accel_x:.3f}, Y={accel_y:.3f}, Z={accel_z:.3f}")
            print(f"Gyro  : X={gyro_x:.3f}, Y={gyro_y:.3f}, Z={gyro_z:.3f}")

            # Respect de la fréquence IMU
            elapsed_time = time.time() - start_time
            time_to_sleep = max(0, interval - elapsed_time)
            time.sleep(time_to_sleep)

    except KeyboardInterrupt:
        print("Arrêt du programme.")