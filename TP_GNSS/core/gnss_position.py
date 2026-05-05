import time
from sensors.GNSS import GNSS
from utils import CSVHandler, LCD
from config import GNSS_DEVICE_ADDR, LCD_DEVICE_ADDR, MODE_GNSS


def gnss_position(mode=MODE_GNSS, csv_out=None, display_LCD=False):
    """
    Lit les données GNSS et affiche la position du module GNSS sur la console et le LCD.
    """
    gnss = GNSS(1, GNSS_DEVICE_ADDR)
    gnss.initialisation(mode)

    record = None
    if csv_out:
        if not csv_out.endswith(".csv"):
            csv_out += ".csv"
        record = CSVHandler(csv_out)
        record.create_csv_with_header(["Timestamp", "UTC", "Latitude", "Longitude"])

    lcd_display = LCD(LCD_DEVICE_ADDR) if display_LCD else None

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

            if record is not None:
                record.append_row([gnss.timestamp, gnss.utc, gnss.latitude.coordinates_DD, gnss.longitude.coordinates_DD])

            # A COMPLETER
            # Récupération des coordonnées
            latitude = gnss.latitude.coordinates_DMS
            longitude = gnss.longitude.coordinates_DMS
            
            if lcd_display is not None:
                # A COMPLETER
                # Affichage des coordonnées sur l'écran LCD
                lcd_display.afficher(f"Lat:{latitude}\nLon:{longitude}")

            print("--------------------------------------------------------------")
            print(f"Nombre de satellites utilisés: {gnss.number_satellites}")
            print(f"Latitude : {latitude}")
            print(f"Longitude : {longitude}")
            print("")

    except KeyboardInterrupt:
        print("Arrêt du programme")
        if lcd_display is not None:
            lcd_display.effacer()
