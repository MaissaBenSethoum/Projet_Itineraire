##################################################
#               LIDAR PARAMETERS
##################################################

MIN_DETECTION_RANGE = 150       # Portée minimale appliquée du LiDAR en mm
MAX_DETECTION_RANGE = 12000     # Portée maximale appliquée du LiDAR en mm
MIN_DETECTION_ANGLE = 0       # Angle minimal du scan en degrés
MAX_DETECTION_ANGLE = 360     # Angle maximal du scan en degrés
QUALITY_THRESHOLD = 0        # Seuil de qualité des mesures du LiDAR (entre 0 et 15)
SCAN_SKIP = 3                    # Ignorer X scans pour alléger l'affichage (via stream_scan.py)

##################################################
#               CAMERA PARAMETERS
##################################################

# Mode de fonctionnement de la caméra
# Valeurs possibles :
#   "preview" : flux vidéo pour affichage en temps réel
#   "still"   : capture d'image haute qualité
#   "video"   : enregistrement vidéo optimisé
CAMERA_MODE = "preview"


# Résolution de l'image capturée (largeur, hauteur) en pixels
# Exemples :
#   (640, 480)
#   (1280, 720)
#   (1920, 1080)
CAMERA_RESOLUTION = (1280, 720)


# Framerate cible en images par seconde
# Valeurs typiques :
#   15
#   30
#   60
# Mettre None pour laisser la caméra choisir automatiquement
CAMERA_FRAMERATE = 15


# Temps d'exposition en microsecondes (µs)
# Valeurs typiques :
#   1000   (1 ms)
#   5000   (5 ms)
#   10000  (10 ms)
#   20000  (20 ms)
# Mettre None pour utiliser l'exposition automatique
CAMERA_EXPOSURE_TIME = None


# Gain analogique du capteur
# Permet d'amplifier le signal du capteur (utile en faible lumière)
# Valeurs typiques :
#   1.0 → gain minimal
#   2.0
#   4.0
# Mettre None pour laisser la caméra gérer automatiquement
CAMERA_GAIN = None


# Activation de la balance des blancs automatique
# Valeurs possibles :
#   True  → balance des blancs automatique
#   False → balance des blancs manuelle
# Mettre None pour ne pas modifier le réglage par défaut
CAMERA_AWB = True


# Luminosité de l'image
# Plage typique :
#   -1.0 → image plus sombre
#    0.0 → valeur neutre
#   +1.0 → image plus lumineuse
CAMERA_BRIGHTNESS = 0.0


# Contraste de l'image
# Plage typique :
#   0.0 → contraste très faible
#   1.0 → contraste normal
#   2.0 → contraste élevé
CAMERA_CONTRAST = 1.0


# Saturation des couleurs
# Plage typique :
#   0.0 → image noir et blanc
#   1.0 → saturation normale
#   2.0 → couleurs très saturées
CAMERA_SATURATION = 1.0


# Netteté de l'image
# Plage typique :
#   0.0 → image floue
#   1.0 → netteté normale
#   2.0 → netteté accentuée
CAMERA_SHARPNESS = 1.0


