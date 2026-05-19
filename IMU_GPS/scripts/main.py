from utils.FiltreKalman import run_kalman
from postprocessing.plot_gnss import plot_GNSS
from core.imu_gps_preprocessing import preprocess_imu_gps_df
from config.parameters import ACCEL_RANGE, ACCEL_FREQ, GYRO_FREQ, GYRO_RANGE
from utils.correction_erreur_systematique import transformation_csv_dataframe, transformation_dataframe_csv,corriger_biais_imu
import argparse
def appliqueKalman(savepath,output):
    """fonction qui permet d'appliquer Kalman à un fichier déjà traité"""
    df = transformation_csv_dataframe(savepath)
    dfKalman = run_kalman(df)
    transformation_dataframe_csv(dfKalman,output)
    
def main_offline(savepath_donnee,savepath_strava,output):
    """
     fonction qui prend un csv d'acquistion brut et le traite les données et génère la carte
    """
    config_imu = (int(ACCEL_RANGE), float(ACCEL_FREQ), int(GYRO_RANGE), float(GYRO_FREQ))
    df1 = transformation_csv_dataframe(savepath_donnee)
    df2 = transformation_csv_dataframe(savepath_strava)
    df_sansbiais = corriger_biais_imu(df1,config_imu)
    df_sansbiais_nettoye= preprocess_imu_gps_df(df_sansbiais)
    df_kalman = run_kalman(df_sansbiais_nettoye)
    plot_GNSS(df_kalman,df2, output)

    

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--mode",
    )

    parser.add_argument(
        "savepath_own",
        type=str,
    )
    parser.add_argument(
        "savepath_strava",
        type=str,
    )

    parser.add_argument(
       "output",
       type=str
    )

    args = parser.parse_args()
    if args.mode == "apk":
        appliqueKalman(args.savepath,args.output)
    if args.mode == "run":
      main_offline(args.savepath_own, args.savepath_strava, args.output)
       