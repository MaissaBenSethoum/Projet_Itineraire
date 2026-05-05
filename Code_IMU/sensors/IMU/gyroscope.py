import smbus
import time
from config import OUTX_L_G, CONFIG_G_FREQ, CONFIG_G_RANGE, CONFIG_G_SENSITIVITY

def gyroscope_configuration(gyro_range, gyro_freq):
    """
    Configure les paramètres du LSM6DSO pour le gyroscope.

    Arguments: 
    - gyro_range: la range du gyroscope
    - gyro_freq: la fréquence d'acquisition du gyroscope

    Résultat : l'octet à écrire dans le registre CTRL2_G pour configurer le gyroscope
    """
    # Configuration du gyroscope
    # A COMPLETER
    odr_bits = CONFIG_G_FREQ[gyro_freq]
    fs_bits = CONFIG_G_RANGE[gyro_range]
    
    config_byte = (odr_bits << 4) | (fs_bits << 2)

    return config_byte

def read_gyroscope(device_addr, gyro_range):
    """
    Lit les données du gyroscope et les convertit.

    Arguments:
    - device_addr: l'adresse I2C du composant
    - gyro_range: la range du gyroscope

    Résultat: les données acquises par le gyroscope en unité physique sur les 3 axes
    """
    from sensors.IMU import read_raw_data
    x, y, z = read_raw_data(device_addr, OUTX_L_G)
    
    # A COMPLETER
    sensitivity = CONFIG_G_SENSITIVITY[gyro_range]
    return x * sensitivity, y * sensitivity, z * sensitivity
