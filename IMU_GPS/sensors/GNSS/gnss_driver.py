"""
Driver GNSS indépendant de la couche I2C.

Ce module contient uniquement la logique métier liée aux trames NMEA :
- conversion des octets bruts en texte,
- extraction / validation des phrases NMEA,
- parsing des trames utiles,
- agrégation des données calculées dans GNSSData.

Il ne dépend ni de smbus, ni de Raspberry Pi, ni de la configuration I2C.
"""

from dataclasses import dataclass, field

KNOT_TO_KMH = 1.852
KNOT_TO_MS = 0.514444444


@dataclass
class SatelliteInfo:
    """Informations d'un satellite annoncé par une trame GSV."""

    prn: str = ""
    elevation_deg = None
    azimuth_deg = None
    snr_dbhz = None
    talker = ""


from dataclasses import dataclass, field

@dataclass
class GNSSData:

    # Temps / position
    year: int = None
    month: int = None
    date: int = None
    hour: int = None
    minute: int = None
    second: int = None
    millisecond: int = None

    latitude_dd: float = None
    latitude_direction: str = None

    longitude_dd: float = None
    longitude_direction: str = None

    altitude_m: float = None
    geoid_separation_m: float = None

    # Fix
    fix_quality: int = None
    fix_type: int = None
    fix_mode: str = None
    navigation_status: str = None
    faa_mode: str = None

    reception_ok: bool = False

    # DOP
    hdop: float = None
    vdop: float = None
    pdop: float = None

    # Satellites
    number_satellites: int = None
    satellites_in_view: int = None

    satellites_used_prn: list = field(default_factory=list)
    satellites: dict = field(default_factory=dict)

    # Navigation
    sog_knots: float = None
    sog_kmh: float = None
    sog_ms: float = None

    cog_true: float = None
    cog_magnetic: float = None
    magnetic_variation_deg: float = None

    # Corrections
    age_dgps_s: float = None
    dgps_station_id: str = None

    gst_rms: float = None
    gst_sigma_major_m: float = None
    gst_sigma_minor_m: float = None
    gst_orientation_deg: float = None
    gst_sigma_lat_m: float = None
    gst_sigma_lon_m: float = None
    gst_sigma_alt_m: float = None

    # Debug
    raw_sentences: list = field(default_factory=list)
    parsed_sentence_types: list = field(default_factory=list)


