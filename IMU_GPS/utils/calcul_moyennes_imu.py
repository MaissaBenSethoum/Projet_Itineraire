import pandas as pd
import argparse

def calcul_moyenne_colonne(df, col):
    return df[col].mean()

if __name__ == "__main__":
    arg = argparse.ArgumentParser(description="Calcul des moyennes des colonnes IMU")
    arg.add_argument("file_path",type=str,help="Chemin du fichier csv")
    args = arg.parse_args()
    df = pd.read_csv(args.file_path)

    colonnes_imu = ["Accel X","Accel Y","Accel Z","Gyro X","Gyro Y","Gyro Z","Magneto X", "Magneto Y", "Magneto Z"]

    print("Moyennes IMU :")

    for col in colonnes_imu:
        moyenne = calcul_moyenne_colonne(df, col)
        print(f"{col} : {moyenne}")