from sensors.LIDAR import LIDAR
import argparse
from config import PORT_LIDAR, LIDAR_MIN_RANGE, LIDAR_MAX_RANGE, MIN_DETECTION_ANGLE, MAX_DETECTION_ANGLE, QUALITY_THRESHOLD, MIN_DETECTION_RANGE, MAX_DETECTION_RANGE
from core.display import plot_scan

def main(save_path):
    # Initialisation du LiDAR
    print("Connexion au LiDAR...")
    lidar = LIDAR(PORT_LIDAR,
                  quality_threshold=QUALITY_THRESHOLD,
                  min_range=MIN_DETECTION_RANGE,
                  max_range=MAX_DETECTION_RANGE,
                  min_angle=MIN_DETECTION_ANGLE,
                  max_angle=MAX_DETECTION_ANGLE)
    
    print("Démarrage du LiDAR...")
    lidar.start()
    lidar.warmup(3)
    timestamp, scan, points = lidar.read_scan()

    print(f"Timestamp : {timestamp}")
    lidar.print_scan(scan)
    lidar.print_points(points)

    # Enregistrement des données dans le fichier CSV
    if save_path:
        pass
        
    # Affichage des points mesurés dans un plan cartésien
    plot_scan(points, LIDAR_MIN_RANGE, LIDAR_MAX_RANGE)
    
    # Arrêt du LiDAR
    print("Arrêt du LiDAR...")
    lidar.stop()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--save-path', '-s',
                        type=str,
                        default=None,
                        help="Chemin où sauvegarder les données.")
    args = parser.parse_args()
    main(args.save_path)