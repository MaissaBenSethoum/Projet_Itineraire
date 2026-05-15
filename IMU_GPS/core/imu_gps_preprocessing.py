import csv
from pathlib import Path
import pandas as pd


def read_imu_gps_csv(csv_path):
    """Lit un CSV d'acquisition (IMU+GPS) et retourne une liste de dictionnaires."""
    csv_path = Path(csv_path)
    rows = []

    with csv_path.open(mode="r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    return rows


def write_imu_gps_csv(rows, csv_path, fieldnames=None):
    """Écrit une liste de dictionnaires dans un CSV de sortie."""
    csv_path = Path(csv_path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    if fieldnames is None and rows:
        fieldnames = list(rows[0].keys())

    with csv_path.open(mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _parse_float(value, default=None):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def clean_rows(rows):
    """Nettoie les lignes brutes GPS et IMU."""
    cleaned = []
    last_lat = None
    last_lon = None
    max_gps_jump = 0.0005
    valid_flags = {"1", "True", "true", "yes", "OK"}

    for row in rows:
        gps_valid = str(row.get("GPS Valid", "0")).strip() in valid_flags
        lat = _parse_float(row.get("Latitude"))
        lon = _parse_float(row.get("Longitude"))

        if gps_valid and lat is not None and lon is not None:
            if last_lat is not None and last_lon is not None:
                if abs(lat - last_lat) > max_gps_jump or abs(lon - last_lon) > max_gps_jump:
                    row = dict(row)
                    row["GPS Valid"] = 0
                    cleaned.append(row)
                    continue
            last_lat = lat
            last_lon = lon

        cleaned.append(row)

    return cleaned
def convert_units(rows):
    """Convertit les champs de texte en nombres et unités exploitables."""
    converted = []

    for row in rows:
        new_row = dict(row)
        new_row["Timestamp"] = _parse_float(row.get("Timestamp"), default=0.0)
        new_row["Latitude"] = _parse_float(row.get("Latitude"))
        new_row["Longitude"] = _parse_float(row.get("Longitude"))
        new_row["Altitude"] = _parse_float(row.get("Altitude"))
        new_row["Nb Satellites"] = _parse_float(row.get("Nb Satellites"), default=0)
        new_row["Accel X"] = _parse_float(row.get("Accel X"))
        gps_valid_raw = row.get("GPS Valid", "0")                                                                                                                                              
        new_row["GPS Valid"] = 1 if str(gps_valid_raw).strip() in {"1", "True", "true", "yes", "OK"} else 0   
        new_row["Accel Y"] = _parse_float(row.get("Accel Y"))
        new_row["Accel Z"] = _parse_float(row.get("Accel Z"))
        new_row["Gyro X"] = _parse_float(row.get("Gyro X"))
        new_row["Gyro Y"] = _parse_float(row.get("Gyro Y"))
        new_row["Gyro Z"] = _parse_float(row.get("Gyro Z"))
        converted.append(new_row)

    return converted


def preprocess_imu_gps_csv(input_csv, output_csv):
    """Lit un CSV brut, réalise le prétraitement et écrit un CSV de sortie."""
    rows = read_imu_gps_csv(input_csv)

    rows = clean_rows(rows)
    rows = convert_units(rows)
    rows = filter_imu_noise(rows)

    write_imu_gps_csv(rows, output_csv)
    return output_csv

def preprocess_imu_gps_df(input_df):
    rows = input_df.to_dict(orient='records')
    rows = clean_rows(rows)
    rows = convert_units(rows)
    return pd.DataFrame(rows)
