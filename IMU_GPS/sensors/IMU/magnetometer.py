import smbus
import time
from config import OUT_X_L, CONFIG_MAG_FREQ, CONFIG_MAG_RANGE, CONFIG_MAG_SENSITIVITY

def magnetometer_configuration(magneto_range, magneto_freq):
    """
    Configure les paramètres du LIS3MDL pour le magnetometer.

    Arguments: 
    - magneto_range: la range du magnetometer
    - magneto_freq: la fréquence d'acquisition du magnetometer

    Résultat : les octets à écrire dans les registres CTRL_REG1 et CTRL_REG2 pour configurer le magnetometer
    """
    # Configuration du magnetometer
    magneto_range_value = CONFIG_MAG_RANGE[magneto_range]
    magneto_freq_value = CONFIG_MAG_FREQ[magneto_freq]
    ctrl_reg1 = (magneto_freq_value << 1)
    ctrl_reg2 = (magneto_range_value << 5)
    return ctrl_reg1, ctrl_reg2

def read_magnetometer(device_addr, magneto_range):
    """
    Lit les données du magnetometer et les convertit.

    Arguments:
    - device_addr: l'adresse I2C du composant
    - magneto_range: la range du magnetometer

    Résultat: les données acquises par le magnetometer en unité physique sur les 3 axes
    """
    from sensors.IMU import read_raw_data
    x, y, z = read_raw_data(device_addr, OUT_X_L)
    
    sensitivity = sensitivity = CONFIG_MAG_SENSITIVITY[magneto_range]
    return x / sensitivity, y / sensitivity, z / sensitivity
