import cv2
import argparse
import math

from sensors.CAMERA import Camera
from core.calibration import load_calibration, undistort_image
from core.detection import detect_target_circle, detect_green_marker
from core.drawing import (
    draw_target_circle,
    draw_marker_center,
    draw_target_marker_link,
)
from config import TARGET_DIAMETER_CM, DISPLAY_SIZE
from core.display import show_frame


def main(calibration_file, size=None):
    print("Initialisation de la caméra...")
    camera = Camera()
    camera.configure()
    camera.start()
    camera.warmup()

    # Chargement de la calibration
    calibration = load_calibration(calibration_file)

    print("Affichage du flux avec détection de la cible.")
    print("Appuyer sur 'q' pour quitter.")

    try:
        while True:
            frame = camera.capture_frame()

            # Correction de la distorsion
            frame = undistort_image(frame, calibration, crop=False)


            # Détection du cercle extérieur de la cible
            circle = detect_target_circle(frame)

            # Détection du marker vert
            marker_center, green_mask = detect_green_marker(frame)

            display = frame.copy()

            target_center = None
            infos_to_display = []

            if circle is not None:
                cx, cy, r = circle
                target_center = (cx, cy)

                draw_target_circle(display, circle)

                target_info = f"Target center: ({cx}, {cy})"
            else:
                target_info = "Target not detected"

            infos_to_display.append(target_info)

            if marker_center is not None:
                mx, my = marker_center

                draw_marker_center(display, marker_center)

                marker_info = f"Marker center: ({mx}, {my})"
            else:
                marker_info = "Marker not detected"

            infos_to_display.append(marker_info)

            if target_center is not None and marker_center is not None:
                cx, cy = target_center
                mx, my = marker_center

                distance_px = math.sqrt((mx - cx) ** 2 + (my - cy) ** 2)

                cm_per_pixel = TARGET_DIAMETER_CM / (2 * r)
                distance_cm = distance_px * cm_per_pixel

                score = max(0, 10 - distance_cm // (TARGET_DIAMETER_CM / 20))

                draw_target_marker_link(display, target_center, marker_center)

                infos_to_display.append(
                    f"Distance: {distance_px:.1f} px - {distance_cm:.1f} cm"
                )
                infos_to_display.append(f"Score : {int(score)} pts")

            infos_to_display.append("Appuyer sur 'q' pour quitter.")

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
    main(size=display_size)