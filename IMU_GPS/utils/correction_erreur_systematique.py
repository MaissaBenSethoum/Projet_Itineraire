import pandas as pd
import argparse
from config import BIAIS_IMU


def correction_syst_col(df, col, erreur_syst):
    df[col] = df[col] - erreur_syst
    return df


def transformation_csv_dataframe(file_path):
    return pd.read_csv(file_path)


def transformation_dataframe_csv(df, file_path):
    df.to_csv(file_path, index=False)


if __name__ == "__main__":
    arg = argparse.ArgumentParser(description="Correction de l'erreur systématique d'un fichier CSV")

    arg.add_argument("file_path", type=str, help="Chemin du fichier CSV à corriger")
    arg.add_argument("-o", "--output", type=str, required=True, help="Chemin du fichier CSV de sortie")

    arg.add_argument("--accel-range", type=float, required=True)
    arg.add_argument("--accel-freq", type=float, required=True)
    arg.add_argument("--gyro-range", type=float, required=True)
    arg.add_argument("--gyro-freq", type=float, required=True)

    args = arg.parse_args()

    df = transformation_csv_dataframe(args.file_path)

    config_imu = (
        int(args.accel_range),
        float(args.accel_freq),
        int(args.gyro_range),
        float(args.gyro_freq)
    )

    colonnes_imu = ["Accel X","Accel Y","Accel Z","Gyro X","Gyro Y","Gyro Z"]
    biais_imu = BIAIS_IMU[config_imu].copy()

    # Accel X contient la gravité : on garde 1g
    biais_imu[0] = biais_imu[0] - 1.0

    for col, biais in zip(colonnes_imu, biais_imu):
        df = correction_syst_col(df, col, biais)

    if not args.output.endswith(".csv"):
        args.output += ".csv"

    transformation_dataframe_csv(df, args.output)

    print(f"Correction terminée : {args.output}")
    print(f"Configuration utilisée : {config_imu}")
    print(f"Biais appliqués : {biais_imu}")