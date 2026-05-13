import pandas as pd
import argparse
from IMU_GPS.config.parameters import BIAIS_IMU


def correction_syst_col(df, col, erreur_syst):
    df[col] = df[col] - erreur_syst
    return df


def transformation_csv_dataframe(file_path):
    return pd.read_csv(file_path)


def transformation_dataframe_csv(df, file_path):
    df.to_csv(file_path, index=False)


def corriger_biais_imu(df, config_imu):
    """
    Corrige le biais IMU d'un DataFrame et retourne le DataFrame corrigé.
    
    config_imu : tuple (accel_range, accel_freq, gyro_range, gyro_freq)
    """
    colonnes_imu = ["Accel X", "Accel Y", "Accel Z", "Gyro X", "Gyro Y", "Gyro Z"]
    
    biais_imu = BIAIS_IMU[config_imu].copy()
    # Accel X contient la gravité : on soustrait 1g du biais
    biais_imu[0] = biais_imu[0] - 1.0
    
    for col, biais in zip(colonnes_imu, biais_imu):
        df = correction_syst_col(df, col, biais)
    
    return df