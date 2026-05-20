import time
import smbus
from config import I2C_ID, I2C_SLEEP_MODE, I2C_GNSS_MODE, I2C_START_GET, I2C_DATA_LEN_H, I2C_ALL_DATA
from .gnss_driver import GNSSDriver


class struct_utc_time:
    """
    Structure pour l'enregistrement temporel (date et heure).
    """
    def __init__(self):
        """
        Initialise une structure date/heure.
        """
        self.year = 2000
        self.month = 1
        self.date = 1
        self.hour = 0
        self.minute = 0
        self.second = 0
        self.millisecond = 0

    def update_utc_time(self, rslt):
        """
        Met à jour la date et l'heure.

        Arguments:
        - rslt: Une liste contenant les informations de date et heure.
        """
        if rslt != -1:
            self.year = rslt[0] * 256 + rslt[1]
            self.month = rslt[2]
            self.date = rslt[3]
            self.hour = rslt[4]
            self.minute = rslt[5]
            self.second = rslt[6]
            self.millisecond = 0

    def update_from_driver(self, data):
        """Met à jour la date et l'heure depuis les données décodées par GNSSDriver."""
        if data.year is not None:
            self.year = data.year
        if data.month is not None:
            self.month = data.month
        if data.date is not None:
            self.date = data.date
        if data.hour is not None:
            self.hour = data.hour
        if data.minute is not None:
            self.minute = data.minute
        if data.second is not None:
            self.second = data.second
        if data.millisecond is not None:
            self.millisecond = data.millisecond

    def __str__(self):
        """
        Renvoie une chaîne de caractères formatée de la date et l'heure.
        """
        if self.millisecond:
            return f"{self.year:04}/{self.month:02}/{self.date:02} - {self.hour:02}:{self.minute:02}:{self.second:02}.{self.millisecond:03}"
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
        self.direction = "S"  # N ou S pour la latitude, E ou W pour la longitude
        self.coordinates_DD = 0.00  # Coordonnées au format degré décimaux
        self.coordinates_DMM = "0.00"  # Coordonnées au format degré / minute décimales
        self.coordinates_DMS = "0.00"  # Coordonnées au format degrés / minutes / secondes

    def update_coordinate(self, rslt):
        """
        Met à jour la coordonnée depuis l'ancien format registre.
        """
        if rslt != -1:
            self.degres = rslt[0]
            self.minutes = rslt[1]
            self.fractions_minutes = rslt[2] * 65536 + rslt[3] * 256 + rslt[4]
            self.direction = chr(rslt[5])

            decimal = self.degres + self.minutes / 60.0 + self.fractions_minutes / 6000000.0
            if self.direction in ("S", "W"):
                decimal = -decimal
            self.update_from_decimal(decimal, self.direction)

    def update_from_decimal(self, decimal_degrees, direction):
        """Met à jour la coordonnée depuis une valeur en degrés décimaux."""
        if decimal_degrees is None:
            return
        self.direction = direction or self.direction
        self.coordinates_DD = decimal_degrees

        absolute = abs(decimal_degrees)
        self.degres = int(absolute)
        decimal_minutes = (absolute - self.degres) * 60.0
        self.minutes = int(decimal_minutes)
        minute_fraction = decimal_minutes - self.minutes
        self.fractions_minutes = int(round(minute_fraction * 100000))

        seconds = minute_fraction * 60.0
        self.coordinates_DMM = f"{self.degres}°{decimal_minutes:.5f}'{self.direction}"
        self.coordinates_DMS = f"{self.degres}°{self.minutes}'{seconds:.2f}\"{self.direction}"


