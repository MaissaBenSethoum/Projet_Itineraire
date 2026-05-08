import time
from config import (LSM6DSO_ADDR,ACCEL_RANGE,ACCEL_FREQ,GYRO_RANGE,GYRO_FREQ,GNSS_DEVICE_ADDR,GNSS_MODES,MODE_GNSS,PORT_BUTTON,PORT_LED)
from core.imu_gps_acquisition import get_imu_gps_data
from utils import Button, LED

if __name__ == "__main__":

    button = Button(PORT_BUTTON)
    led = LED(PORT_LED)
    acquisition_stoppee = False

    def demander_arret():
        nonlocal_acquisition_stoppee[0] = True

    nonlocal_acquisition_stoppee = [False]

    def stop_condition():
        return nonlocal_acquisition_stoppee[0]

    button.on_press(demander_arret)

    try:
        print("Appuie sur le bouton pour démarrer l'acquisition.")
        led.off()

        button.wait_for_press()
        button.wait_for_release()

        print("Acquisition démarrée.")
        led.on()

        csv_name = (
            f"data/acq_"f"{ACCEL_RANGE}_{ACCEL_FREQ}_{GYRO_RANGE}_{GYRO_FREQ}.csv")

        get_imu_gps_data(
            XL_addr=LSM6DSO_ADDR,
            accel_range=ACCEL_RANGE,
            accel_freq=ACCEL_FREQ,
            gyro_range=GYRO_RANGE,
            gyro_freq=GYRO_FREQ,
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