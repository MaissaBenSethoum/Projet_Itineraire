import time
import argparse
from pathlib import Path
import threading
import cv2
import mediapipe as mp

# Imports de la partie Caméra
from sensors.CAMERA import Camera
from utils import Button, LED
from config import (
    PORT_BUTTON, PORT_LED, DISPLAY_SIZE,
    LSM6DSO_ADDR, ACCEL_RANGE, ACCEL_FREQ,
    GYRO_RANGE, GYRO_FREQ, GNSS_DEVICE_ADDR,
    GNSS_MODES, MODE_GNSS, MAGNETO_RANGE, MAGNETO_FREQ, MAG_ADDR
)
from core.display import show_frame

# Imports de la partie IMU / GNSS
from core.imu_gps_acquisition import get_imu_gps_data, get_imu_gps_long_lat

# Dossier de sauvegarde des images
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
    # Initialisation des périphériques d'interface
    button = Button(PORT_BUTTON)
    led = LED(PORT_LED)
    
    # -------------------------------------------------------------
    # ÉTAPE 1 : Attente du premier appui sur le bouton pour démarrer
    # -------------------------------------------------------------
    print("Programme prêt. Appuyez sur le bouton pour démarrer le système...")
    led.off()
    button.wait_for_press()
    button.wait_for_release()
    time.sleep(0.5)
    
    print("\n--- SYSTÈME DÉMARRÉ ---")
    led.on()

    # Initialisation de la caméra
    print("Initialisation de la caméra...")
    camera = Camera()
    camera.configure()
    camera.start()
    camera.warmup()

    SAVE_DIR.mkdir(exist_ok=True)
    index = 0
    cooldown_time = 0 

    # Variables de contrôle pour l'arrêt des deux systèmes
    running = True
    acquisition_stoppee = [False]

    def stop_condition():
        return acquisition_stoppee[0] or not running

    def demander_arret():
        nonlocal running
        print("\n[Bouton] Demande d'arrêt détectée...")
        acquisition_stoppee[0] = True
        running = False

    # On configure l'action du bouton : s'il est ré-appuyé, il déclenche l'arrêt
    button.on_press(demander_arret)

    # -------------------------------------------------------------
    # ÉTAPE 2 : Lancement de l'acquisition IMU + GPS en arrière-plan
    # -------------------------------------------------------------
    csv_name = f"data/acq_{ACCEL_RANGE}_{ACCEL_FREQ}_{GYRO_RANGE}_{GYRO_FREQ}.csv"
    
    imu_gps_thread = threading.Thread(
        target=get_imu_gps_data,
        kwargs={
            "XL_addr": LSM6DSO_ADDR,
            "MAG_addr" : MAG_ADDR,
            "accel_range": ACCEL_RANGE,
            "accel_freq": ACCEL_FREQ,
            "gyro_range": GYRO_RANGE,
            "gyro_freq": GYRO_FREQ,
            "gnss_addr": GNSS_DEVICE_ADDR,
            "gnss_mode": GNSS_MODES[MODE_GNSS],
            "magneto_range" : MAGNETO_RANGE,
            "magneto_freq" : MAGNETO_FREQ,
            "csv_out": csv_name,
            "stop_condition": stop_condition
        },
        daemon=True # Permet au thread de se couper si le script principal meurt brutalement
    )
    imu_gps_thread.start()

    print("Faites le signe 'Victory' (V) pour prendre une photo.")
    print("Appuyez sur le bouton ou faites Ctrl+C / 'q' pour quitter.")

    # -------------------------------------------------------------
    # ÉTAPE 3 : Boucle principale (Caméra + Reconnaissance de la main)
    # -------------------------------------------------------------
    try:
        while running:
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
                    "Bouton ou 'q' pour quitter et enregistrer"
                ]
                if show_frame(
                    display_frame,
                    window_name="Flux Continu",
                    exit_key="q",
                    extra_lines=infos,
                    size=size
                ):
                    running = False
                    acquisition_stoppee[0] = True
                    break

            # 4. Déclenchement de la photo (Geste détecté + Cooldown vérifié)
            # Note : On a retiré button.is_pressed() ici pour que le bouton serve exclusivement à l'arrêt.
            if gesture_detected and time.time() > cooldown_time:
                print(f"Geste détecté ! Capture de la photo {index}...")
                
                # Petit effet visuel avec la LED pour la capture
                led.off() 
                time.sleep(0.1)
                led.on()
    
                latitude = 0
                longitude = 0
                
                latitude, longitude = get_imu_gps_long_lat(
                    XL_addr=LSM6DSO_ADDR,
                    MAG_addr=MAG_ADDR,
                    accel_range=ACCEL_RANGE,
                    accel_freq=ACCEL_FREQ,
                    gyro_range=GYRO_RANGE,
                    gyro_freq=GYRO_FREQ,
                    magneto_range=MAGNETO_RANGE,
                    magneto_freq=MAGNETO_FREQ,
                    gnss_addr=GNSS_DEVICE_ADDR,
                    gnss_mode=GNSS_MODES[MODE_GNSS]
                    )
                
                # Sauvegarde de l'image propre
                filename = SAVE_DIR / f"image_{latitude}_{longitude}.jpg"
                camera.save_frame(frame, str(filename))
                
                # --- EFFET APPAREIL PHOTO (FIGER L'IMAGE) ---
                if show_stream:
                    print("Affichage du rendu (3 secondes)...")
                    freeze_duration = 3.0
                    freeze_until = time.time() + freeze_duration
                    
                    while time.time() < freeze_until and running:
                        show_frame(
                            frame, 
                            window_name="Flux Continu",
                            extra_lines=[f"Photo {index} enregistree !", "Apercu..."],
                            size=size
                        )
                        time.sleep(0.1)
                # ---------------------------------------------

                cooldown_time = time.time() + 5.0
                index += 1

            time.sleep(0.01)

    except KeyboardInterrupt:
        print("\n[KeyboardInterrupt] Arrêt demandé via le terminal.")
        running = False
        acquisition_stoppee[0] = True

    # -------------------------------------------------------------
    # ÉTAPE 4 : Nettoyage et fermeture des périphériques
    # -------------------------------------------------------------
    finally:
        print("\nFermeture du système, veuillez patienter...")
        running = False
        acquisition_stoppee[0] = True
        
        # Attendre que le thread IMU/GPS se termine proprement
        if imu_gps_thread.is_alive():
            imu_gps_thread.join(timeout=2.0)
            
        led.off()
        camera.stop()
        button.cleanup()
        led.cleanup()
        hands.close()
        print("Tous les capteurs sont libérés. Données sauvegardées.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Système embarqué : Photo par geste & Acquisition IMU/GNSS")
    parser.add_argument("--show-stream", action="store_true", default=True, help="Affiche le flux caméra.")
    parser.add_argument("--size", type=int, nargs=2, metavar=("WIDTH", "HEIGHT"), help="Taille de la fenêtre")

    args = parser.parse_args()
    display_size = tuple(args.size) if args.size is not None else DISPLAY_SIZE

    main(show_stream=args.show_stream, size=display_size)
