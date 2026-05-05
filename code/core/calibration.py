import cv2
import numpy as np

def calibrate_camera_from_images(
    image_paths,
    checkerboard_size,
    square_size,
    show_corners=False,
    checkpoint=0
):
    """
    Estime la calibration intrinsèque d'une caméra à partir d'images
    d'un damier.

    Parameters
    ----------
    image_paths : list[str]
        Liste des chemins des images de calibration.
    checkerboard_size : tuple[int, int]
        Nombre de coins intérieurs du damier (colonnes, lignes).
        Exemple : (9, 6)
    square_size : float
        Taille d'un carré du damier, en mètre, centimètre ou millimètre.
        L'unité choisie sera celle des résultats 3D.
    show_corners : bool
        Si True, affiche les coins détectés pour chaque image.
    checkpoint : int
        Mode de fonctionnement :
        - 0 : mode normal, calibration complète sans affichage pédagogique
        - 1 : étape 1 uniquement
        - 2 : jusqu'à l'étape 2
        - 3 : jusqu'à l'étape 3
        - 4 : jusqu'à l'étape 4 avec affichage pédagogique complet

    Returns
    -------
    dict
        Dictionnaire contenant :
        - rms_error
        - camera_matrix
        - dist_coeffs
        - rvecs
        - tvecs
        - image_size
        - valid_images

        Si checkpoint est entre 1 et 3, retourne {}.
    """
    cols, rows = checkerboard_size

    checkpoint_mode = checkpoint > 0

    # ==================================================
    # INITIALISATION
    # ==================================================

    # Critère de raffinement subpixel
    criteria = (
        cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
        30,
        0.001
    )

    # Points 3D du damier dans son repère propre
    objp = np.zeros((rows * cols, 3), np.float32)
    objp[:, :2] = np.mgrid[0:cols, 0:rows].T.reshape(-1, 2)
    objp *= square_size

    object_points = []
    image_points = []

    image_size = None
    valid_images = []

    if len(image_paths) == 0:
        raise RuntimeError("Aucune image fournie pour la calibration.")

    # ==================================================
    # ETAPE 1
    # ==================================================
    if checkpoint_mode:
        if checkpoint >= 1:
            print("=== ETAPE 1 ===")

            first_image_path = image_paths[0]
            image = cv2.imread(str(first_image_path))

            if image is None:
                raise RuntimeError(f"Impossible de lire la première image : {first_image_path}")

            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            image_size = (gray.shape[1], gray.shape[0])

            found, corners = cv2.findChessboardCorners(gray, (cols, rows), None)

            print(f"Première image : {first_image_path}")
            print(f"Taille image   : {image_size}")
            print(f"Damier trouvé  : {found}")

            if checkpoint==1:
                display = image.copy()
                if found:
                    cv2.drawChessboardCorners(display, (cols, rows), corners, found)
                cv2.imshow("Etape 1 - Detection coins", display)
                cv2.waitKey(0)
                cv2.destroyAllWindows()
                return {}
        
        # ==================================================
        # ETAPE 2
        # ==================================================
        if checkpoint >= 2:
            print("\n=== ETAPE 2 ===")

            if not found:
                print("Le damier n'a pas ete detecte dans la premiere image. Impossible de poursuivre l'etape 2.")
                return {}

            corners_refined = cv2.cornerSubPix(
                gray,
                corners,
                (11, 11),
                (-1, -1),
                criteria
            )


            print("\nobjp :")
            print(objp)
            print(f"Shape objp : {objp.shape}")

            print("\ncorners_refined :")
            print(corners_refined)
            print(f"Shape corners_refined : {corners_refined.shape}")

            if checkpoint == 2:
                display_refined = image.copy()
                cv2.drawChessboardCorners(display_refined, (cols, rows), corners_refined, found)
                cv2.imshow("Etape 2 - Coins affines", display_refined)
                cv2.waitKey(0)
                cv2.destroyAllWindows()

                return {}

    # ==================================================
    # ETAPE 3
    # ==================================================
    if checkpoint_mode and checkpoint >= 3:
        print("\n=== ETAPE 3 ===")

    for image_path in image_paths:
        image = cv2.imread(str(image_path))

        if image is None:
            if checkpoint_mode:
                print(f"[WARNING] Impossible de lire l'image : {image_path}")
            continue

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        if image_size is None:
            image_size = (gray.shape[1], gray.shape[0])

        found, corners = cv2.findChessboardCorners(gray, (cols, rows), None)

        if found:
            corners_refined = cv2.cornerSubPix(
                gray,
                corners,
                (11, 11),
                (-1, -1),
                criteria
            )

            object_points.append(objp)
            image_points.append(corners_refined)
            valid_images.append(str(image_path))

            if show_corners or (checkpoint_mode and checkpoint == 3):
                display = image.copy()
                cv2.drawChessboardCorners(display, (cols, rows), corners_refined, found)
                cv2.imshow("Calibration", display)
                cv2.waitKey(300)

        else:
            if checkpoint_mode and checkpoint >= 3:
                print(f"[INFO] Damier non détecté dans : {image_path}")

    if show_corners or (checkpoint_mode and checkpoint >= 3):
        cv2.destroyAllWindows()

    if checkpoint_mode and checkpoint >= 3:
        print(f"Nombre d'images valides : {len(valid_images)}")

    if checkpoint == 3:
        return {}

    # ==================================================
    # ETAPE 4
    # ==================================================
    if len(object_points) < 3:
        raise RuntimeError(
            "Pas assez d'images valides pour calibrer la caméra "
            "(au moins 3 recommandées, davantage en pratique)."
        )

    var1, var2, var3, var4, var5 = cv2.calibrateCamera(
        object_points,
        image_points,
        image_size,
        None,
        None
    )

    if checkpoint_mode and checkpoint >= 4:
        print("\n=== ETAPE 4 ===")
        print("var1 : {}".format(var1))
        print("--------------------------------")
        print("var2 : \n{}".format(var2))
        print("--------------------------------")
        print("var3 : \n{}".format(var3))
        print("--------------------------------")
        print("Premier élément de var4 brut: \n{}".format(var4[0]))
        print("Premier élément de var4 après transformation: \n{}".format(cv2.Rodrigues(var4[0])[0]))
        print("Taille de var4 : {}".format(len(var4)))
        print("--------------------------------")
        print("Premier élément de var5 : \n{}".format(var5[0]))
        print("Taille de var5 : {}".format(len(var5)))
        from postprocessing.plot_calibration_3d import calibration_figure
        calibration_figure(checkerboard_size, square_size, var2, var4, var5)
        return {}








    return {
        "rms_error": var1,
        "camera_matrix": var2,
        "dist_coeffs": var3,
        "rvecs": var4,
        "tvecs": var5,
        "image_size": image_size,
        "valid_images": valid_images,
    }

