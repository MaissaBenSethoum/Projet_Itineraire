import cv2
import argparse

from sensors.CAMERA import Camera
from core.calibration import load_calibration, undistort_image
from core.detection import detect_lines
from core.drawing import draw_lines
from config import DISPLAY_SIZE


def main(calibration_file, show_lines=False, size=None):
    print("Chargement de la calibration...")
    calibration = load_calibration(calibration_file)

    print("Initialisation de la caméra...")
    camera = Camera()
    camera.configure()
    camera.start()
    camera.warmup()

    print("Appuyer sur 'q' pour quitter.")

    try:
        while True:
            frame = camera.capture_frame()

            # Correction de la distorsion
            undistorted = undistort_image(frame, calibration, crop=False)

            display_original = frame.copy()
            display_undistorted = undistorted.copy()

            if show_lines:
                lines_original = detect_lines(display_original)
                lines_undistorted = detect_lines(display_undistorted)

                draw_lines(display_original, lines_original)
                draw_lines(display_undistorted, lines_undistorted)

            # Harmonisation des tailles
            h1, w1 = display_original.shape[:2]
            h2, w2 = display_undistorted.shape[:2]

            if h1 != h2 or w1 != w2:
                display_undistorted = cv2.resize(display_undistorted, (w1, h1))

            # Labels
            cv2.putText(display_original, "Original", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            cv2.putText(display_undistorted, "Undistorted", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            # Concaténation verticale
            combined = cv2.vconcat([display_original, display_undistorted])

            # Resize global
            if size is not None:
                combined = cv2.resize(combined, size)

            cv2.imshow("Undistortion comparison", combined)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break

    finally:
        cv2.destroyAllWindows()
        camera.stop()
        print("Ressources libérées.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Démonstration de la correction de distorsion grâce à la calibration."
    )

    parser.add_argument("calibration_file", type=str, help="Fichier de calibration.")

    parser.add_argument(
        "--show-lines",
        action="store_true",
        help="Affiche la détection de lignes (Hough)"
    )

    parser.add_argument(
        "--size",
        type=int,
        nargs=2,
        metavar=("WIDTH", "HEIGHT"),
        help="Taille d'affichage d'une image unique (ex: --size 640 480)"
    )

    args = parser.parse_args()

    if args.size is not None:
        single_display_size = tuple(args.size)
    else:
        single_display_size = DISPLAY_SIZE

    # Taille finale adaptée au vconcat
    display_size = (single_display_size[0], 2 * single_display_size[1])

    main(
        calibration_file=args.calibration_file,
        show_lines=args.show_lines,
        size=display_size
    )