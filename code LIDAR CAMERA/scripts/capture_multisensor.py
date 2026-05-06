import time
import shutil
import argparse
import traceback
import threading
from pathlib import Path
from core.calibration import load_calibration, undistort_image
from sensors.CAMERA import Camera
from sensors.LIDAR import LIDAR
from utils import Button, LED, create_acquisition_directory, CSVHandler
from config import (
    PORT_BUTTON,
    PORT_LED,
    ACQUISITION_ROOT,
    PORT_LIDAR,
    QUALITY_THRESHOLD,
    MIN_DETECTION_ANGLE,
    MAX_DETECTION_ANGLE,
    MIN_DETECTION_RANGE,
    MAX_DETECTION_RANGE,
)


ACQUISITION_PATH = Path(ACQUISITION_ROOT)


def start_acquisition(state, led):
    """
    Lance une acquisition multisenseur :
    - création du dossier session
    - création des sous-dossiers images / scans
    - création des CSV de timestamps
    """
    session_dir, subdirs = create_acquisition_directory(
        root_dir=ACQUISITION_ROOT,
        prefix="acquisition",
        subdirs=["images", "scans"]
    )

    state["is_acquiring"] = True
    state["session_dir"] = session_dir
    state["images_dir"] = subdirs["images"]
    state["scans_dir"] = subdirs["scans"]
    state["frame_index"] = 0
    state["scan_index"] = 0

    # A COMPLETER
    # Copie du fichier config/parameters.py dans le dossier d'acquisition
    shutil.copyfile(
        "config/parameters.py",
        str(state["session_dir"] / "parameters.py")
    )

    # Création des fichiers CSV timestamps/frames et timestamps/scans
    csv_file_frames = CSVHandler(str(state["session_dir"] / "timestamps_frames.csv"))
    csv_file_frames.create_csv_with_header(["timestamp", "frames"])
    
    csv_file_scans = CSVHandler(str(state["session_dir"] / "timestamps_scans.csv"))
    csv_file_scans.create_csv_with_header(["timestamp", "scans"])

    # Ajout des CSVHandlers créés dans state (pour y accéder en dehors de la fonction)
    state["csv_frames"] = csv_file_frames
    state["csv_scans"] = csv_file_scans

    led.on()
    print(f"Acquisition démarrée : {session_dir}")


def stop_acquisition(state, led, reason=None):
    """
    Arrête l'acquisition en cours et remet l'état session à zéro.
    """
    if reason is not None:
        print(f"Acquisition interrompue : {reason}")
    elif state["session_dir"] is not None:
        print(f"Acquisition arrêtée : {state['session_dir']}")

    state["is_acquiring"] = False
    state["session_dir"] = None
    state["images_dir"] = None
    state["scans_dir"] = None
    state["frame_index"] = 0
    state["scan_index"] = 0
    state["csv_frames"] = None
    state["csv_scans"] = None

    led.off()


def toggle_acquisition(state, led, lock):
    """
    Démarre ou arrête une acquisition.
    """
    with lock:
        if not state["is_acquiring"]:
            start_acquisition(state, led)
        else:
            stop_acquisition(state, led)


def camera_worker(camera, calibration, state, lock, stop_event, extension="jpg"):
    """
    Thread d'acquisition caméra.
    """
    while not stop_event.is_set():
        try:
            # A COMPLETER
            # Lecture d'une acquisition caméra
            frame = camera.capture_frame()
            
            if calibration is not None:
                # Correction de la distorsion
                frame = undistort_image(frame, calibration)
                
            timestamp = time.time()

            with lock:
                if state["is_acquiring"]:
                    # A COMPLETER
                    # Enregistrement de l'image
                    camera.save_frame_sequence(
                        frame=frame,
                        directory=state["images_dir"],
                        index=state["frame_index"],
                        prefix="frame",
                        extension=extension
                    )

                    # A COMPLETER
                    # Mise à jour du fichier timestamp avec la nouvelle acquisition (timestamp et chemin du fichier)
                    index = state["frame_index"]
                    state["csv_frames"].append_row([
                        timestamp,
                        str(state["images_dir"] / f"frame_{index:06d}.{extension}")
                    ])
                    state["frame_index"] += 1

        except Exception:
            traceback.print_exc()
            with lock:
                state["is_acquiring"] = False
                state["session_dir"] = None
                state["images_dir"] = None
                state["scans_dir"] = None
                state["frame_index"] = 0
                state["scan_index"] = 0
                state["csv_frames"] = None
                state["csv_scans"] = None
            time.sleep(0.1)

        time.sleep(0.01)


