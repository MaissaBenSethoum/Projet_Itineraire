import time
from pathlib import Path
import argparse
import shutil

from sensors.CAMERA import Camera
from utils import Button, LED, create_acquisition_directory, CSVHandler
from core.display import stream_frames
from config import PORT_BUTTON, PORT_LED, ACQUISITION_ROOT, DISPLAY_SIZE
from core.calibration import load_calibration, undistort_image


ACQUISITION_PATH = Path(ACQUISITION_ROOT)


def start_acquisition(state, led):
    """
    Lance l'acquisition
    """
    session_dir, subdirs = create_acquisition_directory(
        root_dir=ACQUISITION_ROOT,
        prefix="acquisition",
        subdirs=["images"]
    )

    state["is_acquiring"] = True
    state["session_dir"] = session_dir
    state["images_dir"] = subdirs["images"]
    state["frame_index"] = 0

    # Copie du fichier config/parameters.py dans votre dossier d'acquisition
    shutil.copyfile(
        "config/parameters.py",
        str(state["session_dir"] / "parameters.py")
    )

    # Création du fichier CSV timestamp/images
    csv_file = CSVHandler(str(state["session_dir"] / "timestamps_frames.csv"))
    csv_file.create_csv_with_header(["timestamp", "frame"])
    state["csv_file"] = csv_file

    led.on()
    print(f"Acquisition démarrée : {session_dir}")


def stop_acquisition(state, led, reason=None):
    """
    Arrête l'acquisition en cours et remet l'état à zéro.
    """
    if reason is not None:
        print(f"Acquisition interrompue : {reason}")
    elif state["session_dir"] is not None:
        print(f"Acquisition arrêtée : {state['session_dir']}")

    state["is_acquiring"] = False
    state["session_dir"] = None
    state["images_dir"] = None
    state["frame_index"] = 0
    state["csv_file"] = None

    led.off()


def toggle_acquisition(state, led):
    """
    Démarre ou arrête une acquisition d'images.
    """
    if not state["is_acquiring"]:
        start_acquisition(state, led)
    else:
        stop_acquisition(state, led)


def acquisition_frames(camera, calibration, button, led, state, extension="jpg"):
    """
    Générateur de frames :
    - gère le bouton
    - démarre / arrête l'acquisition
    - capture la frame
    - sauvegarde si nécessaire
    """
    while True:
        if button.is_pressed():
            toggle_acquisition(state, led)
            button.wait_for_release()
            time.sleep(0.05)

        try:
            frame = camera.capture_frame()
            if calibration is not None:
                frame = undistort_image(frame, calibration)
            timestamp = time.time()

            if state["is_acquiring"]:
                camera.save_frame_sequence(
                    frame=frame,
                    directory=state["images_dir"],
                    index=state["frame_index"],
                    prefix="frame",
                    extension=extension
                )
                # Ecriture du fichier CSV timestamp/images
                index = state["frame_index"]
                state["csv_file"].append_row([
                    timestamp,
                    str(state["images_dir"] / f"frame_{index:06d}.{extension}")
                ])
                state["frame_index"] += 1

        except Exception as error:
            stop_acquisition(state, led, reason=str(error))
            print("Le programme continue. Appuyez sur le bouton pour relancer une acquisition.")
            time.sleep(0.1)
            continue

        yield frame
        time.sleep(0.01)


def make_extra_lines_callback(state):
    """
    Fabrique une fonction de callback pour afficher des informations
    dans l'overlay du flux vidéo.
    """
    def extra_lines_callback(frame):
        lines = []

        if state["is_acquiring"]:
            lines.append("ACQUISITION: ON")
            if state["session_dir"] is not None:
                lines.append(f"Session: {state['session_dir'].name}")
            lines.append(f"Frame index: {state['frame_index']}")
        else:
            lines.append("ACQUISITION: OFF")

        lines.append("Appuyer sur le bouton pour start/stop")
        lines.append("Appuyer sur 'q' pour quitter")

        return lines

    return extra_lines_callback


def main(calibration_file=None, show_stream=True, size=None):
    camera = Camera()
    camera.configure()
    camera.start()
    camera.warmup()

    if calibration_file is not None:
        print("Chargement de la calibration...")
        calibration = load_calibration(calibration_file)
    else:
        calibration = None

    button = Button(PORT_BUTTON)
    led = LED(PORT_LED)

    ACQUISITION_PATH.mkdir(parents=True, exist_ok=True)

    state = {
        "is_acquiring": False,
        "session_dir": None,
        "images_dir": None,
        "frame_index": 0,
        "csv_file": None,
    }

    print("Appuyer sur le bouton pour démarrer / arrêter l'acquisition d'images.")
    print("Ctrl+C pour quitter.")

    try:
        frames = acquisition_frames(camera, calibration, button, led, state, extension="jpg")

        if show_stream:
            stream_frames(
                frames,
                window_name="Camera",
                exit_key="q",
                show_fps=True,
                show_timestamp=True,
                size=size,
                extra_lines_callback=make_extra_lines_callback(state)
            )
        else:
            for _ in frames:
                pass

    except KeyboardInterrupt:
        print("\nArrêt du programme demandé par l'utilisateur.")

    finally:
        led.off()
        button.cleanup()
        led.cleanup()
        camera.stop()
        print("Ressources libérées.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enregistrement d'images avec la caméra.")

    parser.add_argument("--calibration_file", 
                        type=str, 
                        help="Fichier de calibration.")

    parser.add_argument(
        "--show-stream",
        action="store_true",
        help="Affiche le flux caméra dans une fenêtre OpenCV."
    )

    parser.add_argument(
        "--size",
        type=int,
        nargs=2,
        metavar=("WIDTH", "HEIGHT"),
        help="Taille de la fenêtre d'affichage (ex: --size 640 480)"
    )

    args = parser.parse_args()

    display_size = tuple(args.size) if args.size is not None else DISPLAY_SIZE

    main(
        args.calibration_file,
        show_stream=args.show_stream,
        size=display_size
    )