class GNSSDriver:
    """Parseur NMEA pur, testable sans matériel."""

    def __init__(self, validate_nmea_checksum = True):
        self.validate_nmea_checksum = validate_nmea_checksum
        self.data = GNSSData()
        self.last_raw_nmea = ""

    def update_from_raw_data(self, raw_data):
        """Met à jour l'état depuis une liste d'octets lue en I2C."""
        return self.update_from_nmea(self.raw_data_to_text(raw_data))

    def update_from_nmea(self, nmea_text):
        """Met à jour l'état depuis un bloc texte contenant des trames NMEA."""
        self.last_raw_nmea = nmea_text or ""
        sentences = self.extract_sentences(self.last_raw_nmea)
        if not sentences:
            self.data.reception_ok = False
            self.data.raw_sentences = []
            self.data.parsed_sentence_types = []
            return False

        self.data.raw_sentences = sentences
        self.data.parsed_sentence_types = []

        parsed_any = False
        for sentence in sentences:
            parsed_any = self.parse_sentence(sentence) or parsed_any

        self._refresh_reception_status()
        return parsed_any

    @staticmethod
    def raw_data_to_text(raw_data):
        """Convertit les octets bruts du capteur en texte NMEA."""
        if raw_data in (-1, None):
            return ""
        if isinstance(raw_data, str):
            return raw_data
        return bytes(byte for byte in raw_data if byte is not None).decode("ascii", errors="ignore")

    @staticmethod
    def extract_sentences(text):
        """Extrait les phrases NMEA complètes ou quasi complètes d'un bloc texte."""
        sentences = []
        for raw_line in (text or "").replace("\r", "\n").split("\n"):
            line = raw_line.strip()
            if not line:
                continue
            dollar_pos = line.find("$")
            if dollar_pos >= 0:
                line = line[dollar_pos:]
            if line.startswith("$") and len(line) >= 6:
                sentences.append(line)
        return sentences

    def parse_sentence(self, sentence):
        payload = _strip_and_validate_sentence(sentence, self.validate_nmea_checksum)
        if payload is None:
            return False

        fields = payload.split(",")
        if not fields or len(fields[0]) < 3:
            return False

        talker = fields[0][:2]
        sentence_type = fields[0][-3:]
        data_fields = fields[1:]

        parsers = {
            "GGA": self._parse_gga,
            "RMC": self._parse_rmc,
            "GSA": self._parse_gsa,
            "GSV": self._parse_gsv,
            "VTG": self._parse_vtg,
            "ZDA": self._parse_zda,
            "GST": self._parse_gst,
        }
        parser = parsers.get(sentence_type)
        if parser is None:
            return False

        parser(data_fields, talker)
        self.data.parsed_sentence_types.append(fields[0])
        return True

    def _parse_gga(self, fields, talker):
        self._update_time(_get(fields, 0))
        self._update_lat_lon(_get(fields, 1), _get(fields, 2), _get(fields, 3), _get(fields, 4))
        self.data.fix_quality = _to_int(_get(fields, 5))
        self.data.number_satellites = _to_int(_get(fields, 6))
        self.data.hdop = _coalesce(_to_float(_get(fields, 7)), self.data.hdop)
        self.data.altitude_m = _coalesce(_to_float(_get(fields, 8)), self.data.altitude_m)
        self.data.geoid_separation_m = _coalesce(_to_float(_get(fields, 10)), self.data.geoid_separation_m)
        self.data.age_dgps_s = _coalesce(_to_float(_get(fields, 12)), self.data.age_dgps_s)
        self.data.dgps_station_id = _get(fields, 13) or self.data.dgps_station_id

    def _parse_rmc(self, fields, talker):
        self._update_time(_get(fields, 0), _get(fields, 8))
        self.data.navigation_status = _get(fields, 1) or self.data.navigation_status
        self._update_lat_lon(_get(fields, 2), _get(fields, 3), _get(fields, 4), _get(fields, 5))
        self._update_speed(_to_float(_get(fields, 6)), None)
        self.data.cog_true = _coalesce(_to_float(_get(fields, 7)), self.data.cog_true)

        mag_var = _to_float(_get(fields, 9))
        mag_dir = _get(fields, 10)
        if mag_var is not None:
            self.data.magnetic_variation_deg = -mag_var if mag_dir == "W" else mag_var
        self.data.faa_mode = _get(fields, 11) or self.data.faa_mode

    def _parse_gsa(self, fields, talker):
        self.data.fix_mode = _get(fields, 0) or self.data.fix_mode
        self.data.fix_type = _coalesce(_to_int(_get(fields, 1)), self.data.fix_type)
        prns = [value for value in fields[2:14] if value]
        if prns:
            self.data.satellites_used_prn = prns
        self.data.pdop = _coalesce(_to_float(_get(fields, 14)), self.data.pdop)
        self.data.hdop = _coalesce(_to_float(_get(fields, 15)), self.data.hdop)
        self.data.vdop = _coalesce(_to_float(_get(fields, 16)), self.data.vdop)

    def _parse_gsv(self, fields, talker):
        self.data.satellites_in_view = _coalesce(_to_int(_get(fields, 2)), self.data.satellites_in_view)
        for index in range(3, len(fields), 4):
            prn = _get(fields, index)
            if not prn:
                continue
            self.data.satellites[f"{talker}{prn}"] = SatelliteInfo(
                prn=prn,
                elevation_deg=_to_int(_get(fields, index + 1)),
                azimuth_deg=_to_int(_get(fields, index + 2)),
                snr_dbhz=_to_int(_get(fields, index + 3)),
                talker=talker,
            )

    def _parse_vtg(self, fields, talker):
        self.data.cog_true = _coalesce(_to_float(_get(fields, 0)), self.data.cog_true)
        self.data.cog_magnetic = _coalesce(_to_float(_get(fields, 2)), self.data.cog_magnetic)
        self._update_speed(_to_float(_get(fields, 4)), _to_float(_get(fields, 6)))
        self.data.faa_mode = _get(fields, 8) or self.data.faa_mode

    def _parse_zda(self, fields, talker):
        self._update_time(_get(fields, 0))
        day = _to_int(_get(fields, 1))
        month = _to_int(_get(fields, 2))
        year = _to_int(_get(fields, 3))
        if year and month and day:
            self.data.year = year
            self.data.month = month
            self.data.date = day

    def _parse_gst(self, fields, talker):
        self._update_time(_get(fields, 0))
        self.data.gst_rms = _coalesce(_to_float(_get(fields, 1)), self.data.gst_rms)
        self.data.gst_sigma_major_m = _coalesce(_to_float(_get(fields, 2)), self.data.gst_sigma_major_m)
        self.data.gst_sigma_minor_m = _coalesce(_to_float(_get(fields, 3)), self.data.gst_sigma_minor_m)
        self.data.gst_orientation_deg = _coalesce(_to_float(_get(fields, 4)), self.data.gst_orientation_deg)
        self.data.gst_sigma_lat_m = _coalesce(_to_float(_get(fields, 5)), self.data.gst_sigma_lat_m)
        self.data.gst_sigma_lon_m = _coalesce(_to_float(_get(fields, 6)), self.data.gst_sigma_lon_m)
        self.data.gst_sigma_alt_m = _coalesce(_to_float(_get(fields, 7)), self.data.gst_sigma_alt_m)

    def _update_time(self, utc_time = "", utc_date = ""):
        parsed_time = _parse_nmea_time(utc_time)
        if parsed_time is not None:
            self.data.hour, self.data.minute, self.data.second, self.data.millisecond = parsed_time
        parsed_date = _parse_nmea_date(utc_date)
        if parsed_date is not None:
            self.data.year, self.data.month, self.data.date = parsed_date

    def _update_lat_lon(self, lat_value, lat_dir, lon_value, lon_dir):
        latitude = _parse_nmea_coordinate(lat_value, lat_dir)
        longitude = _parse_nmea_coordinate(lon_value, lon_dir)
        if latitude is not None:
            self.data.latitude_dd = latitude
            self.data.latitude_direction = lat_dir
        if longitude is not None:
            self.data.longitude_dd = longitude
            self.data.longitude_direction = lon_dir

    def _update_speed(self, speed_knots, speed_kmh):
        if speed_knots is not None:
            self.data.sog_knots = speed_knots
            self.data.sog_kmh = speed_knots * KNOT_TO_KMH
            self.data.sog_ms = speed_knots * KNOT_TO_MS
        if speed_kmh is not None:
            self.data.sog_kmh = speed_kmh
            if speed_knots is None:
                self.data.sog_knots = speed_kmh / KNOT_TO_KMH
                self.data.sog_ms = speed_kmh / 3.6

    def _refresh_reception_status(self):
        has_position = self.data.latitude_dd is not None and self.data.longitude_dd is not None
        gga_fix_ok = self.data.fix_quality is not None and self.data.fix_quality > 0
        gsa_fix_ok = self.data.fix_type is not None and self.data.fix_type >= 2
        rmc_fix_ok = self.data.navigation_status == "A"
        self.data.reception_ok = bool(has_position and (gga_fix_ok or gsa_fix_ok or rmc_fix_ok))


