import argparse
from core.gnss_position import gnss_position
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
    parser.add_argument('--display-LCD', 
                        action='store_true',
                        help="Permet d'afficher la position sur le LCD."
    )
    
    args = parser.parse_args()
    
    gnss_position(mode=GNSS_MODES[args.mode] ,csv_out=args.save_path, display_LCD=args.display_LCD)