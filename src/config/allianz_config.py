"""Configuración específica para Allianz."""

import os
from .base_config import BaseConfig

class AllianzConfig(BaseConfig):
    """Configuración específica para Allianz."""    # Credenciales (desde .env)
    USUARIO: str = os.getenv('ALLIANZ_USUARIO', '')
    CONTRASENA: str = os.getenv('ALLIANZ_CONTRASENA', '')
    
    # URL base (configuración fija)
    BASE_URL: str = 'https://www.allia2net.com.co'
    # URLs específicas
    LOGIN_URL: str = BASE_URL + "/ngx-epac/private/home"
    
    # Configuraciones específicas de Allianz (valores por defecto)
    POLICY_NUMBER: str = '23541048'
    RAMO_SEGURO: str = 'Livianos Particulares'
    TIPO_DOCUMENTO: str = 'CEDULA_CIUDADANIA'
    NUMERO_DOCUMENTO: str = '1026258710'
    
    # Configuraciones de placa
    PLACA_VEHICULO: str = 'IOS190'
    FECHA_NACIMIENTO: str = '01/06/1989'
    GENERO_ASEGURADO: str = 'M'
    DEPARTAMENTO: str = 'ANTIOQUIA'
    CIUDAD: str = 'BELLO'
