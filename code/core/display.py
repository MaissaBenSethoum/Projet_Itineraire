import cv2
import time
import numpy as np
from matplotlib import pyplot as plt
from datetime import datetime


def _compute_font_params(width, height):
    """
    Détermine automatiquement des paramètres de texte adaptés
    à la taille de l'image.
    """
    min_dim = min(width, height)

    if min_dim <= 320:
        font_scale = 0.4
    elif min_dim <= 480:
        font_scale = 0.5
    elif min_dim <= 720:
        font_scale = 0.6
    else:
        font_scale = 0.7

    thickness = 1
    line_height = max(18, int(28 * font_scale))
    origin = (10, max(20, int(25 * font_scale)))

    return font_scale, thickness, origin, line_height


def draw_overlay(frame,
                 fps=None,
                 timestamp=None,
                 extra_lines=None,
                 font_scale=0.7,
                 thickness=1,
                 origin=(10, 30),
                 line_height=30):
    """
    Ajoute un overlay simple sur une frame.

    Parameters
    ----------
    frame : numpy.ndarray
        Image sur laquelle écrire.
    fps : float | None
        FPS à afficher. Si None, rien n'est affiché.
    timestamp : str | None
        Timestamp à afficher. Si None, rien n'est affiché.
    extra_lines : list | None
        Lignes supplémentaires à afficher.
    font_scale : float
        Taille de police OpenCV.
    thickness : int
        Épaisseur du texte.
    origin : tuple[int, int]
        Position du premier texte.
    line_height : int
        Espacement vertical entre deux lignes.

    Returns
    -------
    numpy.ndarray
        Frame annotée.
    """
    x, y = origin

    if fps is not None:
        cv2.putText(
            frame,
            f"FPS: {fps:.1f}",
            (x, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            (255, 255, 255),
            thickness,
            cv2.LINE_AA
        )
        y += line_height

    if timestamp is not None:
        cv2.putText(
            frame,
            str(timestamp),
            (x, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            (255, 255, 255),
            thickness,
            cv2.LINE_AA
        )
        y += line_height

    if extra_lines is not None:
        if not isinstance(extra_lines, list):
            raise TypeError("extra_lines doit être une liste de chaînes ou None")

        for line in extra_lines:
            cv2.putText(
                frame,
                str(line),
                (x, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                font_scale,
                (255, 255, 255),
                thickness,
                cv2.LINE_AA
            )
            y += line_height

    return frame


def show_frame(frame,
               window_name="Frame",
               exit_key=None,
               fps=None,
               timestamp=None,
               extra_lines=None,
               size=None):
    """
    Affiche une frame unique dans une fenêtre OpenCV.
    """
    if size is not None:
        frame = cv2.resize(frame, size)

    height, width = frame.shape[:2]
    font_scale, thickness, origin, line_height = _compute_font_params(width, height)

    draw_overlay(
        frame,
        fps=fps,
        timestamp=timestamp,
        extra_lines=extra_lines,
        font_scale=font_scale,
        thickness=thickness,
        origin=origin,
        line_height=line_height
    )

    cv2.imshow(window_name, frame)

    if exit_key is not None:
        key = cv2.waitKey(1) & 0xFF
        if key == ord(exit_key):
            return True

    return False


def stream_frames(frame_generator,
                  window_name="Camera",
                  exit_key="q",
                  show_fps=False,
                  show_timestamp=False,
                  size=None,
                  timestamp_callback=None,
                  extra_lines_callback=None):
    """
    Affiche un flux d'images provenant d'un générateur.
    """
    exit_key = ord(exit_key)
    prev_time = time.time()

    try:
        for frame in frame_generator:
            fps = None
            if show_fps:
                current_time = time.time()
                fps = 1.0 / (current_time - prev_time)
                prev_time = current_time

            timestamp = None
            if show_timestamp:
                if timestamp_callback is not None:
                    timestamp = timestamp_callback(frame)
                else:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            extra_lines = None
            if extra_lines_callback is not None:
                extra_lines = extra_lines_callback(frame)

            if size is not None:
                frame = cv2.resize(frame, size)

            height, width = frame.shape[:2]
            font_scale, thickness, origin, line_height = _compute_font_params(width, height)

            draw_overlay(
                frame,
                fps=fps,
                timestamp=timestamp,
                extra_lines=extra_lines,
                font_scale=font_scale,
                thickness=thickness,
                origin=origin,
                line_height=line_height
            )

            cv2.imshow(window_name, frame)

            key = cv2.waitKey(1) & 0xFF
            if key == exit_key:
                return True

    finally:
        cv2.destroyAllWindows()

    return False


def plot_scan(points,
              min_range=None,
              max_range=None):
    """
    Affiche un scan LiDAR dans un plan cartésien.
    """
    if not points:
        print("Aucun point à afficher.")
        return

    x = np.array([p[0] for p in points])
    y = np.array([p[1] for p in points])

    distances = np.sqrt(x**2 + y**2)

    fig, ax = plt.subplots()

    scatter = ax.scatter(x, y,
                         c=distances,
                         s=6,
                         cmap="viridis")

    plt.colorbar(scatter, label="Distance")

    ax.scatter(0, 0, marker='x', s=80, color='red', label="Robot")

    if max_range:
        circle_max = plt.Circle((0, 0),
                                max_range,
                                fill=False,
                                linestyle='--',
                                color='gray')
        ax.add_patch(circle_max)

    if min_range:
        circle_min = plt.Circle((0, 0),
                                min_range,
                                fill=False,
                                linestyle=':',
                                color='gray')
        ax.add_patch(circle_min)

    if max_range:
        ax.set_xlim(-max_range, max_range)
        ax.set_ylim(-max_range, max_range)

    ax.set_aspect("equal")
    ax.set_xlabel("X (mm)")
    ax.set_ylabel("Y (mm)")
    ax.set_title("LiDAR Scan")
    ax.grid(True)
    ax.legend()

    plt.show()


def _create_lidar_base_frame(window_size, center, min_range, max_range, scale):
    """
    Crée l'image de base pour le stream LiDAR.
    """
    frame = np.zeros((window_size, window_size, 3), dtype=np.uint8)

    frame[center, :] = (40, 40, 40)
    frame[:, center] = (40, 40, 40)

    if max_range is not None:
        radius_max_px = int(max_range * scale)
        cv2.circle(frame, (center, center), radius_max_px, (80, 80, 80), 1)

    if min_range is not None and min_range > 0:
        radius_min_px = int(min_range * scale)
        cv2.circle(frame, (center, center), radius_min_px, (60, 60, 60), 1)

    cv2.drawMarker(
        frame,
        (center, center),
        (0, 0, 255),
        markerType=cv2.MARKER_CROSS,
        markerSize=12,
        thickness=1
    )

    return frame


def stream_scans(scan_iterator,
                 window_name="LiDAR",
                 exit_key="q",
                 show_fps=False,
                 show_timestamp=False,
                 min_range=None,
                 max_range=None,
                 window_size=400,
                 timestamp_callback=None,
                 extra_lines_callback=None):
    """
    Affiche un flux de scans LiDAR dans une fenêtre OpenCV.
    """
    exit_key = ord(exit_key)
    prev_time = time.time()

    if max_range is None:
        max_range = 2000

    scale = (window_size * 0.45) / max_range
    center = window_size // 2

    base_frame = _create_lidar_base_frame(
        window_size=window_size,
        center=center,
        min_range=min_range,
        max_range=max_range,
        scale=scale
    )

    try:
        for timestamp_value, scan, points in scan_iterator:
            frame = base_frame.copy()

            fps = None
            if show_fps:
                current_time = time.time()
                fps = 1.0 / (current_time - prev_time)
                prev_time = current_time

            if points:
                pts = np.array(points, dtype=np.float32)

                px = (center + pts[:, 0] * scale).astype(int)
                py = (center - pts[:, 1] * scale).astype(int)

                valid = (
                    (px >= 0) & (px < window_size) &
                    (py >= 0) & (py < window_size)
                )

                frame[py[valid], px[valid]] = (255, 255, 255)

            timestamp_text = None
            if show_timestamp:
                if timestamp_callback is not None:
                    timestamp_text = timestamp_callback(timestamp_value, scan, points)
                else:
                    timestamp_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            extra_lines = None
            if extra_lines_callback is not None:
                extra_lines = extra_lines_callback(timestamp_value, scan, points)

            height, width = frame.shape[:2]
            font_scale, thickness, origin, line_height = _compute_font_params(width, height)

            draw_overlay(
                frame,
                fps=fps,
                timestamp=timestamp_text,
                extra_lines=extra_lines,
                font_scale=font_scale,
                thickness=thickness,
                origin=origin,
                line_height=line_height
            )

            cv2.imshow(window_name, frame)

            key = cv2.waitKey(1) & 0xFF
            if key == exit_key:
                return True

    finally:
        cv2.destroyAllWindows()

    return False