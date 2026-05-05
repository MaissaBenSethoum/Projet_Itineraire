import argparse
import pandas as pd
import folium
import os

def plot_GNSS(file_path):
    """
    Fonction pour tracer les données GNSS d'un parcours sur une carte OpenStreetMap, enregistrée dans un fichier HTML.
    
    Arguments:
    - file_path: Le chemin du fichier CSV contenant les données GNSS.
    """
    out_path,filename = os.path.split(file_path)
    data = pd.read_csv(file_path)

    m = folium.Map(location=[data['Latitude'][0], data['Longitude'][0]], zoom_start=12)

    points = list(zip(data['Latitude'], data['Longitude']))
    folium.PolyLine(points, color="blue", weight=2.5, opacity=1).add_to(m)

    m.save(out_path+filename.replace('.csv','.html'))
    print("Carte générée")

if __name__ == "__main__":

	parser = argparse.ArgumentParser()
	parser.add_argument('path', type=str)
	args = parser.parse_args()
	
	plot_GNSS(args.path)
