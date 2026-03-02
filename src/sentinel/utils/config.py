import os
from pathlib import Path
from dotenv import load_dotenv

# Buscamos el .env en la raíz del proyecto (subiendo dos niveles desde sentinel/utils)
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
env_path = BASE_DIR / ".env"

if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    print(f"⚠️ Advertencia: No se encontró el archivo .env en {env_path}")