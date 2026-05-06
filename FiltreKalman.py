import numpy as np

class EFK:

    # Initialisation
    def __init__(self, dt):

        self.x = np.zeros((4, 1)) # Notre variable d'etat
        self.dt = dt

        self.P = np.eye((4))*0.1

        self.Q = np.diag([0.1,0.1,0.1,0.1]) # Attention ici bruit du modèle à determiner expérimentalement
        self.R = np.diag([3,3]) # Bruit liée au GPS
        self.H = np.array([[1, 0, 0, 0], [0, 1, 0, 0]])

    # Création de F et mise à jour
    def F_jacobienne(self):

        dt = self.dt
        x, y, v, theta = self.x.flatten()

        F = np.eye(4)

        F[0][2] = np.cos(theta) * dt
        F[0][3] = - v * np.sin(theta) * dt
        F[1][2] = np.sin(theta) * dt
        F[1][3] = np.cos(theta) * dt

        return F
    
    # Mise à jour de h avec les valeurs du gps, prend x et y en mètres
    def h(self, x, y):

        h = np.array([x, y]) 

        return h

    # Calcule de la prédiction
    def prediction(self, a, w):

        x, y, v, theta = self.x.flatten()
        dt = self.dt

        # calcule de x(k+1)
        x = x + v * np.cos(theta) * dt
        y = y + v * np.sin(theta) * dt
        v = v + a * dt
        theta = theta + w * dt

        self.x = np.array([x], [y], [v], [theta])

        # Mise à jour de F qui dépend de l'état courant
        F = self.F_jacobienne()

        # Mise à jour de P
        self.P = F @ self.P @ F.T + self.Q

    # Calcule de la mise à jour EKF avec la valeur mesurée z
    def miseAJour(self, z):

        H = self.H
        Z = z.reshape(2,1)

        y =  














