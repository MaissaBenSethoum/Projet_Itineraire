import smbus
import time
from config import OUTX_L_A, CONFIG_XL_FREQ, CONFIG_XL_RANGE, CONFIG_XL_SENSITIVITY

def accelerometer_configuration(accel_range, accel_freq):
    """
    Configure les paramètres du LSM6DSO pour l'accéléromètre.

    Arguments: 
    - accel_range: la range de l'accéléromètre
    - accel_freq: la fréquence d'acquisition de l'accéléromètre

    Résultat : l'octet à écrire dans le registre CTRL1_XL pour configurer l'accéléromètre
    """
    # Configuration de l'accéléromètre
    # A COMPLETER
    freq_code = CONFIG_XL_FREQ[accel_freq]
    
    range_code = CONFIG_XL_RANGE[accel_range]

    config_byte = (freq_code << 4) | (range_code << 2)

    return config_byte

def read_accelerometer(device_addr, accel_range):
    """
    Lit les données de l'accéléromètre et les convertit.

    Arguments: 
    - device_addr: l'adresse I2C du composant
    - accel_range: la range de l'accéléromètre

    Résultat: les données acquises par de l'accéléromètre en unité physique sur les 3 axes
    """
    from sensors.IMU import read_raw_data
    x, y, z = read_raw_data(device_addr, OUTX_L_A)

    # A COMPLETER
    sensitivity = CONFIG_XL_SENSITIVITY[accel_range]
    return x * sensitivity, y * sensitivity, z * sensitivity
