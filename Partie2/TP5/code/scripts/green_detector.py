import cv2
import argparse

from sensors.CAMERA import Camera
from core.detection import detect_green_marker
from core.drawing import draw_marker_center
from core.display import show_frame
from config import DISPLAY_SIZE


def main(size=None):
    print("Initialisation de la caméra...")
    camera = Camera()
    camera.configure()
    camera.start()
    camera.warmup()

    print("Appuyer sur 'q' pour quitter.")

    try:
        while True:
            frame = camera.capture_frame()

            marker_center, green_mask = detect_green_marker(frame)

            display = frame.copy()
            infos = []

            if marker_center is not None:
                draw_marker_center(display, marker_center)
                mx, my = marker_center
                infos.append(f"Marker: ({mx}, {my})")
            else:
                infos.append("No green marker detected")

            infos.append("Appuyer sur 'q' pour quitter.")

            # Affichage principal via show_frame
            if show_frame(
                display,
                window_name="Green marker detection",
                exit_key="q",
                extra_lines=infos,
                size=size
            ):
                break

            # Affichage du masque (indépendant)
            if size is not None:
                mask_display = cv2.resize(green_mask, size)
            else:
                mask_display = green_mask

            cv2.imshow("Green mask", mask_display)

    finally:
        cv2.destroyAllWindows()
        camera.stop()
        print("Ressources liberees.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Détection du marker vert.")

    parser.add_argument(
        "--size",
        type=int,
        nargs=2,
        metavar=("WIDTH", "HEIGHT"),
        help="Taille de la fenêtre d'affichage (ex: --size 640 480)"
    )

    args = parser.parse_args()

    display_size = tuple(args.size) if args.size is not None else DISPLAY_SIZE

    main(size=display_size)