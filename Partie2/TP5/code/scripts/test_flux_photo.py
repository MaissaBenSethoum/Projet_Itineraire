import time
import argparse
from pathlib import Path
import cv2
import mediapipe as mp

from sensors.CAMERA import Camera
from utils import Button, LED
from config import PORT_BUTTON, PORT_LED, DISPLAY_SIZE
from core.display import show_frame

# Dossier de sauvegarde
SAVE_DIR = Path("images")

# Initialisation de MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
)
mp_draw = mp.solutions.drawing_utils

def is_victory_gesture(hand_landmarks):
    """Détecte le geste 'Victory' (index et majeur levés)."""
    index_is_open = hand_landmarks.landmark[8].y < hand_landmarks.landmark[6].y
    middle_is_open = hand_landmarks.landmark[12].y < hand_landmarks.landmark[10].y
    ring_is_closed = hand_landmarks.landmark[16].y > hand_landmarks.landmark[14].y
    pinky_is_closed = hand_landmarks.landmark[20].y > hand_landmarks.landmark[18].y

    if index_is_open and middle_is_open and ring_is_closed and pinky_is_closed:
        return True
    return False

def main(show_stream=True, size=None):
    print("Initialisation de la caméra...")
    camera = Camera()
    camera.configure()
    camera.start()
    camera.warmup()

    print("Initialisation des périphériques...")
    led = LED(PORT_LED)
    button = Button(PORT_BUTTON)

    SAVE_DIR.mkdir(exist_ok=True)
    index = 0
    cooldown_time = 0 

    print("Faites le signe 'Victory' (V) pour prendre une photo.")
    print("Ctrl+C ou 'q' pour quitter.")

    try:
        while True:
            # 1. Capture du flux continu
            frame = camera.capture_frame()
            display_frame = frame.copy()

            # 2. Détection MediaPipe
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb_frame)

            gesture_detected = False
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    mp_draw.draw_landmarks(display_frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                    if is_victory_gesture(hand_landmarks):
                        gesture_detected = True

            # 3. Affichage du flux vidéo en continu
            if show_stream:
                infos = [
                    f"Photo index: {index}",
                    "Geste attendu: Victory (V)",
                    "Appuyer sur 'q' pour quitter"
                ]
                if show_frame(
                    display_frame,
                    window_name="Flux Continu",
                    exit_key="q",
                    extra_lines=infos,
                    size=size
                ):
                    break

            # 4. Déclenchement de la photo (Geste détecté + Cooldown vérifié)
            if (gesture_detected or button.is_pressed()) and time.time() > cooldown_time:
                print(f"Geste détecté ! Capture de la photo {index}...")
                led.on()
                
                # Sauvegarde de l'image propre (sans le squelette MediaPipe)
                filename = SAVE_DIR / f"image_{index:06d}.jpg"
                camera.save_frame(frame, str(filename))
                
                led.off()
                
                # --- EFFET APPAREIL PHOTO (FIGER L'IMAGE) ---
                if show_stream:
                    print("Affichage du rendu (3 secondes)...")
                    freeze_duration = 3.0  # Temps pendant lequel la photo reste figée (en secondes)
                    freeze_until = time.time() + freeze_duration
                    
                    # On affiche la photo fixe en boucle pendant 3 secondes
                    while time.time() < freeze_until:
                        # On affiche 'frame' (la photo propre) ou 'display_frame' si tu préférais voir les lignes
                        show_frame(
                            frame, 
                            window_name="Flux Continu",  # Même nom de fenêtre pour remplacer le flux actuel
                            extra_lines=[f"Photo {index} enregistree !", "Apercu..."],
                            size=size
                        )
                        # Une micro-pause pour éviter que la boucle n'utilise 100% du CPU
                        time.sleep(0.1)
                # ---------------------------------------------

                # Configuration du cooldown à 5 secondes pour la prochaine détection
                cooldown_time = time.time() + 5.0
                index += 1

            time.sleep(0.01)

    except KeyboardInterrupt:
        print("\nArrêt du programme.")

    finally:
        led.off()
        camera.stop()
        button.cleanup()
        hands.close()
        print("Ressources libérées.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enregistrement d'images par geste avec la caméra.")
    parser.add_argument("--show-stream", action="store_true", help="Affiche le flux caméra.")
    parser.add_argument("--size", type=int, nargs=2, metavar=("WIDTH", "HEIGHT"), help="Taille de la fenêtre")

    args = parser.parse_args()
    display_size = tuple(args.size) if args.size is not None else DISPLAY_SIZE

    main(show_stream=args.show_stream, size=display_size)