import time
import argparse
from pathlib import Path

from sensors.CAMERA import Camera
from utils import Button, LED
from config import PORT_BUTTON, PORT_LED, DISPLAY_SIZE
from core.display import show_frame


# Dossier de sauvegarde
SAVE_DIR = Path("images")


def main(show_stream=True, size=None):
    print("Initialisation de la caméra...")

    camera = Camera()
    camera.configure()
    camera.start()
    camera.warmup()

    print("Initialisation du bouton...")
    button = Button(PORT_BUTTON)
    led = LED(PORT_LED)

    # Création du dossier de sauvegarde
    SAVE_DIR.mkdir(exist_ok=True)

    index = 0

    print("Appuyer sur le bouton pour prendre une photo.")
    print("Ctrl+C pour quitter.")

    try:
        while True:
            # Capture de l'image
            frame = camera.capture_frame()

            if show_stream:
                infos = [
                    f"Photo index: {index}",
                    "Appuyer sur le bouton pour capturer",
                    "Appuyer sur 'q' pour quitter"
                ]

                if show_frame(
                    frame,
                    window_name="Frame",
                    exit_key="q",
                    extra_lines=infos,
                    size=size
                ):
                    break

            # A COMPLETER
            # Attente que le bouton soit pressé
            # Lorsque le bouton est pressé :
            # - Allumage de la LED
            # - Sauvegarde de l'image (avec nom de fichier à créer)
            # - Affichage de l'image (show_frame dans core/display.py) si l'option show_image est vrai
            if button.is_pressed():
                led.on()
                frame = camera.capture_frame()
                filename = SAVE_DIR / f"image_{index:06d}.jpg"
                camera.save_frame(frame, str(filename))
                led.off()
                show_frame(frame, window_name="Photo")
                button.wait_for_release()
                time.sleep(0.05)
                index += 1


    except KeyboardInterrupt:
        print("\nArrêt du programme.")

    finally:
        led.off()
        camera.stop()
        button.cleanup()
        print("Ressources libérées.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enregistrement d'images avec la caméra.")

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
        show_stream=args.show_stream,
        size=display_size
    )
