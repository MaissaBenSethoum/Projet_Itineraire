import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

class EKF:

    def __init__(self):

        self.x = np.zeros((4, 1))
        self.dt = 0.04

        # self.P = np.eye(4) * 0.1
        self.P = np.diag([10, 10, 5, 1])

        self.Q = np.diag([0.01, 0.01, 0.5, 0.01])
        self.R = np.diag([9, 9])

        self.H = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0]
        ])

        # Dernière mesure GPS injectée (GPS ~2 Hz, IMU ~26 Hz → même position ~13× sinon)
        # Persisté sur l'instance pour que run_kalman_incremental ne répète pas entre appels
        self.last_gps_lat = None
        self.last_gps_lon = None

        self.UERE = 2.5  # User Equivalent Range Error (m)
        
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

    def miseAJour(self, z, hdop=1.0):
        sigma_gps = self.UERE * hdop / 1.18
        self.R = np.diag([sigma_gps**2, sigma_gps**2])

        H = self.H
        z = z.reshape(2, 1)

        y = z - self.h(self.x)

        S = H @ self.P @ H.T + self.R
        K = self.P @ H.T @ np.linalg.inv(S)

        self.x = self.x + K @ y
        I = np.eye(4)
        IKH = I - K @ H
        self.P = IKH @ self.P @ IKH.T + K @ self.R @ K.T

def lat_lon_to_meters(lat, lon, ref_lat, ref_lon):
      y = (lat - ref_lat) * 111139
      x = (lon - ref_lon) * 111139 * np.cos(np.radians(ref_lat))
      return x, y
def meters_to_lat_lon(x,y,ref_lat, ref_lon):
    lat = ref_lat + y / 111139
    lon = ref_lon + x / (111139 * np.cos(np.radians(ref_lat)))
    return lat, lon

def appliquee_efk(df):
    ref_lat, ref_lon = df['Latitude'].iloc[0], df['Longitude'].iloc[0]
    ekf = EKF()
    ekf.x[0:2] = [[0], [0]]
    results = []
    utcs = []

    for i in range(1, len(df)):
        dt = df['Timestamp'].iloc[i] - df['Timestamp'].iloc[i-1]
        if dt <= 0 or dt > 0.5:
            continue

        accel  = (df['Accel X'].iloc[i] - 1.0) * 9.81
        gyro_z = np.radians(df['Gyro Z'].iloc[i])

        ekf.prediction(accel, gyro_z, dt)

        if pd.notnull(df['Latitude'].iloc[i]) and df['GPS Valid'].iloc[i] == 1:
            mx, my = lat_lon_to_meters(df['Latitude'].iloc[i], df['Longitude'].iloc[i], ref_lat, ref_lon)
            if 'HDOP' in df.columns and pd.notnull(df['HDOP'].iloc[i]):
                hdop = max(0.5, min(float(df['HDOP'].iloc[i]), 50.0))
            else:
                hdop = 1.0
            ekf.miseAJour(np.array([mx, my]), hdop=hdop)

        results.append(ekf.x.flatten().copy())
        if 'UTC' in df.columns:
            utcs.append(df['UTC'].iloc[i])

    return results, ref_lat, ref_lon, utcs


def run_kalman(df):
    raw_results, ref_lat, ref_lon, utcs = appliquee_efk(df)

    df_kalman = pd.DataFrame(raw_results, columns=['X_m', 'Y_m', 'V_ms', 'Theta_rad'])

    lats, lons = [], []
    for i in range(len(df_kalman)):
        lat, lon = meters_to_lat_lon(df_kalman['X_m'].iloc[i], df_kalman['Y_m'].iloc[i], ref_lat, ref_lon)
        lats.append(lat)
        lons.append(lon)

    result = pd.DataFrame({
        'Latitude':  lats,
        'Longitude': lons,
        'Vitesse':   df_kalman['V_ms'].values,
        'Cap':       df_kalman['Theta_rad'].values
    })
    if utcs:
        result['UTC'] = utcs
    return result

