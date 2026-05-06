from sensors.LIDAR import LIDAR
from core.display import stream_scans
from config import (
    PORT_LIDAR,
    LIDAR_MIN_RANGE,
    LIDAR_MAX_RANGE,
    MIN_DETECTION_ANGLE,
    MAX_DETECTION_ANGLE,
    QUALITY_THRESHOLD,
    MIN_DETECTION_RANGE,
    MAX_DETECTION_RANGE
)
import argparse


def scan_stream_with_binary(scan_iterator, save_path, lidar):
    for timestamp, measures, points in scan_iterator:
        lidar.save_scan(points, save_path)
        yield timestamp, measures, points

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
        lidar.warmup(3)
        scan_iterator = lidar.iter_scans()
        if save_path:
            scan_iterator = scan_stream_with_binary(scan_iterator, save_path, lidar)

        print("Affichage temps réel du scan...")
        stream_scans(
            scan_iterator,
            min_range=LIDAR_MIN_RANGE,
            max_range=LIDAR_MAX_RANGE,
        )

    except KeyboardInterrupt:
        print("\nStreaming interrompu par l'utilisateur.")

    finally:
        print("Arrêt du LiDAR...")
        lidar.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--save-path", "-s",
        type=str,
        default=None,
        help="Chemin où sauvegarder les scans au format lscan."
    )
    args = parser.parse_args()

    main(args.save_path)