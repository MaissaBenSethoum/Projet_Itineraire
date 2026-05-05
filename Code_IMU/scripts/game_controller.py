import time
import argparse
from config import LSM6DSO_ADDR, ACCEL_RANGE, ACCEL_FREQ, GYRO_RANGE, GYRO_FREQ
from core.imu_controller import game_controller

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--save-path', '-s',
                        type=str,
                        default=None,
                        help="Chemin où sauvegarder les données.")
    args = parser.parse_args()

    game_controller(LSM6DSO_ADDR, ACCEL_RANGE, ACCEL_FREQ, GYRO_RANGE, GYRO_FREQ)