# PI Itinéraire

Système embarqué sur Raspberry Pi pour l'acquisition, le filtrage et la visualisation en temps réel d'un itinéraire GPS, fusionné avec des données IMU (accéléromètre, gyroscope, magnétomètre) via un filtre de Kalman étendu (EKF). La Partie 2 ajoute une caméra avec déclenchement par geste pour la capture de photos géolocalisées.

---

## Matériel requis

| Composant | Référence | Interface |
|---|---|---|
| Microcontrôleur | Raspberry Pi 4 (ou 3B+) | — |
| IMU | LSM6DSO (accél. + gyro) | I2C `0x6B` |
| Magnétomètre | LIS3MDL | I2C `0x1E` |
| Module GNSS | Waveshare GPS/GNSS HAT | I2C `0x20` |
| Caméra | Raspberry Pi Camera Module 3 | CSI |
| Bouton | Poussoir | GPIO 21 |
| LED | LED indicatrice | GPIO 13 |

---

## Structure du projet

```
pi_itineraire/
├── IMU_GPS/                    # Partie 1 — acquisition IMU + GNSS uniquement
│   ├── config/                 # Constantes et paramètres
│   ├── core/                   # Acquisition et prétraitement
│   ├── sensors/                # Pilotes bas niveau (IMU, GNSS)
│   ├── scripts/                # Points d'entrée
│   ├── postprocessing/         # Notebooks d'analyse et visualisation
│   └── data/                   # CSV acquis (ignorés par git)
│
├── Partie2/IMU_GPS_CAM/code/   # Partie 2 — IMU + GNSS + Caméra + Serveur Flask
│   ├── config/                 # Constantes et paramètres (dont caméra)
│   ├── core/                   # Acquisition, prétraitement, affichage
│   ├── sensors/                # Pilotes (IMU, GNSS, Caméra)
│   ├── scripts/                # Points d'entrée
│   ├── servers/                # Serveur Flask + template carte Leaflet
│   ├── utils/                  # Filtre de Kalman, correction biais, LED, Bouton…
│   ├── data/                   # CSV acquis (ignorés par git)
│   └── images/                 # Photos géolocalisées (ignorées par git)
│
└── Strava/                     # Traces GPX de référence pour comparaison
```

---

## Installation

### 1. Cloner le dépôt

```bash
git clone https://gitlab.insa-rouen.fr/mbarry01/pi_itineraire.git
cd pi_itineraire
```

### 2. Installer les dépendances Python

```bash
pip install flask pandas numpy opencv-python mediapipe picamera2 smbus2 folium
```

> Sur Raspberry Pi, `smbus2` et `picamera2` sont généralement pré-installés avec Raspberry Pi OS.

### 3. Activer l'I2C et la caméra

```bash
sudo raspi-config
# Interface Options → I2C → Enable
# Interface Options → Camera → Enable
sudo reboot
```

---

## Utilisation

### Partie 1 — Acquisition IMU + GNSS seule

#### Acquisition

```bash
cd IMU_GPS/scripts
python get_imu_gps_button.py
```

Appuyez sur le bouton pour démarrer / arrêter l'acquisition. Les données sont sauvegardées dans `data/`.

#### Conversion GPX ↔ CSV

Le script `IMU_GPS/utils/conversion_gpx.py` convertit des traces GPX (Strava, etc.) en CSV exploitable, et inversement. La détection du sens est automatique selon l'extension du fichier d'entrée.

```bash
cd IMU_GPS/utils

# GPX → CSV (extrait UTC, Latitude, Longitude)
python conversion_gpx.py <trace.gpx> <sortie.csv>

# CSV → GPX
python conversion_gpx.py <donnees.csv> <sortie.gpx>
```

Le CSV produit contient trois colonnes : `UTC`, `Latitude`, `Longitude`. Le format UTC est `YYYY/MM/DD - HH:MM:SS`.

#### Traçage de la carte

Le script `IMU_GPS/scripts/main.py` génère une carte HTML interactive (Folium / OpenStreetMap) comparant la trajectoire acquise, la trajectoire filtrée par l'EKF et la trace Strava de référence.

**Mode `run` — pipeline complet (correction biais → Kalman → carte) :**

```bash
cd IMU_GPS/scripts
python main.py --mode run <acquisition.csv> --savepath_strava <strava.csv> <carte_sortie.html>
```

**Mode `apk` — applique uniquement le filtre de Kalman sur un CSV déjà traité :**

```bash
python main.py --mode apk <traite.csv> <kalman_sortie.csv>
```

La carte HTML générée superpose trois tracés :

| Couleur | Données |
|---|---|
| Bleu | Trajectoire filtrée Kalman |
| Rouge | Référence Strava |
| Vert | GPS brut |

Ouvrir le fichier `.html` directement dans un navigateur pour visualiser la carte.

### Partie 2 — Acquisition IMU + GNSS + Caméra avec déclenchement par geste

```bash
cd Partie2/IMU_GPS_CAM/code/scripts
python get_imu_gps_cam.py [--show-stream] [--size WIDTH HEIGHT]
```

- Appui bouton pour démarrer, puis signe **Victory (✌)** devant la caméra pour prendre une photo géolocalisée.
- Appui bouton une seconde fois pour arrêter proprement.

### Serveur Flask — Visualisation temps réel sur carte

```bash
cd Partie2/IMU_GPS_CAM/code/servers
python flask_server.py
```

Ouvrir `http://<ip_du_raspberry>:5000` dans un navigateur. La carte se met à jour en temps réel avec la position filtrée par l'EKF.

---

## Algorithme de fusion — Filtre de Kalman Étendu (EKF)

L'EKF fusionne les données IMU (accélération, vitesse angulaire) et GNSS (latitude, longitude). L'état est `[x, y, v, θ]` (position en mètres, vitesse, cap).

- **Prédiction** : modèle cinématique à partir de l'IMU à ~26 Hz
- **Mise à jour** : correction GPS à ~2 Hz, pondérée par le HDOP
- La fonction `run_kalman_incremental` permet un traitement en ligne (mode Flask)

---

## Paramètres de configuration

Modifier `config/parameters.py` pour ajuster :

| Paramètre | Défaut | Description |
|---|---|---|
| `ACCEL_RANGE` | `2` | Plage accéléromètre (g) |
| `ACCEL_FREQ` | `26` | Fréquence accéléromètre (Hz) |
| `GYRO_RANGE` | `250` | Plage gyroscope (°/s) |
| `GYRO_FREQ` | `26` | Fréquence gyroscope (Hz) |
| `MODE_GNSS` | `'gps_beidou_glonass'` | Constellations activées |
| `CAMERA_RESOLUTION` | `(1280, 720)` | Résolution caméra |
| `CAMERA_FRAMERATE` | `15` | Images par seconde |

---

## Auteur

ISIA3  — INSA Rouen Normandie