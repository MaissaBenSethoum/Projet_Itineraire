import cv2
import numpy as np


def draw_lines(frame, lines,
               color=(0, 0, 255),
               thickness=2):
    """
    Dessine des lignes détectées par Hough sur une image.

    Parameters
    ----------
    frame : numpy.ndarray
        Image sur laquelle dessiner.
    lines : numpy.ndarray | None
        Lignes détectées au format retourné par cv2.HoughLines.
    color : tuple[int, int, int]
        Couleur BGR des lignes.
    thickness : int
        Épaisseur des lignes.

    Returns
    -------
    numpy.ndarray
        Image annotée.
    """
    if lines is None:
        return frame

    for i in range(len(lines)):
        rho = lines[i][0][0]
        theta = lines[i][0][1]

        a = np.cos(theta)
        b = np.sin(theta)
        x0 = a * rho
        y0 = b * rho

        pt1 = (int(x0 + 1000 * (-b)), int(y0 + 1000 * a))
        pt2 = (int(x0 - 1000 * (-b)), int(y0 - 1000 * a))

        cv2.line(frame, pt1, pt2, color, thickness, cv2.LINE_AA)

    return frame


def draw_target_circle(frame, circle,
                       circle_color=(0, 255, 0),
                       center_color=(255, 0, 0),
                       thickness=2,
                       center_radius=4):
    """
    Dessine le cercle extérieur de la cible et son centre.

    Parameters
    ----------
    frame : numpy.ndarray
        Image sur laquelle dessiner.
    circle : tuple[int, int, int] | None
        Cercle sous la forme (cx, cy, r).
    circle_color : tuple[int, int, int]
        Couleur BGR du cercle.
    center_color : tuple[int, int, int]
        Couleur BGR du centre.
    thickness : int
        Épaisseur du cercle.
    center_radius : int
        Rayon du point central.

    Returns
    -------
    numpy.ndarray
        Image annotée.
    """
    if circle is None:
        return frame

    cx, cy, r = circle

    cv2.circle(frame, (cx, cy), r, circle_color, thickness)
    cv2.circle(frame, (cx, cy), center_radius, center_color, -1)

    return frame


def draw_marker_center(frame, marker_center,
                       color=(0, 0, 255),
                       radius=4):
    """
    Dessine le centre du marker.

    Parameters
    ----------
    frame : numpy.ndarray
        Image sur laquelle dessiner.
    marker_center : tuple[int, int] | None
        Centre du marker sous la forme (mx, my).
    color : tuple[int, int, int]
        Couleur BGR du point.
    radius : int
        Rayon du point.

    Returns
    -------
    numpy.ndarray
        Image annotée.
    """
    if marker_center is None:
        return frame

    mx, my = marker_center
    cv2.circle(frame, (mx, my), radius, color, -1)

    return frame


def draw_target_marker_link(frame, target_center, marker_center,
                            color=(0, 255, 255),
                            thickness=2):
    """
    Dessine un segment entre le centre de la cible et le centre du marker.

    Parameters
    ----------
    frame : numpy.ndarray
        Image sur laquelle dessiner.
    target_center : tuple[int, int] | None
        Centre de la cible.
    marker_center : tuple[int, int] | None
        Centre du marker.
    color : tuple[int, int, int]
        Couleur BGR du segment.
    thickness : int
        Épaisseur du segment.

    Returns
    -------
    numpy.ndarray
        Image annotée.
    """
    if target_center is None or marker_center is None:
        return frame

    cv2.line(frame, target_center, marker_center, color, thickness)

    return frame


def draw_contour(frame, contour,
                 color=(0, 255, 0),
                 thickness=2):
    """
    Dessine un contour sur une image.

    Parameters
    ----------
    frame : numpy.ndarray
        Image sur laquelle dessiner.
    contour : numpy.ndarray | None
        Contour à dessiner.
    color : tuple[int, int, int]
        Couleur BGR du contour.
    thickness : int
        Épaisseur du contour.

    Returns
    -------
    numpy.ndarray
        Image annotée.
    """
    if contour is None:
        return frame

    cv2.drawContours(frame, [contour], -1, color, thickness)
    return frame