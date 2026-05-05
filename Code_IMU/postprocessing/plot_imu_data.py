import pandas as pd
import matplotlib.pyplot as plt
import argparse

def plot_imu_data(csv_file):
    """
    Lit un fichier CSV contenant les données de l'accéléromètre et du gyroscope,
    et trace les courbes en fonction du temps.
    
    Arguments:
    - csv_file: Chemin du fichier CSV.
    """
    try:
        # Lire les données du fichier CSV
        data = pd.read_csv(csv_file)
        
        # Vérifier si le fichier contient les colonnes nécessaires
        required_columns = ['Timestamp', 'Accel X', 'Accel Y', 'Accel Z', 'Gyro X', 'Gyro Y', 'Gyro Z']
        if not all(col in data.columns for col in required_columns):
            raise ValueError(f"Le fichier CSV doit contenir les colonnes suivantes : {required_columns}")
        
        # Convertir les timestamps en secondes par rapport au premier échantillon
        data['Timestamp'] -= data['Timestamp'].iloc[0]

        # Tracer les courbes de l'accéléromètre
        plt.figure(figsize=(12, 6))
        plt.subplot(2, 1, 1)
        plt.plot(data['Timestamp'], data['Accel X'], label='Accel X (g)', color='r')
        plt.plot(data['Timestamp'], data['Accel Y'], label='Accel Y (g)', color='g')
        plt.plot(data['Timestamp'], data['Accel Z'], label='Accel Z (g)', color='b')
        plt.title('Données de l\'accéléromètre')
        plt.xlabel('Temps (s)')
        plt.ylabel('Accélération (g)')
        plt.legend()
        plt.grid()

        # Tracer les courbes du gyroscope
        plt.subplot(2, 1, 2)
        plt.plot(data['Timestamp'], data['Gyro X'], label='Gyro X (dps)', color='r')
        plt.plot(data['Timestamp'], data['Gyro Y'], label='Gyro Y (dps)', color='g')
        plt.plot(data['Timestamp'], data['Gyro Z'], label='Gyro Z (dps)', color='b')
        plt.title('Données du gyroscope')
        plt.xlabel('Temps (s)')
        plt.ylabel('Vitesse angulaire (dps)')
        plt.legend()
        plt.grid()

        # Ajuster l'espacement entre les graphes
        plt.tight_layout()
        plt.savefig(csv_file.replace(".csv", "_imu.png"), dpi=300)
        plt.close()
    
    except FileNotFoundError:
        print(f"Le fichier {csv_file} n'existe pas.")
    except ValueError as e:
        print(e)

# Exemple d'utilisation
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('path', type=str)
    args = parser.parse_args()
    plot_imu_data(args.path)
