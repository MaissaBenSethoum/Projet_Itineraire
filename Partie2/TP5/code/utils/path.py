from datetime import datetime
from pathlib import Path


def generate_session_name(prefix="acquisition"):
    """
    Génère un nom de session unique basé sur la date et l'heure.

    Parameters
    ----------
    prefix : str
        Préfixe du nom de session.

    Returns
    -------
    str
        Nom de session généré.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}"


def create_acquisition_directory(root_dir="data", prefix="acquisition", subdirs=None):
    """
    Crée un dossier d'acquisition horodaté.

    Parameters
    ----------
    root_dir : str | Path
        Répertoire racine des acquisitions.
    prefix : str
        Préfixe du nom de session.
    subdirs : list[str] | None
        Liste optionnelle de sous-répertoires à créer.

    Returns
    -------
    tuple[Path, dict]
        - le répertoire principal de session
        - un dictionnaire des sous-répertoires créés
    """
    root_dir = Path(root_dir)
    session_name = generate_session_name(prefix=prefix)
    session_dir = root_dir / session_name

    session_dir.mkdir(parents=True, exist_ok=False)

    created_subdirs = {}

    if subdirs is not None:
        for subdir in subdirs:
            subdir_path = session_dir / subdir
            subdir_path.mkdir(parents=True, exist_ok=True)
            created_subdirs[subdir] = subdir_path

    return session_dir, created_subdirs