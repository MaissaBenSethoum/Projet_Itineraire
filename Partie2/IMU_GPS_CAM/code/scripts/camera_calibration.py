from pathlib import Path
import argparse

from core.calibration import calibrate_camera_from_images, save_calibration
from config import DIM_GRID, SQUARE_SIZE


def main(images_dir, output_file, show_corners, checkpoint):
    images_dir = Path(images_dir)

    image_paths = sorted(images_dir.glob("*.jpg"))
    image_paths += sorted(images_dir.glob("*.png"))

    if not image_paths:
        raise RuntimeError(f"Aucune image trouvée dans : {images_dir}")

    calibration = calibrate_camera_from_images(
        image_paths=image_paths,
        checkerboard_size=DIM_GRID,
        square_size=SQUARE_SIZE,
        show_corners=show_corners,
        checkpoint=checkpoint
    )

    if calibration != {}:
        print("\n=== Résultats de calibration ===")
        print(f"Images valides : {len(calibration['valid_images'])}")
        print(f"Erreur RMS    : {calibration['rms_error']:.6f}")
        print("Matrice caméra :")
        print(calibration["camera_matrix"])
        print("Coefficients de distorsion :")
        print(calibration["dist_coeffs"])

        save_calibration(calibration, output_file)
        print(f"\nCalibration sauvegardée dans : {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Calibration d'une caméra à partir d'images d'un damier."
    )

    parser.add_argument(
        "images_dir",
        type=str,
        help="Dossier contenant les images de calibration."
    )

    parser.add_argument(
        "--output",
        type=str,
        default="camera_calibration.npz",
        help="Fichier de sortie .npz"
    )

    parser.add_argument(
        "--show-corners",
        action="store_true",
        help="Affiche les coins détectés."
    )

    parser.add_argument(
        "--checkpoint",
        type=int,
        default=0,
        choices=[0, 1, 2, 3, 4],
        help=(
            "Mode pédagogique :\n"
            "0 = mode normal\n"
            "1 = étape 1\n"
            "2 = étape 2\n"
            "3 = étape 3\n"
            "4 = étape 4 complète avec affichage"
        )
    )

    args = parser.parse_args()

    main(
        images_dir=args.images_dir,
        output_file=str(Path(args.images_dir) / args.output),
        show_corners=args.show_corners,
        checkpoint=args.checkpoint
    )