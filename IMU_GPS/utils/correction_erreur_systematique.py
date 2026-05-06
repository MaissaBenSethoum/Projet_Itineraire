import numpy as np
import pandas as pd
import argparse


def  calul_moyenne_colonne(df, col):
    """"fonction qui permet de calculer la moyenne d'une colonne d'un dataframe"""
    return df[col].mean()

def calcul_ecart_type_colonne(df, col):
    """"fonction qui permet de calculer l'écart type d'une colonne d'un dataframe"""
    return df[col].std()

def calcul_ecart_type(df):
    """"fonction qui permet de calculer l'écart type de toutes les colonnes d'un dataframe"""
    ecart_type = {}
    for col in df.columns:
        ecart_type[col] = df[col].std()
    return ecart_type
def correction_syst_all(df,erreur_syst):
    """"fonction qui permet de corriger l'erreur systématique de toutes les colonnes d'un dataframe en soustrayant la moyenne de chaque colonne à chaque valeur de chaque colonne"""
    for col in df.columns:
        df[col] = df[col] - erreur_syst
    return df
def correction_syst_col(df, col, erreur_syst):
    """"fonction qui permet de corriger l'erreur systématique d'une colonne d'un dataframe en soustrayant la moyenne de la colonne à chaque valeur de la colonne"""
    df[col] = df[col] - erreur_syst
    return df

def transformation_csv_dataframe(file_path):
    """"fonction qui permet de transformer un fichier csv en dataframe pandas"""
    df = pd.read_csv(file_path)
    return df
def transformation_dataframe_csv(df, file_path):
    """"fonction qui permet de transformer un dataframe pandas en fichier csv"""
    df.to_csv(file_path, index=False)

if __name__ == "__main__":
  arg = argparse.ArgumentParser(description="Correction de l'erreur systématique d'un fichier csv")
  arg.add_argument("file_path", type=str, help="Chemin du fichier csv à corriger")
  arg.add_argument("-o", "--output", type=str, help="Chemin du fichier csv de sortie (optionnel)")
  args = arg.parse_args()
  df = transformation_csv_dataframe(args.file_path)
  
  for i in range(7, len(df.columns)):
    print(f"La moyenne de la colonne {df.columns[i]} est : {calul_moyenne_colonne(df, df.columns[i])}")
  for i in range(7, len(df.columns)):
    print(f"L'écart type de la colonne {df.columns[i]} est : {calcul_ecart_type_colonne(df, df.columns[i])}")