def detect_checkerboard(frame, checkerboard_size):
    """
    Détecte un damier dans une image.

    Parameters
    ----------
    frame : numpy.ndarray
        Image BGR.
    checkerboard_size : tuple[int, int]
        Nombre de coins intérieurs (colonnes, lignes).

    Returns
    -------
    tuple[bool, numpy.ndarray | None]
        - found : bool
        - corners : coins détectés (ou None)
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    found, corners = cv2.findChessboardCorners(gray, checkerboard_size, None)

    return found, corners

    
def save_calibration(calibration_data, output_file):
    """
    Sauvegarde les paramètres de calibration dans un fichier .npz.
    """
    np.savez(
        output_file,
        rms_error=calibration_data["rms_error"],
        camera_matrix=calibration_data["camera_matrix"],
        dist_coeffs=calibration_data["dist_coeffs"],
        image_size=np.array(calibration_data["image_size"]),
    )
    
def load_calibration(calibration_file):
    """
    Charge un fichier de calibration .npz.
    """
    data = np.load(calibration_file)

    return {
        "rms_error": float(data["rms_error"]),
        "camera_matrix": data["camera_matrix"],
        "dist_coeffs": data["dist_coeffs"],
        "image_size": tuple(data["image_size"]),
    }
    
def undistort_image(image, calibration_data, crop=False):
    """
    Corrige la distorsion d'une image à partir des paramètres de calibration.

    Parameters
    ----------
    image : numpy.ndarray
        Image à corriger.
    calibration_data : dict
        Dictionnaire contenant au minimum :
        - "camera_matrix"
        - "dist_coeffs"
    crop : bool
        Si True, recadre l'image pour supprimer les zones noires
        introduites par la correction.

    Returns
    -------
    numpy.ndarray
        Image corrigée.
    """
    camera_matrix = calibration_data["camera_matrix"]
    dist_coeffs = calibration_data["dist_coeffs"]

    h, w = image.shape[:2]

    new_camera_matrix, roi = cv2.getOptimalNewCameraMatrix(
        camera_matrix,
        dist_coeffs,
        (w, h),
        1,
        (w, h)
    )

    undistorted = cv2.undistort(
        image,
        camera_matrix,
        dist_coeffs,
        None,
        new_camera_matrix
    )

    if crop:
        x, y, roi_w, roi_h = roi
        undistorted = undistorted[y:y + roi_h, x:x + roi_w]

    return undistorted
