import argparse
import pandas as pd
import folium
import os

def plot_GNSS(df1, df2, output):
    """
    Trace les données GNSS de deux DataFrames sur une carte OpenStreetMap.
    Arguments:
    - df1    : Premier DataFrame contenant les colonnes 'Latitude' et 'Longitude'
    - df2    : Deuxième DataFrame contenant les colonnes 'Latitude' et 'Longitude'
    - output : Chemin du fichier HTML de sortie
    """
    # Centrer la carte sur le premier point du premier trajet
    m = folium.Map(location=[df1['Latitude'].iloc[0], df1['Longitude'].iloc[0]], zoom_start=12)

    configs = [
        (df1, "blue",  "Itinéraire 1"),
        (df2, "red",   "Itinéraire 2"),
    ]
    # configs = [
    #     (df1, "blue",  "Itinéraire 1")
    # ]

    for df, color, label in configs:
        points = list(zip(df['Latitude'], df['Longitude']))
        folium.PolyLine(points, color=color, weight=2.5, opacity=1, tooltip=label).add_to(m)
        folium.Marker(
            location=points[0],
            tooltip=f"{label} — Départ",
            icon=folium.Icon(color=color, icon="play", prefix="fa")
        ).add_to(m)

        folium.Marker(
            location=points[-1],
            tooltip=f"{label} — Arrivée",
            icon=folium.Icon(color=color, icon="flag-checkered", prefix="fa")
        ).add_to(m)

    if not output.endswith('.html'):
        output += '.html'

    m.save(output)
    print(f"Carte générée : {output}")