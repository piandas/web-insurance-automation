"""Configuración específica para Sura."""

import os
from .base_config import BaseConfig
from .client_config import ClientConfig

class SuraConfig(BaseConfig):
    """Configuración específica para Sura - Solo configuraciones técnicas."""
    
    # ==========================================
    # CREDENCIALES Y AUTENTICACIÓN
    # ==========================================
    USUARIO: str = os.getenv('SURA_USUARIO', '')
    CONTRASENA: str = os.getenv('SURA_CONTRASENA', '')
    
    # ==========================================
    # URLS Y ENDPOINTS
    # ==========================================
    LOGIN_URL: str = 'https://login.sura.com/sso/servicelogin.aspx?continueTo=https%3A%2F%2Fasesores.segurossura.com.co&service=portaluasesores'
    BASE_URL: str = 'https://asesores.segurossura.com.co'
    
    # ==========================================
    # CONFIGURACIÓN DE LOGIN DEL ASESOR
    # ==========================================
    TIPO_DOCUMENTO_LOGIN: str = ClientConfig.SURA_LOGIN_DOCUMENT_TYPE
    
    # Tipos de documento disponibles para LOGIN del asesor:
    # C = CEDULA DE CIUDADANIA
    # E = CEDULA DE EXTRANJERIA  
    # P = PASAPORTE
    # N = NIT (Para empresas/agencias)
  