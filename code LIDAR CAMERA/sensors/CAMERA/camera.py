from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FileOutput
import cv2
import time
from pathlib import Path

class Camera:
    def __init__(self):
        self.camera = Picamera2()
        self.is_configured = False
        self.is_running = False
        self.current_mode = None

    ######################################
    #     CONFIGURATION DE LA CAMERA
    ######################################

    def configure(self):
        """
        Configure la caméra à partir des paramètres définis dans
        config/parameters.py.

        Paramètres attendus dans config.parameters :
        - CAMERA_MODE
        - CAMERA_RESOLUTION
        - CAMERA_FRAMERATE
        - CAMERA_EXPOSURE_TIME
        - CAMERA_GAIN
        - CAMERA_AWB
        - CAMERA_BRIGHTNESS
        - CAMERA_CONTRAST
        - CAMERA_SATURATION
        - CAMERA_SHARPNESS
        """

        import config.parameters as params

        allowed_modes = ("preview", "still", "video")
        mode = params.CAMERA_MODE

        if mode not in allowed_modes:
            raise ValueError(
                f"Mode caméra invalide : {mode}. "
                f"Valeurs possibles : {allowed_modes}"
            )

        resolution = params.CAMERA_RESOLUTION
        if (
            not isinstance(resolution, tuple)
            or len(resolution) != 2
            or not all(isinstance(v, int) for v in resolution)
        ):
            raise ValueError(
                "CAMERA_RESOLUTION doit être un tuple de deux entiers, "
                "par exemple (1280, 720)."
            )

        width, height = resolution
        if width <= 0 or height <= 0:
            raise ValueError(
                "CAMERA_RESOLUTION doit contenir des valeurs strictement positives."
            )

        framerate = params.CAMERA_FRAMERATE
        if framerate is not None:
            if not isinstance(framerate, (int, float)) or framerate <= 0:
                raise ValueError(
                    "CAMERA_FRAMERATE doit être un nombre strictement positif ou None."
                )

        exposure_time = params.CAMERA_EXPOSURE_TIME
        if exposure_time is not None:
            if not isinstance(exposure_time, int) or exposure_time <= 0:
                raise ValueError(
                    "CAMERA_EXPOSURE_TIME doit être un entier strictement positif "
                    "(en microsecondes) ou None."
                )

        gain = params.CAMERA_GAIN
        if gain is not None:
            if not isinstance(gain, (int, float)) or gain <= 0:
                raise ValueError(
                    "CAMERA_GAIN doit être un nombre strictement positif ou None."
                )

        awb = params.CAMERA_AWB
        if awb is not None and not isinstance(awb, bool):
            raise ValueError("CAMERA_AWB doit être un booléen ou None.")

        brightness = params.CAMERA_BRIGHTNESS
        if brightness is not None and not isinstance(brightness, (int, float)):
            raise ValueError("CAMERA_BRIGHTNESS doit être un nombre ou None.")

        contrast = params.CAMERA_CONTRAST
        if contrast is not None and not isinstance(contrast, (int, float)):
            raise ValueError("CAMERA_CONTRAST doit être un nombre ou None.")

        saturation = params.CAMERA_SATURATION
        if saturation is not None and not isinstance(saturation, (int, float)):
            raise ValueError("CAMERA_SATURATION doit être un nombre ou None.")

        sharpness = params.CAMERA_SHARPNESS
        if sharpness is not None and not isinstance(sharpness, (int, float)):
            raise ValueError("CAMERA_SHARPNESS doit être un nombre ou None.")

        main_config = {"size": resolution}

        if mode == "preview":
            configuration = self.camera.create_preview_configuration(
                main=main_config
            )
        elif mode == "still":
            configuration = self.camera.create_still_configuration(
                main=main_config
            )
        else:  # mode == "video"
            configuration = self.camera.create_video_configuration(
                main=main_config
            )

        self.camera.configure(configuration)

        controls = {}

        if framerate is not None:
            controls["FrameRate"] = framerate

        if exposure_time is not None:
            controls["ExposureTime"] = exposure_time

        if gain is not None:
            controls["AnalogueGain"] = gain

        if awb is not None:
            controls["AwbEnable"] = awb

        if brightness is not None:
            controls["Brightness"] = brightness

        if contrast is not None:
            controls["Contrast"] = contrast

        if saturation is not None:
            controls["Saturation"] = saturation

        if sharpness is not None:
            controls["Sharpness"] = sharpness

        if controls:
            self.camera.set_controls(controls)

        self.current_mode = mode
        self.is_configured = True

    ######################################
    #    DEMARRAGE / ARRET DE LA CAMERA
    ######################################

    def start(self):
        """
        Démarre la caméra.
        """
        if not self.is_configured:
            self.configure_still()

        self.camera.start()
        self.is_running = True

    def stop(self):
        """
        Arrête la caméra.
        """
        if self.is_running:
            self.camera.stop()
            self.is_running = False

    ######################################
    #       CAPTURE D'IMAGES ET METADATA
    ######################################

    def capture_frame(self):
        """
        Capture une frame sous forme de tableau NumPy.

        Returns
        -------
        numpy.ndarray
            Image capturée.
        """
        return cv2.cvtColor(self.camera.capture_array(),cv2.COLOR_BGR2RGB)

    def capture_metadata(self):
        """
        Capture les métadonnées associées à la dernière image.

        Returns
        -------
        dict
            Métadonnées caméra.
        """
        return self.camera.capture_metadata()

    ######################################
    #       SAUVEGARDE D'IMAGES
    ######################################

    def save_frame(self, frame, file_path="image.jpg"):
        """
        Sauvegarde une frame OpenCV sur disque.

        Parameters
        ----------
        frame : numpy.ndarray
            Image à sauvegarder.
        file_path : str
            Chemin du fichier.
        """
        cv2.imwrite(file_path, frame)
        return file_path

    def save_frame_sequence(self, frame, directory, index, prefix="frame", extension="jpg"):
        """
        Sauvegarde une frame dans une séquence d'images numérotées.

        Parameters
        ----------
        frame : numpy.ndarray
            Image à sauvegarder.
        directory : str | Path
            Répertoire dans lequel enregistrer l'image.
        index : int
            Indice de l'image dans la séquence.
        prefix : str
            Préfixe du nom de fichier.
        extension : str
            Extension du fichier image.

        Returns
        -------
        str
            Chemin du fichier sauvegardé.
        """
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)

        file_name = f"{prefix}_{index:06d}.{extension}"
        file_path = str(directory / file_name)

        return self.save_frame(frame, file_path)

    ######################################
    #      UTILITAIRES DE DEMARRAGE
    ######################################

    def warmup(self, delay=1.0):
        """
        Laisse le temps à la caméra de se stabiliser.

        Parameters
        ----------
        delay : float
            Temps d'attente en secondes.
        """
        time.sleep(delay)

    ######################################
    #       CONTEXT MANAGER
    ######################################

    def __enter__(self):
        self.start()
        self.warmup()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()