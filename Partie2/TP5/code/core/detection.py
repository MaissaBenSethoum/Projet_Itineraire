import cv2
import numpy as np


def detect_lines(frame,
                 canny_threshold1=50,
                 canny_threshold2=200,
                 hough_threshold=150):
    """
    Détecte des lignes dans une image avec Canny + Hough.

    Parameters
    ----------
    frame : numpy.ndarray
        Image BGR.
    canny_threshold1 : int
        Premier seuil pour Canny.
    canny_threshold2 : int
        Second seuil pour Canny.
    hough_threshold : int
        Seuil accumulateur pour HoughLines.

    Returns
    -------
    numpy.ndarray | None
        Lignes détectées (format HoughLines) ou None
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, canny_threshold1, canny_threshold2, None, 3)

    lines = cv2.HoughLines(
        edges,
        rho=1,
        theta=np.pi / 180,
        threshold=hough_threshold
    )

    return lines


def detect_target_circle(frame,
                         dp=1.2,
                         min_dist=100,
                         param1=100,
                         param2=60,
                         min_radius=150,
                         max_radius=0):
    """
    Détecte le cercle extérieur d'une cible et renvoie le plus grand cercle trouvé.

    Returns
    -------
    tuple[int, int, int] | None
        (cx, cy, r) ou None
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (9, 9), 2)

    circles = cv2.HoughCircles(
        gray,
        cv2.HOUGH_GRADIENT,
        dp=dp,
        minDist=min_dist,
        param1=param1,
        param2=param2,
        minRadius=min_radius,
        maxRadius=max_radius
    )

    if circles is None:
        return None

    circles = np.round(circles[0, :]).astype(int)

    largest_circle = max(circles, key=lambda c: c[2])
    cx, cy, r = largest_circle

    return (cx, cy, r)


def detect_green_marker(frame,
                        lower_green=(40, 50, 50),
                        upper_green=(90, 255, 255),
                        min_area=100):
    """
    Détecte un marker vert dans une image.

    Returns
    -------
    tuple[tuple[int, int] | None, numpy.ndarray]
        - centre du marker (cx, cy) ou None
        - masque binaire
    """
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    lower = np.array(lower_green, dtype=np.uint8)
    upper = np.array(upper_green, dtype=np.uint8)

    mask = cv2.inRange(hsv, lower, upper)

    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return None, mask

    largest_contour = max(contours, key=cv2.contourArea)

    if cv2.contourArea(largest_contour) < min_area:
        return None, mask

    moments = cv2.moments(largest_contour)
    if moments["m00"] == 0:
        return None, mask

    cx = int(moments["m10"] / moments["m00"])
    cy = int(moments["m01"] / moments["m00"])

    return (cx, cy), mask