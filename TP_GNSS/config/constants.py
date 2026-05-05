# A COMPLETER
# Adresses I2C et USB des composants
GNSS_DEVICE_ADDR = 0x20           # Adresse I2C du module GNSS
LCD_DEVICE_ADDR = 0x27            # Adresse I2C de l'écran LCD

# Constantes des registres du GNSS
I2C_START_GET = 29
I2C_ID = 30
I2C_DATA_LEN_H = 31
I2C_DATA_LEN_L = 32
I2C_ALL_DATA = 33
I2C_GNSS_MODE = 34
I2C_SLEEP_MODE = 35

# Mode de sélection des satellites GNSS
GPS = 1
BEIDOU = 2
GPS_BEIDOU = 3
GLONASS = 4
GPS_GLONASS = 5
BEIDOU_GLONASS = 6
GPS_BEIDOU_GLONASS = 7

GNSS_MODES = {'gps':GPS,
              'beidou':BEIDOU,
              'glonass':GLONASS,
              'gps_beidou':GPS_BEIDOU,
              'gps_glonass':GPS_GLONASS,
              'beidou_glonass':BEIDOU_GLONASS,
              'gps_beidou_glonass':GPS_BEIDOU_GLONASS
            }