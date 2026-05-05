import csv
import time
import argparse
from pathlib import Path

import cv2
import numpy as np


def read_timestamp_csv(csv_path):
    """
    Lit un fichier CSV de timestamps.

    Format attendu :
    timestamp,filepath
    """
    events = []

    with open(csv_path, "r", newline="") as f:
        reader = csv.reader(f)
        header = next(reader, None)

        for row in reader:
            if len(row) < 2:
                continue

            timestamp = float(row[0])
            filepath = row[1]
            events.append((timestamp, filepath))

    return events


def load_scan_points(scan_path):
    """
    Charge un scan LiDAR depuis un CSV.

    Cette fonction lit un CSV avec header contenant x et y

    Returns
    -------
    list[tuple[float, float]]
        Liste de points (x, y)
    """
    points = []

    with open(scan_path, "r", newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)

    if not rows:
        return points

    data_rows = rows[1:]
    for row in data_rows:
        try:
            x = float(row[0])
            y = float(row[1])
            points.append((x, y))
        except (ValueError, IndexError):
            continue
    return points


def render_lidar_frame(points, max_range=2000, window_size=500, min_range=None):
    """
    Construit une image OpenCV représentant le nuage de points LiDAR.
    """
    scale = (window_size * 0.45) / max_range
    center = window_size // 2

    frame = np.zeros((window_size, window_size, 3), dtype=np.uint8)

    # Axes
    frame[center, :] = (40, 40, 40)
    frame[:, center] = (40, 40, 40)

    # Cercle portée max
    radius_max_px = int(max_range * scale)
    cv2.circle(frame, (center, center), radius_max_px, (80, 80, 80), 1)

    # Cercle portée min
    if min_range is not None and min_range > 0:
        radius_min_px = int(min_range * scale)
        cv2.circle(frame, (center, center), radius_min_px, (60, 60, 60), 1)

    # Centre LiDAR
    cv2.drawMarker(
        frame,
        (center, center),
        (0, 0, 255),
        markerType=cv2.MARKER_CROSS,
        markerSize=12,
        thickness=1
    )

    if points:
        pts = np.array(points, dtype=np.float32)

        px = (center + pts[:, 0] * scale).astype(int)
        py = (center - pts[:, 1] * scale).astype(int)

        valid = (
            (px >= 0) & (px < window_size) &
            (py >= 0) & (py < window_size)
        )

        frame[py[valid], px[valid]] = (255, 255, 255)

    return frame


def draw_text_block(frame, lines, origin=(10, 25), line_height=22, font_scale=0.55):
    """
    Ajoute quelques lignes de texte sur une image.
    """
    x, y = origin
    for i, line in enumerate(lines):
        cv2.putText(
            frame,
            str(line),
            (x, y + i * line_height),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            (255, 255, 255),
            1,
            cv2.LINE_AA
        )


def pad_to_same_height(img1, img2):
    """
    Ajuste deux images pour qu'elles aient la même hauteur.
    """
    h1, w1 = img1.shape[:2]
    h2, w2 = img2.shape[:2]

    target_h = max(h1, h2)

    if h1 != target_h:
        new_w1 = int(w1 * target_h / h1)
        img1 = cv2.resize(img1, (new_w1, target_h))

    if h2 != target_h:
        new_w2 = int(w2 * target_h / h2)
        img2 = cv2.resize(img2, (new_w2, target_h))

    return img1, img2


