"""Prétraitement des données d'acquisition IMU/GNSS.

Le module transforme les données brutes en données exploitables pour le filtre de
Kalman : nettoyage des mesures GPS aberrantes, conversion des champs numériques
et correction du biais hard iron du magnétomètre.
"""

import csv
from pathlib import Path

import pandas as pd

from config.parameters import MAG_BIAS


def corriger_magnetometre(rows):
    """Corrige le décalage hard iron du magnétomètre.

    Paramètres
    ----------
    rows : list[dict]
        Lignes de données contenant les colonnes ``Magneto X``, ``Magneto Y`` et
        ``Magneto Z``.

    Retours
    -------
    list[dict]
        Copie des lignes avec les valeurs du magnétomètre corrigées.
    """
    corrected = []

    for row in rows:
        new_row = dict(row)

        if new_row.get("Magneto X") is not None:
            new_row["Magneto X"] = new_row["Magneto X"] - MAG_BIAS[0]

        if new_row.get("Magneto Y") is not None:
            new_row["Magneto Y"] = new_row["Magneto Y"] - MAG_BIAS[1]

        if new_row.get("Magneto Z") is not None:
            new_row["Magneto Z"] = new_row["Magneto Z"] - MAG_BIAS[2]

        corrected.append(new_row)

    return corrected


def read_imu_gps_csv(csv_path):
    """Lit un CSV d'acquisition IMU/GNSS.

    Paramètres
    ----------
    csv_path : str or pathlib.Path
        Chemin du fichier CSV à lire.

    Retours
    -------
    list[dict]
        Lignes du CSV sous forme de dictionnaires.
    """
    csv_path = Path(csv_path)
    rows = []

    with csv_path.open(mode="r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    return rows


def write_imu_gps_csv(rows, csv_path, fieldnames=None):
    """Écrit une liste de dictionnaires dans un CSV.

    Paramètres
    ----------
    rows : list[dict]
        Données à écrire.
    csv_path : str or pathlib.Path
        Chemin du fichier CSV de sortie.
    fieldnames : list[str], optional
        Liste des colonnes à écrire. Si None, les clés de la première ligne sont utilisées.
    """
    csv_path = Path(csv_path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    if fieldnames is None and rows:
        fieldnames = list(rows[0].keys())

    with csv_path.open(mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _parse_float(value, default=None):
    """Convertit une valeur en flottant, ou retourne une valeur par défaut."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def clean_rows(rows):
    """Nettoie les lignes brutes GPS et IMU.

    Les points GPS marqués valides mais présentant un saut trop important par
    rapport au point précédent sont invalidés.
    """
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
    """Convertit les champs texte du CSV en valeurs numériques exploitables."""
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
                new_row[col] = _parse_float(row.get(col), default=0.0)
            elif col == "Nb Satellites":
                new_row[col] = _parse_float(row.get(col), default=0)
            else:
                new_row[col] = _parse_float(row.get(col))

        gps_valid_raw = row.get("GPS Valid", "0")
        new_row["GPS Valid"] = (
            1 if str(gps_valid_raw).strip() in {"1", "True", "true", "yes", "OK"} else 0
        )

        converted.append(new_row)

    return converted


def preprocess_imu_gps_csv(input_csv, output_csv):
    """Prétraite un fichier CSV d'acquisition et écrit un nouveau CSV corrigé.

    Cette fonction est utile pour produire un fichier intermédiaire de données
    nettoyées. Dans le pipeline principal, la version DataFrame est utilisée.
    """
    rows = read_imu_gps_csv(input_csv)
    rows = clean_rows(rows)
    rows = convert_units(rows)
    rows = corriger_magnetometre(rows)
    write_imu_gps_csv(rows, output_csv)
    return output_csv


def preprocess_imu_gps_df(input_df):
    """Prétraite un DataFrame d'acquisition IMU/GNSS.

    Paramètres
    ----------
    input_df : pandas.DataFrame
        Données brutes ou partiellement corrigées.

    Retours
    -------
    pandas.DataFrame
        Données nettoyées, converties et corrigées côté magnétomètre.
    """
    rows = input_df.to_dict(orient='records')
    rows = clean_rows(rows)
    rows = convert_units(rows)
    rows = corriger_magnetometre(rows)
    return pd.DataFrame(rows)
