"""Script d'acquisition IMU/GNSS contrôlée par un bouton physique.

Fonctionnement :
1. le programme attend un premier appui sur le bouton ;
2. la LED s'allume et l'acquisition commence ;
3. un nouvel appui demande l'arrêt de l'acquisition ;
4. les ressources GPIO sont libérées dans tous les cas.
"""

import time
from config import (
    LSM6DSO_ADDR, ACCEL_RANGE, ACCEL_FREQ,
    GYRO_RANGE, GYRO_FREQ,
    GNSS_DEVICE_ADDR, GNSS_MODES, MODE_GNSS,
    PORT_BUTTON, PORT_LED, MAGNETO_RANGE, MAGNETO_FREQ, MAG_ADDR
)
from core.imu_gps_acquisition import get_imu_gps_data
from utils.Button import Button
from utils.LED import LED


if __name__ == "__main__":

    button = Button(PORT_BUTTON)
    led = LED(PORT_LED)

    acquisition_stoppee = [False]

    def demander_arret():
        acquisition_stoppee[0] = True

    def stop_condition():
        return acquisition_stoppee[0]

    try:
        print("Appuie sur le bouton pour démarrer l'acquisition.")
        led.off()

        button.wait_for_press()
        button.wait_for_release()

        time.sleep(0.5)

        print("Acquisition démarrée.")
        led.on()

        button.on_press(demander_arret)

        csv_name = (
            f"../data/acq_v{ACCEL_RANGE}_{ACCEL_FREQ}_{GYRO_RANGE}_{GYRO_FREQ}.csv"
        )

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
            gnss_mode=GNSS_MODES[MODE_GNSS],
            csv_out=csv_name,
            stop_condition=stop_condition)
        print("Acquisition arrêtée.")
        led.off()

    finally:
        led.off()
        button.cleanup()
        led.cleanup()