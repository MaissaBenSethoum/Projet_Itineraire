import time
import argparse
from config import LSM6DSO_ADDR, ACCEL_RANGE, ACCEL_FREQ, GYRO_RANGE, GYRO_FREQ
from core.imu_acquisition import get_imu_data

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--save-path', '-s',
                        type=str,
                        default=None,
                        help="Chemin où sauvegarder les données.")
    args = parser.parse_args()

    get_imu_data(LSM6DSO_ADDR, ACCEL_RANGE, ACCEL_FREQ, GYRO_RANGE, GYRO_FREQ, args.save_path)