import math
import time
from pathlib import Path    
from .rplidar_driver import RPLidar, RPLidarException
from config import LIDAR_MIN_RANGE, LIDAR_MAX_RANGE, SCAN_SKIP
from utils import CSVHandler


class LIDAR:
    def __init__(
        self,
        port_name,
        min_range=LIDAR_MIN_RANGE,
        max_range=LIDAR_MAX_RANGE,
        quality_threshold=0,
        min_angle=0,
        max_angle=360,
    ):
        """
        Initialise la classe LIDAR et configure les paramètres de mesure.

        Arguments:
        - port_name: nom du port série où est connecté le LiDAR
        - min_range: portée minimale en mm
        - max_range: portée maximale en mm
        - quality_threshold: seuil de qualité pour filtrer les mesures
        - min_angle: angle minimal pour filtrer les mesures (en degrés)
        - max_angle: angle maximal pour filtrer les mesures (en degrés)
        """
        self.lidar = RPLidar(port_name)

        self.quality_threshold = quality_threshold
        self.min_range = min_range
        self.max_range = max_range
        self.min_angle = min_angle
        self.max_angle = max_angle
        self.scan_skip = SCAN_SKIP

        self._scan_iterator = None
        self._is_started = False

    ######################################
    #    DEMARRAGE / ARRET DU LIDAR
    ######################################

    def start(self, min_len=5, max_buf_meas=10000):
        """
        Démarre le LiDAR :
        - moteur
        - scan bas niveau
        - itérateur interne de scans

        Arguments:
        - min_len: nombre minimal de mesures pour qu'un scan soit valide
        - max_buf_meas: taille maximale du buffer interne du driver
        """
        if self._is_started:
            return

        self.lidar.clean_input()
        self.lidar.start_motor()
        time.sleep(0.5)
        
        self.lidar.clean_input()
        self.lidar.start()
        time.sleep(0.1)
        
        self._min_len = min_len
        self._max_buf_meas = max_buf_meas
        self._scan_iterator = self.lidar.iter_scans(
            max_buf_meas=max_buf_meas,
            min_len=min_len
        )
        self._is_started = True

    def stop(self):
        """
        Arrête le LiDAR, son moteur et déconnecte la connexion série.
        """
        try:
            self.lidar.stop()
        except RPLidarException:
            pass

        try:
            self.lidar.stop_motor()
        except RPLidarException:
            pass

        self.lidar.disconnect()
        self._scan_iterator = None
        self._is_started = False

    def warmup(self, n_scans=3):
        """
        Ignore les premiers scans pour laisser le LiDAR se stabiliser.

        Arguments:
        - n_scans: nombre de scans à ignorer
        """
        if self._scan_iterator is None:
            raise RuntimeError("LIDAR non démarré. Appelez start() avant warmup().")

        for _ in range(n_scans):
            next(self._scan_iterator)

    ######################################
    #    LECTURE DE SCANS
    ######################################

    def read_scan(self):
        """
        Lit un seul scan via l'itérateur interne.
        """
        if self._scan_iterator is None:
            raise RuntimeError("LIDAR non démarré. Appelez start() avant read_scan().")

        try:
            raw_scan = next(self._scan_iterator)

        except StopIteration:
            # L'itérateur interne s'est fermé : on relance proprement le scan
            self.lidar.stop()
            self.lidar.clean_input()
            self.lidar.start()

            self._scan_iterator = self.lidar.iter_scans(
                max_buf_meas=self._max_buf_meas,
                min_len=self._min_len
            )

            raw_scan = next(self._scan_iterator)

        filtered_scan = self.filter_scan(raw_scan)
        points = self.polar_to_cartesian(filtered_scan)

        return time.time(), filtered_scan, points

    def iter_scans(self, skip=None):
        """
        Crée un générateur de scans à partir de read_scan().

        Arguments:
        - skip: nombre de scans à sauter entre deux retours

        Yields:
        - timestamp: horodatage Unix du scan
        - filtered_scan: scan filtré [(quality, angle, distance), ...]
        - points: coordonnées cartésiennes [(x, y), ...]
        """
        effective_skip = self.scan_skip if skip is None else max(1, skip)

        idx = 0
        while True:
            timestamp, filtered_scan, points = self.read_scan()
            idx += 1

            if idx % effective_skip != 0:
                continue

            yield timestamp, filtered_scan, points

    ######################################
    #    FILTRAGE DES POINTS DU SCAN
    ######################################

    def filter_range(self, scan):
        """
        Filtre les points du scan en fonction de la range de distance définie.
        """
        scan_copy = scan.copy() 
        for mesure in scan:
            if mesure[2] < self.min_range or mesure[2] > self.max_range:
                scan_copy.remove(mesure)
        return scan_copy

        
    def filter_quality(self, scan):
        """
        Filtre les points du scan en ne conservant que ceux dont la qualité dépasse le seuil défini.
        """
        scan_copy = scan.copy()
        for mesure in scan:
            if mesure[0] < self.quality_threshold:
                scan_copy.remove(mesure)
        return scan_copy

    def filter_angle(self, scan):
        """
        Filtre les points du scan en fonction de la plage d'angle définie.
        """
        scan_copy = scan.copy()
        for mesure in scan:
            if mesure[1] < self.min_angle or mesure[1] > self.max_angle:
                scan_copy.remove(mesure)
        return scan_copy

    def filter_scan(self, scan):
        """
        Filtre les points du scan selon la qualité, la plage d'angle et la range de distance
        """
        filtered = self.filter_quality(scan)
        #filtered = self.filter_angle(filtered)
        #filtered = self.filter_range(filtered)
        return filtered

    ######################################
    #    CONVERSION POLAIRE => CARTESIEN
    ######################################
    
    def polar_to_cartesian(self, scan):
        """
        Convertit les coordonnées polaires (angle, distance) en coordonnées cartésiennes (x, y).
        """
        
        mesures = []
        for mesure in scan:
            angle_rad = math.radians(mesure[1])  # Convertir l'angle en radians
            distance_mm = mesure[2]  # Distance en mm
            x = distance_mm * math.cos(angle_rad)
            y = distance_mm * math.sin(angle_rad)
            mesures.append((x, y))
        
        # A COMPLETER/MODIFIER
        return mesures

    ######################################
    #    AFFICHAGE
    ######################################

    def print_scan(self, scan):
        """
        Affichage console simple d'un scan.
        """
        print("Mesures :")
        for measurement in scan:
            print(measurement)
        print(f"Le scan contient {len(scan)} mesures")

    def print_points(self, points):
        """
        Affichage console simple des coordonnées cartésiennes.
        """
        print("\nCoordonnées des points dans le plan cartésien :")
        for x, y in points:
            print(f"({x}, {y})")
            
    ######################################
    #    SAUVEGARDE
    ######################################

    def save_scan(self, points, file_path):
        """
        Sauvegarde un nuage de point LiDAR sur disque.

        Parameters
        ----------
        points : numpy.ndarray
            Nuage de points à sauvegarder.
        file_path : str
            Chemin du fichier.
        """
        file = CSVHandler(file_path)
        file.create_csv_with_header(['x','y'])
        for x,y in points:
            file.append_row([x,y])
        

    def save_scan_sequence(self, scan, directory, index, prefix="scan"):
        """
        Sauvegarde un scan dans une séquence de scans numérotées.

        Parameters
        ----------
        scan : numpy.ndarray
            Nuage de point à sauvegarder.
        directory : str | Path
            Répertoire dans lequel enregistrer le scan.
        index : int
            Indice du scan dans la séquence.
        prefix : str
            Préfixe du nom de fichier.

        Returns
        -------
        str
            Chemin du fichier sauvegardé.
        """
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)

        file_name = f"{prefix}_{index:06d}.csv"
        file_path = str(directory / file_name)

        return self.save_scan(scan, file_path)