def lidar_worker(lidar, state, lock, stop_event):
    """
    Thread d'acquisition LiDAR.
    """
    while not stop_event.is_set():
        try:
            # A COMPLETER
            # Lecture d'une acquisition LiDAR
            timestamp, measures, points = lidar.read_scan()

            with lock:
                if state["is_acquiring"]:
                    # A COMPLETER
                    # Enregistrement de l'acquisition LiDAR
                    chemin = lidar.save_scan_sequence(points,state["scans_dir"],state['scan_index'],"scan_")

                    # A COMPLETER
                    # Mise à jour du fichier timestamp avec la nouvelle acquisition (timestamp et chemin du fichier)s
                    index = state["scan_index"]
                    state["csv_scans"].append_row([
                        timestamp,
                        str(chemin)
                    ])
                    state["scan_index"] += 1

        except Exception:
            traceback.print_exc()
            with lock:
                state["is_acquiring"] = False
                state["session_dir"] = None
                state["images_dir"] = None
                state["scans_dir"] = None
                state["frame_index"] = 0
                state["scan_index"] = 0
                state["csv_frames"] = None
                state["csv_scans"] = None
            time.sleep(0.1)

        time.sleep(0.01)


def main(calibration_file=None):
    print("Initialisation de la caméra...")
    # A COMPLETER
    # Initialisation de la caméra
    camera = Camera()

    # Configuration de la caméra
    camera.configure()

    # Démarrage de la caméra
    camera.start()
    
    # Chauffe de la caméra (warmup)
    camera.warmup()

    
    if calibration_file is not None:
        print("Chargement de la calibration...")
        calibration = load_calibration(calibration_file)
    else:
        calibration = None
    
    
    print("Initialisation du LiDAR...")
    # A COMPLETER
    # Initialisation du LiDAR
    lidar = LIDAR(PORT_LIDAR)

    # Démarrage du LiDAR
    lidar.start()
    
    # Chauffe du LiDAR (warmup)
    lidar.warmup()
    
    print("Initialisation du bouton...")
    button = Button(PORT_BUTTON)
    led = LED(PORT_LED)

    ACQUISITION_PATH.mkdir(parents=True, exist_ok=True)

    state = {
        "is_acquiring": False,
        "session_dir": None,
        "images_dir": None,
        "scans_dir": None,
        "frame_index": 0,
        "scan_index": 0,
        "csv_frames": None,
        "csv_scans": None,
    }

    lock = threading.Lock()
    stop_event = threading.Event()

    camera_thread = threading.Thread(
        target=camera_worker,
        args=(camera, calibration, state, lock, stop_event),
        daemon=True
    )

    lidar_thread = threading.Thread(
        target=lidar_worker,
        args=(lidar, state, lock, stop_event),
        daemon=True
    )

    print("Appuyer sur le bouton pour démarrer / arrêter l'acquisition multisenseur.")
    print("Ctrl+C pour quitter.")

    try:
        camera_thread.start()
        lidar_thread.start()

        while True:
            if button.is_pressed():
                toggle_acquisition(state, led, lock)
                button.wait_for_release()
                time.sleep(0.05)

            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\nArrêt du programme demandé par l'utilisateur.")

    finally:
        stop_event.set()

        camera_thread.join(timeout=1.0)
        lidar_thread.join(timeout=1.0)

        led.off()
        button.cleanup()
        led.cleanup()
        camera.stop()
        lidar.stop()

        print("Ressources libérées.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Acquisition multisenseur caméra + LiDAR."
    )

    parser.add_argument("--calibration_file", type=str, help="Fichier de calibration.")

    args = parser.parse_args()

    main(args.calibration_file)
