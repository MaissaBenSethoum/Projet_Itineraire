# Adresses I2C des composants
LSM6DSO_ADDR = 0x6b               
LIS3MDL_ADDR = 0x1e   

MAG_ADDR = LIS3MDL_ADDR

PORT_BUTTON = 21 # Port GPIO du Bouton
PORT_LED = 13 # Port GPIO de la LED

DISPLAY_SIZE = (640,480)

# Constantes des registres de configuration de l'IMU (LSM6DSO)
CTRL1_XL = 0x10                   # Configuration de l'accéléromètre 
CTRL2_G = 0x11                    # Configuration du gyroscope 
OUTX_L_A = 0x28                   # Données accéléromètre  
OUTX_L_G = 0x22                   # Données gyroscope  

CONFIG_XL_FREQ = {0: 0b0000, 1.6: 0b1011,
    12.5: 0b0001, 26: 0b0010, 52: 0b0011, 104: 0b0100, 208: 0b0101, 
    416: 0b0110, 833: 0b0111, 1660: 0b1000, 3330: 0b1001, 6660: 0b1010
}


CONFIG_XL_RANGE = {
    2:  0b00,
    16: 0b01,
    4:  0b10,
    8:  0b11
}

#Il faut diviser par 1000 car c'est en mg dans la datasheet
CONFIG_XL_SENSITIVITY = {2:  0.000061,
    4:  0.000122,
    8:  0.000244,
    16: 0.000488
}

CONFIG_G_FREQ = {0: 0b000,
    12.5: 0b0001, 26: 0b0010, 52: 0b0011, 104: 0b0100, 208: 0b0101,
    416: 0b0110, 833: 0b0111, 1660: 0b1000, 3330: 0b1001, 6660: 0b1010
}


CONFIG_G_RANGE = {
    250:  0b00,
    500:  0b01,
    1000: 0b10,
    2000: 0b11
}

# Ici aussi il faut diviser par 1000
CONFIG_G_SENSITIVITY = {125:  0.004375,
    250:  0.00875,
    500:  0.0175,
    1000: 0.035,
    2000: 0.070
}

GNSS_DEVICE_ADDR = 0x20
LCD_DEVICE_ADDR = 0x27

I2C_START_GET = 29
I2C_ID = 30
I2C_DATA_LEN_H = 31
I2C_DATA_LEN_L = 32
I2C_ALL_DATA = 33
I2C_GNSS_MODE = 34
I2C_SLEEP_MODE = 35

GPS = 1
BEIDOU = 2
GPS_BEIDOU = 3
GLONASS = 4
GPS_GLONASS = 5
BEIDOU_GLONASS = 6
GPS_BEIDOU_GLONASS = 7

GNSS_MODES = {
    'gps': GPS,
    'beidou': BEIDOU,
    'glonass': GLONASS,
    'gps_beidou': GPS_BEIDOU,
    'gps_glonass': GPS_GLONASS,
    'beidou_glonass': BEIDOU_GLONASS,
    'gps_beidou_glonass': GPS_BEIDOU_GLONASS
}

CTRL_REG1 = 0x20  # Registre de configuration du magnetometre (frequence)
CTRL_REG2 = 0x21  # Registre de configuration du magnetometre (plage)
OUT_X_L = 0x28  # Registre de lecture du magnetometre

# Mappages des frequences (Hz) pour le magnetometre
CONFIG_MAG_FREQ = {
    0.625: 0b000000,
    1.25: 0b000010,
    2.5: 0b000100,
    5: 0b000110,
    10: 0b001000,
    20: 0b001010,
    40: 0b001100,
    80: 0b001110,
    155: 0b110001,
    300: 0b100001,
    560: 0b010001,
    1000: 0b000001,
}

# Mappages des plages (full-scale range) pour le magnetometre
CONFIG_MAG_RANGE = {
    4: 0,  # +/-4 gauss
    8: 1,  # +/-8 gauss
    12: 2,  # +/-12 gauss
    16: 3,  # +/-16 gauss
}

# Sensibilites du magnetometre pour convertir les donnees brutes
CONFIG_MAG_SENSITIVITY = {
    4: 6842,  # LSB/gauss
    8: 3421,  # LSB/gauss
    12: 2281,  # LSB/gauss
    16: 1711,  # LSB/gauss
}
