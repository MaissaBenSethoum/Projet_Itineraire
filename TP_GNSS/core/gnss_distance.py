from config import GNSS_DEVICE_ADDR, LCD_DEVICE_ADDR, MODE_GNSS
from sensors.GNSS import GNSS
from utils import LCD
import time
import numpy as np

def compute_distance(pt1,pt2):
    """
    Calcul de la distance entre 2 points en coordonnées latitude/longitude.

    Arguments:
    - pt1: tuple des coordonnées du 1er point (latitude/longitude).
    - pt2: tuple des coordonnées du 2ème point (latitude/longitude).

    Sortie: La distance en mètre entre les 2 points en vol d'oiseau sur la surface de la Terre (sphérique).
    """
    # A COMPLETER
    # Calcul de la distance en mètre entre pt1 et pt2
    return np.arccos(np.sin(pt1[0])*np.sin(pt2[0])+np.cos(pt1[0])*np.cos(pt2[0])*np.cos(pt1[1]-pt2[1]))

def format_distance(distance_meters):
    """
    Formate une chaîne représentant une distance avec des unités adaptées (m ou km)
    et une précision dépendant de la distance.

    :param distance_meters: La distance en mètres (float ou int).
    :return: Une chaîne formatée avec l'unité appropriée.
    """
    if distance_meters < 1000:
        # Distance inférieure à 1 km, rester en mètres
        return f"{distance_meters:.0f} m"
    else:
        # Distance égale ou supérieure à 1 km, convertir en kilomètres
        distance_km = distance_meters / 1000
        if distance_km < 10:
            # Moins de 10 km : 2 décimales
            return f"{distance_km:.2f} km"
        elif distance_km < 100:
            # Entre 10 et 100 km : 1 décimale
            return f"{distance_km:.1f} km"
        else:
            # 100 km ou plus : pas de décimales
            return f"{distance_km:.0f} km"

def gnss_distance(position_target,mode=MODE_GNSS):
    """
    Lit les données GNSS et affiche la distance en vol d'oiseau du point d'intérêt.

    Arguments:
    - position_target: Tuple indiquant la position du point d'intérêt (latitude et longitude en degrés décimaux).
    """

    gnss = GNSS(1, GNSS_DEVICE_ADDR)
    gnss.initialisation(mode)

    lcd_display = LCD(LCD_DEVICE_ADDR)
    
    try:
        while True:
            
            # Récupération du prochain scan GPS
            gnss.wait_for_next_scan(timeout=1.0)

            # Gestion d'un signal mauvais
            if not(gnss.reception_ok):
                if lcd_display is not None:
                    lcd_display.afficher("Recherche de    signal GNSS...")
                print("Recherche de signal GNSS...")
                continue
                    
            # Calcul de la distance à la target
            distance = format_distance(compute_distance(position_target,(gnss.latitude.coordinates_DD,gnss.longitude.coordinates_DD)))
            
            # Affichage sur le LCD
            lcd_display.afficher(f"Distance:       {distance}")
            
            # Affichage sur console
            print("--------------------------------------------------------------")
            print(f"Distance de la target: {distance}")
            print("")
                
            time.sleep(1)
        
    except KeyboardInterrupt as e:
        print("Arrêt du programme")
        if lcd_display is not None:
            lcd_display.effacer()