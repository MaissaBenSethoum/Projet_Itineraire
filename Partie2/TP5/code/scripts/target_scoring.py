import cv2
import argparse
import math

from sensors.CAMERA import Camera
from core.detection import detect_target_circle, detect_green_marker
from core.drawing import (
    draw_target_circle,
    draw_marker_center,
    draw_target_marker_link,
)
from core.display import show_frame
from core.calibration import load_calibration, undistort_image
from config import TARGET_DIAMETER_CM, DISPLAY_SIZE



def main(calibration_file, size=None):
    print("Initialisation de la caméra...")
    camera = Camera()
    camera.configure()
    camera.start()
    camera.warmup()

    # A COMPLETER
    # Chargement de la calibration
    calibration_data = load_calibration(calibration_file)

    print("Affichage du flux avec détection de la cible.")
    print("Appuyer sur 'q' pour quitter.")

    try:
        while True:
            frame = camera.capture_frame()

            # A COMPLETER
            # Correction de l'image via la calibration
            frame = undistort_image(frame,calibration_data)

            display = frame.copy()
            infos_to_display = [] # Texte que vous voulez afficher sur la fenêtre, sous forme de liste de chaînes de caractères
            
            # A COMPLETER
            # Détection du cercle extérieur de la cible
            target_circle = detect_target_circle(frame)

            # Détection du marker vert
            marker_center = detect_green_marker(frame)

            # Tracé du cercle sur l'image display
            if target_circle is not None:
                draw_target_circle(display, target_circle)

            # Tracé du centre du marker vert sur l'image display
            if marker_center is not None:
                draw_marker_center(display, marker_center)
            
            if target_circle is not None and marker_center is not None:
                (cx, cy, radius) = target_circle
                (mx, my) = marker_center

                # Tracer la liaison
                draw_target_marker_link(display, (cx, cy), (mx, my))

                # Calcul de la distance en pixel des deux points d'intérêts
                distance_px = math.hypot(mx - cx, my - cy)
                
                # Conversion pixel -> cm
                pixels_per_cm = (2 * radius) / TARGET_DIAMETER_CM

                # Calcul de la distance en cm des deux points d'intérêts
                distance_cm = distance_px / pixels_per_cm
                
                # Calcul du score obtenu (plus on est proche du centre, meilleur score)
                # Exemple simple : score sur 10
                score = max(0, 10 * (1 - distance_px / radius))

                infos_to_display.append(f"Distance: {distance_cm:.2f} cm")
                infos_to_display.append(f"Score: {score:.2f}")

            else:
                infos_to_display.append("Cible ou marker non detecte")

            if show_frame(
                display,
                "Target detection",
                exit_key="q",
                extra_lines=infos_to_display,
                size=size
            ):
                break

    finally:
        cv2.destroyAllWindows()
        camera.stop()
        print("Ressources liberees.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Détection de cible et calcul de score."
    )

    parser.add_argument("calibration_file", type=str, help="Fichier de calibration.")

    parser.add_argument(
        "--size",
        type=int,
        nargs=2,
        metavar=("WIDTH", "HEIGHT"),
        help="Taille de la fenêtre d'affichage (ex: --size 640 480)"
    )

    args = parser.parse_args()

    display_size = tuple(args.size) if args.size is not None else DISPLAY_SIZE

    main(args.calibration_file, size=display_size)
