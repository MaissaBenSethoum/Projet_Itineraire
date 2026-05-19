from pathlib import Path
import argparse
import cv2

from sensors.CAMERA import Camera
from core.calibration import detect_checkerboard
from core.display import show_frame
from utils import create_acquisition_directory
from config import DIM_GRID, DISPLAY_SIZE


def main(output_root, size=None):
    print("Initialisation de la caméra...")
    camera = Camera()
    camera.configure()
    camera.start()
    camera.warmup()

    session_dir, subdirs = create_acquisition_directory(
        root_dir=output_root,
        prefix="calibration",
        subdirs=["images"]
    )
    images_dir = subdirs["images"]

    saved_count = 0

    print(f"Dossier de sauvegarde : {images_dir}")
    print("Présentez le damier devant la caméra.")
    print("Appuyez sur 'c' pour capturer une image candidate.")
    print("Puis :")
    print("  - 's' pour sauvegarder")
    print("  - 'n' pour ignorer")
    print("  - 'q' pour quitter")

    try:
        while True:
            # Mode flux normal : pas de détection du damier
            frame = camera.capture_frame()

            live_lines = [
                f"Saved images: {saved_count}",
                "Press 'c' to capture candidate image",
                "Press 'q' to quit"
            ]

            show_frame(
              frame,
              window_name="Calibration capture",
              exit_key=None,
              extra_lines=live_lines,
              size=size
            )

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break

            if key == ord("c"):
                # Capture d'une image candidate
                candidate_frame = frame.copy()

                # Détection du damier uniquement ici
                found, corners = detect_checkerboard(candidate_frame, DIM_GRID)

                candidate_display = candidate_frame.copy()
                if found:
                    cv2.drawChessboardCorners(
                        candidate_display,
                        DIM_GRID,
                        corners,
                        found
                    )

                candidate_lines = [
                    f"Corners detected: {'YES' if found else 'NO'}",
                    f"Saved images: {saved_count}",
                    "Press 's' to save, 'n' to skip, 'q' to quit"
                ]

                # Boucle sur l'image candidate figée
                while True:
                    if show_frame(
                        candidate_display,
                        window_name="Calibration capture",
                        exit_key=None,
                        extra_lines=candidate_lines,
                        size=size
                    ):
                        break

                    candidate_key = cv2.waitKey(1) & 0xFF

                    if candidate_key == ord("q"):
                        return

                    if candidate_key == ord("n"):
                        print("Image ignorée.")
                        break

                    if candidate_key == ord("s"):
                        if found:
                            file_path = camera.save_frame_sequence(
                                frame=candidate_frame,
                                directory=images_dir,
                                index=saved_count,
                                prefix="calib",
                                extension="jpg"
                            )
                            saved_count += 1
                            print(f"Image sauvegardée : {file_path}")
                        else:
                            print("Damier non détecté : image non sauvegardée.")
                        break

    finally:
        cv2.destroyAllWindows()
        camera.stop()
        print("Ressources libérées.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Capture semi-automatique d'images de calibration."
    )

    parser.add_argument(
        "--output-root",
        type=str,
        default="data",
        help="Répertoire racine pour enregistrer les images de calibration."
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
        output_root=Path(args.output_root),
        size=display_size
    )