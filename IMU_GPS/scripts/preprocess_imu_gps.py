import argparse
from IMU_GPS.core.imu_gps_preprocessing import preprocess_imu_gps_csv


def main():
    parser = argparse.ArgumentParser(
        description="Lance le prétraitement IMU+GPS sur un fichier CSV brut."
    )

    parser.add_argument(
        "--input",
        type=str,
        default="data/acquisition_imu_gps.csv",
        help="Chemin du CSV brut généré par l'acquisition."
    )

    parser.add_argument(
        "--output",
        type=str,
        default="data/preprocessed_imu_gps.csv",
        help="Chemin du CSV prétraité à générer."
    )

    args = parser.parse_args()

    output_path = preprocess_imu_gps_csv(
        input_csv=args.input,
        output_csv=args.output,
    )

    print(f"Prétraitement terminé. Fichier généré : {output_path}")


if __name__ == "__main__":
    main()
