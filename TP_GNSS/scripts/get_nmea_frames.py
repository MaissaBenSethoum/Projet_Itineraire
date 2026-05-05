import argparse
from core.gnss_nmea_frames import gnss_nmea_frames
from config import GNSS_MODES, MODE_GNSS
 
if __name__ == "__main__":
    # Instancie le parser
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--mode", "-m",
        type=str,
        choices=GNSS_MODES.keys(),
        default=MODE_GNSS,
        help="Mode GNSS à utiliser"
    )

    parser.add_argument('--save-path', '-s',
                        type=str,
                        default=None,
                        help="Chemin où sauvegarder les données."
    )
	
    args = parser.parse_args()
    
    gnss_nmea_frames(
        mode=GNSS_MODES[args.mode],
        nmea_out=args.save_path
    )