class GNSS:
    """
    Classe pour la gestion des acquisitions du GNSS.

    La structure publique reste proche de la version d'origine : les attributs
    GPS principaux sont exposés directement dans GNSS. La différence est que
    update() lit maintenant les trames NMEA brutes et délègue leur décodage à
    GNSSDriver, au lieu d'utiliser le bloc de registres I2C limité.
    """
    def __init__(self, bus, addr, validate_nmea_checksum=True):
        """
        Intialise le module de gestion du GNSS.

        Arguments:
        - bus: Le bus de communication du module GNSS.
        - addr: L'adresse I2C de communication du module GNSS.
        - validate_nmea_checksum: active ou non la validation des checksums NMEA.
        """
        self.i2cbus = smbus.SMBus(bus)
        self.__addr = addr
        self.__driver = GNSSDriver(validate_nmea_checksum=validate_nmea_checksum)

        self.timestamp = 0
        self.utc = struct_utc_time()
        self.latitude = struct_GNSS_coordinate()
        self.longitude = struct_GNSS_coordinate()
        self.altitude = 0
        self.number_satellites = 0
        self.COG = 0
        self.SOG = 0
        self.reception_ok = False

        # Données supplémentaires disponibles via les trames NMEA.
        self.fix_quality = 0
        self.fix_type = 1
        self.fix_mode = None
        self.navigation_status = None
        self.faa_mode = None
        self.HDOP = None
        self.VDOP = None
        self.PDOP = None
        self.hdop = None
        self.vdop = None
        self.pdop = None
        self.geoid_separation = None
        self.SOG_kmh = None
        self.SOG_ms = None
        self.COG_magnetic = None
        self.magnetic_variation = None
        self.satellites_in_view = 0
        self.satellites_used_prn = []
        self.satellites = {}
        self.age_dgps = None
        self.dgps_station_id = None
        self.gst_rms = None
        self.gst_sigma_major = None
        self.gst_sigma_minor = None
        self.gst_orientation = None
        self.gst_sigma_lat = None
        self.gst_sigma_lon = None
        self.gst_sigma_alt = None
        self.last_raw_nmea = ""
        self.last_nmea_sentences = []
        self.last_nmea_types = []

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
        """
        rslt = self._read_reg(I2C_GNSS_MODE, 1)
        if rslt == -1:
            return None
        return rslt[0]

    def set_mode(self, mode):
        """
        Actualise le mode GNSS du capteur.
        """
        self._write_reg(I2C_GNSS_MODE, [mode])
        time.sleep(0.1)

    def initialisation(self, mode):
        """
        Initialise le module GNSS avant acquisition.
        """
        while self.begin() == False:
            print("Echec de l'initialisation")
            time.sleep(1)
        self.enable_power()
        self.set_mode(mode)

    def update_timestamp(self):
        self.timestamp = time.time()

    def update(self):
        """
        Actualise les données GNSS depuis les trames NMEA.

        La lecture I2C reste faite ici, comme dans la classe d'origine, mais le
        décodage métier est délégué à GNSSDriver.
        """
        raw_data = self.get_raw_data()
        if not raw_data:
            self.reception_ok = False
            return False

        parsed_any = self.__driver.update_from_raw_data(raw_data)
        self._update_from_driver()

        if parsed_any:
            self.update_timestamp()
        return parsed_any

    def update_from_nmea(self, nmea_text):
        """
        Actualise les données GNSS depuis un texte NMEA.

        Méthode utile pour tester sans Raspberry Pi ni capteur.
        """
        parsed_any = self.__driver.update_from_nmea(nmea_text)
        self._update_from_driver()
        if parsed_any:
            self.update_timestamp()
        return parsed_any

    def _update_from_driver(self):
        """Copie les données décodées par GNSSDriver dans les attributs publics GNSS."""
        data = self.__driver.data

        self.utc.update_from_driver(data)
        self.latitude.update_from_decimal(data.latitude_dd, data.latitude_direction)
        self.longitude.update_from_decimal(data.longitude_dd, data.longitude_direction)

        if data.altitude_m is not None:
            self.altitude = data.altitude_m
        if data.number_satellites is not None:
            self.number_satellites = data.number_satellites
        if data.cog_true is not None:
            self.COG = data.cog_true
        if data.sog_knots is not None:
            self.SOG = data.sog_knots

        self.reception_ok = data.reception_ok
        self.fix_quality = data.fix_quality if data.fix_quality is not None else 0
        self.fix_type = data.fix_type if data.fix_type is not None else 1
        self.fix_mode = data.fix_mode
        self.navigation_status = data.navigation_status
        self.faa_mode = data.faa_mode

        self.HDOP = data.hdop
        self.VDOP = data.vdop
        self.PDOP = data.pdop
        self.hdop = data.hdop
        self.vdop = data.vdop
        self.pdop = data.pdop

        self.geoid_separation = data.geoid_separation_m
        self.SOG_kmh = data.sog_kmh
        self.SOG_ms = data.sog_ms
        self.COG_magnetic = data.cog_magnetic
        self.magnetic_variation = data.magnetic_variation_deg
        self.satellites_in_view = data.satellites_in_view or 0
        self.satellites_used_prn = list(data.satellites_used_prn)
        self.satellites = dict(data.satellites)
        self.age_dgps = data.age_dgps_s
        self.dgps_station_id = data.dgps_station_id
        self.gst_rms = data.gst_rms
        self.gst_sigma_major = data.gst_sigma_major_m
        self.gst_sigma_minor = data.gst_sigma_minor_m
        self.gst_orientation = data.gst_orientation_deg
        self.gst_sigma_lat = data.gst_sigma_lat_m
        self.gst_sigma_lon = data.gst_sigma_lon_m
        self.gst_sigma_alt = data.gst_sigma_alt_m
        self.last_raw_nmea = self.__driver.last_raw_nmea
        self.last_nmea_sentences = list(data.raw_sentences)
        self.last_nmea_types = list(data.parsed_sentence_types)

    def wait_for_next_scan(self, timeout=5.0):
        """
        Attend le passage à la seconde suivante en se basant sur l'horloge UTC du GPS.
        """
        start_time = time.time()
        last_second = getattr(self.utc, "second", None)

        while True:
            self.update()

            if self.utc is not None and self.utc.second != last_second:
                return

            if time.time() - start_time > timeout:
                return

            time.sleep(0.05)

    def get_gnss_len(self):
        """
        Retourne la longueur des données GNSS reçues.
        """
        self._write_reg(I2C_START_GET, [0x55])
        time.sleep(0.1)
        rslt = self._read_reg(I2C_DATA_LEN_H, 2)
        if rslt != -1:
            return rslt[0] * 256 + rslt[1]
        else:
            return 0

    def get_raw_data(self):
        """
        Retourne les données brutes reçues par le GNSS, c'est-à-dire les trames NMEA.
        """
        data_len = self.get_gnss_len()
        if data_len <= 0:
            return []

        time.sleep(0.1)
        all_data = []
        full_chunks = data_len // 32
        remaining = data_len % 32

        for num in range(0, full_chunks + 1):
            chunk_len = remaining if num == full_chunks else 32
            if chunk_len == 0:
                continue

            rslt = self._read_reg(I2C_ALL_DATA, chunk_len)
            if rslt == -1:
                return all_data

            for byte in rslt[:chunk_len]:
                all_data.append(0x0A if byte == 0 else byte)

        return all_data

    def raw_data_to_text(self, raw_data):
        """Convertit une liste d'octets en texte NMEA."""
        return GNSSDriver.raw_data_to_text(raw_data)

    def _write_reg(self, reg, data):
        while 1:
            try:
                self.i2cbus.write_i2c_block_data(self.__addr, reg, data)
                return
            except Exception:
                print("Problème d'écriture")
                time.sleep(1)

    def _read_reg(self, reg, len):
        try:
            rslt = self.i2cbus.read_i2c_block_data(self.__addr, reg, len)
        except Exception:
            rslt = -1
        return rslt
