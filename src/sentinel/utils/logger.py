"""
Módulo de logging centralizado para Sentinel.

Uso en cualquier módulo:
    from sentinel.utils.logger import get_logger
    logger = get_logger(__name__)
"""
import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "sentinel.log")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

_FORMATTER = logging.Formatter(
    fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def _setup_root_logger() -> logging.Logger:
    """Configura el logger raíz 'sentinel' una sola vez."""
    root = logging.getLogger("sentinel")
    if root.handlers:
        # Ya inicializado (Streamlit recarga el módulo; evitamos duplicar handlers)
        return root

    root.setLevel(LOG_LEVEL)

    # --- Handler de consola ---
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(_FORMATTER)
    root.addHandler(console_handler)

    # --- Handler de fichero rotativo (5 MB × 3 backups) ---
    os.makedirs(LOG_DIR, exist_ok=True)
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(_FORMATTER)
    root.addHandler(file_handler)

    # Evitar que los mensajes suban al logger raíz de Python (stdout duplicado)
    root.propagate = False

    return root


# Inicializamos al importar el módulo
_setup_root_logger()


def get_logger(name: str) -> logging.Logger:
    """
    Devuelve un logger hijo del logger raíz 'sentinel'.

    Args:
        name: Normalmente __name__ del módulo que llama.
    """
    # Si el nombre ya empieza por 'sentinel', lo usamos directamente;
    # si no (ej. '__main__'), lo colgamos del raíz.
    if not name.startswith("sentinel"):
        name = f"sentinel.{name}"
    return logging.getLogger(name)
