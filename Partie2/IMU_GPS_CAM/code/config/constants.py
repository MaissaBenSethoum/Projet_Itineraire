# Adresses I2C des composants
LSM6DSO_ADDR = 0x6b               
LIS3MDL_ADDR = 0x1e   

PORT_BUTTON = 21 # Port GPIO du Bouton
PORT_LED = 13 # Port GPIO de la LED

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
