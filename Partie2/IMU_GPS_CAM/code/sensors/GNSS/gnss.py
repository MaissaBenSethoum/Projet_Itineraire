import time
import smbus
import time
from config import I2C_ID, I2C_SLEEP_MODE, I2C_GNSS_MODE, I2C_START_GET, I2C_DATA_LEN_H, I2C_ALL_DATA

class struct_utc_time:
    """
    Structure pour l'enregistrement temporel (date et heure).
    """
    def __init__(self):
        """
        Initialise une structure date/heure.
        """
        self.year=2000
        self.month=1
        self.date=1
        self.hour=0
        self.minute=0
        self.second=0
    
    def update_utc_time(self,rslt):
        """
        Met à jour la date et l'heure.

        Arguments:
        - rslt: Une liste contenant les informations de date et heure (lue directement via smbus).
        """
        if rslt != -1:
            self.year = rslt[0]*256 + rslt[1]
            self.month = rslt[2]
            self.date = rslt[3]        
            self.hour = rslt[4]
            self.minute = rslt[5]
            self.second = rslt[6]
            
    def __str__(self):
        """
        Renvoie une chaîne de caractères formatée de la date et l'heure.

        Sortie: Une chaîne de caractère formatée.
        """
        return f"{self.year:04}/{self.month:02}/{self.date:02} - {self.hour:02}:{self.minute:02}:{self.second:02}" 

class struct_GNSS_coordinate:
    """
    Structure pour l'enregistrement positionel (coordonnée latitude ou longitude).
    """
    def __init__(self):
        """
        Initialise une stucture coordonnée.
        """
        self.degres = 0
        self.minutes = 0
        self.fractions_minutes = 0
        self.direction = "S" # N ou S pour la latitude, E ou W pour la longitude
        self.coordinates_DD = 0.00 # Coordonnées au format degré décimaux
        self.coordinates_DMM = "0.00" # Coordonnées au format degré / minute décimales
        self.coordinates_DMS = "0.00" # Coordonnées au format degré décimaux / minutes / secondes
    
    def update_coordinate(self,rslt):
        """
        Met à jour la coordonnée.
        """
        if rslt != -1:
            self.degres = rslt[0]
            self.minutes = rslt[1]
            self.fractions_minutes = rslt[2]*65536 + rslt[3]*256 + rslt[4]
            self.direction = chr(rslt[5])

            minutes_totales = self.minutes + (self.fractions_minutes / 100000.0)
            
            # A COMPLETER
            self.coordinates_DD = (self.degres + (minutes_totales / 60.0)) * (-1 if self.direction in ['S', 'W'] else 1) 
            self.coordinates_DMS = f"{int(self.coordinates_DD)}° {(self.coordinates_DD - int(self.coordinates_DD))*60}  {(self.fractions_minutes)*60 } {self.direction}"
            self.coordinates_DMM = f"{int(self.coordinates_DD)}° {(self.coordinates_DD - int(self.coordinates_DD))*60} {self.direction}"
    
