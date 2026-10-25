# Configuraciones globales
import os
from pathlib import Path

# Rutas
BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"

# Persistencia (evita perder datos al cerrar / en apps empaquetadas)
APP_NAME = "KM_Tickets"


def _default_user_data_dir() -> Path:
    base = os.getenv("LOCALAPPDATA") or os.getenv("APPDATA")
    if base:
        return Path(base) / APP_NAME
    return Path.home() / f".{APP_NAME}"


USER_DATA_DIR = Path(os.getenv("KM_USER_DATA_DIR", "")) if os.getenv("KM_USER_DATA_DIR") else _default_user_data_dir()
DATA_DIR = USER_DATA_DIR / "data"
TICKETS_DIR = USER_DATA_DIR / "tickets"

# Para migrar datos antiguos (cuando se guardaban junto al código)
LEGACY_DATA_DIR = BASE_DIR / "data"

# Configuración UI
TITLE_FONT = ("Arial", 14, "bold")
LABEL_FONT = ("Arial", 10)
ENTRY_FONT = ("Arial", 10)
DEFAULT_TICKET_WIDTH = 80

# Validaciones
ALLOWED_IMAGE_EXTENSIONS = ['.png', '.jpg', '.jpeg']
