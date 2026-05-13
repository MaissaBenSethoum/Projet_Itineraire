import argparse
import pandas as pd
import folium
import os

def plot_GNSS(df, output):
    """
    Trace les données GNSS d'un DataFrame sur une carte OpenStreetMap.
    
    Arguments:
    - df     : DataFrame contenant les colonnes 'Latitude' et 'Longitude'
    - output : Chemin du fichier HTML de sortie
    """
    m = folium.Map(location=[df['Latitude'].iloc[0], df['Longitude'].iloc[0]], zoom_start=12)
    
    points = list(zip(df['Latitude'], df['Longitude']))
    folium.PolyLine(points, color="blue", weight=2.5, opacity=1).add_to(m)
    
    if not output.endswith('.html'):
        output += '.html'
    
    m.save(output)
    print(f"Carte générée : {output}")