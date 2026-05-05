import shutil
import argparse
from pathlib import Path
from utils import CSVHandler

def read_timestamp_csv(csv_path):
    """
    Lit un CSV de timestamps au format :
    timestamp, chemin

    Returns
    -------
    list[dict]
        Liste de dictionnaires :
        - "timestamp"
        - "path"
    """
    rows = CSVHandler(str(csv_path)).read_dict_rows()
    entries = []

    for row in rows:
        try:
            keys = list(row.keys())
            if len(keys) < 2:
                continue

            timestamp = float(row[keys[0]])
            path = row[keys[1]]

            entries.append({
                "timestamp": timestamp,
                "path": path,
            })

        except (ValueError, TypeError):
            continue

    return entries


def create_output_directory(raw_acquisition_dir, suffix="_synced"):
    """
    Crée le dossier de sortie de la synchro offline.
    """
    raw_acquisition_dir = Path(raw_acquisition_dir)
    output_dir = raw_acquisition_dir.parent / f"{raw_acquisition_dir.name}{suffix}"

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "images").mkdir(exist_ok=True)
    (output_dir / "scans").mkdir(exist_ok=True)

    parameters_file = raw_acquisition_dir / "parameters.py"
    if parameters_file.exists():
        shutil.copy2(parameters_file, output_dir / "parameters.py")

    return output_dir


def synchronize_offline(raw_acquisition_dir, threshold=0.10, suffix="_synced"):
    """
    Calcule les paires caméra/LiDAR synchronisées à partir d'une acquisition brute
    et les enregistre dans un nouveau dossier.

    Parameters
    ----------
    raw_acquisition_dir : str | Path
        Dossier de l'acquisition brute.
    threshold : float
        Seuil maximal |t_cam - t_lidar| en secondes.
    suffix : str
        Suffixe ajouté au nom du dossier de sortie.
    """
    raw_acquisition_dir = Path(raw_acquisition_dir)

    # Lecture des fichiers timestamps de la caméra et du LiDAR
    frames_csv = raw_acquisition_dir / "timestamps_frames.csv"
    scans_csv = raw_acquisition_dir / "timestamps_scans.csv"

    if not frames_csv.exists():
        raise FileNotFoundError(f"Fichier absent : {frames_csv}")
    if not scans_csv.exists():
        raise FileNotFoundError(f"Fichier absent : {scans_csv}")

    frame_entries = read_timestamp_csv(frames_csv)
    scan_entries = read_timestamp_csv(scans_csv)

    if not frame_entries:
        raise RuntimeError("Aucune frame trouvée dans timestamps_frames.csv")
    if not scan_entries:
        raise RuntimeError("Aucun scan trouvé dans timestamps_scans.csv")

    print("Données caméras : [")
    for f in frame_entries:
        print(f)
    print(']')
    print("Données LiDAR : [")
    for s in scan_entries:
        print(s)
    print(']')
    
    # Création du dossier d'acquisition syncrhonisée
    output_dir = create_output_directory(raw_acquisition_dir, suffix=suffix)
    output_images_dir = output_dir / "images"
    output_scans_dir = output_dir / "scans"

    # Création du fichier CSV indiquant les appariements réalisés
    synced_csv_path = output_dir / "synced_cam_lidar.csv"
    synced_csv = CSVHandler(str(synced_csv_path))
    # Header du CSV :
    # - pair_id : Identifiant de la paire
    # - frame_id : Identifiant de l'image dans le dossier d'acquisition brut (frame_xxxxxx.jpg)
    # - t_frame : Timestamp de l'image
    # - scan_id : Identifiant du scan dans le dossier d'acquisition brut (scan_xxxxxx.csv)
    # - t_scan : Timestamp du scan
    # - dt_s : Différence absolue entre les deux timestamps
    # - image_file : Chemin du fichier image    
    # - scan_file : Chemin du fichier scan

    synced_csv.create_csv_with_header([
        "pair_id",
        "frame_id",
        "t_camera",
        "scan_id",
        "t_lidar",
        "dt_s",
        "image_file",
        "scan_file",
    ])

    synced_count = 0
    used_scan_indices = set()

    for frame_id, frame_entry in enumerate(frame_entries):
        # A COMPLETER
        # Récupération du timestamp de l'image
        ...

        # Recherche du scan avec le timestamp le plus proche
        ...

        # Récupération du timestamp du scan le plus proche temporellement
        ...
        
        # Calcul de la différence absolue entre les deux timestamps
        ...

        # Sélection de la paire si la différence de temps est inférieure à un seuil prédéfini
        if ...: # Condition pour éliminer une paire
            continue

        # Récupération de l'index du scan le plus proche (dans le dossier d'acquisition)
        ...

        # Sélection de la paire si le scan appairé n'a pas déjà été précédemment utilisé
        if ...: # Condition pour éliminer une paire
            continue

        # Ajout de l'identifiant du scan dans le set des scans déjà utilisés
        ...

        # Copie des fichiers images et scans dans le dossier d'acquisition synchronisé 
        # ATTENTION : l'identifiant des nouveaux fichiers est différents des identifiants dans l'acquisition brute
        ...

        # Ecriture de la paire dans le fichier d'appariement CSV
        ...

        synced_count += 1

    print(f"Dossier brut        : {raw_acquisition_dir}")
    print(f"Dossier synchronisé : {output_dir}")
    print(f"Seuil utilisé       : {threshold * 1000:.1f} ms")
    print(f"Paires conservées   : {synced_count}")


def main(raw_acquisition_dir, threshold, suffix):
    synchronize_offline(
        raw_acquisition_dir=raw_acquisition_dir,
        threshold=threshold,
        suffix=suffix,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Synchronisation offline caméra / LiDAR à partir d'une acquisition brute."
    )

    parser.add_argument(
        "raw_acquisition_dir",
        type=str,
        help="Dossier de l'acquisition brute."
    )

    parser.add_argument(
        "--threshold",
        type=float,
        default=0.10,
        help="Seuil maximal |t_cam - t_lidar| en secondes (défaut: 0.10)."
    )

    parser.add_argument(
        "--suffix",
        type=str,
        default="_synced",
        help="Suffixe du dossier de sortie (défaut: _synced)."
    )

    args = parser.parse_args()

    main(
        raw_acquisition_dir=args.raw_acquisition_dir,
        threshold=args.threshold,
        suffix=args.suffix,
    )