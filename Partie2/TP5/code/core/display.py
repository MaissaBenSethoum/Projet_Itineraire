import cv2
import time
from datetime import datetime


def draw_overlay(frame, fps=None, timestamp=None, extra_lines=None):
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
        Lignes supplémentaires à afficher (sous forme de liste)

    Returns
    -------
    numpy.ndarray
        Frame annotée.
    """
    y = 30
    line_height = 30

    if fps is not None:
        cv2.putText(
            frame,
            f"FPS: {fps:.1f}",
            (10, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            1,
            cv2.LINE_AA
        )
        y += line_height

    if timestamp is not None:
        cv2.putText(
            frame,
            str(timestamp),
            (10, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            1,
            cv2.LINE_AA
        )
        y += line_height

    # Gestion des lignes supplémentaires
    if extra_lines is not None:
        if not isinstance(extra_lines, list):
            raise TypeError("extra_lines doit être une liste de chaînes ou None")

        for line in extra_lines:
            cv2.putText(
                frame,
                str(line),
                (10, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                1,
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

    Parameters
    ----------
    frame : numpy.ndarray
        Image à afficher.
    window_name : str
        Nom de la fenêtre.
    exit_key : str | None
        Touche permettant de fermer la fenêtre.
    fps : float | None
        FPS à afficher.
    timestamp : str | None
        Timestamp à afficher.
    extra_lines : list | None
        Lignes supplémentaires à afficher.
    size : tuple[int, int] | None
        Taille d'affichage (largeur, hauteur). Si None, pas de redimensionnement.

    Returns
    -------
    bool
        True si la touche exit_key a été pressée.
    """
    if size is not None:
        frame = cv2.resize(frame, size)

    draw_overlay(frame, fps=fps, timestamp=timestamp, extra_lines=extra_lines)

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

    Parameters
    ----------
    frame_generator : iterable
        Générateur produisant des frames.
    window_name : str
        Nom de la fenêtre OpenCV.
    exit_key : str
        Touche permettant de quitter le flux.
    show_fps : bool
        Affiche les FPS si True.
    show_timestamp : bool
        Affiche un timestamp si True.
    size : tuple[int, int] | None
        Taille d'affichage (largeur, hauteur).
    timestamp_callback : callable | None
        Fonction pour générer le timestamp.
    extra_lines_callback : callable | None
        Fonction pour générer des lignes supplémentaires.

    Returns
    -------
    bool
        True si la touche exit_key a été pressée, False sinon.
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

            draw_overlay(frame, fps=fps, timestamp=timestamp, extra_lines=extra_lines)

            cv2.imshow(window_name, frame)

            key = cv2.waitKey(1) & 0xFF
            if key == exit_key:
                return True

    finally:
        cv2.destroyAllWindows()

    return False