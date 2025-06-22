"""Configuración específica para Sura."""

import os
from .base_config import BaseConfig

class SuraConfig(BaseConfig):
    """Configuración específica para Sura."""
    
    # Credenciales (desde .env)
    USUARIO: str = os.getenv('SURA_USUARIO', '')
    CONTRASENA: str = os.getenv('SURA_CONTRASENA', '')
    
    # URLs específicas
    LOGIN_URL: str = 'https://login.sura.com/sso/servicelogin.aspx?continueTo=https%3A%2F%2Fasesores.segurossura.com.co&service=portaluasesores'
    BASE_URL: str = 'https://asesores.segurossura.com.co'
      # Tipo de documento por defecto
    TIPO_DOCUMENTO: str = 'C'  # C = CEDULA
    
