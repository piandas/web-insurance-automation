"""Configuración base común para todas las aseguradoras."""

import os
from dotenv import load_dotenv
from typing import Optional

# Cargar variables de entorno
load_dotenv()

class BaseConfig:
    """Configuración base compartida por todas las aseguradoras."""
    
    # Configuraciones generales desde .env
    HEADLESS: bool = os.getenv('HEADLESS', 'False').lower() == 'true'
    MINIMIZED: bool = os.getenv('MINIMIZED', 'True').lower() == 'true'
    TIMEOUT: int = int(os.getenv('TIMEOUT', '30000'))
    
    # Directorio base del proyecto (subir 4 niveles: config -> src -> Varios -> raíz)
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    # Directorios
    DOWNLOADS_DIR: str = os.path.join(BASE_DIR, 'Descargas')
    LOGS_DIR: str = os.path.join(BASE_DIR, 'Varios', 'LOGS')
    
    @classmethod
    def get_company_config(cls, company: str) -> dict:
        """Obtiene configuración específica por compañía."""
        configs = {
            'allianz': {
                'usuario': os.getenv('ALLIANZ_USUARIO', ''),
                'contrasena': os.getenv('ALLIANZ_CONTRASENA', ''),
                'base_url': os.getenv('ALLIANZ_BASE_URL', ''),
                'downloads_dir': os.path.join(cls.DOWNLOADS_DIR, 'allianz'),
                'logs_dir': os.path.join(cls.LOGS_DIR, 'allianz')
            },
            'sura': {
                'usuario': os.getenv('SURA_USUARIO', ''),
                'contrasena': os.getenv('SURA_CONTRASENA', ''),
                'base_url': os.getenv('SURA_BASE_URL', ''),
                'downloads_dir': os.path.join(cls.DOWNLOADS_DIR, 'sura'),
                'logs_dir': os.path.join(cls.LOGS_DIR, 'sura')
            }
        }
        
        return configs.get(company.lower(), {})
