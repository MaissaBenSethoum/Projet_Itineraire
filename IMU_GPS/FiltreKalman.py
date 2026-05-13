import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

class EKF:

    def __init__(self, dt_initial):

        self.x = np.zeros((4, 1))
        self.dt = dt_initial

        self.P = np.eye(4) * 0.1

        self.Q = np.diag([0.1, 0.1, 0.1, 0.1])
        self.R = np.diag([3, 3])

        self.H = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0]
        ])

    def F_jacobienne(self, dt):

        x, y, v , theta = self.x.flatten()

        F = np.eye(4)

        F[0, 2] = np.cos(theta) * dt
        F[0, 3] = -v * np.sin(theta) * dt
        F[1, 2] = np.sin(theta) * dt
        F[1, 3] = v * np.cos(theta) * dt

        return F

    def h(self, x):

        return np.array([[x[0, 0]], [x[1, 0]]])

    def prediction(self, a, w, dt):

        x, y, v, theta = self.x.flatten()

        x = x + v * np.cos(theta) * dt
        y = y + v * np.sin(theta) * dt
        v = v + a * dt
        theta = theta + w * dt

        self.x = np.array([[x], [y], [v], [theta]])

        F = self.F_jacobienne(dt)

        self.P = F @ self.P @ F.T + self.Q

    def miseAJour(self, z):

        H = self.H
        z = z.reshape(2, 1)

        y = z - self.h(self.x)

        S = H @ self.P @ H.T + self.R
        K = self.P @ H.T @ np.linalg.inv(S)

        self.x = self.x + K @ y

        I = np.eye(4)
        self.P = (I - K @ H) @ self.P

def lat_lon_to_meters(lat, lon, ref_lat, ref_lon):
    y = (lat - ref_lat) * 111139
    x = (lon - ref_lon) * 111139 * np.cos(np.radians(ref_lat))
    return x, y

df = pd.read_csv("IMU_GPS/data/test_corrige_2_26_250_26.csv")

ref_lat, ref_lon = df['Latitude'].iloc[0], df['Longitude'].iloc[0]
ekf = EKF(dt_initial=0.04)
ekf.x[0:2] = [[0], [0]]

results = []

for i in range(1, len(df)):

    dt = df['Timestamp'].iloc[i] - df['Timestamp'].iloc[i-1]
    
    #Entrées capteurs (IMU)
    # On prend l'accélération X et le Gyro Z (rotation lacet)
    accel = df['Accel X'].iloc[i] * 9.81
    gyro_z = np.radians(df['Gyro Z'].iloc[i])
    
    #Prédiction
    ekf.prediction(accel, gyro_z, dt)
    
    # Mise à jour si le GPS est valide
    if pd.notnull(df['Latitude'].iloc[i]) and df['GPS Valid'].iloc[i] == 1:
        mx, my = lat_lon_to_meters(df['Latitude'].iloc[i], df['Longitude'].iloc[i], ref_lat, ref_lon)
        ekf.miseAJour(np.array([mx, my]))
    
    results.append(ekf.x.flatten())

# Conversion des résultats en DataFrame pour analyse
res_df = pd.DataFrame(results, columns=['X_m', 'Y_m', 'V_ms', 'Theta_rad'])

raw_gps_x = []
raw_gps_y = []
for i in range(len(df)):
    mx, my = lat_lon_to_meters(df['Latitude'].iloc[i], df['Longitude'].iloc[i], ref_lat, ref_lon)
    raw_gps_x.append(mx)
    raw_gps_y.append(my)

plt.figure(figsize=(10, 6))
plt.plot(raw_gps_x, raw_gps_y, 'r--', alpha=0.5, label="GPS Brut (Bruité)")
plt.plot(res_df['X_m'], res_df['Y_m'], 'b-', label="Trajectoire Filtrée (EKF)")
plt.legend()
plt.title("Comparaison GPS Brut vs Filtre de Kalman")
plt.xlabel("X (mètres)")
plt.ylabel("Y (mètres)")
plt.grid(True)
plt.show()



