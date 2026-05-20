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
    """Convertit les champs texte en valeurs numériques exploitables."""
    converted = []

    for row in rows:
        new_row = dict(row)
        colonnes_numeriques = [
            "Timestamp",
            "Latitude",
            "Longitude",
            "Altitude",
            "Nb Satellites",
            "Fix Quality",
            "Fix Type",
            "HDOP",
            "VDOP",
            "PDOP",
            "SOG_ms",
            "COG",
            "Accel X",
            "Accel Y",
            "Accel Z",
            "Gyro X",
            "Gyro Y",
            "Gyro Z",
            "Magneto X",
            "Magneto Y",
            "Magneto Z"]

        for col in colonnes_numeriques:
            if col == "Timestamp":
                new_row[col] = _parse_float(row.get(col),default=0.0)

            elif col == "Nb Satellites":new_row[col] = _parse_float(row.get(col),default=0)

            else:
                new_row[col] = _parse_float(row.get(col))

        gps_valid_raw = row.get("GPS Valid", "0")

        new_row["GPS Valid"] = (1 if str(gps_valid_raw).strip() in {"1", "True", "true", "yes", "OK"}else 0)

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
