import numpy as np

class EFK:

    def __init__(self, dt):

        self.x = np.zeros((4, 1))
        self.dt = dt

        self.P = np.eye(4) * 0.1

        self.Q = np.diag([0.1, 0.1, 0.1, 0.1])
        self.R = np.diag([3, 3])

        self.H = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0]
        ])

    def F_jacobienne(self):

        dt = self.dt
        x, y, v, theta = self.x.flatten()

        F = np.eye(4)

        F[0, 2] = np.cos(theta) * dt
        F[0, 3] = -v * np.sin(theta) * dt
        F[1, 2] = np.sin(theta) * dt
        F[1, 3] = v * np.cos(theta) * dt

        return F

    def h(self, x):

        return np.array([[x[0, 0]], [x[1, 0]]])

    def prediction(self, a, w):

        x, y, v, theta = self.x.flatten()
        dt = self.dt

        x = x + v * np.cos(theta) * dt
        y = y + v * np.sin(theta) * dt
        v = v + a * dt
        theta = theta + w * dt

        self.x = np.array([[x], [y], [v], [theta]])

        F = self.F_jacobienne()

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