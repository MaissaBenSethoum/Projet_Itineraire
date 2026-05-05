from config import GNSS_DEVICE_ADDR, MODE_GNSS
from sensors.GNSS import GNSS
import time

def gnss_nmea_frames(mode=MODE_GNSS, nmea_out=None):
    """
    Lit les données GNSS brutes (trames NMEA) toutes les 3 secondes,
    les affiche et les enregistre dans un fichier si output_file est fourni.
    
    Arguments:
    - mode: Mode de fonctionnement du module GNSS. Valeur par défaut à GPS_BEIDOU_GLONASS.
    - nmea_out: Le chemin et nom de fichier NMEA pour l'enregistrement des acquisitions GNSS. 
             S'il n'est pas défini, aucun enregistrement n'est effectué.
    """
    gnss = GNSS(1, GNSS_DEVICE_ADDR)
    gnss.initialisation(mode)

    # Ouverture du fichier si demandé
    file = None
    if nmea_out is not None:
        if not(nmea_out.endswith('.nmea')):  
            nmea_out +='.nmea'
        file = open(nmea_out, "a", encoding="ascii")

    try:
        while True:
            rslt = gnss.get_raw_data()

            # Conversion des octets en chaîne de caractères
            data = "".join(chr(b) for b in rslt)

            # Affichage console
            print(data)
            print("")

            # Écriture dans le fichier
            if file is not None:
                file.write(data)
                if not data.endswith("\n"):
                    file.write("\n")
                file.write()
                file.flush()

            time.sleep(3)

    finally:
        # Fermeture propre du fichier
        if file is not None:
            file.close()
