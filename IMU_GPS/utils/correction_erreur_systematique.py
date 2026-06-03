"""Correction des biais systématiques mesurés sur l'IMU.

Les biais sont obtenus à partir de mesures réalisées avec l'IMU immobile. Ils
sont stockés dans config.parameters.BIAIS_IMU et appliqués aux colonnes de
l'accéléromètre et du gyroscope avant le filtrage.
"""

import pandas as pd

from config.parameters import BIAIS_IMU


def correction_syst_col(df, col, erreur_syst):
    """Soustrait une erreur systématique à une colonne d'un DataFrame.

    Paramètres
    ----------
    df : pandas.DataFrame
        Données à corriger.
    col : str
        Nom de la colonne à corriger.
    erreur_syst : float
        Valeur du biais à soustraire.

    Retours
    -------
    pandas.DataFrame
        DataFrame corrigé.
    """
    df[col] = df[col] - erreur_syst
    return df


def transformation_csv_dataframe(file_path):
    """Charge un fichier CSV dans un DataFrame pandas."""
    return pd.read_csv(file_path)


def transformation_dataframe_csv(df, file_path):
    """Sauvegarde un DataFrame pandas dans un fichier CSV."""
    df.to_csv(file_path, index=False)


def corriger_biais_imu(df, config_imu):
    """Corrige les biais de l'accéléromètre et du gyroscope.

    Paramètres
    ----------
    df : pandas.DataFrame
        DataFrame contenant les colonnes ``Accel X``, ``Accel Y``, ``Accel Z``,
        ``Gyro X``, ``Gyro Y`` et ``Gyro Z``.
    config_imu : tuple
        Configuration IMU sous la forme ``(accel_range, accel_freq, gyro_range, gyro_freq)``.

    Retours
    -------
    pandas.DataFrame
        DataFrame avec les colonnes IMU corrigées.
    """
    colonnes_imu = ["Accel X", "Accel Y", "Accel Z", "Gyro X", "Gyro Y", "Gyro Z"]

    biais_imu = BIAIS_IMU[config_imu].copy()
    # Accel X contient la gravité dans les acquisitions immobiles : on retire 1 g du biais.
    biais_imu[0] = biais_imu[0] - 1.0

    for col, biais in zip(colonnes_imu, biais_imu):
        df = correction_syst_col(df, col, biais)

    return df