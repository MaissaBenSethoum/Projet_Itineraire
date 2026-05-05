import argparse
from core.gnss_distance import gnss_distance
from config import GNSS_MODES, MODE_GNSS        

if __name__ == "__main__":
    # Instancie le parser
    parser = argparse.ArgumentParser()
    parser.add_argument('latitude', 
                        type=float,
                        help="Latitude du point d'intérêt (en degrés décimaux)")
    parser.add_argument('longitude', 
                        type=float,
                        help="Longitude du point d'intérêt (en degrés décimaux)")

    parser.add_argument(
        "--mode", "-m",
        type=str,
        choices=GNSS_MODES.keys(),
        default=MODE_GNSS,
        help="Mode GNSS à utiliser"
    )
	
    args = parser.parse_args()
    

    gnss_distance((args.latitude,args.longitude),mode=GNSS_MODES[args.mode])