class GNSS:
    """
    Classe pour la gestion des acqusitions du GNSS.
    """
    def __init__(self, bus, addr):
        """
        Intialise le module de gestion du GNSS.

        Arguments:
        - bus: Le bus de communication du module GNSS.
        - addr: L'adresse I2C de communication du module GNSS.
        """
        self.i2cbus = smbus.SMBus(bus)
        self.__addr = addr
        self.timestamp = 0
        self.utc = struct_utc_time()
        self.latitude = struct_GNSS_coordinate()
        self.longitude = struct_GNSS_coordinate()
        self.altitude = 0
        self.number_satellites = 0
        self.COG = 0
        self.SOG = 0
        self.reception_ok=False
        
    def begin(self):
        """
        Initialise la connexion au capteur GNSS.     
        """
        rslt = self._read_reg(I2C_ID, 1)
        time.sleep(0.1)
        if rslt == -1:
            return False
        if rslt[0] != self.__addr:
            return False
        return True

    def enable_power(self):
        """
        Active la récupération des données GNSS.
        """
        self._write_reg(I2C_SLEEP_MODE, [0])
        time.sleep(0.1)

    def disable_power(self):
        """
        Désactive la récupération des données GNSS. 
        """
        self._write_reg(I2C_SLEEP_MODE, [1])
        time.sleep(0.1)
    
    def get_mode(self):
        """
        Retourne le mode GNSS utilisé.
        
        Sortie: le mode GNSS utilisé.    
        """
        rslt = self._read_reg(I2C_GNSS_MODE, 1)
        return rslt[0]

    def set_mode(self, mode):
        """
        Actualise le mode GNSS du capteur.
        
        Arguments:
        - mode: le mode GNSS.
        """
        self._write_reg(I2C_GNSS_MODE, [mode])
        time.sleep(0.1) 
        
    def initialisation(self,mode):
        """
        Initialise le module GNSS avant acquisition.
        
        Arguments:
        - mode: le mode GNSS.
        """
        while (self.begin() == False):
            print("Echec de l'initialisation")
            time.sleep(1)
        self.enable_power()
        self.set_mode(mode)

    def update_timestamp(self):
        self.timestamp=time.time()

    def update(self):
        """
        Actualise les données GNSS avec une seule requête I2C.
        """
        rslt = self._read_reg(0, 29)

        if rslt == -1:
            self.reception_ok = False
            return

        # Nombre de satellites
        self.number_satellites = rslt[19]

        if self.number_satellites == 0:
            self.reception_ok = False
            return

        self.reception_ok = True

        # Mise à jour UTC
        self.utc.year = rslt[0] * 256 + rslt[1]
        self.utc.month = rslt[2]
        self.utc.date = rslt[3]
        self.utc.hour = rslt[4]
        self.utc.minute = rslt[5]
        self.utc.second = rslt[6]

        # Mise à jour timestamp
        self.update_timestamp()

        # Mise à jour Latitude
        lat_rslt = rslt[7:12] + [rslt[18]]    # Ajout de la direction
        self.latitude.update_coordinate(lat_rslt)

        # Mise à jour Longitude
        lon_rslt = rslt[13:18] + [rslt[12]]    # Ajout de la direction
        self.longitude.update_coordinate(lon_rslt)

        # Mise à jour Altitude
        self.altitude = rslt[20] * 256 + rslt[21] + rslt[22] / 100.0

        # Mise à jour COG
        self.COG = rslt[26] * 256 + rslt[27] + rslt[28] / 100.0

        # Mise à jour SOG
        self.SOG = rslt[23] * 256 + rslt[24] + rslt[25] / 100.0

    def wait_for_next_scan(self, timeout=5.0):
        """
        Attend le passage à la seconde suivante en se basant sur l'horloge UTC du GPS.

        Arguments:
                timeout: Le temps maximum d'attente en secondes

        """
        start_time = time.time()
        last_second = getattr(self.utc, "second", None)

        while True:
            self.update()

            # UTC valide et changement de seconde
            if self.utc is not None and self.utc.second != last_second:
                return

            # Timeout
            if time.time() - start_time > timeout:
                return

            time.sleep(0.05)

    def get_gnss_len(self):
        """
        Retourne la longueur des données GNSS reçues.
        
        Sortie: la longueur des données GNSS.
        """
        self._write_reg(I2C_START_GET, [0x55])
        time.sleep(0.1)
        rslt = self._read_reg(I2C_DATA_LEN_H, 2)
        if rslt != -1:
            return rslt[0]*256 + rslt[1]
        else:
            return 0

    def get_raw_data(self):
        """
        Retourne les données brutes reçues par le GNSS (les différentes trames NMEA).
        """
        len = self.get_gnss_len()
        time.sleep(0.1)
        all_data = [0]*(len+1)
        len1 = (len) // 32
        len2 = ((len)%32) 
        for num in range (0, len1+1):
            if num == len1:
                rslt = self._read_reg(I2C_ALL_DATA, len2)
                for i in range (0, len2):
                    if rslt[i] == 0:
                        rslt[i] = 0x0A
                all_data[num*32:] = rslt
            else:
                rslt = self._read_reg(I2C_ALL_DATA, 32)
                for i in range (0, 32):
                    if rslt[i] == 0:
                        rslt[i] = 0x0A
                all_data[num*32:] = rslt
        return all_data

    def _write_reg(self, reg, data):
        while 1:
            try:
                self.i2cbus.write_i2c_block_data(self.__addr, reg, data)
                return
            except:
                print("Problème d'écriture")
                time.sleep(1)

    def _read_reg(self, reg, len):
        try:
            rslt = self.i2cbus.read_i2c_block_data(self.__addr, reg, len)
        except:
            rslt = -1
        return rslt