def _get(fields, index):
    if index < 0 or index >= len(fields):
        return ""
    return fields[index].strip()


def _coalesce(value, fallback):
    return value if value is not None else fallback


def _to_float(value):
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value):
    try:
        if value in (None, ""):
            return None
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _parse_nmea_time(value):
    if not value:
        return None
    try:
        hour = int(value[0:2])
        minute = int(value[2:4])
        second_float = float(value[4:])
        second = int(second_float)
        millisecond = int(round((second_float - second) * 1000))
        if millisecond == 1000:
            second += 1
            millisecond = 0
        return hour, minute, second, millisecond
    except (ValueError, IndexError):
        return None


def _parse_nmea_date(value):
    if not value or len(value) < 6:
        return None
    try:
        day = int(value[0:2])
        month = int(value[2:4])
        year_2d = int(value[4:6])
        year = 2000 + year_2d if year_2d < 80 else 1900 + year_2d
        return year, month, day
    except ValueError:
        return None


def _parse_nmea_coordinate(value, direction):
    if not value or not direction:
        return None
    try:
        raw = float(value)
        degrees = int(raw // 100)
        minutes = raw - degrees * 100
        decimal = degrees + minutes / 60.0
        if direction in ("S", "W"):
            decimal = -decimal
        return decimal
    except ValueError:
        return None


def _strip_and_validate_sentence(sentence, validate_checksum=True):
    sentence = sentence.strip()
    if not sentence.startswith("$"):
        return None

    without_dollar = sentence[1:]
    if "*" not in without_dollar:
        return without_dollar

    payload, checksum = without_dollar.split("*", 1)
    checksum = checksum[:2]
    if validate_checksum:
        try:
            expected = int(checksum, 16)
        except ValueError:
            return None
        calculated = 0
        for char in payload:
            calculated ^= ord(char)
        if calculated != expected:
            return None
    return payload
