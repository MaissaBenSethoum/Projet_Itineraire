import time
from sensors.IMU import read_IMU, initialize_sensors
from evdev import UInput, ecodes as e

ui = UInput()

def send_key(key, press_or_release=0):
    """
    Envoie au système une instruction sur une touche clavier (pressée ou relachée)
    
    Arguments: 
    - key: La touche à contrôler :
            - e.KEY_UP : Touche haut
            - e.KEY_DOWN : Touche bas
            - e.KEY_LEFT : Touche gauche
            - e.KEY_RIGHT : Touche droite
    - press_or_release: L'état de la touche à contrôler:
            - press_or_release=0 => release
            - press_or_release=1 => press
    """
    ui.write(e.EV_KEY, key, press_or_release)
    ui.syn()


def game_controller(XL_addr, accel_range, accel_freq, gyro_range, gyro_freq):
    """
    Mappe les touches directionnelles du clavier en fonction de l'orientation de l'IMU

    Arguments:
    - XL_addr: l'adresse I2C du LSM6DSO 
    - accel_range: la plage de mesure de l'accéléromètre (g).
    - accel_freq: la fréquence d'échantillonnage de l'accéléromètre (Hz).
    - gyro_range: la plage de mesure du gyroscope (dps).
    - gyro_freq: la fréquence d'échantillonnage du gyroscope (Hz).
    """
    
    # Initialisation des capteurs
    initialize_sensors(XL_addr, accel_range, accel_freq, gyro_range, gyro_freq)

    try:
        while True:

            # Lecture des données
            accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z = read_IMU(XL_addr, accel_range, gyro_range)

            # A COMPLETER
            # TOUCHE HAUT
            if ...:  # Incliné vers l'avant
                print("UP")
                ...
            else:
                ...
                                
            # TOUCHE BAS
            if ...:  # Incliné vers l'arrière
                print("DOWN")
                ...
            else:
                ...
                
            # TOUCHE GAUCHE
            if ...:  # Incliné à gauche
                print("LEFT")
                ...
            else:
                ...
                
            # TOUCHE DROITE
            if ...:  # Incliné à droite
                print("RIGHT")
                ...
            else:
                ...
            
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("Arrêt du programme.")

