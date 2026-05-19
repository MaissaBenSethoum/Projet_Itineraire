import csv
import os

class CSVHandler:
    """
    Classe pour la création et l'écriture d'un fichier CSV pour l'enregistrement des données GNSS.
    """
    def __init__(self, file_path):
        """
        Initialise un gestionnaire pour un fichier CSV.
        
        Arguments:
        - file_path: Chemin vers le fichier CSV.
        """
        assert file_path.endswith('.csv'), f"Le nom de fichier de sauvegarde ({file_path}) doit avoir une extension csv"
        self.file_path = file_path

    def create_csv_with_header(self, header):
        """
        Crée un fichier CSV avec un en-tête s'il n'existe pas déjà.
        
        Arguments:
        - header: Liste contenant les noms des colonnes.
        """
        if not os.path.isfile(self.file_path):
            try:
                with open(self.file_path, mode='w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow(header)
            except Exception as e:
                print(f"Erreur lors de la création du fichier CSV : {e}")


    def append_row(self, data):
        """
        Ajoute une ligne de données dans le fichier CSV.
        
        Arguments:
        - data: Liste contenant les valeurs de la ligne à ajouter.
        """
        try:
            with open(self.file_path, mode='a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(data)
        except Exception as e:
            print(f"Erreur lors de l'ajout de la ligne dans le fichier CSV : {e}")