def replay_acquisition(acquisition_dir,
                       speed=1.0,
                       camera_size=(640, 480),
                       lidar_size=500,
                       lidar_max_range=2000,
                       lidar_min_range=None):
    """
    Rejoue une acquisition multisenseur à partir d'un dossier.
    """
    acquisition_dir = Path(acquisition_dir)

    frames_csv = acquisition_dir / "timestamps_frames.csv"
    scans_csv = acquisition_dir / "timestamps_scans.csv"

    if not frames_csv.exists():
        raise FileNotFoundError(f"Fichier absent : {frames_csv}")
    if not scans_csv.exists():
        raise FileNotFoundError(f"Fichier absent : {scans_csv}")

    frame_events = read_timestamp_csv(frames_csv)
    scan_events = read_timestamp_csv(scans_csv)

    events = []
    for ts, path in frame_events:
        events.append(("frame", ts, Path(path)))
    for ts, path in scan_events:
        events.append(("scan", ts, Path(path)))

    if not events:
        raise RuntimeError("Aucun événement à rejouer.")

    events.sort(key=lambda e: e[1])

    last_camera_frame = np.zeros((camera_size[1], camera_size[0], 3), dtype=np.uint8)
    draw_text_block(last_camera_frame, ["Aucune image encore chargee"])

    last_lidar_frame = render_lidar_frame(
        points=[],
        max_range=lidar_max_range,
        window_size=lidar_size,
        min_range=lidar_min_range
    )
    draw_text_block(last_lidar_frame, ["Aucun scan encore charge"])

    t0_data = events[0][1]
    t0_wall = time.time()

    event_index = 0
    total_events = len(events)

    while event_index < total_events:
        event_type, timestamp_data, filepath = events[event_index]

        elapsed_data = timestamp_data - t0_data
        target_wall = t0_wall + elapsed_data / speed

        now = time.time()
        wait_time = target_wall - now
        if wait_time > 0:
            time.sleep(min(wait_time, 0.01))

        now = time.time()
        if now < target_wall:
            # pas encore l'heure de cet événement
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            continue

        if event_type == "frame":
            image = cv2.imread(str(filepath))
            if image is not None:
                image = cv2.resize(image, camera_size)
                overlay_lines = [
                    f"Camera timestamp: {timestamp_data:.3f}",
                    f"Replay speed: x{speed:.2f}",
                    "Press 'q' to quit"
                ]
                draw_text_block(image, overlay_lines)
                last_camera_frame = image

        elif event_type == "scan":
            points = load_scan_points(filepath)
            lidar_frame = render_lidar_frame(
                points=points,
                max_range=lidar_max_range,
                window_size=lidar_size,
                min_range=lidar_min_range
            )
            overlay_lines = [
                f"LiDAR timestamp: {timestamp_data:.3f}",
                f"Points: {len(points)}",
                f"Replay speed: x{speed:.2f}",
                "Press 'q' to quit"
            ]
            draw_text_block(lidar_frame, overlay_lines)
            last_lidar_frame = lidar_frame

        common_lines = [
            f"Event {event_index + 1}/{total_events}",
            f"t = {timestamp_data - t0_data:.3f} s"
        ]

        cam_display = last_camera_frame.copy()
        draw_text_block(
            cam_display,
            common_lines,
            origin=(10, cam_display.shape[0] - 45),
            line_height=20,
            font_scale=0.5
        )

        lidar_display = last_lidar_frame.copy()
        draw_text_block(
            lidar_display,
            common_lines,
            origin=(10, lidar_display.shape[0] - 45),
            line_height=20,
            font_scale=0.5
        )

        cv2.imshow("Camera", cam_display)
        cv2.imshow("LiDAR", lidar_display)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break

        event_index += 1

    cv2.destroyAllWindows()


def main(acquisition_dir, speed, camera_width, camera_height, lidar_size, lidar_max_range):
    replay_acquisition(
        acquisition_dir=acquisition_dir,
        speed=speed,
        camera_size=(camera_width, camera_height),
        lidar_size=lidar_size,
        lidar_max_range=lidar_max_range,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Replay d'une acquisition multisenseur.")

    parser.add_argument(
        "acquisition_dir",
        type=str,
        help="Dossier de l'acquisition à rejouer."
    )

    parser.add_argument(
        "--speed",
        type=float,
        default=1.0,
        help="Vitesse de replay (ex: 1.0 = temps réel, 2.0 = deux fois plus vite)."
    )

    parser.add_argument(
        "--camera-width",
        type=int,
        default=640,
        help="Largeur d'affichage de la caméra."
    )

    parser.add_argument(
        "--camera-height",
        type=int,
        default=480,
        help="Hauteur d'affichage de la caméra."
    )

    parser.add_argument(
        "--lidar-size",
        type=int,
        default=500,
        help="Taille carrée d'affichage du LiDAR."
    )

    parser.add_argument(
        "--lidar-max-range",
        type=float,
        default=2000,
        help="Portée max utilisée pour l'affichage LiDAR."
    )

    args = parser.parse_args()

    main(
        acquisition_dir=args.acquisition_dir,
        speed=args.speed,
        camera_width=args.camera_width,
        camera_height=args.camera_height,
        lidar_size=args.lidar_size,
        lidar_max_range=args.lidar_max_range,
    )