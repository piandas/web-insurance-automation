# config.py
# Configuración global del proyecto
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    USUARIO: str = os.getenv('USUARIO', '')
    CONTRASENA: str = os.getenv('CONTRASENA', '')
    HEADLESS: bool = os.getenv('HEADLESS', 'False').lower() == 'true'
    # Puedes agregar más parámetros globales aquí
    BASE_URL: str = os.getenv('BASE_URL', 'https://www.allia2net.com.co')
    TIMEOUT: int = int(os.getenv('TIMEOUT', '30000'))
