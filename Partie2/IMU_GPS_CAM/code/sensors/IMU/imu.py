import smbus
import time
from .accelerometer import accelerometer_configuration, read_accelerometer
from .gyroscope import gyroscope_configuration, read_gyroscope
from config import CTRL1_XL, CTRL2_G

# Initialisation du bus I2C
bus = smbus.SMBus(1)

def initialize_sensors(XL_addr, 
                       accel_range, accel_freq, 
                       gyro_range, gyro_freq):
    """
    Initialise les capteurs en écrivant dans leurs registres de configuration en fonction des paramètres de configuration précisés.

    Arguments:
    - XL_addr: l'adresse I2C du LSM6DSO 
    - accel_range: la range de l'accéléromètre
    - accel_freq: la fréquence d'acquisition de l'accélomètre
    - gyro_range: la range du gyroscope
    - gyro_freq: la fréquence d'acquisition du gyroscope
    """
    bus.write_byte_data(XL_addr, CTRL1_XL, accelerometer_configuration(accel_range,accel_freq))
    bus.write_byte_data(XL_addr, CTRL2_G, gyroscope_configuration(gyro_range,gyro_freq))
    time.sleep(0.1)


def read_raw_data(device_addr, start_register):
    """
    Lit 6 octets depuis le capteur à l'adresse spécifiée et retourne les valeurs signées.

    Arguments:
    - device_addr: l'adresse I2C du composant
    - start_register: l'addresse du premier registre à lire 

    Résultat: les données acquises de l'accéléromètre ou gyroscope sur ces 3 axes (en valeur entières brutes signées)
    """
    data = bus.read_i2c_block_data(device_addr, start_register, 6)
    x = data[0] | (data[1] << 8)
    y = data[2] | (data[3] << 8)
    z = data[4] | (data[5] << 8)

    # Convertir en valeurs signées 16 bits
    x = x - 65536 if x > 32767 else x
    y = y - 65536 if y > 32767 else y
    z = z - 65536 if z > 32767 else z
    return x, y, z


def read_IMU(XL_addr, accel_range, gyro_range):
    """
    Lit les données d'acquisition de l'IMU (accéléromètre et gyroscope)

    Arguments:
    - XL_addr: l'adresse I2C du LSM6DSO 
    - accel_range: la range de l'accéléromètre
    - gyro_range: la range du gyroscope

    Résultat: Les données acquises par l'accéléromètre (accel_x,accel_y,accel_z), le gyroscope (gyro_x,gyro_y,gyro_z)
    """
    accel_x,accel_y,accel_z = read_accelerometer(XL_addr, accel_range)
    gyro_x,gyro_y,gyro_z = read_gyroscope(XL_addr, gyro_range)
    return accel_x,accel_y,accel_z,gyro_x,gyro_y,gyro_z