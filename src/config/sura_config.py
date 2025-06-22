"""Configuración específica para Sura."""

import os
from .base_config import BaseConfig

class SuraConfig(BaseConfig):
    """Configuración específica para Sura."""
      # Credenciales (desde .env)
    USUARIO: str = os.getenv('SURA_USUARIO', '')
    CONTRASENA: str = os.getenv('SURA_CONTRASENA', '')
    
    # URL base (configuración fija)
    BASE_URL: str = 'https://www.sura.com'
      # Configuraciones específicas de Sura (valores por defecto)
    POLICY_NUMBER: str = '12345678'
    RAMO_SEGURO: str = 'Automóviles'
    TIPO_DOCUMENTO: str = 'CEDULA_CIUDADANIA'
    NUMERO_DOCUMENTO: str = '1234567890'
    
    # Configuraciones de vehículo
    PLACA_VEHICULO: str = 'ABC123'
    FECHA_NACIMIENTO: str = '01/01/1990'
    GENERO_ASEGURADO: str = 'M'
    DEPARTAMENTO: str = 'BOGOTA D.C.'
    CIUDAD: str = 'BOGOTA'
    
    # URLs específicas (por definir cuando se implemente)
    LOGIN_URL: str = BASE_URL + "/login"  # URL de ejemplo
