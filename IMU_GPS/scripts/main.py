"""Pipeline principal de post-traitement des données ITIPhone.

Deux modes sont proposés :
- run : traite un CSV d'acquisition brut, applique la correction des biais,
  nettoie les données, lance le filtre de Kalman et génère une carte HTML avec
  comparaison aux données Strava ;
- apk : applique uniquement le filtre de Kalman sur un fichier déjà traité
  et sauvegarde le résultat dans un CSV.
"""
from utils.FiltreKalman import run_kalman
from postprocessing.plot_gnss import plot_GNSS
from core.imu_gps_preprocessing import preprocess_imu_gps_df
from config.parameters import ACCEL_RANGE, ACCEL_FREQ, GYRO_FREQ, GYRO_RANGE
from utils.correction_erreur_systematique import transformation_csv_dataframe, transformation_dataframe_csv,corriger_biais_imu
import argparse
def appliqueKalman(savepath,output):
    """Applique le filtre de Kalman à un fichier CSV déjà traité.

    Paramètres
    ----------
    savepath : str
        Chemin du fichier CSV d'entrée.
    output : str
        Chemin du fichier CSV de sortie contenant la trajectoire filtrée.
    """
    df = transformation_csv_dataframe(savepath)
    df_sansbiais = corriger_biais_imu(df, (int(ACCEL_RANGE), float(ACCEL_FREQ), int(GYRO_RANGE), float(GYRO_FREQ)))
    df_nettoye = preprocess_imu_gps_df(df_sansbiais)
    dfKalman = run_kalman(df_nettoye)
    transformation_dataframe_csv(dfKalman,output)


def main_offline(savepath_donnee,savepath_strava,output):
    """Traite une acquisition brute et génère une carte de comparaison.

    Paramètres
    ----------
    savepath_donnee : str
        Chemin du CSV d'acquisition IMU/GNSS brut.
    savepath_strava : str
        Chemin du CSV de référence exporté depuis Strava.
    output : str
        Chemin du fichier HTML de sortie pour la carte.
    """
    config_imu = (int(ACCEL_RANGE), float(ACCEL_FREQ), int(GYRO_RANGE), float(GYRO_FREQ))
    df1 = transformation_csv_dataframe(savepath_donnee)
    df2 = transformation_csv_dataframe(savepath_strava)
    df_sansbiais = corriger_biais_imu(df1,config_imu)
    df_sansbiais_nettoye= preprocess_imu_gps_df(df_sansbiais)
    df3 = df_sansbiais_nettoye[df_sansbiais_nettoye['GPS Valid'] == 1]
    df_kalman = run_kalman(df_sansbiais_nettoye)
    plot_GNSS(df_kalman,df2,df3, output)

    

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--mode",
    )

    parser.add_argument(
        "savepath_kalman",
        type=str,
    )
    parser.add_argument(
        "--savepath_strava",
        type=str,
    )

    parser.add_argument(
       "output",
       type=str
    )

    args = parser.parse_args()
    if args.mode == "apk":
        appliqueKalman(args.savepath_kalman,args.output)
    if args.mode == "run":
        main_offline(args.savepath_kalman, args.savepath_strava, args.output)
        #main_offline(args.savepath_own, args.output)
       