from sensors.LIDAR import LIDAR
from config import (
    PORT_LIDAR,
    MIN_DETECTION_RANGE,
    MAX_DETECTION_RANGE,
    MIN_DETECTION_ANGLE,
    MAX_DETECTION_ANGLE,
    QUALITY_THRESHOLD,
)
from utils import CSVHandler
import argparse
import numpy as np


def measure_distance(scan_iterator, save_path=None):
    """
    Fonction qui mesure la distance moyenne dans un secteur angulaire prédéfinie
    """
    for timestamp, scan, points in scan_iterator:
        
        # A COMPLETER
        ...
        mean_distance = ...
        std_distance = ...
        
        yield timestamp, mean_distance, std_distance


def main(save_path=None):
    print("Connexion au LiDAR...")
    lidar = LIDAR(
        PORT_LIDAR,
        quality_threshold=QUALITY_THRESHOLD,
        min_range=MIN_DETECTION_RANGE,
        max_range=MAX_DETECTION_RANGE,
        min_angle=MIN_DETECTION_ANGLE,
        max_angle=MAX_DETECTION_ANGLE,
    )

    try:
        print("Démarrage du LiDAR...")
        lidar.start()

        scan_iterator = lidar.iter_scans()
        distance_iterator = measure_distance(
            scan_iterator,
            save_path=save_path,
        )

        for _, _, _ in distance_iterator:
            pass

    except KeyboardInterrupt:
        print("\nMesure interrompue par l'utilisateur.")

    finally:
        print("Arrêt du LiDAR...")
        lidar.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--save-path", "-s",
        type=str,
        default=None,
        help="Chemin où sauvegarder les distances moyennes."
    )
    args = parser.parse_args()

    main(args.save_path)