import pandas as pd
import xml.etree.ElementTree as ET
import re
from datetime import datetime

def convert_gpx_to_csv(gpx_file, csv_file):
    """
    Convertit un fichier GPX en un fichier CSV avec les colonnes 'Timestamp', 'Latitude' et 'Longitude'.
    
    Arguments:
    - gpx_file: Chemin du fichier GPX d'entrée.
    - csv_file: Chemin du fichier CSV de sortie.
    """
    
    def get_namespace(element):
        """ Récupère l'espace de noms utilisé dans le fichier GPX """
        match = re.match(r'\{.*\}', element.tag)
        return match.group(0) if match else ''
    
    def format_time(date_str):
        date_obj = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
        return f"{date_obj.year:04}/{date_obj.month:02}/{date_obj.day:02} - {date_obj.hour:02}:{date_obj.minute:02}:{date_obj.second:02}"
    
    # Parse le fichier GPX
    tree = ET.parse(gpx_file)
    root = tree.getroot()

    # Détecter l'espace de noms utilisé
    namespace = get_namespace(root)

    # Extraire les données
    data = []
    for trk in root.findall(f"{namespace}trk"):
        for trkseg in trk.findall(f"{namespace}trkseg"):
            for trkpt in trkseg.findall(f"{namespace}trkpt"):
                lat = trkpt.get("lat")
                lon = trkpt.get("lon")
                time_element = trkpt.find(f"{namespace}time")
                timestamp = time_element.text if time_element is not None else None
                data.append([format_time(timestamp), lat, lon])

    # Convertir en DataFrame
    df = pd.DataFrame(data, columns=["UTC", "Latitude", "Longitude"])

    # Enregistrer en fichier CSV
    df.to_csv(csv_file, index=False)
    print(f"Conversion terminée ! Fichier enregistré : {csv_file}")
    
    
def convert_csv_to_gpx(csv_file, gpx_file):
    """
    Convertit un fichier CSV avec les colonnes 'UTC', 'Latitude' et 'Longitude' en un fichier GPX.
    
    Arguments:
    - csv_file: Chemin du fichier CSV d'entrée.
    - gpx_file: Chemin du fichier GPX de sortie.
    """

    # Lecture du CSV
    df = pd.read_csv(csv_file)

    # Création de l’arbre XML GPX
    gpx = ET.Element("gpx", version="1.1", creator="convert_csv_to_gpx", xmlns="http://www.topografix.com/GPX/1/1")
    trk = ET.SubElement(gpx, "trk")
    trkseg = ET.SubElement(trk, "trkseg")

    for _, row in df.iterrows():
        trkpt = ET.SubElement(trkseg, "trkpt", lat=str(row["Latitude"]), lon=str(row["Longitude"]))
        
        # Conversion du temps vers format ISO 8601
        try:
            dt = datetime.strptime(row["UTC"], "%Y/%m/%d - %H:%M:%S")
            time_elem = ET.SubElement(trkpt, "time")
            time_elem.text = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        except Exception as e:
            print(f"Erreur de conversion de temps à la ligne {_}: {e}")

    # Sauvegarde du fichier GPX
    tree = ET.ElementTree(gpx)
    tree.write(gpx_file, encoding="utf-8", xml_declaration=True)
    print(f"Conversion terminée ! Fichier enregistré : {gpx_file}")