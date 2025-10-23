"""Configuración específica para Allianz."""

import os
from .base_config import BaseConfig

class AllianzConfig(BaseConfig):
    """Configuración específica para Allianz - Solo configuraciones técnicas."""
    
    # ==========================================
    # CREDENCIALES Y AUTENTICACIÓN
    # ==========================================
    USUARIO: str = os.getenv('ALLIANZ_USUARIO', '')
    CONTRASENA: str = os.getenv('ALLIANZ_CONTRASENA', '')
    
    # ==========================================
    # URLS Y ENDPOINTS
    # ==========================================
    BASE_URL: str = 'https://www.allia2net.com.co'
    LOGIN_URL: str = BASE_URL + "/ngx-epac/private/home"