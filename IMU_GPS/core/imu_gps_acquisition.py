import time
import os

from sensors.IMU import initialize_sensors, read_IMU
from sensors.GNSS import GNSS
from utils import CSVHandler


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
        magneto_freq
    )

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